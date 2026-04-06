"""Google Play Developer API provider for reviews."""

from __future__ import annotations

import json
import urllib.error
from datetime import UTC, datetime
from typing import Any

from app_reviews.models.result import FetchFailure, FetchResult
from app_reviews.models.review import Review
from app_reviews.utils.http import http_get

_PROVIDER = "official"

_REVIEWS_URL_TEMPLATE = (
    "https://androidpublisher.googleapis.com"
    "/androidpublisher/v3/applications/{app_id}/reviews"
)


def _map_entry(entry: dict[str, Any], app_id: str) -> Review:
    """Map a Google Developer API review entry to a Review."""
    review_id = entry["reviewId"]
    comment = entry["comments"][0]["userComment"]

    rating = int(comment.get("starRating", 0))
    body = comment.get("text", "")
    app_version = comment.get("appVersionName")

    last_modified = comment.get("lastModified", {})
    seconds = int(last_modified.get("seconds", 0))
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
    """Fetches reviews from the Google Play Developer API v3."""

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
        base_url = _REVIEWS_URL_TEMPLATE.format(app_id=app_id)
        params: dict[str, str] = {}

        while True:
            try:
                response = http_get(
                    base_url,
                    params=params,
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
            for entry in data.get("reviews", []):
                all_reviews.append(_map_entry(entry, app_id))

            next_token = data.get("tokenPagination", {}).get("nextPageToken")
            if not next_token:
                break
            params["token"] = next_token

        return FetchResult(reviews=all_reviews, failures=all_failures)
