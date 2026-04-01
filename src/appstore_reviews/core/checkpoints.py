"""JSON-file backed checkpoint for resumable fetches."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path


class Checkpoint:
    """JSON-file backed checkpoint for resumable fetches."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self) -> dict[str, str]:
        """Load checkpoint data from disk. Returns empty dict if missing."""
        if not self._path.exists():
            return {}
        try:
            raw = self._path.read_text(encoding="utf-8")
            data: dict[str, str] = json.loads(raw)
            return data
        except (json.JSONDecodeError, ValueError, OSError):
            return {}

    def save(self, data: dict[str, str]) -> None:
        """Atomically write checkpoint data to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=self._path.parent, suffix=".tmp")
        try:
            with open(fd, "w", encoding="utf-8") as f:
                json.dump(data, f)
            Path(tmp_path).replace(self._path)
        except BaseException:
            Path(tmp_path).unlink(missing_ok=True)
            raise

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
