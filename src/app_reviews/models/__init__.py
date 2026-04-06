"""Public models for app-reviews."""

from __future__ import annotations

from typing import Any

from app_reviews.models.auth import (
    AppStoreAuth,
    ConnectCredentials,
    GooglePlayAuth,
)
from app_reviews.models.callback import FetchCallback
from app_reviews.models.checkpoint import CheckpointConfig
from app_reviews.models.config import ReviewConfig
from app_reviews.models.country import Country
from app_reviews.models.export import ExportConfig
from app_reviews.models.metadata import AppMetadata
from app_reviews.models.proxy import ProxyConfig
from app_reviews.models.result import (
    CountryStatus,
    FetchFailure,
    FetchResult,
    FetchStats,
    FetchWarning,
)
from app_reviews.models.retry import RetryConfig
from app_reviews.models.review import Review
from app_reviews.models.sort import Sort


def load_config(overrides: dict[str, Any] | None = None) -> ReviewConfig:
    """Build a ReviewConfig from optional overrides."""
    if not overrides:
        return ReviewConfig()

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
    "AppStoreAuth",
    "CheckpointConfig",
    "ConnectCredentials",
    "Country",
    "CountryStatus",
    "ExportConfig",
    "FetchCallback",
    "FetchFailure",
    "FetchResult",
    "FetchStats",
    "FetchWarning",
    "GooglePlayAuth",
    "ProxyConfig",
    "RetryConfig",
    "Review",
    "ReviewConfig",
    "Sort",
    "load_config",
]
