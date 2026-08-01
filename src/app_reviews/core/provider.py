"""What a review provider is."""

from __future__ import annotations

from typing import Protocol

from app_reviews.models.page import PageResult
from app_reviews.models.types import Source

__all__ = ["ReviewProvider"]


class ReviewProvider(Protocol):
    """Interface for review providers.

    Each provider fetches one page for one ``(app_id, country)`` pair. The
    client drives pagination and country iteration.
    """

    source: Source
    """Which source this provider is. Used to look up its capabilities.

    Whether the country dimension exists is *not* a provider decision; the
    client reads ``core.paging.is_per_country``. A provider that also
    answered that question would be a second source of truth for one boolean.
    """

    def fetch_page(self, app_id: str, country: str, cursor: str | None) -> PageResult:
        """Fetch one page of reviews.

        ``country`` is the empty string for global providers, and ``cursor`` is
        None on the first page. In the result, a ``next_cursor`` of None means
        there are no more pages and a set ``error`` means this page failed,
        which is reported rather than raised, because ``iter_pages`` reports page
        failures instead. (``AuthError`` is the one carve-out; see
        ``BaseReviews._page``.)
        """
        ...

    async def afetch_page(
        self, app_id: str, country: str, cursor: str | None
    ) -> PageResult:
        """Async equivalent of ``fetch_page``, with identical semantics.

        Shares the same parse logic as ``fetch_page``; only the I/O differs.
        """
        ...
