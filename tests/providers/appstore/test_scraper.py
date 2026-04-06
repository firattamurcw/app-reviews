"""Behavioral tests for the App Store RSS (scraper) provider.

Tests verify: fetching returns normalized reviews, errors become failures,
partial failures are handled gracefully, pagination works, and normalized
fields are correct.
"""

import json
from typing import Any
from unittest.mock import patch

from app_reviews.models.review import Review
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


class TestRssProvider:
    """Fetching from RSS returns normalized Review objects."""

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_returns_normalized_reviews(self, mock_get: Any) -> None:
        entry = _rss_entry(
            review_id="42",
            rating="3",
            title="  Decent  ",
            body="It works\r\n",
            author="  Bob  ",
            version="2.1",
        )
        mock_get.return_value = _rss_response([entry])

        provider = RSSProvider(countries=["jp"])
        result = provider.fetch("99999")

        assert len(result.reviews) == 1
        review = result.reviews[0]
        assert isinstance(review, Review)
        assert review.app_id == "99999"
        assert review.country == "jp"
        assert review.rating == 3
        assert review.title == "Decent"
        assert review.body == "It works"
        assert review.author_name == "Bob"
        assert review.app_version == "2.1"
        assert review.source == "appstore_scraper"
        assert review.id == "appstore_scraper-42"

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_multiple_countries_fetch_independently(self, mock_get: Any) -> None:
        calls: list[str] = []

        def side_effect(url: str, **kwargs: Any) -> HttpResponse:
            calls.append(url)
            return _rss_response([_rss_entry()])

        mock_get.side_effect = side_effect

        provider = RSSProvider(countries=["us", "gb", "jp"])
        result = provider.fetch("12345")

        assert len(result.reviews) == 3
        assert any("/us/" in c for c in calls)
        assert any("/gb/" in c for c in calls)
        assert any("/jp/" in c for c in calls)

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_pagination_fetches_multiple_pages(self, mock_get: Any) -> None:
        calls: list[str] = []

        def side_effect(url: str, **kwargs: Any) -> HttpResponse:
            calls.append(url)
            return _rss_response([_rss_entry()])

        mock_get.side_effect = side_effect

        provider = RSSProvider(countries=["us"], pages=2)
        result = provider.fetch("12345")

        assert len(calls) == 2
        assert any("page=1" in c for c in calls)
        assert any("page=2" in c for c in calls)
        assert len(result.reviews) == 2

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_http_error_becomes_failure(self, mock_get: Any) -> None:
        mock_get.return_value = HttpResponse(status=503, body="Service Unavailable")

        provider = RSSProvider(countries=["us"])
        result = provider.fetch("12345")

        assert result.reviews == []
        assert len(result.failures) == 1
        assert result.failures[0].provider == "scraper"

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_connection_error_becomes_failure(self, mock_get: Any) -> None:
        import urllib.error

        mock_get.side_effect = urllib.error.URLError("connection refused")

        provider = RSSProvider(countries=["us"])
        result = provider.fetch("12345")

        assert result.reviews == []
        assert len(result.failures) == 1

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_partial_failure_across_countries(self, mock_get: Any) -> None:
        def side_effect(url: str, **kwargs: Any) -> HttpResponse:
            if "/gb/" in url:
                return HttpResponse(status=500, body="fail")
            return _rss_response([_rss_entry()])

        mock_get.side_effect = side_effect

        provider = RSSProvider(countries=["us", "gb"])
        result = provider.fetch("12345")

        assert len(result.reviews) == 1
        assert result.reviews[0].country == "us"
        assert len(result.failures) == 1
        assert result.failures[0].country == "gb"

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_empty_feed_returns_no_reviews(self, mock_get: Any) -> None:
        mock_get.return_value = _rss_response([])

        provider = RSSProvider(countries=["us"])
        result = provider.fetch("12345")

        assert result.reviews == []
        assert result.failures == []
