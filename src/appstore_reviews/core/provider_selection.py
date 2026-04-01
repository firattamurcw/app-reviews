"""Provider selection logic."""

from __future__ import annotations

from appstore_reviews.config.models import AuthConfig

_VALID_PROVIDERS = {"rss", "connect", "auto"}


def _has_full_connect_auth(auth: AuthConfig) -> bool:
    return bool(auth.key_id and auth.issuer_id and auth.key_path)


def select_provider(provider: str, auth: AuthConfig) -> str:
    """Resolve the effective provider name."""
    if provider not in _VALID_PROVIDERS:
        raise ValueError(
            f"Unknown provider {provider!r}. Must be one of: rss, connect, auto."
        )

    if provider == "auto":
        return "connect" if _has_full_connect_auth(auth) else "rss"
    return provider
