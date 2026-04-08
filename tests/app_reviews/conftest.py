"""Shared test fixtures for app-reviews."""

from datetime import UTC, datetime

from app_reviews.models.review import Review

_BASE_DT = datetime(2024, 3, 15, 10, 0, 0, tzinfo=UTC)


def make_review(
    *,
    id: str = "scraper-1",
    app_id: str = "12345",
    country: str = "us",
    language: str | None = None,
    rating: int = 5,
    title: str = "Great app",
    body: str = "Love it",
    author_name: str = "Alice",
    app_version: str | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    is_edited: bool = False,
    source: str = "appstore_scraper",
    raw: dict | None = None,
    fetched_at: datetime | None = None,
    store: str = "appstore",
) -> Review:
    """Build a Review with sensible defaults. Override any field by keyword."""
    return Review(
        store=store,
        app_id=app_id,
        country=country,
        language=language,
        rating=rating,
        title=title,
        body=body,
        author_name=author_name,
        app_version=app_version,
        created_at=created_at or _BASE_DT,
        updated_at=updated_at,
        is_edited=is_edited,
        source=source,
        raw=raw,
        fetched_at=fetched_at or _BASE_DT,
        id=id,
    )
