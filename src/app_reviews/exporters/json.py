"""Export reviews as a JSON array."""

from __future__ import annotations

import json
from pathlib import Path

from app_reviews.exporters import review_to_dict, write_output
from app_reviews.models.review import Review


def export_json(
    reviews: list[Review],
    *,
    output: str | Path | None = None,
    overwrite: bool = False,
    include_raw: bool = False,
) -> str:
    """Export reviews as a pretty-printed JSON array string.

    Args:
        reviews: List of Review objects to export.
        output: Optional file path to write the JSON output.
        overwrite: If True, overwrite an existing output file.
        include_raw: If True, include the raw provider payload in each review.

    Returns:
        The JSON string.
    """
    rows = [review_to_dict(r, include_raw=include_raw) for r in reviews]
    text = json.dumps(rows, indent=2, default=str)
    write_output(text, output, overwrite)
    return text
