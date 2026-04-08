"""Fetch result and related models."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from typing import Any

from .review import Review
from .sort import Sort

_SORT_KEYS = {
    Sort.NEWEST: (lambda r: r.created_at, True),
    Sort.OLDEST: (lambda r: r.created_at, False),
    Sort.RATING: (lambda r: r.rating, True),
}


@dataclass(frozen=True, slots=True)
class FetchError:
    """A per-country fetch failure."""

    country: str
    message: str


@dataclass(frozen=True, slots=True)
class FetchResult:
    """Structured result container for a fetch operation."""

    reviews: list[Review] = field(default_factory=list)
    errors: list[FetchError] = field(default_factory=list)

    def __iter__(self) -> Iterator[Review]:
        return iter(self.reviews)

    def __len__(self) -> int:
        return len(self.reviews)

    def __bool__(self) -> bool:
        return bool(self.reviews)

    def filter(
        self,
        *,
        ratings: list[int] | None = None,
        since: date | datetime | None = None,
        until: date | datetime | None = None,
    ) -> FetchResult:
        """Return a new FetchResult with filtered reviews (non-destructive)."""
        filtered = list(self.reviews)
        if ratings is not None:
            rating_set = set(ratings)
            filtered = [r for r in filtered if r.rating in rating_set]
        if since is not None:
            since_dt = _to_aware_datetime(since)
            filtered = [r for r in filtered if r.created_at >= since_dt]
        if until is not None:
            until_dt = _to_aware_datetime(until)
            filtered = [r for r in filtered if r.created_at <= until_dt]
        return FetchResult(reviews=filtered, errors=self.errors)

    def sort(self, order: Sort = Sort.NEWEST) -> FetchResult:
        """Return a new FetchResult with sorted reviews (non-destructive)."""
        key_fn, reverse = _SORT_KEYS[order]
        return FetchResult(
            reviews=sorted(self.reviews, key=key_fn, reverse=reverse),
            errors=self.errors,
        )

    def limit(self, n: int | None) -> FetchResult:
        """Return a new FetchResult truncated to n reviews. No-op if n is None."""
        if n is None or n >= len(self.reviews):
            return self
        return FetchResult(reviews=self.reviews[:n], errors=self.errors)

    def to_dicts(self) -> list[dict[str, Any]]:
        """Convert reviews to a list of plain dicts."""
        return [asdict(r) for r in self.reviews]


def _to_aware_datetime(d: date | datetime) -> datetime:
    """Convert a date or datetime to a timezone-aware datetime."""
    if isinstance(d, datetime):
        return d if d.tzinfo else d.replace(tzinfo=UTC)
    return datetime(d.year, d.month, d.day, tzinfo=UTC)
