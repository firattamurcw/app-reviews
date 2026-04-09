"""Live E2E tests that hit real store endpoints.

These tests are NOT run in normal CI. They are only run by the
scheduled GitHub Action (scheduled_e2e_test.yml) to verify that
the scrapers still work against live APIs.

Run manually with: pytest tests/app_reviews/e2e/test_live.py -m live -v
"""

from __future__ import annotations

import csv
import io
import json

import pytest

from app_reviews import (
    AppStoreReviews,
    Country,
    GooglePlayReviews,
    Review,
    Sort,
)
from app_reviews.exporters.csv import export_csv
from app_reviews.exporters.json import export_json
from app_reviews.exporters.jsonl import export_jsonl

# Well-known, popular apps unlikely to be removed.
APPLE_APP_ID = "389801252"  # Instagram
GOOGLE_APP_ID = "com.google.android.apps.maps"  # Google Maps

_LIMIT = 20

pytestmark = pytest.mark.live


# ===================================================================
# App Store
# ===================================================================


class TestLiveAppStore:
    """Smoke tests for the App Store RSS scraper."""

    def test_fetch_returns_reviews(self) -> None:
        result = AppStoreReviews().fetch(
            APPLE_APP_ID, countries=[Country.US], limit=_LIMIT
        )
        assert len(result.reviews) > 0
        assert len(result.errors) == 0

        review = result.reviews[0]
        assert isinstance(review, Review)
        assert review.store == "appstore"
        assert review.app_id == APPLE_APP_ID
        assert review.country == "us"
        assert 1 <= review.rating <= 5
        assert review.body
        assert review.author_name
        assert review.created_at is not None

    def test_multi_country(self) -> None:
        result = AppStoreReviews().fetch(
            APPLE_APP_ID,
            countries=[Country.US, Country.GB],
            limit=_LIMIT,
        )
        assert len(result.reviews) > 0

    def test_filter_by_rating(self) -> None:
        result = AppStoreReviews().fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            ratings=[4, 5],
            limit=_LIMIT,
        )
        if result.reviews:
            assert all(r.rating >= 4 for r in result.reviews)

    def test_sort_newest(self) -> None:
        result = AppStoreReviews().fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            sort=Sort.NEWEST,
            limit=_LIMIT,
        )
        if len(result.reviews) >= 2:
            dates = [r.created_at for r in result.reviews]
            assert dates == sorted(dates, reverse=True)

    def test_limit(self) -> None:
        result = AppStoreReviews().fetch(APPLE_APP_ID, countries=[Country.US], limit=3)
        assert len(result.reviews) <= 3


# ===================================================================
# Google Play
# ===================================================================


class TestLiveGooglePlay:
    """Smoke tests for the Google Play batchexecute scraper."""

    def test_fetch_returns_reviews(self) -> None:
        result = GooglePlayReviews().fetch(
            GOOGLE_APP_ID, countries=[Country.US], limit=_LIMIT
        )
        assert len(result.reviews) > 0
        assert len(result.errors) == 0

        review = result.reviews[0]
        assert isinstance(review, Review)
        assert review.store == "googleplay"
        assert review.app_id == GOOGLE_APP_ID
        assert 1 <= review.rating <= 5
        assert review.body is not None
        assert review.author_name
        assert review.created_at is not None

    def test_multi_country(self) -> None:
        result = GooglePlayReviews().fetch(
            GOOGLE_APP_ID,
            countries=[Country.US, Country.GB],
            limit=_LIMIT,
        )
        assert len(result.reviews) > 0

    def test_filter_by_rating(self) -> None:
        result = GooglePlayReviews().fetch(
            GOOGLE_APP_ID,
            countries=[Country.US],
            ratings=[1, 2],
            limit=_LIMIT,
        )
        if result.reviews:
            assert all(r.rating <= 2 for r in result.reviews)

    def test_sort_newest(self) -> None:
        result = GooglePlayReviews().fetch(
            GOOGLE_APP_ID,
            countries=[Country.US],
            sort=Sort.NEWEST,
            limit=_LIMIT,
        )
        if len(result.reviews) >= 2:
            dates = [r.created_at for r in result.reviews]
            assert dates == sorted(dates, reverse=True)

    def test_limit(self) -> None:
        result = GooglePlayReviews().fetch(
            GOOGLE_APP_ID, countries=[Country.US], limit=3
        )
        assert len(result.reviews) <= 3


# ===================================================================
# Exports — verify all formats work with real data
# ===================================================================


class TestLiveExport:
    """Export real reviews to JSON, JSONL, and CSV."""

    def test_all_formats(self) -> None:
        result = GooglePlayReviews().fetch(
            GOOGLE_APP_ID, countries=[Country.US], limit=5
        )
        assert result.reviews, "Need reviews to test exports"
        reviews = result.reviews

        # JSON
        parsed = json.loads(export_json(reviews))
        assert len(parsed) == len(reviews)
        assert parsed[0]["store"] == "googleplay"

        # JSONL
        lines = [ln for ln in export_jsonl(reviews).strip().split("\n") if ln]
        assert len(lines) == len(reviews)

        # CSV
        rows = list(csv.DictReader(io.StringIO(export_csv(reviews))))
        assert len(rows) == len(reviews)


# ===================================================================
# FetchResult operations
# ===================================================================


class TestLiveFetchResult:
    """FetchResult iteration, chaining, and immutability."""

    def test_filter_sort_limit_chain(self) -> None:
        result = GooglePlayReviews().fetch(
            GOOGLE_APP_ID, countries=[Country.US], limit=_LIMIT
        )
        original_count = len(result)

        refined = result.filter(ratings=[3, 4, 5]).sort(Sort.NEWEST).limit(5)

        # Original unchanged
        assert len(result) == original_count
        # Chain applied
        assert len(refined) <= 5
        if refined.reviews:
            assert all(r.rating >= 3 for r in refined.reviews)


# ===================================================================
# Cross-store consistency
# ===================================================================


class TestLiveCrossStore:
    """Both stores produce structurally consistent output."""

    def test_same_json_keys(self) -> None:
        as_result = AppStoreReviews().fetch(
            APPLE_APP_ID, countries=[Country.US], limit=1
        )
        gp_result = GooglePlayReviews().fetch(
            GOOGLE_APP_ID, countries=[Country.US], limit=1
        )
        if as_result.reviews and gp_result.reviews:
            as_keys = set(json.loads(export_json(as_result.reviews))[0].keys())
            gp_keys = set(json.loads(export_json(gp_result.reviews))[0].keys())
            assert as_keys == gp_keys

    def test_core_fields_populated(self) -> None:
        as_result = AppStoreReviews().fetch(
            APPLE_APP_ID, countries=[Country.US], limit=1
        )
        gp_result = GooglePlayReviews().fetch(
            GOOGLE_APP_ID, countries=[Country.US], limit=1
        )
        for label, result, store in [
            ("App Store", as_result, "appstore"),
            ("Google Play", gp_result, "googleplay"),
        ]:
            assert result.reviews, f"{label} returned no reviews"
            r = result.reviews[0]
            assert r.store == store
            assert r.app_id
            assert 1 <= r.rating <= 5
            assert r.author_name
            assert r.created_at is not None
