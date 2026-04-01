"""Behavioral tests for RSS and Connect providers.

Tests verify: fetching returns normalized reviews, errors become failures,
partial failures are handled gracefully, pagination works, and normalized
fields are correct (replacing standalone normalizer tests).
"""

from typing import Any

import httpx

from appstore_reviews.models.review import Review
from appstore_reviews.providers.connect import (
    fetch_connect_reviews,
    fetch_connect_reviews_async,
)
from appstore_reviews.providers.rss import (
    fetch_rss_reviews,
    fetch_rss_reviews_async,
)

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
) -> httpx.Response:
    body = {"feed": {"entry": entries}} if entries else {"feed": {}}
    return httpx.Response(status_code, json=body)


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
) -> httpx.Response:
    body: dict[str, Any] = {"data": entries}
    if next_url:
        body["links"] = {"next": next_url}
    return httpx.Response(status_code, json=body)


# ── RSS Provider ─────────────────────────────────────────────────────


class TestRssProvider:
    """Fetching from RSS returns normalized Review objects."""

    def test_returns_normalized_reviews(self) -> None:
        """Reviews come back with correct fields from RSS normalization."""
        entry = _rss_entry(
            review_id="42",
            rating="3",
            title="  Decent  ",
            body="It works\r\n",
            author="  Bob  ",
            version="2.1",
        )

        def handler(request: httpx.Request) -> httpx.Response:
            return _rss_response([entry])

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = fetch_rss_reviews(
            app_id="99999",
            app_input="99999",
            countries=["jp"],
            client=client,
        )

        assert len(result.reviews) == 1
        review = result.reviews[0]
        assert isinstance(review, Review)
        # Normalized fields (replaces standalone normalizer tests)
        assert review.app_id == "99999"
        assert review.country == "jp"
        assert review.rating == 3
        assert review.title == "Decent"  # whitespace stripped
        assert review.body == "It works"  # \r\n cleaned
        assert review.author_name == "Bob"  # whitespace stripped
        assert review.app_version == "2.1"
        assert review.source == "rss"
        assert review.source_review_id == "42"
        assert review.canonical_key == "99999-42"
        assert review.review_id == "rss-42"

    def test_multiple_countries_fetch_independently(self) -> None:
        """Each country is fetched separately; all reviews collected."""
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(str(request.url))
            return _rss_response([_rss_entry()])

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = fetch_rss_reviews(
            app_id="12345",
            app_input="12345",
            countries=["us", "gb", "jp"],
            client=client,
        )

        assert len(result.reviews) == 3
        assert any("/us/" in c for c in calls)
        assert any("/gb/" in c for c in calls)
        assert any("/jp/" in c for c in calls)

    def test_pagination_fetches_multiple_pages(self) -> None:
        """pages=2 fetches two pages per country."""
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(str(request.url))
            return _rss_response([_rss_entry()])

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = fetch_rss_reviews(
            app_id="12345",
            app_input="12345",
            countries=["us"],
            pages=2,
            client=client,
        )

        assert len(calls) == 2
        assert any("page=1" in c for c in calls)
        assert any("page=2" in c for c in calls)
        assert len(result.reviews) == 2

    def test_http_error_becomes_failure(self) -> None:
        """Non-200 responses are recorded as failures, not exceptions."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, text="Service Unavailable")

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = fetch_rss_reviews(
            app_id="12345",
            app_input="12345",
            countries=["us"],
            client=client,
        )

        assert result.reviews == []
        assert len(result.failures) == 1
        assert result.failures[0].provider == "rss"

    def test_connection_error_becomes_failure(self) -> None:
        """Network errors are captured as failures, not raised."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = fetch_rss_reviews(
            app_id="12345",
            app_input="12345",
            countries=["us"],
            client=client,
        )

        assert result.reviews == []
        assert len(result.failures) == 1

    def test_partial_failure_across_countries(self) -> None:
        """Some countries succeed, some fail — both recorded."""

        def handler(request: httpx.Request) -> httpx.Response:
            if "/gb/" in str(request.url):
                return httpx.Response(500, text="fail")
            return _rss_response([_rss_entry()])

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = fetch_rss_reviews(
            app_id="12345",
            app_input="12345",
            countries=["us", "gb"],
            client=client,
        )

        assert len(result.reviews) == 1
        assert result.reviews[0].country == "us"
        assert len(result.failures) == 1
        assert result.failures[0].country == "gb"

    def test_empty_feed_returns_no_reviews(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return _rss_response([])

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = fetch_rss_reviews(
            app_id="12345",
            app_input="12345",
            countries=["us"],
            client=client,
        )

        assert result.reviews == []
        assert result.failures == []


# ── RSS Async ────────────────────────────────────────────────────────


class TestRssProviderAsync:
    async def test_returns_reviews(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return _rss_response([_rss_entry()])

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        result = await fetch_rss_reviews_async(
            app_id="12345",
            app_input="12345",
            countries=["us"],
            client=client,
        )

        assert len(result.reviews) == 1
        assert result.reviews[0].source == "rss"

    async def test_partial_failure(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            if "/gb/" in str(request.url):
                return httpx.Response(500, text="fail")
            return _rss_response([_rss_entry()])

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        result = await fetch_rss_reviews_async(
            app_id="12345",
            app_input="12345",
            countries=["us", "gb"],
            client=client,
        )

        assert len(result.reviews) == 1
        assert len(result.failures) == 1


# ── Connect Provider ─────────────────────────────────────────────────


class TestConnectProvider:
    """Fetching from Connect API returns normalized Review objects."""

    def test_returns_normalized_reviews(self) -> None:
        """Reviews come back with correct fields from Connect normalization."""
        entry = _connect_entry(
            review_id="xyz-789",
            rating=4,
            title="Pretty good",
            body="Works well",
            author="Charlie",
            territory="GBR",
        )

        def handler(request: httpx.Request) -> httpx.Response:
            return _connect_response([entry])

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = fetch_connect_reviews(
            app_id="55555",
            app_input="55555",
            auth_header="Bearer fake",
            client=client,
        )

        assert len(result.reviews) == 1
        review = result.reviews[0]
        assert isinstance(review, Review)
        # Normalized fields (replaces standalone normalizer tests)
        assert review.app_id == "55555"
        assert review.country == "GBR"
        assert review.rating == 4
        assert review.title == "Pretty good"
        assert review.body == "Works well"
        assert review.author_name == "Charlie"
        assert review.source == "connect"
        assert review.source_review_id == "xyz-789"
        assert review.canonical_key == "55555-xyz-789"
        assert review.review_id == "connect-xyz-789"

    def test_pagination_follows_next_link(self) -> None:
        """Connect provider follows pagination links until exhausted."""
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _connect_response(
                    [_connect_entry(review_id="r1")],
                    next_url="https://api.appstoreconnect.apple.com/v1/next",
                )
            return _connect_response([_connect_entry(review_id="r2")])

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = fetch_connect_reviews(
            app_id="12345",
            app_input="12345",
            auth_header="Bearer fake",
            client=client,
        )

        assert call_count == 2
        assert len(result.reviews) == 2

    def test_auth_header_is_sent(self) -> None:
        """Authorization header is passed through to the API."""
        captured: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured.update(dict(request.headers))
            return _connect_response([_connect_entry()])

        client = httpx.Client(transport=httpx.MockTransport(handler))
        fetch_connect_reviews(
            app_id="12345",
            app_input="12345",
            auth_header="Bearer my-jwt",
            client=client,
        )

        assert captured["authorization"] == "Bearer my-jwt"

    def test_http_error_becomes_failure(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, text="Unauthorized")

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = fetch_connect_reviews(
            app_id="12345",
            app_input="12345",
            auth_header="Bearer bad",
            client=client,
        )

        assert result.reviews == []
        assert len(result.failures) == 1
        assert result.failures[0].provider == "connect"

    def test_connection_error_becomes_failure(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = fetch_connect_reviews(
            app_id="12345",
            app_input="12345",
            auth_header="Bearer fake",
            client=client,
        )

        assert result.reviews == []
        assert len(result.failures) == 1

    def test_empty_response_returns_no_reviews(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return _connect_response([])

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = fetch_connect_reviews(
            app_id="12345",
            app_input="12345",
            auth_header="Bearer fake",
            client=client,
        )

        assert result.reviews == []
        assert result.failures == []


# ── Connect Async ────────────────────────────────────────────────────


class TestConnectProviderAsync:
    async def test_returns_reviews(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return _connect_response([_connect_entry()])

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        result = await fetch_connect_reviews_async(
            app_id="12345",
            app_input="12345",
            auth_header="Bearer fake",
            client=client,
        )

        assert len(result.reviews) == 1
        assert result.failures == []

    async def test_pagination(self) -> None:
        call_count = 0

        async def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _connect_response(
                    [_connect_entry(review_id="r1")],
                    next_url="https://api.appstoreconnect.apple.com/next",
                )
            return _connect_response([_connect_entry(review_id="r2")])

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        result = await fetch_connect_reviews_async(
            app_id="12345",
            app_input="12345",
            auth_header="Bearer fake",
            client=client,
        )

        assert len(result.reviews) == 2

    async def test_http_error_recorded(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="fail")

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        result = await fetch_connect_reviews_async(
            app_id="12345",
            app_input="12345",
            auth_header="Bearer fake",
            client=client,
        )

        assert result.reviews == []
        assert len(result.failures) == 1
