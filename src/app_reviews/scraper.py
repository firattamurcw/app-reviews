"""Public facade APIs for fetching reviews."""

from __future__ import annotations

from app_reviews.core.execution import execute_fetch
from app_reviews.models.auth import AppStoreAuthConfig, GooglePlayAuthConfig
from app_reviews.models.config import ReviewConfig
from app_reviews.models.result import FetchResult
from app_reviews.models.types import Provider


class AppStoreScraper:
    """Sync facade for fetching App Store reviews."""

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
        ids = app_ids or ([app_id] if app_id else [])
        auth: AppStoreAuthConfig | None = None
        if key_id and issuer_id and key_path:
            auth = AppStoreAuthConfig(
                key_id=key_id, issuer_id=issuer_id, key_path=key_path
            )
        self._config = ReviewConfig(
            store="appstore",
            app_ids=ids,
            countries=countries or ["us"],
            provider=provider,
            auth=auth,
        )

    def fetch(self) -> FetchResult:
        """Execute a synchronous fetch and return structured results."""
        return execute_fetch(self._config)


class GooglePlayScraper:
    """Sync facade for fetching Google Play reviews."""

    def __init__(
        self,
        *,
        app_id: str | None = None,
        app_ids: list[str] | None = None,
        countries: list[str] | None = None,
        provider: Provider = "auto",
        service_account_path: str | None = None,
    ) -> None:
        ids = app_ids or ([app_id] if app_id else [])
        auth = None
        if service_account_path:
            auth = GooglePlayAuthConfig(service_account_path=service_account_path)
        self._config = ReviewConfig(
            store="googleplay",
            app_ids=ids,
            countries=countries or ["us"],
            provider=provider,
            auth=auth,
        )

    def fetch(self) -> FetchResult:
        """Execute a synchronous fetch and return structured results."""
        return execute_fetch(self._config)
