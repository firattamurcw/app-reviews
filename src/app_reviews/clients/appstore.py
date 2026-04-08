"""Client for fetching App Store reviews."""

from __future__ import annotations

from pathlib import Path

from app_reviews.auth.appstore.connect import ConnectAuth
from app_reviews.clients.base import BaseReviews
from app_reviews.models.auth import AppStoreAuth, ConnectCredentials
from app_reviews.models.retry import RetryConfig
from app_reviews.providers.appstore.official import ConnectProvider
from app_reviews.providers.appstore.scraper import RSSProvider
from app_reviews.providers.base import ReviewProvider


class AppStoreReviews(BaseReviews):
    """Client for fetching App Store reviews."""

    def __init__(
        self,
        *,
        auth: AppStoreAuth | None = None,
        proxy: str | None = None,
        retry: RetryConfig | None = None,
    ) -> None:
        super().__init__(proxy=proxy, retry=retry)
        self._auth = auth

    def _build_provider(self) -> ReviewProvider:
        if self._auth:
            creds = ConnectCredentials(
                key_id=self._auth.key_id,
                issuer_id=self._auth.issuer_id,
                private_key=Path(self._auth.key_path).read_text(),
            )
            header = ConnectAuth(creds).authorization_header()
            return ConnectProvider(header, **self._provider_kwargs)
        return RSSProvider(**self._provider_kwargs)
