"""Single-page provider result."""

from __future__ import annotations

from dataclasses import dataclass, field

from app_reviews.models.result import FetchError
from app_reviews.models.review import Review
from app_reviews.models.types import StopReason


@dataclass(frozen=True, slots=True)
class PageResult:
    """Result of a single provider page request.

    ``next_cursor`` is opaque and provider-specific; persist it verbatim to
    resume a walk later. ``None`` means there are no more pages.

    ``stopped_because`` is set only on the last page of a walk.
    """

    reviews: list[Review] = field(default_factory=list)
    next_cursor: str | None = None
    error: FetchError | None = None
    stopped_because: StopReason | None = None
