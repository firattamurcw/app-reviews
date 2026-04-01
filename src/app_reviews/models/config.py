"""Root application configuration model."""

from __future__ import annotations

from dataclasses import dataclass, field

from app_reviews.models.auth import AppStoreAuthConfig, GooglePlayAuthConfig
from app_reviews.models.checkpoint import CheckpointConfig
from app_reviews.models.export import ExportConfig
from app_reviews.models.proxy import ProxyConfig
from app_reviews.models.retry import RetryConfig
from app_reviews.models.types import Provider, Store


@dataclass(slots=True)
class ReviewConfig:
    """Root configuration for app-reviews."""

    store: Store = "appstore"
    app_ids: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=lambda: ["us"])
    provider: Provider = "auto"
    auth: AppStoreAuthConfig | GooglePlayAuthConfig | None = None
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    checkpoint: CheckpointConfig = field(default_factory=CheckpointConfig)
    strict: bool = False
    debug: bool = False
