"""Environment variable parser for appstore-reviews config."""

import os
from typing import Any


def load_env_config() -> dict[str, Any]:
    """Read APPSTORE_REVIEWS_* env vars and return a config dict."""
    config: dict[str, Any] = {}

    app_ids = os.environ.get("APPSTORE_REVIEWS_APP_IDS")
    if app_ids is not None:
        config["app_ids"] = [a.strip() for a in app_ids.split(",") if a.strip()]

    countries = os.environ.get("APPSTORE_REVIEWS_COUNTRIES")
    if countries is not None:
        config["countries"] = [c.strip() for c in countries.split(",") if c.strip()]

    provider = os.environ.get("APPSTORE_REVIEWS_PROVIDER")
    if provider is not None:
        config["provider"] = provider

    debug_raw = os.environ.get("APPSTORE_REVIEWS_DEBUG")
    if debug_raw is not None:
        config["debug"] = debug_raw.strip().lower() in ("1", "true", "yes")

    # Nested auth fields
    key_id = os.environ.get("APPSTORE_REVIEWS_KEY_ID")
    issuer_id = os.environ.get("APPSTORE_REVIEWS_ISSUER_ID")
    key_path = os.environ.get("APPSTORE_REVIEWS_KEY_PATH")
    if key_id is not None or issuer_id is not None or key_path is not None:
        auth: dict[str, Any] = {}
        if key_id is not None:
            auth["key_id"] = key_id
        if issuer_id is not None:
            auth["issuer_id"] = issuer_id
        if key_path is not None:
            auth["key_path"] = key_path
        config["auth"] = auth

    # Nested proxy fields
    proxy_url = os.environ.get("APPSTORE_REVIEWS_PROXY_URL")
    if proxy_url is not None:
        config["proxy"] = {"url": proxy_url}

    # Nested retry fields
    timeout_raw = os.environ.get("APPSTORE_REVIEWS_TIMEOUT")
    if timeout_raw is not None:
        config["retry"] = {"timeout": float(timeout_raw)}

    return config
