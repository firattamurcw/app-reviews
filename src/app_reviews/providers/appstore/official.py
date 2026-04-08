"""App Store Connect API provider for reviews."""

from __future__ import annotations

import json
import urllib.error
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app_reviews.models.result import FetchError
from app_reviews.models.review import Review
from app_reviews.providers.base import PageResult
from app_reviews.utils.http import http_get

if TYPE_CHECKING:
    from app_reviews.models.retry import RetryConfig

CONNECT_REVIEWS_URL_TEMPLATE = (
    "https://api.appstoreconnect.apple.com/v1/apps/{app_id}/customerReviews"
    "?sort=-createdDate&limit=200"
)

_PROVIDER = "official"


def _map_entry(entry: dict[str, Any], app_id: str) -> Review:
    source_review_id: str = entry["id"]
    attrs: dict[str, Any] = entry["attributes"]

    return Review(
        store="appstore",
        app_id=app_id,
        country=attrs.get("territory", ""),
        rating=int(attrs["rating"]),
        title=attrs["title"],
        body=attrs["body"],
        author_name=attrs["reviewerNickname"],
        created_at=datetime.fromisoformat(attrs["createdDate"]),
        source="appstore_official",
        raw=entry,
        fetched_at=datetime.now(tz=UTC),
        id=f"appstore_official-{source_review_id}",
    )


class ConnectProvider:
    """Fetches one page from the App Store Connect API."""

    def __init__(
        self,
        auth_header: str,
        timeout: float = 30.0,
        proxy: str | None = None,
        retry: RetryConfig | None = None,
    ) -> None:
        self._auth_header = auth_header
        self._timeout = timeout
        self._proxy = proxy
        self._retry = retry

    def countries(self, requested: list[str]) -> list[str]:
        """Connect API is global — always one call."""
        return [""]

    def fetch_page(self, app_id: str, country: str, cursor: str | None) -> PageResult:
        """Fetch one page. cursor is the next URL from previous response."""
        url = cursor or CONNECT_REVIEWS_URL_TEMPLATE.format(app_id=app_id)

        try:
            response = http_get(
                url,
                headers={"Authorization": self._auth_header},
                timeout=self._timeout,
                proxy=self._proxy,
                retry=self._retry,
            )
        except urllib.error.URLError as exc:
            return PageResult(error=FetchError(country="", message=str(exc)))

        if response.status != 200:
            return PageResult(
                error=FetchError(country="", message=f"HTTP {response.status}")
            )

        data = json.loads(response.body)
        reviews = [_map_entry(e, app_id) for e in data.get("data", [])]
        next_cursor: str | None = data.get("links", {}).get("next")
        return PageResult(reviews=reviews, next_cursor=next_cursor)
