"""Tests for GoogleDeveloperApiProvider.fetch_page."""

import json
from typing import Any
from unittest.mock import patch

from app_reviews.providers.googleplay.official import GoogleDeveloperApiProvider
from app_reviews.utils.http import HttpResponse


def _gplay_entry(
    review_id: str = "rev-001",
    rating: int = 4,
    body: str = "Works great",
    author: str = "Bob",
    version: str = "3.0",
    seconds: int = 1700000000,
) -> dict[str, Any]:
    return {
        "reviewId": review_id,
        "authorName": author,
        "comments": [
            {
                "userComment": {
                    "text": body,
                    "starRating": rating,
                    "appVersionName": version,
                    "lastModified": {"seconds": str(seconds)},
                }
            }
        ],
    }


def _gplay_response(
    entries: list[dict[str, Any]],
    next_token: str | None = None,
    status_code: int = 200,
) -> HttpResponse:
    body: dict[str, Any] = {"reviews": entries}
    if next_token:
        body["tokenPagination"] = {"nextPageToken": next_token}
    return HttpResponse(status=status_code, body=json.dumps(body))


class TestGoogleDeveloperApiProviderCountries:
    def test_returns_single_empty_string(self):
        provider = GoogleDeveloperApiProvider("Bearer fake")
        assert provider.countries(["us", "gb"]) == [""]

    def test_returns_single_empty_string_for_empty_list(self):
        provider = GoogleDeveloperApiProvider("Bearer fake")
        assert provider.countries([]) == [""]


class TestGoogleDeveloperApiProviderFetchPage:
    @patch("app_reviews.providers.googleplay.official.http_get")
    def test_returns_normalized_reviews(self, mock_get):
        entry = _gplay_entry(
            review_id="rev-001",
            rating=4,
            body="Works great",
            author="Bob",
        )
        mock_get.return_value = _gplay_response([entry])
        provider = GoogleDeveloperApiProvider("Bearer fake")
        page = provider.fetch_page("com.example", "", cursor=None)
        assert page.error is None
        assert len(page.reviews) == 1
        r = page.reviews[0]
        assert r.store == "googleplay"
        assert r.rating == 4
        assert r.body == "Works great"
        assert r.author_name == "Bob"
        assert r.source == "googleplay_official"
        assert r.id == "googleplay_official-rev-001"

    @patch("app_reviews.providers.googleplay.official.http_get")
    def test_next_cursor_is_page_token(self, mock_get):
        mock_get.return_value = _gplay_response([_gplay_entry()], next_token="tok-abc")
        provider = GoogleDeveloperApiProvider("Bearer fake")
        page = provider.fetch_page("com.example", "", cursor=None)
        assert page.next_cursor == "tok-abc"

    @patch("app_reviews.providers.googleplay.official.http_get")
    def test_cursor_passed_as_token_param(self, mock_get):
        mock_get.return_value = _gplay_response([])
        provider = GoogleDeveloperApiProvider("Bearer fake")
        provider.fetch_page("com.example", "", cursor="my-token")
        params = mock_get.call_args[1].get("params", {})
        assert params.get("token") == "my-token"

    @patch("app_reviews.providers.googleplay.official.http_get")
    def test_no_next_token_means_no_cursor(self, mock_get):
        mock_get.return_value = _gplay_response([_gplay_entry()])
        provider = GoogleDeveloperApiProvider("Bearer fake")
        page = provider.fetch_page("com.example", "", cursor=None)
        assert page.next_cursor is None

    @patch("app_reviews.providers.googleplay.official.http_get")
    def test_auth_header_sent(self, mock_get):
        captured: dict[str, str] = {}

        def side_effect(url, **kwargs):
            captured.update(kwargs.get("headers", {}))
            return _gplay_response([])

        mock_get.side_effect = side_effect
        provider = GoogleDeveloperApiProvider("Bearer my-token")
        provider.fetch_page("com.example", "", cursor=None)
        assert captured["Authorization"] == "Bearer my-token"

    @patch("app_reviews.providers.googleplay.official.http_get")
    def test_http_error_returns_fetch_error(self, mock_get):
        mock_get.return_value = HttpResponse(status=403, body="Forbidden")
        provider = GoogleDeveloperApiProvider("Bearer bad")
        page = provider.fetch_page("com.example", "", cursor=None)
        assert page.error is not None

    @patch("app_reviews.providers.googleplay.official.http_get")
    def test_url_error_returns_fetch_error(self, mock_get):
        import urllib.error

        mock_get.side_effect = urllib.error.URLError("refused")
        provider = GoogleDeveloperApiProvider("Bearer fake")
        page = provider.fetch_page("com.example", "", cursor=None)
        assert page.error is not None

    @patch("app_reviews.providers.googleplay.official.http_get")
    def test_empty_response_no_error(self, mock_get):
        mock_get.return_value = _gplay_response([])
        provider = GoogleDeveloperApiProvider("Bearer fake")
        page = provider.fetch_page("com.example", "", cursor=None)
        assert page.reviews == []
        assert page.error is None
