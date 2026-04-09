"""Tests for GooglePlaySearch."""

import json
from typing import Any
from unittest.mock import patch

import pytest

from app_reviews.clients.googleplay_search import (
    GooglePlaySearch,
    _extract_datasets,
    _parse_detail_html,
    _parse_search_html,
)
from app_reviews.errors import HttpError
from app_reviews.models.metadata import AppMetadata
from app_reviews.utils.http import HttpResponse

# ---------------------------------------------------------------------------
# Search fixtures
# ---------------------------------------------------------------------------

# Each search entry is [app_data] where app_data holds fields at known indices.
_APP_DATA_1: list[Any] = [
    ["com.whatsapp", 7],  # [0]: [app_id, type]
    [  # [1]: icon at [1][3][2]
        None,
        2,
        [512, 512],
        [None, None, "https://play-lh.googleusercontent.com/icon1.png"],
    ],
    None,  # [2]
    "WhatsApp Messenger",  # [3]: name
    [None, 4.7],  # [4]: rating at [4][1]
    "Communication",  # [5]: genre
    None,
    None,  # [6], [7]
    [None, [None, [0, "USD"]]],  # [8]: price at [8][1][0][0]=0 (free)
    None,
    None,
    None,
    None,
    None,  # [9]-[13]
    "WhatsApp LLC",  # [14]: developer
]

_APP_DATA_2: list[Any] = [
    ["com.whatsapp.w4b", 7],
    [
        None,
        2,
        [512, 512],
        [None, None, "https://play-lh.googleusercontent.com/icon2.png"],
    ],
    None,
    "WhatsApp Business",
    [None, 4.5],
    "Communication",
    None,
    None,
    [None, [None, [0, "USD"]]],
    None,
    None,
    None,
    None,
    None,
    "WhatsApp LLC",
]

_ENTRY_1 = [_APP_DATA_1]
_ENTRY_2 = [_APP_DATA_2]

# section[22] = [group]; group = [entry1, entry2]
_search_section: list[Any] = [None] * 22 + [[[_ENTRY_1, _ENTRY_2]]]

# ds:4[0][1] = sections list
_SEARCH_DS4: list[Any] = [[None, [None, _search_section]]]

_SEARCH_HTML = (
    "<html><body>"
    "<script>AF_initDataCallback({key: 'ds:4', hash: '4', "
    "data:" + json.dumps(_SEARCH_DS4) + ", "
    "sideChannel: {}});</script>"
    "</body></html>"
)

_empty_section: list[Any] = [None] * 22 + [[]]
_SEARCH_EMPTY_DS4: list[Any] = [[None, [None, _empty_section]]]
_SEARCH_EMPTY_HTML = (
    "<html><body>"
    "<script>AF_initDataCallback({key: 'ds:4', hash: '4', "
    "data:" + json.dumps(_SEARCH_EMPTY_DS4) + ", "
    "sideChannel: {}});</script>"
    "</body></html>"
)

# ---------------------------------------------------------------------------
# Lookup fixtures
# ---------------------------------------------------------------------------


def _build_detail_base() -> list[Any]:
    """Build mock detail data (ds:5[1][2]) with known field values."""
    base: list[Any] = [None] * 141
    base[0] = ["WhatsApp Messenger"]  # name at [0][0]
    base[51] = [[None, 4.7], None, [None, 232000]]  # rating, count
    base[57] = [[[[[None, [[0, "USD"]]]]]]]  # price (free)
    base[68] = ["WhatsApp LLC"]  # developer at [68][0]
    base[79] = [[["Communication", None, "COMMUNICATION"]]]  # genre
    base[95] = [  # icon at [95][0][3][2]
        [
            None,
            None,
            None,
            [None, None, "https://play-lh.googleusercontent.com/icon1.png"],
        ]
    ]
    base[140] = [[["2.24.1"]]]  # version at [140][0][0][0]
    return base


_DETAIL_DS5: list[Any] = [None, [None, None, _build_detail_base()]]

_LOOKUP_HTML = (
    "<html><body>"
    "<script>AF_initDataCallback({key: 'ds:5', hash: '5', "
    "data:" + json.dumps(_DETAIL_DS5) + ", "
    "sideChannel: {}});</script>"
    "</body></html>"
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGooglePlaySearchConstruction:
    def test_default(self) -> None:
        client = GooglePlaySearch()
        assert client is not None

    def test_with_proxy(self) -> None:
        client = GooglePlaySearch(proxy="http://proxy:8080")
        assert client._proxy == "http://proxy:8080"


class TestExtractDatasets:
    def test_extracts_keyed_datasets(self) -> None:
        datasets = _extract_datasets(_SEARCH_HTML)
        assert "ds:4" in datasets

    def test_multiple_datasets(self) -> None:
        html = (
            "<html><body>"
            "<script>AF_initDataCallback({key: 'ds:3', "
            "data:[1], sideChannel: {}});</script>"
            "<script>AF_initDataCallback({key: 'ds:5', "
            "data:[2], sideChannel: {}});</script>"
            "</body></html>"
        )
        datasets = _extract_datasets(html)
        assert datasets == {"ds:3": [1], "ds:5": [2]}

    def test_no_callbacks_returns_empty(self) -> None:
        assert _extract_datasets("<html><body>no data</body></html>") == {}

    def test_malformed_json_skipped(self) -> None:
        html = (
            "<script>AF_initDataCallback({key: 'ds:0', "
            "data:INVALID, sideChannel: {}});</script>"
        )
        assert _extract_datasets(html) == {}


class TestParseSearchHtml:
    def test_no_af_callback_returns_empty(self) -> None:
        assert _parse_search_html("<html><body>no data</body></html>") == []

    def test_wrong_data_shape_returns_empty(self) -> None:
        html = (
            "<script>AF_initDataCallback({key: 'ds:0', "
            "data:[1,2,3], sideChannel: {}})</script>"
        )
        assert _parse_search_html(html) == []

    def test_deduplicates_by_app_id(self) -> None:
        dup_section: list[Any] = [None] * 22 + [[[_ENTRY_1], [_ENTRY_1]]]
        ds4: list[Any] = [[None, [None, dup_section]]]
        html = (
            "<html><body>"
            "<script>AF_initDataCallback({key: 'ds:4', hash: '4', "
            "data:" + json.dumps(ds4) + ", "
            "sideChannel: {}});</script>"
            "</body></html>"
        )
        results = _parse_search_html(html)
        assert len(results) == 1
        assert results[0].app_id == "com.whatsapp"


class TestParseDetailHtml:
    def test_parses_all_fields(self) -> None:
        result = _parse_detail_html("com.whatsapp", _LOOKUP_HTML)
        assert result.app_id == "com.whatsapp"
        assert result.name == "WhatsApp Messenger"
        assert result.developer == "WhatsApp LLC"
        assert result.category == "Communication"
        assert result.rating == 4.7
        assert result.rating_count == 232000
        assert result.version == "2.24.1"
        assert result.price == "Free"

    def test_no_datasets_returns_fallback(self) -> None:
        result = _parse_detail_html("com.test", "<html>no data</html>")
        assert result.name == "Unknown"
        assert result.rating == 0.0


class TestGooglePlaySearchSearch:
    @patch("app_reviews.clients.googleplay_search.http_get")
    def test_returns_list_of_app_metadata(self, mock_get):  # type: ignore[no-untyped-def]
        mock_get.return_value = HttpResponse(status=200, body=_SEARCH_HTML)
        results = GooglePlaySearch().search("whatsapp")
        assert len(results) == 2
        assert all(isinstance(r, AppMetadata) for r in results)

    @patch("app_reviews.clients.googleplay_search.http_get")
    def test_maps_fields_correctly(self, mock_get):  # type: ignore[no-untyped-def]
        mock_get.return_value = HttpResponse(status=200, body=_SEARCH_HTML)
        results = GooglePlaySearch().search("whatsapp")
        app = results[0]
        assert app.app_id == "com.whatsapp"
        assert app.store == "googleplay"
        assert app.name == "WhatsApp Messenger"
        assert app.developer == "WhatsApp LLC"
        assert app.category == "Communication"
        assert app.price == "Free"
        assert app.rating == 4.7
        assert app.icon_url == "https://play-lh.googleusercontent.com/icon1.png"
        assert app.url == "https://play.google.com/store/apps/details?id=com.whatsapp"

    @patch("app_reviews.clients.googleplay_search.http_get")
    def test_empty_results_returns_empty_list(self, mock_get):  # type: ignore[no-untyped-def]
        mock_get.return_value = HttpResponse(status=200, body=_SEARCH_EMPTY_HTML)
        results = GooglePlaySearch().search("xyznonexistent")
        assert results == []

    @patch("app_reviews.clients.googleplay_search.http_get")
    def test_http_error_raises(self, mock_get):  # type: ignore[no-untyped-def]
        mock_get.return_value = HttpResponse(status=503, body="error")
        with pytest.raises(HttpError):
            GooglePlaySearch().search("whatsapp")

    @patch("app_reviews.clients.googleplay_search.http_get")
    def test_limit_is_applied(self, mock_get):  # type: ignore[no-untyped-def]
        mock_get.return_value = HttpResponse(status=200, body=_SEARCH_HTML)
        results = GooglePlaySearch().search("whatsapp", limit=1)
        assert len(results) == 1


class TestGooglePlaySearchLookup:
    @patch("app_reviews.clients.googleplay_search.http_get")
    def test_returns_app_metadata(self, mock_get):  # type: ignore[no-untyped-def]
        mock_get.return_value = HttpResponse(status=200, body=_LOOKUP_HTML)
        result = GooglePlaySearch().lookup("com.whatsapp")
        assert isinstance(result, AppMetadata)
        assert result.app_id == "com.whatsapp"
        assert result.name == "WhatsApp Messenger"
        assert result.developer == "WhatsApp LLC"
        assert result.category == "Communication"
        assert result.rating == 4.7
        assert result.rating_count == 232000
        assert result.version == "2.24.1"
        assert result.price == "Free"
        assert result.store == "googleplay"
        assert result.icon_url == "https://play-lh.googleusercontent.com/icon1.png"

    @patch("app_reviews.clients.googleplay_search.http_get")
    def test_not_found_returns_none(self, mock_get):  # type: ignore[no-untyped-def]
        mock_get.return_value = HttpResponse(status=404, body="Not Found")
        result = GooglePlaySearch().lookup("com.nonexistent.app")
        assert result is None

    @patch("app_reviews.clients.googleplay_search.http_get")
    def test_http_error_raises(self, mock_get):  # type: ignore[no-untyped-def]
        mock_get.return_value = HttpResponse(status=503, body="error")
        with pytest.raises(HttpError):
            GooglePlaySearch().lookup("com.whatsapp")
