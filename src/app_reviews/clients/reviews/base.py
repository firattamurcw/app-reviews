"""Base client that owns pagination, threading, and the fetch pipeline."""

from __future__ import annotations

import abc
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from typing import Any

from app_reviews.models.result import FetchError, FetchResult
from app_reviews.models.retry import RetryConfig
from app_reviews.models.review import Review
from app_reviews.models.sort import Sort
from app_reviews.providers.base import ReviewProvider

logger = logging.getLogger(__name__)


class BaseReviews(abc.ABC):
    """Base client that owns pagination, threading, and the fetch pipeline."""

    def __init__(
        self,
        *,
        proxy: str | None = None,
        retry: RetryConfig | None = None,
    ) -> None:
        self._proxy = proxy
        self._retry = retry or RetryConfig()

    @property
    def _provider_kwargs(self) -> dict[str, Any]:
        return {
            "timeout": self._retry.timeout,
            "proxy": self._proxy,
            "retry": self._retry,
        }

    @abc.abstractmethod
    def _build_provider(self) -> ReviewProvider: ...

    def fetch(
        self,
        app_id: str,
        *,
        countries: list[str] | None = None,
        since: date | datetime | None = None,
        until: date | datetime | None = None,
        ratings: list[int] | None = None,
        sort: Sort = Sort.NEWEST,
        limit: int | None = None,
    ) -> FetchResult:
        provider = self._build_provider()
        resolved = provider.countries(countries or ["us"])
        return (
            self._run_fetch(provider, app_id, resolved, limit)
            .filter(since=since, until=until, ratings=ratings)
            .sort(sort)
            .limit(limit)
        )

    def _run_fetch(
        self,
        provider: ReviewProvider,
        app_id: str,
        countries: list[str],
        limit: int | None,
    ) -> FetchResult:
        if not countries:
            return FetchResult()

        all_reviews: list[Review] = []
        all_errors: list[FetchError] = []

        with ThreadPoolExecutor(max_workers=len(countries)) as pool:
            futures = {
                pool.submit(self._fetch_country, provider, app_id, c, limit): c
                for c in countries
            }
            for future in as_completed(futures):
                reviews, error = future.result()
                all_reviews.extend(reviews)
                if error:
                    all_errors.append(error)

        return FetchResult(reviews=all_reviews, errors=all_errors)

    @staticmethod
    def _fetch_country(
        provider: ReviewProvider,
        app_id: str,
        country: str,
        limit: int | None,
    ) -> tuple[list[Review], FetchError | None]:
        reviews: list[Review] = []
        cursor: str | None = None

        while True:
            page = provider.fetch_page(app_id, country, cursor)
            if page.error:
                if reviews:
                    logger.warning(
                        "Pagination failed after %d reviews for %s/%s: %s",
                        len(reviews),
                        app_id,
                        country,
                        page.error.message,
                    )
                    return reviews, None
                return [], page.error
            reviews.extend(page.reviews)
            if limit is not None and len(reviews) >= limit:
                break
            if not page.next_cursor:
                break
            cursor = page.next_cursor

        return reviews, None
