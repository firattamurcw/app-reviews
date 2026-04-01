"""Fetch execution orchestration."""

from __future__ import annotations

import httpx

from appstore_reviews.config.models import AppStoreConfig
from appstore_reviews.core.provider_selection import select_provider
from appstore_reviews.models.result import FetchResult, FetchStats
from appstore_reviews.providers.client import create_sync_client
from appstore_reviews.providers.rss import fetch_rss_reviews


def execute_fetch(
    config: AppStoreConfig,
    *,
    sync_client: httpx.Client | None = None,
) -> FetchResult:
    """Orchestrate a sync fetch across apps and providers."""
    if not config.app_ids:
        return FetchResult()

    provider = select_provider(config.provider, config.auth)
    client = sync_client or create_sync_client(
        timeout=config.retry.timeout,
        proxy_url=config.proxy.url,
    )
    close_client = sync_client is None

    all_reviews = []
    all_failures = []

    try:
        for app_id in config.app_ids:
            if provider == "rss":
                result = fetch_rss_reviews(
                    app_id=app_id,
                    app_input=app_id,
                    countries=config.countries,
                    client=client,
                )
            elif provider == "connect":
                from appstore_reviews.auth.connect import ConnectAuth
                from appstore_reviews.providers.connect import fetch_connect_reviews

                auth = ConnectAuth(
                    key_id=config.auth.key_id or "",
                    issuer_id=config.auth.issuer_id or "",
                    private_key=_load_key(config.auth.key_path or ""),
                )
                result = fetch_connect_reviews(
                    app_id=app_id,
                    app_input=app_id,
                    auth_header=auth.authorization_header(),
                    client=client,
                )
            else:
                continue

            all_reviews.extend(result.reviews)
            all_failures.extend(result.failures)
    finally:
        if close_client:
            client.close()

    countries_seen = {r.country for r in all_reviews}
    stats = FetchStats(
        total_reviews=len(all_reviews),
        total_countries=len(countries_seen) or len(config.countries),
        total_failures=len(all_failures),
    )

    return FetchResult(reviews=all_reviews, failures=all_failures, stats=stats)


def _load_key(path: str) -> str:
    """Read a private key file."""
    from pathlib import Path

    return Path(path).read_text()
