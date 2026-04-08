"""Review exporters for CSV, JSON, and JSONL formats."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

from app_reviews.models.review import Review

# Fields excluded from all exports unless explicitly requested.
_EXCLUDED_FIELDS = {"raw"}

# Fields included in CSV export (raw is always excluded).
CSV_FIELDS: list[str] = [
    "id",
    "app_id",
    "country",
    "language",
    "rating",
    "title",
    "body",
    "author_name",
    "app_version",
    "created_at",
    "updated_at",
    "is_edited",
    "source",
    "fetched_at",
]


def review_to_dict(review: Review, *, include_raw: bool = False) -> dict[str, Any]:
    """Convert a Review to a plain dict, optionally stripping the raw payload.

    Args:
        review: The Review object to convert.
        include_raw: If True, keep the raw provider payload in the output.

    Returns:
        A plain dictionary representation of the review.
    """
    d = dataclasses.asdict(review)
    if not include_raw:
        for field in _EXCLUDED_FIELDS:
            d.pop(field, None)
    return d


def write_output(text: str, output: str | Path | None, overwrite: bool) -> None:
    """Write text to a file if output path is given.

    Args:
        text: The content to write.
        output: File path to write to, or None to skip writing.
        overwrite: If True, overwrite an existing file.

    Raises:
        FileExistsError: If the file exists and overwrite is False.
    """
    if output is not None:
        p = Path(output)
        if p.exists() and not overwrite:
            raise FileExistsError(f"Output file already exists: {p}")
        p.write_text(text)
