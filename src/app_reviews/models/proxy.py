"""Proxy configuration model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProxyConfig:
    """HTTP proxy settings."""

    url: str | None = None
