"""Tests for provider selection logic."""

import pytest

from appstore_reviews.config.models import AuthConfig
from appstore_reviews.core.provider_selection import select_provider


class TestSelectProvider:
    def test_explicit_rss_returns_rss(self) -> None:
        assert select_provider("rss", AuthConfig()) == "rss"

    def test_explicit_connect_returns_connect(self) -> None:
        auth = AuthConfig(key_id="k", issuer_id="i", key_path="/tmp/k.p8")
        assert select_provider("connect", auth) == "connect"

    def test_auto_without_auth_returns_rss(self) -> None:
        assert select_provider("auto", AuthConfig()) == "rss"

    def test_auto_with_full_auth_returns_connect(self) -> None:
        auth = AuthConfig(key_id="k", issuer_id="i", key_path="/tmp/k.p8")
        assert select_provider("auto", auth) == "connect"

    def test_auto_with_partial_auth_returns_rss(self) -> None:
        auth = AuthConfig(key_id="k")
        assert select_provider("auto", auth) == "rss"

    def test_invalid_provider_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown provider"):
            select_provider("unknown", AuthConfig())
