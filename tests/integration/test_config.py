"""Tests for config loading precedence: overrides > env > file > defaults."""

from pathlib import Path

import pytest

from appstore_reviews.config.loaders import load_config, load_yaml_config

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "config"
SAMPLE_YAML = str(FIXTURE_DIR / "sample.yaml")


class TestLoadYamlConfig:
    def test_loads_sample_yaml(self) -> None:
        data = load_yaml_config(SAMPLE_YAML)
        assert data["app_ids"] == ["123456789"]
        assert data["countries"] == ["us", "gb"]
        assert data["provider"] == "rss"
        assert data["retry"]["max_retries"] == 5
        assert data["retry"]["timeout"] == 60.0

    def test_missing_file_raises_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            load_yaml_config(str(tmp_path / "nonexistent.yaml"))

    def test_invalid_yaml_raises_value_error(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.yaml"
        bad.write_text("{invalid: yaml: content: [}")
        with pytest.raises(ValueError, match="Invalid YAML"):
            load_yaml_config(str(bad))

    def test_empty_yaml_returns_empty_dict(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty.yaml"
        empty.write_text("")
        data = load_yaml_config(str(empty))
        assert data == {}

    def test_non_mapping_yaml_raises_value_error(self, tmp_path: Path) -> None:
        list_yaml = tmp_path / "list.yaml"
        list_yaml.write_text("- a\n- b\n")
        with pytest.raises(ValueError, match="must contain a YAML mapping"):
            load_yaml_config(str(list_yaml))


class TestLoadConfigFromFile:
    def test_file_values_loaded(self) -> None:
        cfg = load_config(config_path=SAMPLE_YAML)
        assert cfg.app_ids == ["123456789"]
        assert cfg.countries == ["us", "gb"]
        assert cfg.provider == "rss"
        assert cfg.retry.max_retries == 5
        assert cfg.retry.timeout == 60.0

    def test_defaults_when_no_args(self) -> None:
        cfg = load_config()
        assert cfg.app_ids == []
        assert cfg.countries == ["us"]
        assert cfg.provider == "auto"
        assert cfg.debug is False


class TestEnvOverridesFile:
    def test_env_provider_overrides_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APPSTORE_REVIEWS_PROVIDER", "connect")
        cfg = load_config(config_path=SAMPLE_YAML)
        assert cfg.provider == "connect"

    def test_env_app_ids_overrides_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APPSTORE_REVIEWS_APP_IDS", "111,222")
        cfg = load_config(config_path=SAMPLE_YAML)
        assert cfg.app_ids == ["111", "222"]

    def test_env_timeout_overrides_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APPSTORE_REVIEWS_TIMEOUT", "99.0")
        cfg = load_config(config_path=SAMPLE_YAML)
        assert cfg.retry.timeout == 99.0

    def test_env_debug_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APPSTORE_REVIEWS_DEBUG", "true")
        cfg = load_config()
        assert cfg.debug is True

    def test_env_debug_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APPSTORE_REVIEWS_DEBUG", "1")
        cfg = load_config()
        assert cfg.debug is True

    def test_env_debug_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APPSTORE_REVIEWS_DEBUG", "false")
        cfg = load_config()
        assert cfg.debug is False

    def test_env_auth_fields(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APPSTORE_REVIEWS_KEY_ID", "KID123")
        monkeypatch.setenv("APPSTORE_REVIEWS_ISSUER_ID", "ISS456")
        monkeypatch.setenv("APPSTORE_REVIEWS_KEY_PATH", "/path/to/key.p8")
        cfg = load_config()
        assert cfg.auth.key_id == "KID123"
        assert cfg.auth.issuer_id == "ISS456"
        assert cfg.auth.key_path == "/path/to/key.p8"

    def test_env_proxy_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APPSTORE_REVIEWS_PROXY_URL", "http://proxy:8080")
        cfg = load_config()
        assert cfg.proxy.url == "http://proxy:8080"


class TestOverridesBeatEnv:
    def test_overrides_beat_env_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APPSTORE_REVIEWS_PROVIDER", "rss")
        cfg = load_config(overrides={"provider": "connect"})
        assert cfg.provider == "connect"

    def test_overrides_beat_env_debug(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APPSTORE_REVIEWS_DEBUG", "false")
        cfg = load_config(overrides={"debug": True})
        assert cfg.debug is True

    def test_overrides_beat_file(self) -> None:
        cfg = load_config(config_path=SAMPLE_YAML, overrides={"provider": "auto"})
        assert cfg.provider == "auto"

    def test_overrides_nested_retry(self) -> None:
        cfg = load_config(
            config_path=SAMPLE_YAML, overrides={"retry": {"timeout": 5.0}}
        )
        assert cfg.retry.timeout == 5.0
        # max_retries should still come from the file
        assert cfg.retry.max_retries == 5
