"""Live E2E tests that hit real store endpoints.

These tests are NOT run in normal CI. They are only run by the
scheduled GitHub Action (scheduled_e2e_test.yml) to verify that
the scrapers still work against live APIs.

Run manually with: pytest tests/e2e/test_live.py -m live
"""

from __future__ import annotations

import pytest

from app_reviews import AppStoreReviews, Country, GooglePlayReviews, Review
from app_reviews.models.result import FetchResult

# A well-known, stable app that is unlikely to be removed.
APPLE_APP_ID = "364709193"  # iBooks / Apple Books
GOOGLE_APP_ID = "com.google.android.apps.maps"  # Google Maps


pytestmark = pytest.mark.live


def _print_stats(store: str, result: FetchResult) -> None:
    """Print a summary table for CI logs."""
    stats = result.stats
    countries = sorted({r.country for r in result.reviews})
    ratings = {}
    for r in result.reviews:
        ratings[r.rating] = ratings.get(r.rating, 0) + 1

    print(f"\n{'=' * 50}")
    print(f"  {store} E2E Results")
    print(f"{'=' * 50}")
    print(f"  Reviews:     {stats.total_reviews}")
    print(f"  Countries:   {stats.total_countries} ({', '.join(countries)})")
    print(f"  Failures:    {stats.total_failures}")
    print(f"  Warnings:    {stats.total_warnings}")
    print(f"  Ratings:     {dict(sorted(ratings.items()))}")
    if result.reviews:
        sample = result.reviews[0]
        print(
            f"  Sample:      [{sample.rating}*]"
            f" {sample.title!r} by {sample.author_name}"
        )
    print(f"{'=' * 50}\n")


class TestLiveAppStore:
    def test_fetch_returns_reviews(self) -> None:
        client = AppStoreReviews()
        result = client.fetch(APPLE_APP_ID, countries=[Country.US])

        _print_stats("App Store (single country)", result)

        assert len(result.reviews) > 0, "Expected at least one review from App Store"
        assert result.failures == [], f"Unexpected failures: {result.failures}"

        review = result.reviews[0]
        assert isinstance(review, Review)
        assert review.store == "appstore"
        assert review.app_id == APPLE_APP_ID
        assert review.source == "appstore_scraper"
        assert 1 <= review.rating <= 5
        assert review.title is not None
        assert review.body is not None
        assert review.author_name != ""

    def test_fetch_multiple_countries(self) -> None:
        client = AppStoreReviews()
        result = client.fetch(APPLE_APP_ID, countries=[Country.US, Country.GB])

        _print_stats("App Store (multi country)", result)

        assert len(result.reviews) > 0
        assert result.stats.total_countries >= 1


class TestLiveGooglePlay:
    def test_fetch_returns_reviews(self) -> None:
        client = GooglePlayReviews()
        result = client.fetch(GOOGLE_APP_ID, countries=[Country.US])

        _print_stats("Google Play (single country)", result)

        assert len(result.reviews) > 0, "Expected at least one review from Google Play"
        assert result.failures == [], f"Unexpected failures: {result.failures}"

        review = result.reviews[0]
        assert isinstance(review, Review)
        assert review.store == "googleplay"
        assert review.app_id == GOOGLE_APP_ID
        assert review.source == "googleplay_scraper"
        assert 1 <= review.rating <= 5
        assert review.body is not None
        assert review.author_name != ""

    def test_fetch_multiple_countries(self) -> None:
        client = GooglePlayReviews()
        result = client.fetch(GOOGLE_APP_ID, countries=[Country.US, Country.GB])

        _print_stats("Google Play (multi country)", result)

        assert len(result.reviews) > 0
