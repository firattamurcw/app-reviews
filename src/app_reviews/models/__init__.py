"""Public models for app-reviews."""

from __future__ import annotations

from typing import Any

from app_reviews.models.auth import (
    AppStoreAuthConfig,
    ConnectCredentials,
    GooglePlayAuthConfig,
)
from app_reviews.models.checkpoint import CheckpointConfig
from app_reviews.models.config import ReviewConfig
from app_reviews.models.export import ExportConfig
from app_reviews.models.metadata import AppMetadata
from app_reviews.models.proxy import ProxyConfig
from app_reviews.models.result import (
    FetchFailure,
    FetchResult,
    FetchStats,
    FetchWarning,
)
from app_reviews.models.retry import RetryConfig
from app_reviews.models.review import Review


def load_config(overrides: dict[str, Any] | None = None) -> ReviewConfig:
    """Build a ReviewConfig from optional overrides."""
    if not overrides:
        return ReviewConfig()

    # Handle nested config objects
    raw = dict(overrides)
    nested_map = {
        "proxy": ProxyConfig,
        "retry": RetryConfig,
        "export": ExportConfig,
        "checkpoint": CheckpointConfig,
    }
    for key, cls in nested_map.items():
        if key in raw and isinstance(raw[key], dict):
            raw[key] = cls(**raw[key])

    return ReviewConfig(**raw)


__all__ = [
    "AppMetadata",
    "AppStoreAuthConfig",
    "CheckpointConfig",
    "ConnectCredentials",
    "ExportConfig",
    "FetchFailure",
    "FetchResult",
    "FetchStats",
    "FetchWarning",
    "GooglePlayAuthConfig",
    "ProxyConfig",
    "RetryConfig",
    "Review",
    "ReviewConfig",
    "load_config",
]
