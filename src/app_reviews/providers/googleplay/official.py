"""Google Play Developer API provider for reviews."""

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

_PROVIDER = "official"

_REVIEWS_URL_TEMPLATE = (
    "https://androidpublisher.googleapis.com"
    "/androidpublisher/v3/applications/{app_id}/reviews"
)


def _map_entry(entry: dict[str, Any], app_id: str) -> Review:
    review_id = entry["reviewId"]
    comment = entry["comments"][0]["userComment"]
    rating = int(comment.get("starRating", 0))
    body = comment.get("text", "")
    app_version = comment.get("appVersionName")
    seconds = int(comment.get("lastModified", {}).get("seconds", 0))
    created_at = datetime.fromtimestamp(seconds, tz=UTC)
    author_name = entry.get("authorName", "")

    return Review(
        store="googleplay",
        app_id=app_id,
        country="",
        rating=rating,
        title="",
        body=body,
        author_name=author_name,
        app_version=app_version,
        created_at=created_at,
        source="googleplay_official",
        raw=entry,
        fetched_at=datetime.now(tz=UTC),
        id=f"googleplay_official-{review_id}",
    )


class GoogleDeveloperApiProvider:
    """Fetches one page from the Google Play Developer API v3."""

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
        """Developer API is global — always one call."""
        return [""]

    def fetch_page(self, app_id: str, country: str, cursor: str | None) -> PageResult:
        """Fetch one page. cursor is the nextPageToken from previous response."""
        base_url = _REVIEWS_URL_TEMPLATE.format(app_id=app_id)
        params: dict[str, str] = {}
        if cursor:
            params["token"] = cursor

        try:
            response = http_get(
                base_url,
                params=params,
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
        reviews = [_map_entry(e, app_id) for e in data.get("reviews", [])]
        next_cursor: str | None = data.get("tokenPagination", {}).get("nextPageToken")
        return PageResult(reviews=reviews, next_cursor=next_cursor)
