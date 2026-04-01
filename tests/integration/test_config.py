"""Tests for config loading."""

from app_reviews.models import load_config


class TestLoadConfig:
    def test_defaults_when_no_overrides(self) -> None:
        cfg = load_config()
        assert cfg.app_ids == []
        assert cfg.countries == ["us"]
        assert cfg.provider == "auto"
        assert cfg.debug is False

    def test_overrides_apply(self) -> None:
        cfg = load_config(overrides={"provider": "official", "debug": True})
        assert cfg.provider == "official"
        assert cfg.debug is True

    def test_nested_overrides(self) -> None:
        cfg = load_config(overrides={"retry": {"timeout": 5.0, "max_retries": 10}})
        assert cfg.retry.timeout == 5.0
        assert cfg.retry.max_retries == 10
