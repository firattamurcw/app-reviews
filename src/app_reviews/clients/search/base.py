"""Base client for app search and lookup."""

from __future__ import annotations

import abc

from app_reviews.models.country import Country
from app_reviews.models.metadata import AppMetadata
from app_reviews.models.retry import RetryConfig


class BaseSearch(abc.ABC):
    """Abstract base for store search and lookup clients."""

    def __init__(
        self,
        *,
        proxy: str | None = None,
        retry: RetryConfig | None = None,
    ) -> None:
        self._proxy = proxy
        self._retry = retry or RetryConfig()

    @abc.abstractmethod
    def search(
        self,
        query: str,
        *,
        country: Country = Country.US,
        limit: int = 50,
    ) -> list[AppMetadata]: ...

    @abc.abstractmethod
    def lookup(
        self,
        app_id: str,
        *,
        country: Country = Country.US,
    ) -> AppMetadata | None: ...
