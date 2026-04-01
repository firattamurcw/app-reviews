"""YAML config file loader and precedence-based config builder."""

from pathlib import Path
from typing import Any

import yaml

from appstore_reviews.config.env import load_env_config
from appstore_reviews.config.models import AppStoreConfig


def load_yaml_config(path: str) -> dict[str, Any]:
    """Load and return config dict from a YAML file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file contains invalid YAML.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    try:
        with p.open() as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in config file {path!r}: {exc}") from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(
            f"Config file {path!r} must contain a YAML mapping, "
            f"got {type(data).__name__}"
        )
    return dict(data)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base*, returning a new dict."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(
    *,
    config_path: str | None = None,
    overrides: dict[str, Any] | None = None,
) -> AppStoreConfig:
    """Load config with precedence: overrides > env > file > defaults."""
    merged: dict[str, Any] = {}

    # 1. File layer
    if config_path is not None:
        file_data = load_yaml_config(config_path)
        merged = _deep_merge(merged, file_data)

    # 2. Env layer
    env_data = load_env_config()
    merged = _deep_merge(merged, env_data)

    # 3. Explicit overrides layer
    if overrides:
        merged = _deep_merge(merged, overrides)

    return AppStoreConfig.model_validate(merged)
