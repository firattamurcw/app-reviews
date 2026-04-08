"""RSS feed provider for App Store reviews."""

from __future__ import annotations

import json
import urllib.error
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app_reviews.models.result import FetchError
from app_reviews.models.review import Review
from app_reviews.providers.base import PageResult
from app_reviews.utils.http import http_get
from app_reviews.utils.text import clean_text

if TYPE_CHECKING:
    from app_reviews.models.retry import RetryConfig

_PROVIDER = "scraper"

RSS_URL_TEMPLATE = (
    "https://itunes.apple.com/{country}/rss/customerreviews"
    "/id={app_id}/sortBy=mostRecent/page={page}/json"
)


def _map_entry(entry: dict[str, Any], app_id: str, country: str) -> Review:
    source_review_id: str = entry["id"]["label"]
    version: str | None = entry.get("im:version", {}).get("label") or None

    return Review(
        store="appstore",
        app_id=app_id,
        country=country,
        rating=int(entry["im:rating"]["label"]),
        title=clean_text(entry["title"]["label"]),
        body=clean_text(entry["content"]["label"]),
        author_name=clean_text(entry["author"]["name"]["label"]),
        app_version=version,
        created_at=datetime.fromisoformat(entry["updated"]["label"]),
        source="appstore_scraper",
        raw=entry,
        fetched_at=datetime.now(tz=UTC),
        id=f"appstore_scraper-{source_review_id}",
    )


def _parse_entries(response_body: str, app_id: str, country: str) -> list[Review]:
    data = json.loads(response_body)
    entries = data.get("feed", {}).get("entry", [])
    return [
        _map_entry(entry, app_id, country)
        for entry in entries
        if isinstance(entry, dict)
        and "im:rating" in entry
        and isinstance(entry.get("id"), dict)
    ]


class RSSProvider:
    """Fetches one page of App Store RSS reviews per call."""

    _MAX_PAGES = 10

    def __init__(
        self,
        timeout: float = 30.0,
        proxy: str | None = None,
        retry: RetryConfig | None = None,
    ) -> None:
        self._timeout = timeout
        self._proxy = proxy
        self._retry = retry

    def countries(self, requested: list[str]) -> list[str]:
        """RSS requires one request per country — return all requested."""
        return requested

    def fetch_page(self, app_id: str, country: str, cursor: str | None) -> PageResult:
        """Fetch one RSS page. cursor is the page number string (None = page 1)."""
        page = int(cursor) if cursor else 1
        if page > self._MAX_PAGES:
            return PageResult()

        url = RSS_URL_TEMPLATE.format(country=country, app_id=app_id, page=page)

        try:
            response = http_get(
                url,
                timeout=self._timeout,
                proxy=self._proxy,
                retry=self._retry,
            )
        except urllib.error.URLError as exc:
            return PageResult(error=FetchError(country=country, message=str(exc)))

        if response.status != 200:
            return PageResult(
                error=FetchError(country=country, message=f"HTTP {response.status}")
            )

        reviews = _parse_entries(response.body, app_id, country)
        next_cursor = str(page + 1) if reviews else None
        return PageResult(reviews=reviews, next_cursor=next_cursor)
