"""Tests for ConnectProvider.fetch_page."""

import json
from typing import Any
from unittest.mock import patch

from app_reviews.providers.appstore.official import ConnectProvider
from app_reviews.utils.http import HttpResponse


def _connect_entry(
    review_id: str = "abc-111",
    rating: int = 5,
    title: str = "Great app",
    body: str = "Love it",
    author: str = "Alice",
    territory: str = "USA",
    created: str = "2024-03-15T10:00:00Z",
) -> dict[str, Any]:
    return {
        "type": "customerReviews",
        "id": review_id,
        "attributes": {
            "rating": rating,
            "title": title,
            "body": body,
            "reviewerNickname": author,
            "createdDate": created,
            "territory": territory,
        },
    }


def _connect_response(
    entries: list[dict[str, Any]],
    next_url: str | None = None,
    status_code: int = 200,
) -> HttpResponse:
    body: dict[str, Any] = {"data": entries}
    if next_url:
        body["links"] = {"next": next_url}
    return HttpResponse(status=status_code, body=json.dumps(body))


class TestConnectProviderCountries:
    def test_returns_single_empty_string(self):
        """Connect API is global — always one call regardless of requested countries."""
        provider = ConnectProvider("Bearer fake")
        assert provider.countries(["us", "gb", "de"]) == [""]

    def test_returns_single_empty_string_for_empty_list(self):
        provider = ConnectProvider("Bearer fake")
        assert provider.countries([]) == [""]


class TestConnectProviderFetchPage:
    @patch("app_reviews.providers.appstore.official.http_get")
    def test_first_page_uses_base_url(self, mock_get):
        mock_get.return_value = _connect_response([])
        provider = ConnectProvider("Bearer fake")
        provider.fetch_page("55555", "", cursor=None)
        url = mock_get.call_args[0][0]
        assert "55555" in url
        assert "customerReviews" in url

    @patch("app_reviews.providers.appstore.official.http_get")
    def test_cursor_used_as_url(self, mock_get):
        next_url = "https://api.appstoreconnect.apple.com/v1/next"
        mock_get.return_value = _connect_response([])
        provider = ConnectProvider("Bearer fake")
        provider.fetch_page("55555", "", cursor=next_url)
        url = mock_get.call_args[0][0]
        assert url == next_url

    @patch("app_reviews.providers.appstore.official.http_get")
    def test_returns_normalized_reviews(self, mock_get):
        entry = _connect_entry(
            review_id="xyz-789",
            rating=4,
            title="Pretty good",
            body="Works well",
            author="Charlie",
            territory="GBR",
        )
        mock_get.return_value = _connect_response([entry])
        provider = ConnectProvider("Bearer fake")
        page = provider.fetch_page("55555", "", cursor=None)
        assert page.error is None
        assert len(page.reviews) == 1
        r = page.reviews[0]
        assert r.app_id == "55555"
        assert r.country == "GBR"
        assert r.rating == 4
        assert r.source == "appstore_official"
        assert r.id == "appstore_official-xyz-789"

    @patch("app_reviews.providers.appstore.official.http_get")
    def test_next_cursor_is_next_url(self, mock_get):
        next_url = "https://api.appstoreconnect.apple.com/v1/next"
        mock_get.return_value = _connect_response([_connect_entry()], next_url=next_url)
        provider = ConnectProvider("Bearer fake")
        page = provider.fetch_page("12345", "", cursor=None)
        assert page.next_cursor == next_url

    @patch("app_reviews.providers.appstore.official.http_get")
    def test_no_next_link_means_no_cursor(self, mock_get):
        mock_get.return_value = _connect_response([_connect_entry()])
        provider = ConnectProvider("Bearer fake")
        page = provider.fetch_page("12345", "", cursor=None)
        assert page.next_cursor is None

    @patch("app_reviews.providers.appstore.official.http_get")
    def test_auth_header_sent(self, mock_get):
        captured: dict[str, str] = {}

        def side_effect(url, **kwargs):
            captured.update(kwargs.get("headers", {}))
            return _connect_response([])

        mock_get.side_effect = side_effect
        ConnectProvider("Bearer my-jwt").fetch_page("12345", "", cursor=None)
        assert captured["Authorization"] == "Bearer my-jwt"

    @patch("app_reviews.providers.appstore.official.http_get")
    def test_http_error_returns_fetch_error(self, mock_get):
        mock_get.return_value = HttpResponse(status=401, body="Unauthorized")
        page = ConnectProvider("Bearer bad").fetch_page("12345", "", cursor=None)
        assert page.reviews == []
        assert page.error is not None

    @patch("app_reviews.providers.appstore.official.http_get")
    def test_url_error_returns_fetch_error(self, mock_get):
        import urllib.error

        mock_get.side_effect = urllib.error.URLError("refused")
        page = ConnectProvider("Bearer fake").fetch_page("12345", "", cursor=None)
        assert page.error is not None

    @patch("app_reviews.providers.appstore.official.http_get")
    def test_empty_response_no_error(self, mock_get):
        mock_get.return_value = _connect_response([])
        page = ConnectProvider("Bearer fake").fetch_page("12345", "", cursor=None)
        assert page.reviews == []
        assert page.error is None
        assert page.next_cursor is None
