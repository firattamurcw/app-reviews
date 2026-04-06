"""Tests for provider selection logic."""

import pytest

from app_reviews.core.provider_selection import select_provider
from app_reviews.models.auth import AppStoreAuth, GooglePlayAuth


class TestSelectProviderApple:
    def test_explicit_scraper_returns_scraper(self) -> None:
        assert select_provider("appstore", "scraper", None) == "scraper"

    def test_explicit_official_returns_official(self) -> None:
        auth = AppStoreAuth(key_id="k", issuer_id="i", key_path="/tmp/k.p8")
        assert select_provider("appstore", "official", auth) == "official"

    def test_auto_without_auth_returns_scraper(self) -> None:
        assert select_provider("appstore", "auto", None) == "scraper"

    def test_auto_with_full_auth_returns_official(self) -> None:
        auth = AppStoreAuth(key_id="k", issuer_id="i", key_path="/tmp/k.p8")
        assert select_provider("appstore", "auto", auth) == "official"

    def test_invalid_apple_provider_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid Apple provider"):
            select_provider("appstore", "developer_api", None)


class TestSelectProviderGoogle:
    def test_auto_no_auth_returns_scraper(self) -> None:
        assert select_provider("googleplay", "auto", None) == "scraper"

    def test_auto_with_auth_returns_official(self) -> None:
        auth = GooglePlayAuth(service_account_path="/path/to/sa.json")
        assert select_provider("googleplay", "auto", auth) == "official"

    def test_explicit_scraper(self) -> None:
        assert select_provider("googleplay", "scraper", None) == "scraper"

    def test_explicit_official(self) -> None:
        auth = GooglePlayAuth(service_account_path="/path/to/sa.json")
        assert select_provider("googleplay", "official", auth) == "official"

    def test_invalid_google_provider_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid Google provider"):
            select_provider("googleplay", "rss", None)
