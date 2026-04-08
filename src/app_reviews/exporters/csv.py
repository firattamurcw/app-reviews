"""Export reviews as CSV."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from app_reviews.exporters import CSV_FIELDS, review_to_dict, write_output
from app_reviews.models.review import Review


def export_csv(
    reviews: list[Review],
    *,
    output: str | Path | None = None,
    overwrite: bool = False,
) -> str:
    """Export reviews as a CSV string with a header row.

    Args:
        reviews: List of Review objects to export.
        output: Optional file path to write the CSV output.
        overwrite: If True, overwrite an existing output file.

    Returns:
        The CSV string, or empty string if no reviews.
    """
    if not reviews:
        return ""

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for r in reviews:
        d = review_to_dict(r)
        writer.writerow({k: d.get(k, "") for k in CSV_FIELDS})

    text = buf.getvalue()
    write_output(text, output, overwrite)
    return text
