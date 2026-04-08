"""Live E2E tests that hit real store endpoints.

These tests are NOT run in normal CI. They are only run by the
scheduled GitHub Action (scheduled_e2e_test.yml) to verify that
the scrapers still work against live APIs.

Run manually with: pytest tests/app_reviews/e2e/test_live.py -m live
"""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime, timedelta

import pytest

from app_reviews import (
    AppStoreReviews,
    Country,
    FetchResult,
    GooglePlayReviews,
    Review,
    Sort,
)
from app_reviews.exporters.csv import export_csv
from app_reviews.exporters.json import export_json
from app_reviews.exporters.jsonl import export_jsonl

# Well-known, stable apps unlikely to be removed.
APPLE_APP_ID = "364709193"  # iBooks / Apple Books
GOOGLE_APP_ID = "com.google.android.apps.maps"  # Google Maps

# Cap live fetches to avoid hanging on popular apps with thousands of pages.
_DEFAULT_LIMIT = 50

pytestmark = pytest.mark.live


def _print_stats(store: str, result: FetchResult) -> None:
    """Print a summary table for CI logs."""
    countries = sorted({r.country for r in result.reviews})
    ratings: dict[int, int] = {}
    for r in result.reviews:
        ratings[r.rating] = ratings.get(r.rating, 0) + 1

    print(f"\n{'=' * 50}")
    print(f"  {store} E2E Results")
    print(f"{'=' * 50}")
    print(f"  Reviews:     {len(result.reviews)}")
    print(f"  Countries:   {len(countries)} ({', '.join(countries)})")
    print(f"  Errors:      {len(result.errors)}")
    print(f"  Ratings:     {dict(sorted(ratings.items()))}")
    if result.reviews:
        sample = result.reviews[0]
        print(
            f"  Sample:      [{sample.rating}*]"
            f" {sample.title!r} by {sample.author_name}"
        )
    print(f"{'=' * 50}\n")


# ===================================================================
# App Store — basic fetch
# ===================================================================


class TestLiveAppStoreFetch:
    """Core fetch flows against the real App Store RSS API."""

    def test_single_country_returns_reviews(self) -> None:
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            limit=_DEFAULT_LIMIT,
        )

        _print_stats("App Store (US)", result)

        assert len(result.reviews) > 0, "Expected at least one review"
        assert len(result.errors) == 0, f"Unexpected errors: {result.errors}"

        review = result.reviews[0]
        assert isinstance(review, Review)
        assert review.store == "appstore"
        assert review.app_id == APPLE_APP_ID
        assert review.country == "us"
        assert review.source == "appstore_scraper"
        assert 1 <= review.rating <= 5
        assert review.title
        assert review.body
        assert review.author_name
        assert review.created_at is not None
        assert review.fetched_at is not None
        assert review.id.startswith("appstore_scraper-")

    def test_multiple_countries(self) -> None:
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US, Country.GB],
            limit=_DEFAULT_LIMIT,
        )

        _print_stats("App Store (US + GB)", result)

        assert len(result.reviews) > 0
        countries = {r.country for r in result.reviews}
        # At least one country should have reviews
        assert len(countries) >= 1

    def test_three_countries(self) -> None:
        """Fetch from US, GB, and DE to verify parallel execution."""
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US, Country.GB, Country.DE],
            limit=_DEFAULT_LIMIT,
        )

        _print_stats("App Store (US + GB + DE)", result)

        assert len(result.reviews) > 0
        # Reviews from multiple countries should be present
        countries = {r.country for r in result.reviews}
        assert len(countries) >= 1


# ===================================================================
# App Store — filtering
# ===================================================================


class TestLiveAppStoreFiltering:
    """Filter, sort, and limit with real data."""

    def test_filter_by_high_ratings(self) -> None:
        """Only 4- and 5-star reviews."""
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            ratings=[4, 5],
            limit=_DEFAULT_LIMIT,
        )

        _print_stats("App Store (ratings 4-5)", result)

        if result.reviews:
            assert all(r.rating >= 4 for r in result.reviews)

    def test_filter_by_low_ratings(self) -> None:
        """Only 1- and 2-star reviews."""
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            ratings=[1, 2],
            limit=_DEFAULT_LIMIT,
        )

        _print_stats("App Store (ratings 1-2)", result)

        if result.reviews:
            assert all(r.rating <= 2 for r in result.reviews)

    def test_filter_by_single_rating(self) -> None:
        """Only 5-star reviews."""
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            ratings=[5],
            limit=_DEFAULT_LIMIT,
        )

        if result.reviews:
            assert all(r.rating == 5 for r in result.reviews)

    def test_filter_since_date(self) -> None:
        """Reviews from the last year only."""
        since = datetime.now(tz=UTC) - timedelta(days=365)
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            since=since,
            limit=_DEFAULT_LIMIT,
        )

        _print_stats("App Store (last year)", result)

        if result.reviews:
            assert all(r.created_at >= since for r in result.reviews)

    def test_filter_until_date(self) -> None:
        """Reviews before a certain date."""
        until = datetime(2024, 1, 1, tzinfo=UTC)
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            until=until,
            limit=_DEFAULT_LIMIT,
        )

        if result.reviews:
            assert all(r.created_at <= until for r in result.reviews)

    def test_filter_date_range(self) -> None:
        """Reviews within a specific date window."""
        since = datetime(2024, 1, 1, tzinfo=UTC)
        until = datetime(2024, 12, 31, tzinfo=UTC)
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            since=since,
            until=until,
            limit=_DEFAULT_LIMIT,
        )

        _print_stats("App Store (2024 only)", result)

        if result.reviews:
            for r in result.reviews:
                assert since <= r.created_at <= until

    def test_combined_rating_and_date_filter(self) -> None:
        """5-star reviews from the last 6 months."""
        since = datetime.now(tz=UTC) - timedelta(days=180)
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            ratings=[5],
            since=since,
            limit=_DEFAULT_LIMIT,
        )

        if result.reviews:
            assert all(r.rating == 5 for r in result.reviews)
            assert all(r.created_at >= since for r in result.reviews)


# ===================================================================
# App Store — sorting
# ===================================================================


class TestLiveAppStoreSorting:
    """Sort order verification with real data."""

    def test_sort_newest(self) -> None:
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            sort=Sort.NEWEST,
            limit=_DEFAULT_LIMIT,
        )

        if len(result.reviews) >= 2:
            dates = [r.created_at for r in result.reviews]
            assert dates == sorted(dates, reverse=True), "Not sorted newest first"

    def test_sort_oldest(self) -> None:
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            sort=Sort.OLDEST,
            limit=_DEFAULT_LIMIT,
        )

        if len(result.reviews) >= 2:
            dates = [r.created_at for r in result.reviews]
            assert dates == sorted(dates), "Not sorted oldest first"

    def test_sort_by_rating(self) -> None:
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            sort=Sort.RATING,
            limit=_DEFAULT_LIMIT,
        )

        if len(result.reviews) >= 2:
            ratings = [r.rating for r in result.reviews]
            assert ratings == sorted(ratings, reverse=True), "Not sorted by rating"


# ===================================================================
# App Store — limit
# ===================================================================


class TestLiveAppStoreLimit:
    """Limit caps results."""

    def test_limit_reduces_count(self) -> None:
        client = AppStoreReviews()
        full = client.fetch(APPLE_APP_ID, countries=[Country.US], limit=20)
        limited = client.fetch(APPLE_APP_ID, countries=[Country.US], limit=3)

        if len(full.reviews) > 3:
            assert len(limited.reviews) == 3

    def test_limit_one(self) -> None:
        client = AppStoreReviews()
        result = client.fetch(APPLE_APP_ID, countries=[Country.US], limit=1)

        assert len(result.reviews) <= 1


# ===================================================================
# App Store — exports
# ===================================================================


class TestLiveAppStoreExport:
    """Export real fetched data to all formats."""

    def test_json_export(self) -> None:
        client = AppStoreReviews()
        result = client.fetch(APPLE_APP_ID, countries=[Country.US], limit=5)

        text = export_json(result.reviews)
        parsed = json.loads(text)
        assert isinstance(parsed, list)
        assert len(parsed) == len(result.reviews)
        if parsed:
            assert parsed[0]["store"] == "appstore"
            assert parsed[0]["app_id"] == APPLE_APP_ID
            assert "raw" not in parsed[0]

    def test_json_export_include_raw(self) -> None:
        client = AppStoreReviews()
        result = client.fetch(APPLE_APP_ID, countries=[Country.US], limit=2)

        text = export_json(result.reviews, include_raw=True)
        parsed = json.loads(text)
        if parsed:
            assert "raw" in parsed[0]
            assert parsed[0]["raw"] is not None

    def test_jsonl_export(self) -> None:
        client = AppStoreReviews()
        result = client.fetch(APPLE_APP_ID, countries=[Country.US], limit=5)

        text = export_jsonl(result.reviews)
        lines = [ln for ln in text.strip().split("\n") if ln]
        assert len(lines) == len(result.reviews)
        for line in lines:
            obj = json.loads(line)
            assert obj["store"] == "appstore"

    def test_csv_export(self) -> None:
        client = AppStoreReviews()
        result = client.fetch(APPLE_APP_ID, countries=[Country.US], limit=5)

        text = export_csv(result.reviews)
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        assert len(rows) == len(result.reviews)
        if rows:
            assert rows[0]["app_id"] == APPLE_APP_ID
            assert rows[0]["source"] == "appstore_scraper"


# ===================================================================
# App Store — FetchResult operations
# ===================================================================


class TestLiveAppStoreFetchResult:
    """FetchResult protocol and chaining with real data."""

    def test_iteration(self) -> None:
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            limit=_DEFAULT_LIMIT,
        )

        collected = list(result)
        assert len(collected) == len(result.reviews)
        assert all(isinstance(r, Review) for r in collected)

    def test_bool_truthy(self) -> None:
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            limit=_DEFAULT_LIMIT,
        )

        assert result, "Expected non-empty result to be truthy"

    def test_to_dicts(self) -> None:
        client = AppStoreReviews()
        result = client.fetch(APPLE_APP_ID, countries=[Country.US], limit=3)

        dicts = result.to_dicts()
        assert isinstance(dicts, list)
        assert len(dicts) == len(result.reviews)
        if dicts:
            d = dicts[0]
            assert isinstance(d, dict)
            assert "store" in d
            assert "rating" in d
            assert "title" in d
            assert "body" in d

    def test_post_fetch_filter_does_not_mutate(self) -> None:
        """filter() returns new FetchResult, original unchanged."""
        client = AppStoreReviews()
        original = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            limit=_DEFAULT_LIMIT,
        )
        original_count = len(original)

        filtered = original.filter(ratings=[5])

        assert len(original) == original_count  # original unchanged
        if original_count > 0:
            assert len(filtered) <= original_count

    def test_post_fetch_sort_does_not_mutate(self) -> None:
        client = AppStoreReviews()
        original = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            limit=_DEFAULT_LIMIT,
        )
        original_ids = [r.id for r in original]

        sorted_result = original.sort(Sort.OLDEST)

        assert [r.id for r in original] == original_ids  # original order preserved
        assert len(sorted_result) == len(original)

    def test_chained_filter_sort_limit(self) -> None:
        """Full post-fetch pipeline: filter → sort → limit."""
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            limit=_DEFAULT_LIMIT,
        )

        refined = result.filter(ratings=[4, 5]).sort(Sort.OLDEST).limit(3)

        assert len(refined) <= 3
        if refined.reviews:
            assert all(r.rating >= 4 for r in refined.reviews)
        if len(refined.reviews) >= 2:
            dates = [r.created_at for r in refined.reviews]
            assert dates == sorted(dates)

    def test_failed_countries_empty_on_success(self) -> None:
        client = AppStoreReviews()
        result = client.fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            limit=_DEFAULT_LIMIT,
        )

        assert [e.country for e in result.errors] == []


# ===================================================================
# Google Play — basic fetch
# ===================================================================


class TestLiveGooglePlayFetch:
    """Core fetch flows against the real Google Play batchexecute API."""

    def test_single_country_returns_reviews(self) -> None:
        client = GooglePlayReviews()
        result = client.fetch(
            GOOGLE_APP_ID,
            countries=[Country.US],
            limit=_DEFAULT_LIMIT,
        )

        _print_stats("Google Play (US)", result)

        assert len(result.reviews) > 0, "Expected at least one review"
        assert len(result.errors) == 0, f"Unexpected errors: {result.errors}"

        review = result.reviews[0]
        assert isinstance(review, Review)
        assert review.store == "googleplay"
        assert review.app_id == GOOGLE_APP_ID
        assert review.source == "googleplay_scraper"
        assert 1 <= review.rating <= 5
        assert review.body is not None
        assert review.author_name
        assert review.created_at is not None
        assert review.fetched_at is not None
        assert review.id.startswith("googleplay_scraper-")

    def test_multiple_countries(self) -> None:
        client = GooglePlayReviews()
        result = client.fetch(
            GOOGLE_APP_ID,
            countries=[Country.US, Country.GB],
            limit=_DEFAULT_LIMIT,
        )

        _print_stats("Google Play (US + GB)", result)

        assert len(result.reviews) > 0

    def test_three_countries(self) -> None:
        """Fetch from US, GB, and JP to verify parallel execution."""
        client = GooglePlayReviews()
        result = client.fetch(
            GOOGLE_APP_ID,
            countries=[Country.US, Country.GB, Country.JP],
            limit=_DEFAULT_LIMIT,
        )

        _print_stats("Google Play (US + GB + JP)", result)

        assert len(result.reviews) > 0


# ===================================================================
# Google Play — filtering
# ===================================================================


class TestLiveGooglePlayFiltering:
    """Filter, sort, and limit with real Google Play data."""

    def test_filter_by_high_ratings(self) -> None:
        client = GooglePlayReviews()
        result = client.fetch(
            GOOGLE_APP_ID,
            countries=[Country.US],
            ratings=[4, 5],
            limit=_DEFAULT_LIMIT,
        )

        _print_stats("Google Play (ratings 4-5)", result)

        if result.reviews:
            assert all(r.rating >= 4 for r in result.reviews)

    def test_filter_by_low_ratings(self) -> None:
        client = GooglePlayReviews()
        result = client.fetch(
            GOOGLE_APP_ID,
            countries=[Country.US],
            ratings=[1, 2],
            limit=_DEFAULT_LIMIT,
        )

        if result.reviews:
            assert all(r.rating <= 2 for r in result.reviews)

    def test_filter_since_date(self) -> None:
        since = datetime.now(tz=UTC) - timedelta(days=365)
        client = GooglePlayReviews()
        result = client.fetch(
            GOOGLE_APP_ID,
            countries=[Country.US],
            since=since,
            limit=_DEFAULT_LIMIT,
        )

        if result.reviews:
            assert all(r.created_at >= since for r in result.reviews)

    def test_filter_date_range(self) -> None:
        since = datetime(2024, 1, 1, tzinfo=UTC)
        until = datetime(2024, 12, 31, tzinfo=UTC)
        client = GooglePlayReviews()
        result = client.fetch(
            GOOGLE_APP_ID,
            countries=[Country.US],
            since=since,
            until=until,
            limit=_DEFAULT_LIMIT,
        )

        if result.reviews:
            for r in result.reviews:
                assert since <= r.created_at <= until

    def test_combined_rating_and_date_filter(self) -> None:
        since = datetime.now(tz=UTC) - timedelta(days=180)
        client = GooglePlayReviews()
        result = client.fetch(
            GOOGLE_APP_ID,
            countries=[Country.US],
            ratings=[1],
            since=since,
            limit=_DEFAULT_LIMIT,
        )

        if result.reviews:
            assert all(r.rating == 1 for r in result.reviews)
            assert all(r.created_at >= since for r in result.reviews)


# ===================================================================
# Google Play — sorting
# ===================================================================


class TestLiveGooglePlaySorting:
    """Sort order verification with real Google Play data."""

    def test_sort_newest(self) -> None:
        client = GooglePlayReviews()
        result = client.fetch(
            GOOGLE_APP_ID,
            countries=[Country.US],
            sort=Sort.NEWEST,
            limit=_DEFAULT_LIMIT,
        )

        if len(result.reviews) >= 2:
            dates = [r.created_at for r in result.reviews]
            assert dates == sorted(dates, reverse=True)

    def test_sort_oldest(self) -> None:
        client = GooglePlayReviews()
        result = client.fetch(
            GOOGLE_APP_ID,
            countries=[Country.US],
            sort=Sort.OLDEST,
            limit=_DEFAULT_LIMIT,
        )

        if len(result.reviews) >= 2:
            dates = [r.created_at for r in result.reviews]
            assert dates == sorted(dates)

    def test_sort_by_rating(self) -> None:
        client = GooglePlayReviews()
        result = client.fetch(
            GOOGLE_APP_ID,
            countries=[Country.US],
            sort=Sort.RATING,
            limit=_DEFAULT_LIMIT,
        )

        if len(result.reviews) >= 2:
            ratings = [r.rating for r in result.reviews]
            assert ratings == sorted(ratings, reverse=True)


# ===================================================================
# Google Play — limit
# ===================================================================


class TestLiveGooglePlayLimit:
    """Limit caps Google Play results."""

    def test_limit_reduces_count(self) -> None:
        client = GooglePlayReviews()
        full = client.fetch(GOOGLE_APP_ID, countries=[Country.US], limit=20)
        limited = client.fetch(GOOGLE_APP_ID, countries=[Country.US], limit=5)

        if len(full.reviews) > 5:
            assert len(limited.reviews) == 5

    def test_limit_one(self) -> None:
        client = GooglePlayReviews()
        result = client.fetch(GOOGLE_APP_ID, countries=[Country.US], limit=1)

        assert len(result.reviews) <= 1


# ===================================================================
# Google Play — exports
# ===================================================================


class TestLiveGooglePlayExport:
    """Export real Google Play data to all formats."""

    def test_json_export(self) -> None:
        client = GooglePlayReviews()
        result = client.fetch(GOOGLE_APP_ID, countries=[Country.US], limit=5)

        text = export_json(result.reviews)
        parsed = json.loads(text)
        assert isinstance(parsed, list)
        assert len(parsed) == len(result.reviews)
        if parsed:
            assert parsed[0]["store"] == "googleplay"
            assert parsed[0]["app_id"] == GOOGLE_APP_ID

    def test_jsonl_export(self) -> None:
        client = GooglePlayReviews()
        result = client.fetch(GOOGLE_APP_ID, countries=[Country.US], limit=5)

        text = export_jsonl(result.reviews)
        lines = [ln for ln in text.strip().split("\n") if ln]
        assert len(lines) == len(result.reviews)
        for line in lines:
            obj = json.loads(line)
            assert obj["store"] == "googleplay"

    def test_csv_export(self) -> None:
        client = GooglePlayReviews()
        result = client.fetch(GOOGLE_APP_ID, countries=[Country.US], limit=5)

        text = export_csv(result.reviews)
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        assert len(rows) == len(result.reviews)
        if rows:
            assert rows[0]["source"] == "googleplay_scraper"


# ===================================================================
# Google Play — FetchResult operations
# ===================================================================


class TestLiveGooglePlayFetchResult:
    """FetchResult protocol and chaining with real Google Play data."""

    def test_iteration_and_len(self) -> None:
        client = GooglePlayReviews()
        result = client.fetch(
            GOOGLE_APP_ID,
            countries=[Country.US],
            limit=_DEFAULT_LIMIT,
        )

        collected = list(result)
        assert len(collected) == len(result)

    def test_to_dicts(self) -> None:
        client = GooglePlayReviews()
        result = client.fetch(GOOGLE_APP_ID, countries=[Country.US], limit=3)

        dicts = result.to_dicts()
        assert len(dicts) == len(result.reviews)
        if dicts:
            assert isinstance(dicts[0], dict)
            assert dicts[0]["store"] == "googleplay"

    def test_chained_filter_sort_limit(self) -> None:
        client = GooglePlayReviews()
        result = client.fetch(
            GOOGLE_APP_ID,
            countries=[Country.US],
            limit=_DEFAULT_LIMIT,
        )

        refined = result.filter(ratings=[3, 4, 5]).sort(Sort.NEWEST).limit(5)

        assert len(refined) <= 5
        if refined.reviews:
            assert all(r.rating >= 3 for r in refined.reviews)
        if len(refined.reviews) >= 2:
            dates = [r.created_at for r in refined.reviews]
            assert dates == sorted(dates, reverse=True)


# ===================================================================
# Cross-store consistency
# ===================================================================


class TestLiveCrossStore:
    """Verify both stores produce structurally consistent output."""

    def test_json_export_same_keys(self) -> None:
        """Both stores produce JSON with identical top-level keys."""
        as_result = AppStoreReviews().fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            limit=1,
        )
        gp_result = GooglePlayReviews().fetch(
            GOOGLE_APP_ID,
            countries=[Country.US],
            limit=1,
        )

        if as_result.reviews and gp_result.reviews:
            as_json = json.loads(export_json(as_result.reviews))
            gp_json = json.loads(export_json(gp_result.reviews))
            assert set(as_json[0].keys()) == set(gp_json[0].keys())

    def test_csv_export_same_columns(self) -> None:
        """Both stores produce CSV with identical column headers."""
        as_result = AppStoreReviews().fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            limit=1,
        )
        gp_result = GooglePlayReviews().fetch(
            GOOGLE_APP_ID,
            countries=[Country.US],
            limit=1,
        )

        if as_result.reviews and gp_result.reviews:
            as_csv = export_csv(as_result.reviews)
            gp_csv = export_csv(gp_result.reviews)
            as_reader = csv.DictReader(io.StringIO(as_csv))
            gp_reader = csv.DictReader(io.StringIO(gp_csv))
            assert as_reader.fieldnames == gp_reader.fieldnames

    def test_review_model_fields_populated(self) -> None:
        """Both stores populate core Review fields."""
        as_result = AppStoreReviews().fetch(
            APPLE_APP_ID,
            countries=[Country.US],
            limit=1,
        )
        gp_result = GooglePlayReviews().fetch(
            GOOGLE_APP_ID,
            countries=[Country.US],
            limit=1,
        )

        for label, result, expected_store in [
            ("App Store", as_result, "appstore"),
            ("Google Play", gp_result, "googleplay"),
        ]:
            assert result.reviews, f"{label} returned no reviews"
            r = result.reviews[0]
            assert r.store == expected_store, f"{label}: wrong store"
            assert r.app_id, f"{label}: missing app_id"
            assert 1 <= r.rating <= 5, f"{label}: invalid rating {r.rating}"
            assert r.author_name, f"{label}: missing author_name"
            assert r.created_at is not None, f"{label}: missing created_at"
            assert r.fetched_at is not None, f"{label}: missing fetched_at"
            assert r.source, f"{label}: missing source"
            assert r.id, f"{label}: missing id"
