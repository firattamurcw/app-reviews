"""Root application configuration model."""

from __future__ import annotations

from dataclasses import dataclass, field

from app_reviews.models.auth import AppStoreAuth, GooglePlayAuth
from app_reviews.models.export import ExportConfig
from app_reviews.models.proxy import ProxyConfig
from app_reviews.models.retry import RetryConfig
from app_reviews.models.types import Store


@dataclass(slots=True)
class ReviewConfig:
    """Root configuration for app-reviews."""

    store: Store = "appstore"
    app_id: str = ""
    countries: list[str] = field(default_factory=lambda: ["us"])
    auth: AppStoreAuth | GooglePlayAuth | None = None
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    strict: bool = False
