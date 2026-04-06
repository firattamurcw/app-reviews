"""Tests for AppStoreReviews and GooglePlayReviews client classes."""

import os
import sys
from unittest.mock import patch

from app_reviews.client import AppStoreReviews, GooglePlayReviews
from app_reviews.models.auth import AppStoreAuth, GooglePlayAuth
from app_reviews.models.result import FetchResult, FetchStats
from app_reviews.models.retry import RetryConfig

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from conftest import make_review


class TestAppStoreReviews:
    def test_default_construction(self):
        client = AppStoreReviews()
        assert client is not None

    def test_construction_with_auth(self):
        auth = AppStoreAuth(key_id="K", issuer_id="I", key_path="p.p8")
        client = AppStoreReviews(auth=auth)
        assert client is not None

    def test_construction_with_proxy(self):
        client = AppStoreReviews(proxy="http://proxy:8080")
        assert client is not None

    def test_construction_with_retry_config(self):
        client = AppStoreReviews(retry=RetryConfig(max_retries=5))
        assert client is not None

    def test_construction_with_debug(self):
        client = AppStoreReviews(debug=True)
        assert client is not None

    def test_construction_with_on_review(self):
        client = AppStoreReviews(on_review=lambda r: None)
        assert client is not None

    @patch("app_reviews.client.execute_fetch")
    def test_fetch_returns_fetch_result(self, mock_exec):
        reviews = [make_review(id="1")]
        mock_exec.return_value = FetchResult(
            reviews=reviews, stats=FetchStats(total_reviews=1)
        )
        client = AppStoreReviews()
        result = client.fetch("324684580")
        assert len(result) == 1
        assert next(iter(result)).id == "1"

    @patch("app_reviews.client.execute_fetch")
    def test_fetch_with_countries(self, mock_exec):
        mock_exec.return_value = FetchResult()
        client = AppStoreReviews()
        client.fetch("324684580", countries=["us", "gb"])
        config = mock_exec.call_args[0][0]
        assert config.countries == ["us", "gb"]

    @patch("app_reviews.client.execute_fetch")
    def test_fetch_with_limit(self, mock_exec):
        reviews = [make_review(id=str(i)) for i in range(10)]
        mock_exec.return_value = FetchResult(
            reviews=reviews, stats=FetchStats(total_reviews=10)
        )
        client = AppStoreReviews()
        result = client.fetch("324684580", limit=3)
        assert len(result) == 3

    @patch("app_reviews.client.execute_fetch")
    def test_fetch_reusable_client(self, mock_exec):
        mock_exec.return_value = FetchResult()
        client = AppStoreReviews()
        client.fetch("324684580")
        client.fetch("389801252")
        assert mock_exec.call_count == 2

    @patch("app_reviews.client.execute_fetch")
    def test_fetch_with_ratings_filter(self, mock_exec):
        reviews = [
            make_review(id="1", rating=5),
            make_review(id="2", rating=1),
        ]
        mock_exec.return_value = FetchResult(
            reviews=reviews, stats=FetchStats(total_reviews=2)
        )
        client = AppStoreReviews()
        result = client.fetch("123", ratings=[4, 5])
        assert len(result) == 1
        assert next(iter(result)).rating == 5

    @patch("app_reviews.client.execute_fetch")
    def test_fetch_on_review_callback(self, mock_exec):
        reviews = [make_review(id="1"), make_review(id="2")]
        mock_exec.return_value = FetchResult(
            reviews=reviews, stats=FetchStats(total_reviews=2)
        )
        seen = []
        client = AppStoreReviews(on_review=lambda r: seen.append(r.id))
        client.fetch("123")
        assert seen == ["1", "2"]


class TestGooglePlayReviews:
    def test_default_construction(self):
        client = GooglePlayReviews()
        assert client is not None

    def test_construction_with_auth(self):
        auth = GooglePlayAuth(service_account_path="sa.json")
        client = GooglePlayReviews(auth=auth)
        assert client is not None

    @patch("app_reviews.client.execute_fetch")
    def test_fetch_returns_fetch_result(self, mock_exec):
        reviews = [make_review(id="1", store="googleplay", source="googleplay_scraper")]
        mock_exec.return_value = FetchResult(
            reviews=reviews, stats=FetchStats(total_reviews=1)
        )
        client = GooglePlayReviews()
        result = client.fetch("com.example.app")
        assert len(result) == 1
