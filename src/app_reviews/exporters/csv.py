"""CSV exporter for reviews."""

from __future__ import annotations

import csv
import dataclasses
import io
from pathlib import Path

from app_reviews.models.review import Review

_CSV_FIELDS: list[str] = [
    "review_id",
    "canonical_key",
    "app_id",
    "app_input",
    "country",
    "locale",
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
    "source_review_id",
    "fetched_at",
]


def export_csv(
    reviews: list[Review],
    *,
    output: str | Path | None = None,
    overwrite: bool = False,
) -> str:
    """Export reviews as CSV. Optionally writes to file."""
    if not reviews:
        return ""

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_CSV_FIELDS)
    writer.writeheader()
    for r in reviews:
        d = dataclasses.asdict(r)
        row = {k: d.get(k, "") for k in _CSV_FIELDS}
        writer.writerow(row)

    text = buf.getvalue()

    if output is not None:
        p = Path(output)
        if p.exists() and not overwrite:
            raise FileExistsError(f"Output file already exists: {p}")
        p.write_text(text)

    return text
