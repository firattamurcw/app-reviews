"""App metadata model."""

from __future__ import annotations

from dataclasses import dataclass

from app_reviews.models.types import Store


@dataclass(frozen=True, slots=True)
class AppMetadata:
    """App metadata from a store lookup."""

    app_id: str
    store: Store
    name: str
    developer: str
    category: str
    price: str
    version: str
    rating: float
    rating_count: int
    url: str
