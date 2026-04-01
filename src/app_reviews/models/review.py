"""Canonical normalized review model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app_reviews.models.types import Source, Store


@dataclass(frozen=True, slots=True)
class Review:
    """Canonical normalized review from any provider."""

    store: Store
    review_id: str
    canonical_key: str
    app_id: str
    app_input: str
    country: str
    rating: int
    title: str
    body: str
    author_name: str
    created_at: datetime
    source: Source
    source_review_id: str
    fetched_at: datetime
    locale: str | None = None
    language: str | None = None
    app_version: str | None = None
    updated_at: datetime | None = None
    is_edited: bool = False
    source_payload: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.rating <= 5:
            raise ValueError(f"rating must be 1-5, got {self.rating}")
