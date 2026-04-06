"""Provider selection logic."""

from __future__ import annotations

from app_reviews.models.auth import AppStoreAuth, GooglePlayAuth
from app_reviews.models.types import (
    AppStoreProvider,
    GooglePlayProvider,
    Provider,
    Store,
)


def select_provider(
    store: Store,
    provider: Provider,
    auth: AppStoreAuth | GooglePlayAuth | None,
) -> AppStoreProvider | GooglePlayProvider:
    """Resolve the effective provider name for a given store."""
    if store == "appstore":
        if provider == "auto":
            return "official" if isinstance(auth, AppStoreAuth) else "scraper"
        if provider not in ("scraper", "official"):
            raise ValueError(
                f"Invalid Apple provider {provider!r}."
                " Must be: scraper, official, auto."
            )
        return provider
    if store == "googleplay":
        if provider == "auto":
            if isinstance(auth, GooglePlayAuth):
                return "official"
            return "scraper"
        if provider not in ("scraper", "official"):
            raise ValueError(
                f"Invalid Google provider {provider!r}."
                " Must be: scraper, official, auto."
            )
        return provider
    raise ValueError(f"Unknown store {store!r}.")
