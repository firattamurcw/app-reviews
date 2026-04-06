"""Fetch execution orchestration."""

from __future__ import annotations

from pathlib import Path

from app_reviews.core.provider_selection import select_provider
from app_reviews.models.config import ReviewConfig
from app_reviews.models.result import FetchFailure, FetchResult, FetchStats
from app_reviews.models.review import Review
from app_reviews.providers.base import ReviewProvider


def _compute_stats(
    reviews: list[Review],
    failures: list[FetchFailure],
    fallback_country_count: int,
) -> FetchStats:
    """Build FetchStats from collected reviews and failures."""
    countries_seen = {r.country for r in reviews}
    return FetchStats(
        total_reviews=len(reviews),
        total_countries=len(countries_seen) or fallback_country_count,
        total_failures=len(failures),
    )


def _build_provider(config: ReviewConfig) -> ReviewProvider:
    """Build the appropriate provider based on config."""
    from app_reviews.models.auth import AppStoreAuth

    provider_name = select_provider(config.store, config.provider, config.auth)

    if config.store == "appstore" and provider_name == "official":
        from app_reviews.auth.appstore.connect import ConnectAuth
        from app_reviews.models.auth import ConnectCredentials
        from app_reviews.providers.appstore.official import ConnectProvider

        assert isinstance(config.auth, AppStoreAuth)
        credentials = ConnectCredentials(
            key_id=config.auth.key_id,
            issuer_id=config.auth.issuer_id,
            private_key=Path(config.auth.key_path).read_text(),
        )
        auth = ConnectAuth(credentials)
        return ConnectProvider(
            auth.authorization_header(), timeout=config.retry.timeout
        )

    if config.store == "appstore" and provider_name == "scraper":
        from app_reviews.providers.appstore.scraper import RSSProvider

        return RSSProvider(countries=config.countries, timeout=config.retry.timeout)

    if config.store == "googleplay" and provider_name == "scraper":
        from app_reviews.providers.googleplay.scraper import GoogleScraperProvider

        # Use the first configured country for hl/gl locale params.
        country = config.countries[0] if config.countries else "us"
        return GoogleScraperProvider(
            timeout=config.retry.timeout,
            max_retries=config.retry.max_retries,
            country=country,
        )

    if config.store == "googleplay" and provider_name == "official":
        from app_reviews.auth.googleplay.service_account import GoogleAuth
        from app_reviews.models.auth import GooglePlayAuth
        from app_reviews.providers.googleplay.official import (
            GoogleDeveloperApiProvider,
        )

        assert isinstance(config.auth, GooglePlayAuth)
        gauth = GoogleAuth(config.auth.service_account_path)
        return GoogleDeveloperApiProvider(
            gauth.authorization_header(), timeout=config.retry.timeout
        )

    raise ValueError(f"Unsupported provider {provider_name!r}.")


def execute_fetch(config: ReviewConfig) -> FetchResult:
    """Orchestrate a sync fetch across apps and providers."""
    if not config.app_ids:
        return FetchResult()

    provider = _build_provider(config)

    all_reviews: list[Review] = []
    all_failures: list[FetchFailure] = []

    for app_id in config.app_ids:
        result = provider.fetch(app_id)
        all_reviews.extend(result.reviews)
        all_failures.extend(result.failures)

    stats = _compute_stats(all_reviews, all_failures, len(config.countries))
    return FetchResult(reviews=all_reviews, failures=all_failures, stats=stats)
