"""Pydantic config models for appstore-reviews."""

from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    key_id: str | None = None
    issuer_id: str | None = None
    key_path: str | None = None  # .p8 file path


class ProxyConfig(BaseModel):
    url: str | None = None


class RetryConfig(BaseModel):
    max_retries: int = Field(default=3, ge=0)
    backoff_factor: float = Field(default=0.5, ge=0)
    timeout: float = Field(default=30.0, gt=0)


class ExportConfig(BaseModel):
    format: str = "jsonl"  # json, jsonl, csv
    output: str | None = None  # file path, None = stdout
    overwrite: bool = False
    include_raw: bool = False


class CheckpointConfig(BaseModel):
    enabled: bool = False
    path: str | None = None


class AppStoreConfig(BaseModel):
    """Root configuration for appstore-reviews."""

    app_ids: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=lambda: ["us"])
    provider: str = "auto"  # auto, rss, connect
    auth: AuthConfig = Field(default_factory=AuthConfig)
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    checkpoint: CheckpointConfig = Field(default_factory=CheckpointConfig)
    strict: bool = False
    debug: bool = False
