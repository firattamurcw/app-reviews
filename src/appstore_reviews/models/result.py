"""Fetch result and related models."""

from datetime import datetime

from pydantic import BaseModel, Field

from .review import Review


class FetchFailure(BaseModel):
    """A single fetch failure for a specific app/country/provider combination."""

    app_id: str
    country: str
    provider: str
    error: str
    timestamp: datetime


class FetchWarning(BaseModel):
    """A non-fatal warning encountered during fetching."""

    message: str
    context: dict[str, str] = Field(default_factory=dict)


class FetchStats(BaseModel):
    """Summary statistics for a fetch operation."""

    total_reviews: int = 0
    total_countries: int = 0
    total_failures: int = 0
    total_warnings: int = 0
    duration_seconds: float = 0.0


class FetchResult(BaseModel):
    """Structured result container for a fetch operation."""

    reviews: list[Review] = Field(default_factory=list)
    failures: list[FetchFailure] = Field(default_factory=list)
    warnings: list[FetchWarning] = Field(default_factory=list)
    stats: FetchStats = Field(default_factory=FetchStats)
    checkpoint: dict[str, str] = Field(default_factory=dict)
