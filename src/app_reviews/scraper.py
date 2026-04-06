"""Backwards-compatible aliases for the old scraper API.

These aliases are deprecated. Use AppStoreReviews and GooglePlayReviews instead.
"""

from __future__ import annotations

import warnings

from app_reviews.core.execution import execute_fetch
from app_reviews.models.auth import AppStoreAuth, GooglePlayAuth
from app_reviews.models.config import ReviewConfig
from app_reviews.models.result import FetchResult
from app_reviews.models.types import Provider


class AppStoreScraper:
    """Deprecated. Use AppStoreReviews instead."""

    def __init__(
        self,
        *,
        app_id: str | None = None,
        app_ids: list[str] | None = None,
        countries: list[str] | None = None,
        provider: Provider = "auto",
        key_id: str | None = None,
        issuer_id: str | None = None,
        key_path: str | None = None,
    ) -> None:
        warnings.warn(
            "AppStoreScraper is deprecated. Use AppStoreReviews instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        ids = app_ids or ([app_id] if app_id else [])
        auth: AppStoreAuth | None = None
        if key_id and issuer_id and key_path:
            auth = AppStoreAuth(key_id=key_id, issuer_id=issuer_id, key_path=key_path)
        self._config = ReviewConfig(
            store="appstore",
            app_ids=ids,
            countries=countries or ["us"],
            provider=provider,
            auth=auth,
        )

    def fetch(self) -> FetchResult:
        return execute_fetch(self._config)


class GooglePlayScraper:
    """Deprecated. Use GooglePlayReviews instead."""

    def __init__(
        self,
        *,
        app_id: str | None = None,
        app_ids: list[str] | None = None,
        countries: list[str] | None = None,
        provider: Provider = "auto",
        service_account_path: str | None = None,
    ) -> None:
        warnings.warn(
            "GooglePlayScraper is deprecated. Use GooglePlayReviews instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        ids = app_ids or ([app_id] if app_id else [])
        auth = None
        if service_account_path:
            auth = GooglePlayAuth(service_account_path=service_account_path)
        self._config = ReviewConfig(
            store="googleplay",
            app_ids=ids,
            countries=countries or ["us"],
            provider=provider,
            auth=auth,
        )

    def fetch(self) -> FetchResult:
        return execute_fetch(self._config)
