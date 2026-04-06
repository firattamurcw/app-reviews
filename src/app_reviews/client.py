"""Reusable client classes for fetching reviews."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from app_reviews.core.execution import execute_fetch
from app_reviews.models.auth import AppStoreAuth, GooglePlayAuth
from app_reviews.models.config import ReviewConfig
from app_reviews.models.proxy import ProxyConfig
from app_reviews.models.result import FetchResult
from app_reviews.models.retry import RetryConfig
from app_reviews.models.review import Review
from app_reviews.models.sort import Sort

_logger = logging.getLogger("app_reviews")
_logger.addHandler(logging.NullHandler())


class AppStoreReviews:
    """Reusable client for fetching App Store reviews."""

    def __init__(
        self,
        *,
        auth: AppStoreAuth | None = None,
        proxy: str | None = None,
        retry: RetryConfig | None = None,
        debug: bool = False,
        callbacks: list[Any] | None = None,
        on_review: Callable[[Review], None] | None = None,
    ) -> None:
        self._auth = auth
        self._proxy = proxy
        self._retry = retry or RetryConfig()
        self._callbacks = callbacks or []
        self._on_review = on_review

        if debug:
            _logger.setLevel(logging.DEBUG)
            if not any(isinstance(h, logging.StreamHandler) for h in _logger.handlers):
                _logger.addHandler(logging.StreamHandler())

    def fetch(
        self,
        app_id: str,
        *,
        countries: list[str] | None = None,
        since: date | datetime | None = None,
        until: date | datetime | None = None,
        ratings: list[int] | None = None,
        sort: Sort | str = Sort.NEWEST,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> FetchResult:
        """Fetch reviews for a single app."""
        config = ReviewConfig(
            store="appstore",
            app_ids=[app_id],
            countries=countries or ["us"],
            provider="auto",
            auth=self._auth,
            proxy=ProxyConfig(url=self._proxy),
            retry=self._retry,
        )

        result = execute_fetch(config)

        # Apply client-side filters
        result = result.filter(ratings=ratings, since=since, until=until)

        # Apply sort
        if sort:
            from app_reviews.core.filters import sort_reviews

            sort_key = str(sort)
            sort_map = {"newest": "newest", "oldest": "oldest", "rating": "highest"}
            filter_sort = sort_map.get(sort_key, "newest")
            sorted_reviews = sort_reviews(result.reviews, filter_sort)
            result = FetchResult(
                reviews=sorted_reviews,
                failures=result.failures,
                warnings=result.warnings,
                stats=result.stats,
                countries=result.countries,
                cursor=result.cursor,
                checkpoint=result.checkpoint,
            )

        # Apply limit
        if limit is not None and len(result.reviews) > limit:
            result = FetchResult(
                reviews=result.reviews[:limit],
                failures=result.failures,
                warnings=result.warnings,
                stats=result.stats,
                countries=result.countries,
                cursor=result.cursor,
                checkpoint=result.checkpoint,
            )

        # Fire callbacks
        for review in result.reviews:
            if self._on_review:
                self._on_review(review)
            for cb in self._callbacks:
                if hasattr(cb, "on_review"):
                    cb.on_review(review)

        return result


class GooglePlayReviews:
    """Reusable client for fetching Google Play reviews."""

    def __init__(
        self,
        *,
        auth: GooglePlayAuth | None = None,
        proxy: str | None = None,
        retry: RetryConfig | None = None,
        debug: bool = False,
        callbacks: list[Any] | None = None,
        on_review: Callable[[Review], None] | None = None,
    ) -> None:
        self._auth = auth
        self._proxy = proxy
        self._retry = retry or RetryConfig()
        self._callbacks = callbacks or []
        self._on_review = on_review

        if debug:
            _logger.setLevel(logging.DEBUG)
            if not any(isinstance(h, logging.StreamHandler) for h in _logger.handlers):
                _logger.addHandler(logging.StreamHandler())

    def fetch(
        self,
        app_id: str,
        *,
        countries: list[str] | None = None,
        since: date | datetime | None = None,
        until: date | datetime | None = None,
        ratings: list[int] | None = None,
        sort: Sort | str = Sort.NEWEST,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> FetchResult:
        """Fetch reviews for a single app."""
        config = ReviewConfig(
            store="googleplay",
            app_ids=[app_id],
            countries=countries or ["us"],
            provider="auto",
            auth=self._auth,
            proxy=ProxyConfig(url=self._proxy),
            retry=self._retry,
        )

        result = execute_fetch(config)

        # Apply client-side filters
        result = result.filter(ratings=ratings, since=since, until=until)

        # Apply sort
        if sort:
            from app_reviews.core.filters import sort_reviews

            sort_key = str(sort)
            sort_map = {"newest": "newest", "oldest": "oldest", "rating": "highest"}
            filter_sort = sort_map.get(sort_key, "newest")
            sorted_reviews = sort_reviews(result.reviews, filter_sort)
            result = FetchResult(
                reviews=sorted_reviews,
                failures=result.failures,
                warnings=result.warnings,
                stats=result.stats,
                countries=result.countries,
                cursor=result.cursor,
                checkpoint=result.checkpoint,
            )

        # Apply limit
        if limit is not None and len(result.reviews) > limit:
            result = FetchResult(
                reviews=result.reviews[:limit],
                failures=result.failures,
                warnings=result.warnings,
                stats=result.stats,
                countries=result.countries,
                cursor=result.cursor,
                checkpoint=result.checkpoint,
            )

        # Fire callbacks
        for review in result.reviews:
            if self._on_review:
                self._on_review(review)
            for cb in self._callbacks:
                if hasattr(cb, "on_review"):
                    cb.on_review(review)

        return result
