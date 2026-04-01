"""Checkpoint configuration model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CheckpointConfig:
    """Resume-from-checkpoint settings."""

    enabled: bool = False
    path: str | None = None
