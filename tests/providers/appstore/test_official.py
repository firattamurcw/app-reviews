"""Behavioral tests for the App Store Connect (official) provider.

Tests verify: fetching returns normalized reviews, pagination follows next
links, auth headers are sent, and errors become failures.
"""

import json
from typing import Any
from unittest.mock import patch

from app_reviews.models.review import Review
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
        assert review.id == "appstore_official-xyz-789"

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
