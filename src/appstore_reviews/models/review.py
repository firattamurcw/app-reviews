"""Canonical normalized review model."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Review(BaseModel):
    """Canonical normalized review from any provider."""

    review_id: str
    canonical_key: str
    app_id: str
    app_input: str
    country: str
    locale: str | None = None
    language: str | None = None
    rating: int = Field(ge=1, le=5)
    title: str
    body: str
    author_name: str
    app_version: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    is_edited: bool = False
    source: str  # "rss" or "connect"
    source_review_id: str
    source_payload: dict[str, Any] | None = None
    fetched_at: datetime

    model_config = {"frozen": True}
