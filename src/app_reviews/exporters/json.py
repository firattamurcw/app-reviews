"""JSON exporter for reviews."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from app_reviews.models.review import Review


def export_json(
    reviews: list[Review],
    *,
    output: str | Path | None = None,
    overwrite: bool = False,
    include_raw: bool = False,
) -> str:
    """Export reviews as a JSON array string. Optionally writes to file."""
    rows = []
    for r in reviews:
        d = dataclasses.asdict(r)
        if not include_raw:
            d.pop("source_payload", None)
        rows.append(d)

    text = json.dumps(rows, indent=2, default=str)

    if output is not None:
        p = Path(output)
        if p.exists() and not overwrite:
            raise FileExistsError(f"Output file already exists: {p}")
        p.write_text(text)

    return text
