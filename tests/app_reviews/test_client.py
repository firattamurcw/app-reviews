"""Tests for AppStoreReviews and GooglePlayReviews client classes."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from unittest.mock import MagicMock, patch

from conftest import make_review

from app_reviews.clients import AppStoreReviews, GooglePlayReviews
from app_reviews.models.auth import AppStoreAuth, GooglePlayAuth
from app_reviews.models.result import FetchError
from app_reviews.models.retry import RetryConfig
from app_reviews.providers.base import PageResult


def _mock_provider(pages: list[PageResult], countries: list[str] | None = None):
    """Build a mock provider that returns pages in sequence."""
    provider = MagicMock()
    provider.countries.return_value = countries or ["us"]
    provider.fetch_page.side_effect = pages
    return provider


class TestAppStoreReviews:
    def test_default_construction(self):
        assert AppStoreReviews() is not None

    def test_construction_with_auth(self):
        auth = AppStoreAuth(key_id="K", issuer_id="I", key_path="p.p8")
        assert AppStoreReviews(auth=auth) is not None

    def test_construction_with_retry_config(self):
        assert AppStoreReviews(retry=RetryConfig(max_retries=5)) is not None

    @patch.object(AppStoreReviews, "_build_provider")
    def test_fetch_returns_fetch_result(self, mock_build):
        reviews = [make_review(id="1")]
        mock_build.return_value = _mock_provider(
            [PageResult(reviews=reviews, next_cursor=None)]
        )
        result = AppStoreReviews().fetch("324684580")
        assert len(result) == 1
        assert next(iter(result)).id == "1"

    @patch.object(AppStoreReviews, "_build_provider")
    def test_fetch_default_country_is_us(self, mock_build):
        mock_build.return_value = _mock_provider([PageResult()])
        AppStoreReviews().fetch("324684580")
        provider = mock_build.return_value
        provider.countries.assert_called_once_with(["us"])

    @patch.object(AppStoreReviews, "_build_provider")
    def test_fetch_passes_countries(self, mock_build):
        mock_build.return_value = _mock_provider(
            [PageResult(), PageResult()], countries=["us", "gb"]
        )
        AppStoreReviews().fetch("324684580", countries=["us", "gb"])
        provider = mock_build.return_value
        provider.countries.assert_called_once_with(["us", "gb"])

    @patch.object(AppStoreReviews, "_build_provider")
    def test_fetch_with_limit(self, mock_build):
        reviews = [make_review(id=str(i)) for i in range(10)]
        mock_build.return_value = _mock_provider(
            [PageResult(reviews=reviews, next_cursor=None)]
        )
        result = AppStoreReviews().fetch("324684580", limit=3)
        assert len(result) == 3

    @patch.object(AppStoreReviews, "_build_provider")
    def test_fetch_with_ratings_filter(self, mock_build):
        reviews = [make_review(id="1", rating=5), make_review(id="2", rating=1)]
        mock_build.return_value = _mock_provider(
            [PageResult(reviews=reviews, next_cursor=None)]
        )
        result = AppStoreReviews().fetch("123", ratings=[4, 5])
        assert len(result) == 1
        assert next(iter(result)).rating == 5

    @patch.object(AppStoreReviews, "_build_provider")
    def test_fetch_reusable(self, mock_build):
        mock_build.return_value = _mock_provider([PageResult(), PageResult()])
        client = AppStoreReviews()
        client.fetch("324684580")
        client.fetch("389801252")
        assert mock_build.call_count == 2

    @patch.object(AppStoreReviews, "_build_provider")
    def test_errors_passed_through(self, mock_build):
        err = FetchError(country="gb", message="timeout")
        mock_build.return_value = _mock_provider([PageResult(error=err)])
        result = AppStoreReviews().fetch("123")
        assert len(result.errors) == 1
        assert result.errors[0].country == "gb"


class TestGooglePlayReviews:
    def test_default_construction(self):
        assert GooglePlayReviews() is not None

    def test_construction_with_auth(self):
        auth = GooglePlayAuth(service_account_path="sa.json")
        assert GooglePlayReviews(auth=auth) is not None

    @patch.object(GooglePlayReviews, "_build_provider")
    def test_fetch_returns_fetch_result(self, mock_build):
        reviews = [make_review(id="1", store="googleplay", source="googleplay_scraper")]
        mock_build.return_value = _mock_provider(
            [PageResult(reviews=reviews, next_cursor=None)]
        )
        result = GooglePlayReviews().fetch("com.example.app")
        assert len(result) == 1
