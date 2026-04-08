"""Export reviews as newline-delimited JSON (JSONL)."""

from __future__ import annotations

import json
from pathlib import Path

from app_reviews.exporters import review_to_dict, write_output
from app_reviews.models.review import Review


def export_jsonl(
    reviews: list[Review],
    *,
    output: str | Path | None = None,
    overwrite: bool = False,
    include_raw: bool = False,
) -> str:
    """Export reviews as newline-delimited JSON (one JSON object per line).

    Args:
        reviews: List of Review objects to export.
        output: Optional file path to write the JSONL output.
        overwrite: If True, overwrite an existing output file.
        include_raw: If True, include the raw provider payload in each review.

    Returns:
        The JSONL string, or empty string if no reviews.
    """
    if not reviews:
        return ""

    lines = [
        json.dumps(review_to_dict(r, include_raw=include_raw), default=str)
        for r in reviews
    ]
    text = "\n".join(lines) + "\n"
    write_output(text, output, overwrite)
    return text
