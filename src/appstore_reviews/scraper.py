"""Public facade APIs for fetching App Store reviews."""

from __future__ import annotations

import httpx

from appstore_reviews.config.models import AppStoreConfig
from appstore_reviews.core.execution import execute_fetch
from appstore_reviews.models.result import FetchResult, FetchStats
from appstore_reviews.providers.client import create_async_client
from appstore_reviews.providers.rss import fetch_rss_reviews_async


class AppStoreScraper:
    """Sync facade for fetching App Store reviews."""

    def __init__(
        self,
        *,
        app_id: str | None = None,
        app_ids: list[str] | None = None,
        countries: list[str] | None = None,
        provider: str = "auto",
    ) -> None:
        ids = app_ids or ([app_id] if app_id else [])
        self._config = AppStoreConfig(
            app_ids=ids,
            countries=countries or ["us"],
            provider=provider,
        )

    def fetch(self, *, sync_client: httpx.Client | None = None) -> FetchResult:
        """Execute a synchronous fetch and return structured results."""
        return execute_fetch(self._config, sync_client=sync_client)


class AsyncAppStoreScraper:
    """Async facade for fetching App Store reviews."""

    def __init__(
        self,
        *,
        app_id: str | None = None,
        app_ids: list[str] | None = None,
        countries: list[str] | None = None,
        provider: str = "auto",
    ) -> None:
        ids = app_ids or ([app_id] if app_id else [])
        self._config = AppStoreConfig(
            app_ids=ids,
            countries=countries or ["us"],
            provider=provider,
        )

    async def fetch(
        self, *, async_client: httpx.AsyncClient | None = None
    ) -> FetchResult:
        """Execute an async fetch and return structured results."""
        if not self._config.app_ids:
            return FetchResult()

        client = async_client or create_async_client(
            timeout=self._config.retry.timeout,
            proxy_url=self._config.proxy.url,
        )
        close_client = async_client is None

        all_reviews = []
        all_failures = []

        try:
            for app_id in self._config.app_ids:
                result = await fetch_rss_reviews_async(
                    app_id=app_id,
                    app_input=app_id,
                    countries=self._config.countries,
                    client=client,
                )
                all_reviews.extend(result.reviews)
                all_failures.extend(result.failures)
        finally:
            if close_client:
                await client.aclose()

        countries_seen = {r.country for r in all_reviews}
        stats = FetchStats(
            total_reviews=len(all_reviews),
            total_countries=len(countries_seen) or len(self._config.countries),
            total_failures=len(all_failures),
        )

        return FetchResult(reviews=all_reviews, failures=all_failures, stats=stats)
