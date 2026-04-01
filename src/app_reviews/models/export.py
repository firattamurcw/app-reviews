"""Export configuration model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExportConfig:
    """Output format and file settings."""

    format: str = "jsonl"  # json, jsonl, csv
    output: str | None = None  # file path, None = stdout
    overwrite: bool = False
    include_raw: bool = False
