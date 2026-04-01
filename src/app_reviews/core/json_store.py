"""Atomic JSON file storage primitive."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON dict from disk. Returns empty dict if missing or corrupt."""
    if not path.exists():
        return {}
    try:
        raw = path.read_text(encoding="utf-8")
        data: dict[str, Any] = json.loads(raw)
        return data
    except (json.JSONDecodeError, ValueError, OSError):
        return {}


def save_json(path: Path, data: dict[str, Any]) -> None:
    """Atomically write a JSON dict to disk (write-to-temp then rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        Path(tmp_path).replace(path)
    except BaseException:
        Path(tmp_path).unlink(missing_ok=True)
        raise
