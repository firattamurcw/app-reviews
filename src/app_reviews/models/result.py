"""Fetch result and related models."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from typing import Any, Literal

from .review import Review


@dataclass(frozen=True, slots=True)
class FetchFailure:
    """A single fetch failure for a specific app/country/provider combination."""

    app_id: str
    country: str
    provider: str
    error: str
    timestamp: datetime

    @classmethod
    def create(
        cls, app_id: str, provider: str, error: str, country: str = ""
    ) -> FetchFailure:
        return cls(
            app_id=app_id,
            country=country,
            provider=provider,
            error=error,
            timestamp=datetime.now(tz=UTC),
        )


@dataclass(frozen=True, slots=True)
class FetchWarning:
    """A non-fatal warning encountered during fetching."""

    message: str
    context: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FetchStats:
    """Summary statistics for a fetch operation."""

    total_reviews: int = 0
    total_countries: int = 0
    total_failures: int = 0
    total_warnings: int = 0
    duration_seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class CountryStatus:
    """Per-country fetch status."""

    country: str
    state: Literal["success", "empty", "failed", "rate_limited"]
    review_count: int = 0
    error: str | None = None
    status_code: int | None = None
    duration_seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class FetchResult:
    """Structured result container for a fetch operation."""

    reviews: list[Review] = field(default_factory=list)
    failures: list[FetchFailure] = field(default_factory=list)
    warnings: list[FetchWarning] = field(default_factory=list)
    stats: FetchStats = field(default_factory=FetchStats)
    countries: dict[str, CountryStatus] = field(default_factory=dict)
    cursor: str | None = None
    checkpoint: dict[str, str] = field(default_factory=dict)

    def __iter__(self) -> Iterator[Review]:
        return iter(self.reviews)

    def __len__(self) -> int:
        return len(self.reviews)

    def __bool__(self) -> bool:
        return len(self.reviews) > 0

    @property
    def succeeded(self) -> list[str]:
        """Countries that completed successfully."""
        return [c for c, s in self.countries.items() if s.state == "success"]

    @property
    def failed(self) -> list[str]:
        """Countries that failed."""
        return [c for c, s in self.countries.items() if s.state == "failed"]

    def filter(
        self,
        *,
        countries: list[str] | None = None,
        ratings: list[int] | None = None,
        since: date | datetime | None = None,
        until: date | datetime | None = None,
    ) -> FetchResult:
        """Return a new FetchResult with filtered reviews (non-destructive)."""
        filtered = list(self.reviews)

        if countries is not None:
            country_set = set(countries)
            filtered = [r for r in filtered if r.country in country_set]

        if ratings is not None:
            rating_set = set(ratings)
            filtered = [r for r in filtered if r.rating in rating_set]

        if since is not None:
            since_dt = _to_aware_datetime(since)
            filtered = [r for r in filtered if r.created_at >= since_dt]

        if until is not None:
            until_dt = _to_aware_datetime(until)
            filtered = [r for r in filtered if r.created_at <= until_dt]

        return FetchResult(
            reviews=filtered,
            failures=self.failures,
            warnings=self.warnings,
            stats=FetchStats(
                total_reviews=len(filtered),
                total_countries=len({r.country for r in filtered}),
                total_failures=self.stats.total_failures,
                total_warnings=self.stats.total_warnings,
                duration_seconds=self.stats.duration_seconds,
            ),
            countries=self.countries,
            cursor=self.cursor,
            checkpoint=self.checkpoint,
        )

    def to_dicts(self) -> list[dict[str, Any]]:
        """Convert reviews to a list of plain dicts."""
        return [asdict(r) for r in self.reviews]


def _to_aware_datetime(d: date | datetime) -> datetime:
    """Convert a date or datetime to a timezone-aware datetime."""
    if isinstance(d, datetime):
        if d.tzinfo is None:
            return d.replace(tzinfo=UTC)
        return d
    return datetime(d.year, d.month, d.day, tzinfo=UTC)
