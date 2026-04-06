"""App Store Connect API provider for reviews."""

from __future__ import annotations

import json
import urllib.error
from datetime import UTC, datetime
from typing import Any

from app_reviews.models.result import FetchFailure, FetchResult
from app_reviews.models.review import Review
from app_reviews.utils.http import http_get

CONNECT_REVIEWS_URL_TEMPLATE = (
    "https://api.appstoreconnect.apple.com/v1/apps/{app_id}/customerReviews"
    "?sort=-createdDate&limit=200"
)


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


_PROVIDER = "official"


class ConnectProvider:
    """Fetches reviews from the App Store Connect API."""

    def __init__(
        self,
        auth_header: str,
        timeout: float = 30.0,
    ) -> None:
        self._auth_header = auth_header
        self._timeout = timeout

    def fetch(self, app_id: str) -> FetchResult:
        all_reviews: list[Review] = []
        all_failures: list[FetchFailure] = []
        url: str | None = CONNECT_REVIEWS_URL_TEMPLATE.format(app_id=app_id)

        while url:
            try:
                response = http_get(
                    url,
                    headers={"Authorization": self._auth_header},
                    timeout=self._timeout,
                )
            except urllib.error.URLError as exc:
                all_failures.append(FetchFailure.create(app_id, _PROVIDER, str(exc)))
                break

            if response.status != 200:
                all_failures.append(
                    FetchFailure.create(app_id, _PROVIDER, f"HTTP {response.status}")
                )
                break

            data = json.loads(response.body)
            for entry in data.get("data", []):
                all_reviews.append(_map_entry(entry, app_id))
            url = data.get("links", {}).get("next")

        return FetchResult(reviews=all_reviews, failures=all_failures)
