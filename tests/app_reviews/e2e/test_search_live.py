"""Live tests for search and lookup — hit real APIs.

Run with: uv run python -m pytest -m live tests/app_reviews/e2e/test_search_live.py -v
"""

import pytest

from app_reviews.clients.search.appstore import AppStoreSearch
from app_reviews.clients.search.googleplay import GooglePlaySearch
from app_reviews.models.metadata import AppMetadata


@pytest.mark.live
class TestAppStoreSearchLive:
    def test_search_returns_results(self):
        results = AppStoreSearch().search("whatsapp", limit=5)
        assert len(results) > 0
        assert all(isinstance(r, AppMetadata) for r in results)
        assert all(r.store == "appstore" for r in results)

    def test_search_respects_limit(self):
        results = AppStoreSearch().search("game", limit=3)
        assert len(results) <= 3

    def test_lookup_known_app(self):
        result = AppStoreSearch().lookup("com.burbn.instagram")
        assert result is not None
        assert result.name != "Unknown"
        assert result.store == "appstore"


@pytest.mark.live
class TestGooglePlaySearchLive:
    def test_search_returns_results(self):
        results = GooglePlaySearch().search("whatsapp", limit=5)
        assert len(results) > 0
        assert all(isinstance(r, AppMetadata) for r in results)
        assert all(r.store == "googleplay" for r in results)

    def test_search_respects_limit(self):
        results = GooglePlaySearch().search("game", limit=3)
        assert len(results) <= 3

    def test_lookup_known_app(self):
        result = GooglePlaySearch().lookup("com.whatsapp")
        assert result is not None
        assert result.name != "Unknown"
        assert result.store == "googleplay"
