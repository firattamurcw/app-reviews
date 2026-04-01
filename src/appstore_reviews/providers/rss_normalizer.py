"""Normalizer for App Store RSS feed review entries."""

from datetime import UTC, datetime
from typing import Any

from appstore_reviews.models.review import Review


def _clean_text(text: str) -> str:
    """Strip whitespace and normalize line endings."""
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def normalize_rss_entry(
    entry: dict[str, Any],
    *,
    app_id: str,
    app_input: str,
    country: str,
) -> Review:
    """Normalize a single RSS feed entry into a canonical Review."""
    source_review_id: str = entry["id"]["label"]
    rating_raw: str = entry["im:rating"]["label"]
    title_raw: str = entry["title"]["label"]
    body_raw: str = entry["content"]["label"]
    author_raw: str = entry["author"]["name"]["label"]
    updated_raw: str = entry["updated"]["label"]
    version: str | None = entry.get("im:version", {}).get("label") or None

    return Review(
        review_id=f"rss-{source_review_id}",
        canonical_key=f"{app_id}-{source_review_id}",
        app_id=app_id,
        app_input=app_input,
        country=country,
        rating=int(rating_raw),
        title=_clean_text(title_raw),
        body=_clean_text(body_raw),
        author_name=_clean_text(author_raw),
        app_version=version,
        created_at=datetime.fromisoformat(updated_raw),
        source="rss",
        source_review_id=source_review_id,
        source_payload=entry,
        fetched_at=datetime.now(tz=UTC),
    )
