"""Fetch result and related models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

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
    ) -> "FetchFailure":
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
class FetchResult:
    """Structured result container for a fetch operation."""

    reviews: list[Review] = field(default_factory=list)
    failures: list[FetchFailure] = field(default_factory=list)
    warnings: list[FetchWarning] = field(default_factory=list)
    stats: FetchStats = field(default_factory=FetchStats)
    checkpoint: dict[str, str] = field(default_factory=dict)
