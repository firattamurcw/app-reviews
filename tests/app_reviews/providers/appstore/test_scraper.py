"""Tests for RSSProvider.fetch_page."""

import json
from typing import Any
from unittest.mock import patch

from app_reviews.providers.appstore.scraper import RSSProvider
from app_reviews.utils.http import HttpResponse


def _rss_entry(
    review_id: str = "111",
    rating: str = "5",
    title: str = "Great app",
    body: str = "Love it",
    author: str = "Alice",
    version: str = "1.0",
    updated: str = "2024-03-15T10:00:00-07:00",
) -> dict[str, Any]:
    return {
        "id": {"label": review_id},
        "im:rating": {"label": rating},
        "title": {"label": title},
        "content": {"label": body},
        "author": {"name": {"label": author}},
        "im:version": {"label": version},
        "updated": {"label": updated},
    }


def _rss_response(
    entries: list[dict[str, Any]], status_code: int = 200
) -> HttpResponse:
    body = {"feed": {"entry": entries}} if entries else {"feed": {}}
    return HttpResponse(status=status_code, body=json.dumps(body))


class TestRSSProviderCountries:
    def test_returns_requested_countries(self):
        provider = RSSProvider()
        assert provider.countries(["us", "gb", "de"]) == ["us", "gb", "de"]

    def test_empty_requested_returns_empty(self):
        provider = RSSProvider()
        assert provider.countries([]) == []


class TestRSSProviderFetchPage:
    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_first_page_uses_page_1(self, mock_get):
        mock_get.return_value = _rss_response([_rss_entry()])
        provider = RSSProvider()
        provider.fetch_page("12345", "us", cursor=None)
        url = mock_get.call_args[0][0]
        assert "/page=1/" in url

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_cursor_sets_page_number(self, mock_get):
        mock_get.return_value = _rss_response([_rss_entry()])
        provider = RSSProvider()
        provider.fetch_page("12345", "us", cursor="3")
        url = mock_get.call_args[0][0]
        assert "/page=3/" in url

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_returns_normalized_reviews(self, mock_get):
        entry = _rss_entry(
            review_id="42",
            rating="3",
            title="  Decent  ",
            body="It works\r\n",
            author="  Bob  ",
        )
        mock_get.return_value = _rss_response([entry])
        provider = RSSProvider()
        page = provider.fetch_page("99999", "jp", cursor=None)
        assert page.error is None
        assert len(page.reviews) == 1
        r = page.reviews[0]
        assert r.app_id == "99999"
        assert r.country == "jp"
        assert r.rating == 3
        assert r.title == "Decent"
        assert r.body == "It works"
        assert r.author_name == "Bob"
        assert r.source == "appstore_scraper"
        assert r.id == "appstore_scraper-42"

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_non_empty_page_returns_next_cursor(self, mock_get):
        mock_get.return_value = _rss_response([_rss_entry()])
        provider = RSSProvider()
        page = provider.fetch_page("12345", "us", cursor=None)
        assert page.next_cursor == "2"

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_empty_page_returns_no_next_cursor(self, mock_get):
        mock_get.return_value = _rss_response([])
        provider = RSSProvider()
        page = provider.fetch_page("12345", "us", cursor="2")
        assert page.reviews == []
        assert page.next_cursor is None
        assert page.error is None

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_http_error_returns_fetch_error(self, mock_get):
        mock_get.return_value = HttpResponse(status=503, body="error")
        provider = RSSProvider()
        page = provider.fetch_page("12345", "us", cursor=None)
        assert page.reviews == []
        assert page.next_cursor is None
        assert page.error is not None
        assert page.error.country == "us"

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_url_error_returns_fetch_error(self, mock_get):
        import urllib.error

        mock_get.side_effect = urllib.error.URLError("refused")
        provider = RSSProvider()
        page = provider.fetch_page("12345", "us", cursor=None)
        assert page.error is not None
        assert page.error.country == "us"

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_non_review_entries_skipped(self, mock_get):
        app_metadata = {
            "id": "https://apps.apple.com/us/app/id12345",
            "im:rating": {"label": "4"},
        }
        mock_get.return_value = _rss_response(
            ["string-entry", app_metadata, _rss_entry()]
        )
        provider = RSSProvider()
        page = provider.fetch_page("12345", "us", cursor=None)
        assert len(page.reviews) == 1
