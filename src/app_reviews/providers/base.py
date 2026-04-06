"""Provider protocol for fetching reviews."""

from __future__ import annotations

from typing import Protocol

from app_reviews.models.result import FetchResult


class ReviewProvider(Protocol):
    """Interface for review providers."""

    def fetch(self, app_id: str) -> FetchResult: ...
