"""JSON-file backed cache for previously fetched reviews."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any


class ReviewCache:
    """JSON-file backed cache for previously fetched reviews."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def _load_all(self) -> dict[str, dict[str, Any]]:
        """Load all cached data from disk. Returns empty dict if missing."""
        if not self._path.exists():
            return {}
        try:
            raw = self._path.read_text(encoding="utf-8")
            data: dict[str, dict[str, Any]] = json.loads(raw)
            return data
        except (json.JSONDecodeError, ValueError, OSError):
            return {}

    def _save_all(self, data: dict[str, dict[str, Any]]) -> None:
        """Atomically write all cached data to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=self._path.parent, suffix=".tmp")
        try:
            with open(fd, "w", encoding="utf-8") as f:
                json.dump(data, f)
            Path(tmp_path).replace(self._path)
        except BaseException:
            Path(tmp_path).unlink(missing_ok=True)
            raise

    def get(self, canonical_key: str) -> dict[str, Any] | None:
        """Look up a cached review by canonical key. Returns None on miss."""
        data = self._load_all()
        return data.get(canonical_key)

    def put(self, canonical_key: str, review_data: dict[str, Any]) -> None:
        """Store a review's dict representation."""
        data = self._load_all()
        data[canonical_key] = review_data
        self._save_all(data)

    def put_many(self, reviews: list[tuple[str, dict[str, Any]]]) -> None:
        """Store multiple reviews at once."""
        data = self._load_all()
        for key, review_data in reviews:
            data[key] = review_data
        self._save_all(data)

    def size(self) -> int:
        """Return number of cached reviews."""
        return len(self._load_all())

    def clear(self) -> None:
        """Remove cache file from disk."""
        self._path.unlink(missing_ok=True)
