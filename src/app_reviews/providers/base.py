"""Provider protocol and page result model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app_reviews.models.result import FetchError
from app_reviews.models.review import Review


@dataclass
class PageResult:
    """Result of a single provider page request."""

    reviews: list[Review] = field(default_factory=list)
    next_cursor: str | None = None
    error: FetchError | None = None


class ReviewProvider(Protocol):
    """Interface for review providers.

    Each provider fetches one page for one (app_id, country) pair.
    The execution layer drives pagination and country iteration.
    """

    def countries(self, requested: list[str]) -> list[str]:
        """Return the list of countries to iterate.

        Providers that support per-country requests return ``requested``.
        Providers with global APIs return ``[""]`` (called once, country ignored).
        """
        ...

    def fetch_page(self, app_id: str, country: str, cursor: str | None) -> PageResult:
        """Fetch one page of reviews.

        Args:
            app_id: The app identifier.
            country: Country code (may be empty string for global providers).
            cursor: Pagination cursor from previous page, or None for first page.

        Returns:
            PageResult with reviews and optional next_cursor.
            If next_cursor is None, there are no more pages.
            If error is set, this country fetch failed.
        """
        ...
