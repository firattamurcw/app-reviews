"""App Store Connect API provider for reviews."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from appstore_reviews.models.result import FetchFailure, FetchResult
from appstore_reviews.providers.connect_normalizer import normalize_connect_entry

CONNECT_REVIEWS_URL_TEMPLATE = (
    "https://api.appstoreconnect.apple.com/v1/apps/{app_id}/customerReviews"
    "?sort=-createdDate&limit=200"
)


def _make_failure(app_id: str, error: str) -> FetchFailure:
    return FetchFailure(
        app_id=app_id,
        country="",
        provider="connect",
        error=error,
        timestamp=datetime.now(tz=UTC),
    )


def fetch_connect_reviews(
    *,
    app_id: str,
    app_input: str,
    auth_header: str,
    client: httpx.Client,
) -> FetchResult:
    """Fetch reviews from App Store Connect API (sync), following pagination."""
    all_reviews = []
    all_failures = []
    url: str | None = CONNECT_REVIEWS_URL_TEMPLATE.format(app_id=app_id)

    while url:
        try:
            response = client.get(url, headers={"Authorization": auth_header})
        except httpx.HTTPError as exc:
            all_failures.append(_make_failure(app_id, str(exc)))
            break

        if response.status_code != 200:
            all_failures.append(_make_failure(app_id, f"HTTP {response.status_code}"))
            break

        data = response.json()
        entries = data.get("data", [])
        for entry in entries:
            all_reviews.append(
                normalize_connect_entry(entry, app_id=app_id, app_input=app_input)
            )

        url = data.get("links", {}).get("next")

    return FetchResult(reviews=all_reviews, failures=all_failures)


async def fetch_connect_reviews_async(
    *,
    app_id: str,
    app_input: str,
    auth_header: str,
    client: httpx.AsyncClient,
) -> FetchResult:
    """Fetch reviews from App Store Connect API (async), following pagination."""
    all_reviews = []
    all_failures = []
    url: str | None = CONNECT_REVIEWS_URL_TEMPLATE.format(app_id=app_id)

    while url:
        try:
            response = await client.get(url, headers={"Authorization": auth_header})
        except httpx.HTTPError as exc:
            all_failures.append(_make_failure(app_id, str(exc)))
            break

        if response.status_code != 200:
            all_failures.append(_make_failure(app_id, f"HTTP {response.status_code}"))
            break

        data = response.json()
        entries = data.get("data", [])
        for entry in entries:
            all_reviews.append(
                normalize_connect_entry(entry, app_id=app_id, app_input=app_input)
            )

        url = data.get("links", {}).get("next")

    return FetchResult(reviews=all_reviews, failures=all_failures)
