"""Behavioral tests for RSS and Connect providers.

Tests verify: fetching returns normalized reviews, errors become failures,
partial failures are handled gracefully, pagination works, and normalized
fields are correct.
"""

import json
from typing import Any
from unittest.mock import patch

from app_reviews.models.review import Review
from app_reviews.providers.appstore.official import ConnectProvider
from app_reviews.providers.appstore.scraper import RSSProvider
from app_reviews.utils.http import HttpResponse

# ── RSS fixtures ─────────────────────────────────────────────────────


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


# ── Connect fixtures ─────────────────────────────────────────────────


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
        "relationships": {"response": {"data": None}},
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


# ── RSS Provider ─────────────────────────────────────────────────────


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


# ── Connect Provider ─────────────────────────────────────────────────


class TestConnectProvider:
    """Fetching from Connect API returns normalized Review objects."""

    @patch("app_reviews.providers.appstore.official.http_get")
    def test_returns_normalized_reviews(self, mock_get: Any) -> None:
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
        result = provider.fetch("55555")

        assert len(result.reviews) == 1
        review = result.reviews[0]
        assert isinstance(review, Review)
        assert review.app_id == "55555"
        assert review.country == "GBR"
        assert review.rating == 4
        assert review.title == "Pretty good"
        assert review.body == "Works well"
        assert review.author_name == "Charlie"
        assert review.source == "appstore_official"

    @patch("app_reviews.providers.appstore.official.http_get")
    def test_pagination_follows_next_link(self, mock_get: Any) -> None:
        call_count = 0

        def side_effect(url: str, **kwargs: Any) -> HttpResponse:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _connect_response(
                    [_connect_entry(review_id="r1")],
                    next_url="https://api.appstoreconnect.apple.com/v1/next",
                )
            return _connect_response([_connect_entry(review_id="r2")])

        mock_get.side_effect = side_effect

        provider = ConnectProvider("Bearer fake")
        result = provider.fetch("12345")

        assert call_count == 2
        assert len(result.reviews) == 2

    @patch("app_reviews.providers.appstore.official.http_get")
    def test_auth_header_is_sent(self, mock_get: Any) -> None:
        captured: dict[str, str] = {}

        def side_effect(url: str, **kwargs: Any) -> HttpResponse:
            captured.update(kwargs.get("headers", {}))
            return _connect_response([_connect_entry()])

        mock_get.side_effect = side_effect

        provider = ConnectProvider("Bearer my-jwt")
        provider.fetch("12345")

        assert captured["Authorization"] == "Bearer my-jwt"

    @patch("app_reviews.providers.appstore.official.http_get")
    def test_http_error_becomes_failure(self, mock_get: Any) -> None:
        mock_get.return_value = HttpResponse(status=401, body="Unauthorized")

        provider = ConnectProvider("Bearer bad")
        result = provider.fetch("12345")

        assert result.reviews == []
        assert len(result.failures) == 1
        assert result.failures[0].provider == "official"

    @patch("app_reviews.providers.appstore.official.http_get")
    def test_connection_error_becomes_failure(self, mock_get: Any) -> None:
        import urllib.error

        mock_get.side_effect = urllib.error.URLError("refused")

        provider = ConnectProvider("Bearer fake")
        result = provider.fetch("12345")

        assert result.reviews == []
        assert len(result.failures) == 1

    @patch("app_reviews.providers.appstore.official.http_get")
    def test_empty_response_returns_no_reviews(self, mock_get: Any) -> None:
        mock_get.return_value = _connect_response([])

        provider = ConnectProvider("Bearer fake")
        result = provider.fetch("12345")

        assert result.reviews == []
        assert result.failures == []
