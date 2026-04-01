"""JSON-file backed checkpoint for resumable fetches."""

from __future__ import annotations

from pathlib import Path

from app_reviews.core.json_store import load_json, save_json


class Checkpoint:
    """JSON-file backed checkpoint for resumable fetches."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self) -> dict[str, str]:
        """Load checkpoint data from disk. Returns empty dict if missing."""
        return load_json(self._path)

    def save(self, data: dict[str, str]) -> None:
        """Atomically write checkpoint data to disk."""
        save_json(self._path, data)

    def mark_fetched(self, app_id: str, country: str, provider: str) -> None:
        """Record that a specific app/country/provider was fetched."""
        key = f"{app_id}:{country}:{provider}"
        data = self.load()
        data[key] = "done"
        self.save(data)

    def is_fetched(self, app_id: str, country: str, provider: str) -> bool:
        """Check if a specific app/country/provider was already fetched."""
        key = f"{app_id}:{country}:{provider}"
        data = self.load()
        return key in data

    def clear(self) -> None:
        """Remove checkpoint file from disk."""
        self._path.unlink(missing_ok=True)
