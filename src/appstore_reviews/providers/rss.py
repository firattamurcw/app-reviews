"""RSS feed provider for App Store reviews."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from appstore_reviews.models.result import FetchFailure, FetchResult
from appstore_reviews.providers.rss_normalizer import normalize_rss_entry

RSS_URL_TEMPLATE = (
    "https://itunes.apple.com/{country}/rss/customerreviews"
    "/id={app_id}/sortBy=mostRecent/page={page}/json"
)


def _fetch_page(
    client: httpx.Client,
    *,
    app_id: str,
    app_input: str,
    country: str,
    page: int,
) -> FetchResult:
    """Fetch a single page of RSS reviews for one app+country."""
    url = RSS_URL_TEMPLATE.format(country=country, app_id=app_id, page=page)
    try:
        response = client.get(url)
    except httpx.HTTPError as exc:
        return FetchResult(
            failures=[
                FetchFailure(
                    app_id=app_id,
                    country=country,
                    provider="rss",
                    error=str(exc),
                    timestamp=datetime.now(tz=UTC),
                )
            ]
        )

    if response.status_code != 200:
        return FetchResult(
            failures=[
                FetchFailure(
                    app_id=app_id,
                    country=country,
                    provider="rss",
                    error=f"HTTP {response.status_code}",
                    timestamp=datetime.now(tz=UTC),
                )
            ]
        )

    data = response.json()
    entries = data.get("feed", {}).get("entry", [])
    reviews = [
        normalize_rss_entry(entry, app_id=app_id, app_input=app_input, country=country)
        for entry in entries
    ]
    return FetchResult(reviews=reviews)


def fetch_rss_reviews(
    *,
    app_id: str,
    app_input: str,
    countries: list[str],
    pages: int = 1,
    client: httpx.Client,
) -> FetchResult:
    """Fetch RSS reviews for one app across countries and pages (sync)."""
    all_reviews = []
    all_failures = []

    for country in countries:
        for page in range(1, pages + 1):
            result = _fetch_page(
                client, app_id=app_id, app_input=app_input, country=country, page=page
            )
            all_reviews.extend(result.reviews)
            all_failures.extend(result.failures)

    return FetchResult(reviews=all_reviews, failures=all_failures)


async def _fetch_page_async(
    client: httpx.AsyncClient,
    *,
    app_id: str,
    app_input: str,
    country: str,
    page: int,
) -> FetchResult:
    """Fetch a single page of RSS reviews for one app+country (async)."""
    url = RSS_URL_TEMPLATE.format(country=country, app_id=app_id, page=page)
    try:
        response = await client.get(url)
    except httpx.HTTPError as exc:
        return FetchResult(
            failures=[
                FetchFailure(
                    app_id=app_id,
                    country=country,
                    provider="rss",
                    error=str(exc),
                    timestamp=datetime.now(tz=UTC),
                )
            ]
        )

    if response.status_code != 200:
        return FetchResult(
            failures=[
                FetchFailure(
                    app_id=app_id,
                    country=country,
                    provider="rss",
                    error=f"HTTP {response.status_code}",
                    timestamp=datetime.now(tz=UTC),
                )
            ]
        )

    data = response.json()
    entries = data.get("feed", {}).get("entry", [])
    reviews = [
        normalize_rss_entry(entry, app_id=app_id, app_input=app_input, country=country)
        for entry in entries
    ]
    return FetchResult(reviews=reviews)


async def fetch_rss_reviews_async(
    *,
    app_id: str,
    app_input: str,
    countries: list[str],
    pages: int = 1,
    client: httpx.AsyncClient,
) -> FetchResult:
    """Fetch RSS reviews for one app across countries and pages (async)."""
    all_reviews = []
    all_failures = []

    for country in countries:
        for page in range(1, pages + 1):
            result = await _fetch_page_async(
                client, app_id=app_id, app_input=app_input, country=country, page=page
            )
            all_reviews.extend(result.reviews)
            all_failures.extend(result.failures)

    return FetchResult(reviews=all_reviews, failures=all_failures)
