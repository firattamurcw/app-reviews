"""Tests for config loading."""

from app_reviews.models import load_config


class TestLoadConfig:
    def test_defaults_when_no_overrides(self) -> None:
        cfg = load_config()
        assert cfg.app_id == ""
        assert cfg.countries == ["us"]

    def test_overrides_apply(self) -> None:
        cfg = load_config(overrides={"strict": True})
        assert cfg.strict is True

    def test_nested_overrides(self) -> None:
        cfg = load_config(overrides={"retry": {"timeout": 5.0, "max_retries": 10}})
        assert cfg.retry.timeout == 5.0
        assert cfg.retry.max_retries == 10
