"""Client for fetching Google Play reviews."""

from __future__ import annotations

from app_reviews.auth.googleplay.service_account import GoogleAuth
from app_reviews.clients.base_reviews import BaseReviews
from app_reviews.models.auth import GooglePlayAuth
from app_reviews.models.retry import RetryConfig
from app_reviews.providers.base import ReviewProvider
from app_reviews.providers.googleplay.official import GoogleDeveloperApiProvider
from app_reviews.providers.googleplay.scraper import GoogleScraperProvider


class GooglePlayReviews(BaseReviews):
    """Client for fetching Google Play reviews."""

    def __init__(
        self,
        *,
        auth: GooglePlayAuth | None = None,
        proxy: str | None = None,
        retry: RetryConfig | None = None,
    ) -> None:
        super().__init__(proxy=proxy, retry=retry)
        self._auth = auth

    def _build_provider(self) -> ReviewProvider:
        if self._auth:
            gauth = GoogleAuth(self._auth.service_account_path)
            header = gauth.authorization_header()
            return GoogleDeveloperApiProvider(header, **self._provider_kwargs)
        return GoogleScraperProvider(**self._provider_kwargs)
