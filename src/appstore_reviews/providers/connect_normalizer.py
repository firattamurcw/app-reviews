"""Normalizer for App Store Connect API review entries."""

from datetime import UTC, datetime
from typing import Any

from appstore_reviews.models.review import Review


def normalize_connect_entry(
    entry: dict[str, Any],
    *,
    app_id: str,
    app_input: str,
) -> Review:
    """Normalize a single Connect API review entry into a canonical Review."""
    source_review_id: str = entry["id"]
    attrs: dict[str, Any] = entry["attributes"]

    rating: int = int(attrs["rating"])
    title: str = attrs["title"]
    body: str = attrs["body"]
    author_name: str = attrs["reviewerNickname"]
    created_date: str = attrs["createdDate"]
    territory: str = attrs.get("territory", "")

    return Review(
        review_id=f"connect-{source_review_id}",
        canonical_key=f"{app_id}-{source_review_id}",
        app_id=app_id,
        app_input=app_input,
        country=territory,
        rating=rating,
        title=title,
        body=body,
        author_name=author_name,
        created_at=datetime.fromisoformat(created_date),
        source="connect",
        source_review_id=source_review_id,
        source_payload=entry,
        fetched_at=datetime.now(tz=UTC),
    )
