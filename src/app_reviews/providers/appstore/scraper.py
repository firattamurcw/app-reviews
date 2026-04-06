"""RSS feed provider for App Store reviews."""

from __future__ import annotations

import json
import urllib.error
from datetime import UTC, datetime
from typing import Any

from app_reviews.models.result import FetchFailure, FetchResult
from app_reviews.models.review import Review
from app_reviews.utils.http import HttpResponse, http_get
from app_reviews.utils.text import clean_text

_PROVIDER = "scraper"

RSS_URL_TEMPLATE = (
    "https://itunes.apple.com/{country}/rss/customerreviews"
    "/id={app_id}/sortBy=mostRecent/page={page}/json"
)


def _map_entry(
    entry: dict[str, Any], app_id: str, country: str
) -> Review:
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


def _parse_entries(
    response: HttpResponse, app_id: str, country: str
) -> list[Review]:
    data = json.loads(response.body)
    entries = data.get("feed", {}).get("entry", [])
    return [
        _map_entry(entry, app_id, country)
        for entry in entries
        if "im:rating" in entry
    ]


class RSSProvider:
    """Fetches reviews from the App Store RSS feed."""

    def __init__(
        self,
        countries: list[str] | None = None,
        pages: int = 1,
        timeout: float = 30.0,
    ) -> None:
        self._countries = countries or ["us"]
        self._pages = pages
        self._timeout = timeout

    def _fetch_page(
        self, app_id: str, country: str, page: int
    ) -> FetchResult:
        url = RSS_URL_TEMPLATE.format(country=country, app_id=app_id, page=page)
        try:
            response = http_get(url, timeout=self._timeout)
        except urllib.error.URLError as exc:
            return FetchResult(
                failures=[FetchFailure.create(app_id, _PROVIDER, str(exc), country)]
            )

        if response.status != 200:
            return FetchResult(
                failures=[
                    FetchFailure.create(
                        app_id, _PROVIDER, f"HTTP {response.status}", country
                    )
                ]
            )

        return FetchResult(reviews=_parse_entries(response, app_id, country))

    def fetch(self, app_id: str) -> FetchResult:
        all_reviews: list[Review] = []
        all_failures: list[FetchFailure] = []

        for country in self._countries:
            for page in range(1, self._pages + 1):
                result = self._fetch_page(app_id, country, page)
                all_reviews.extend(result.reviews)
                all_failures.extend(result.failures)

        return FetchResult(reviews=all_reviews, failures=all_failures)
