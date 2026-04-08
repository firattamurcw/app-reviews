"""End-to-end tests covering the full fetch-to-export flow.

Tests exercise client → provider → execution → FetchResult → export
with mocked HTTP, covering both App Store and Google Play stores.
"""

import csv
import io
import json
from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch

from app_reviews import (
    AppStoreReviews,
    GooglePlayReviews,
    Review,
    Sort,
)
from app_reviews.exporters.csv import export_csv
from app_reviews.exporters.json import export_json
from app_reviews.exporters.jsonl import export_jsonl
from app_reviews.utils.http import HttpResponse

# ---------------------------------------------------------------------------
# App Store RSS helpers
# ---------------------------------------------------------------------------

_BASE_DT = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


def _make_rss_entry(
    review_id: str,
    rating: str = "5",
    title: str | None = None,
    body: str | None = None,
    author: str | None = None,
    version: str = "2.0",
    updated: str | None = None,
) -> dict[str, Any]:
    return {
        "id": {"label": review_id},
        "im:rating": {"label": rating},
        "title": {"label": title or f"Review {review_id}"},
        "content": {"label": body or f"Body for {review_id}"},
        "author": {"name": {"label": author or f"Author{review_id}"}},
        "im:version": {"label": version},
        "updated": {"label": updated or "2024-06-01T12:00:00-07:00"},
    }


def _rss_page(entries: list[dict[str, Any]]) -> HttpResponse:
    body = {"feed": {"entry": entries}} if entries else {"feed": {}}
    return HttpResponse(status=200, body=json.dumps(body))


def _rss_empty() -> HttpResponse:
    return HttpResponse(status=200, body=json.dumps({"feed": {}}))


# ---------------------------------------------------------------------------
# Google Play batchexecute helpers
# ---------------------------------------------------------------------------

_GP_PREFIX = ")]}'\n\n"
_GP_RPC_ID = "oCPfdb"


def _make_gp_review(
    review_id: str,
    author: str = "GPUser",
    rating: int = 4,
    body: str = "Nice app",
    created_ts: int = 1717200000,
    updated_ts: int | None = None,
    app_version: str | None = None,
) -> list[Any]:
    """Build a single batchexecute review array."""
    timestamps = [created_ts]
    if updated_ts:
        timestamps.append(updated_ts)
    entry: list[Any] = [
        review_id,  # 0: review ID
        [author],  # 1: author info
        rating,  # 2: rating
        None,  # 3: unused
        body,  # 4: body
        timestamps,  # 5: timestamps
        None,
        None,
        None,
        None,  # 6-9: unused
    ]
    if app_version:
        entry.append(app_version)
    return entry


def _gp_response(
    reviews: list[list[Any]],
    page_token: str | None = None,
) -> HttpResponse:
    """Build a valid batchexecute HTTP response.

    The parser expects: data[0] = reviews, data[-2][-1] = page_token.
    """
    # Structure: [reviews, token_container, trailing_null]
    # so data[-2] is the token_container
    if page_token:
        inner_data: list[Any] = [reviews, [None, page_token], None]
    else:
        inner_data = [reviews, None, None]
    inner_json = json.dumps(inner_data)
    outer = [["wrb.fr", _GP_RPC_ID, inner_json, None, None]]
    body = _GP_PREFIX + json.dumps(outer)
    return HttpResponse(status=200, body=body)


def _gp_empty() -> HttpResponse:
    """Empty Google Play response (no reviews)."""
    return _gp_response([])


# ===================================================================
# App Store E2E tests
# ===================================================================


class TestAppStoreFetchAndExport:
    """Full fetch-to-export flow for the App Store RSS scraper."""

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_single_country_json(self, mock_get: Any) -> None:
        """Fetch US reviews → JSON export with field verification."""
        entries = [
            _make_rss_entry("r1", "5", "Amazing", "Love it", "Alice"),
            _make_rss_entry("r2", "3", "Meh", "Could be better", "Bob"),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url and "/us/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"])

        assert len(result) == 2
        assert all(isinstance(r, Review) for r in result)

        text = export_json(result.reviews)
        parsed = json.loads(text)
        assert len(parsed) == 2
        assert parsed[0]["store"] == "appstore"
        assert parsed[0]["app_id"] == "12345"
        assert parsed[0]["country"] == "us"
        assert parsed[0]["source"] == "appstore_scraper"
        assert "raw" not in parsed[0]  # raw excluded by default

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_single_country_json_include_raw(self, mock_get: Any) -> None:
        """JSON export with include_raw=True preserves raw data."""
        entries = [_make_rss_entry("r1")]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"])

        text = export_json(result.reviews, include_raw=True)
        parsed = json.loads(text)
        assert "raw" in parsed[0]
        assert parsed[0]["raw"]["id"]["label"] == "r1"

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_single_country_jsonl(self, mock_get: Any) -> None:
        """Fetch → JSONL export, each line is valid JSON."""
        entries = [
            _make_rss_entry("r1", "5"),
            _make_rss_entry("r2", "4"),
            _make_rss_entry("r3", "2"),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"])

        text = export_jsonl(result.reviews)
        lines = [ln for ln in text.strip().split("\n") if ln]
        assert len(lines) == 3
        for line in lines:
            obj = json.loads(line)
            assert obj["app_id"] == "12345"
            assert obj["store"] == "appstore"

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_single_country_csv(self, mock_get: Any) -> None:
        """Fetch → CSV export, header and rows."""
        entries = [
            _make_rss_entry("r1", "5", "Great", "Love", "Alice", "3.1"),
            _make_rss_entry("r2", "1", "Bad", "Hate", "Bob", "3.0"),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"])

        text = export_csv(result.reviews)
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["app_id"] == "12345"
        assert rows[0]["rating"] == "5"
        assert rows[1]["rating"] == "1"
        assert "id" in reader.fieldnames
        assert "body" in reader.fieldnames

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_multiple_countries(self, mock_get: Any) -> None:
        """Fetches from US and GB, reviews tagged with correct country."""

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" not in url:
                return _rss_empty()
            if "/us/" in url:
                return _rss_page(
                    [
                        _make_rss_entry("us-1", "5"),
                        _make_rss_entry("us-2", "4"),
                    ]
                )
            if "/gb/" in url:
                return _rss_page([_make_rss_entry("gb-1", "3")])
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("99999", countries=["us", "gb"])

        assert len(result) == 3
        countries = {r.country for r in result}
        assert countries == {"us", "gb"}

        us_reviews = [r for r in result if r.country == "us"]
        gb_reviews = [r for r in result if r.country == "gb"]
        assert len(us_reviews) == 2
        assert len(gb_reviews) == 1

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_pagination_multiple_pages(self, mock_get: Any) -> None:
        """Two pages of reviews are stitched together."""
        page1_entries = [_make_rss_entry("p1-1"), _make_rss_entry("p1-2")]
        page2_entries = [_make_rss_entry("p2-1")]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(page1_entries)
            if "/page=2/" in url:
                return _rss_page(page2_entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"])

        assert len(result) == 3
        ids = {r.id for r in result}
        assert "appstore_scraper-p1-1" in ids
        assert "appstore_scraper-p2-1" in ids


class TestAppStoreFiltering:
    """Filter, sort, and limit through the client API."""

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_filter_by_ratings(self, mock_get: Any) -> None:
        """Only return reviews matching requested ratings."""
        entries = [
            _make_rss_entry("r1", "5"),
            _make_rss_entry("r2", "3"),
            _make_rss_entry("r3", "1"),
            _make_rss_entry("r4", "5"),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"], ratings=[5])

        assert len(result) == 2
        assert all(r.rating == 5 for r in result)

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_filter_by_multiple_ratings(self, mock_get: Any) -> None:
        """Filter for ratings 1 and 2."""
        entries = [
            _make_rss_entry("r1", "5"),
            _make_rss_entry("r2", "2"),
            _make_rss_entry("r3", "1"),
            _make_rss_entry("r4", "3"),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"], ratings=[1, 2])

        assert len(result) == 2
        assert {r.rating for r in result} == {1, 2}

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_filter_by_since(self, mock_get: Any) -> None:
        """Only reviews after the since cutoff."""
        entries = [
            _make_rss_entry("old", updated="2024-01-01T00:00:00+00:00"),
            _make_rss_entry("new", updated="2024-08-01T00:00:00+00:00"),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        since = datetime(2024, 6, 1, tzinfo=UTC)
        result = AppStoreReviews().fetch("12345", countries=["us"], since=since)

        assert len(result) == 1
        assert result.reviews[0].id == "appstore_scraper-new"

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_filter_by_until(self, mock_get: Any) -> None:
        """Only reviews before the until cutoff."""
        entries = [
            _make_rss_entry("old", updated="2024-01-01T00:00:00+00:00"),
            _make_rss_entry("new", updated="2024-08-01T00:00:00+00:00"),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        until = datetime(2024, 6, 1, tzinfo=UTC)
        result = AppStoreReviews().fetch("12345", countries=["us"], until=until)

        assert len(result) == 1
        assert result.reviews[0].id == "appstore_scraper-old"

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_filter_since_and_until_combined(self, mock_get: Any) -> None:
        """Date range filter with both since and until."""
        entries = [
            _make_rss_entry("jan", updated="2024-01-15T00:00:00+00:00"),
            _make_rss_entry("mar", updated="2024-03-15T00:00:00+00:00"),
            _make_rss_entry("jun", updated="2024-06-15T00:00:00+00:00"),
            _make_rss_entry("sep", updated="2024-09-15T00:00:00+00:00"),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch(
            "12345",
            countries=["us"],
            since=datetime(2024, 2, 1, tzinfo=UTC),
            until=datetime(2024, 7, 1, tzinfo=UTC),
        )

        assert len(result) == 2
        ids = {r.id for r in result}
        assert "appstore_scraper-mar" in ids
        assert "appstore_scraper-jun" in ids

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_filter_ratings_and_date_combined(self, mock_get: Any) -> None:
        """Combine rating + date range filter."""
        entries = [
            _make_rss_entry("old5", "5", updated="2024-01-01T00:00:00+00:00"),
            _make_rss_entry("new5", "5", updated="2024-08-01T00:00:00+00:00"),
            _make_rss_entry("new1", "1", updated="2024-08-01T00:00:00+00:00"),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch(
            "12345",
            countries=["us"],
            ratings=[5],
            since=datetime(2024, 6, 1, tzinfo=UTC),
        )

        assert len(result) == 1
        assert result.reviews[0].id == "appstore_scraper-new5"

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_sort_newest(self, mock_get: Any) -> None:
        """Default sort: newest first."""
        entries = [
            _make_rss_entry("old", updated="2024-01-01T00:00:00+00:00"),
            _make_rss_entry("new", updated="2024-08-01T00:00:00+00:00"),
            _make_rss_entry("mid", updated="2024-05-01T00:00:00+00:00"),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"], sort=Sort.NEWEST)

        dates = [r.created_at for r in result]
        assert dates == sorted(dates, reverse=True)

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_sort_oldest(self, mock_get: Any) -> None:
        """Sort oldest first."""
        entries = [
            _make_rss_entry("old", updated="2024-01-01T00:00:00+00:00"),
            _make_rss_entry("new", updated="2024-08-01T00:00:00+00:00"),
            _make_rss_entry("mid", updated="2024-05-01T00:00:00+00:00"),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"], sort=Sort.OLDEST)

        dates = [r.created_at for r in result]
        assert dates == sorted(dates)

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_sort_rating(self, mock_get: Any) -> None:
        """Sort by rating descending."""
        entries = [
            _make_rss_entry("r1", "3"),
            _make_rss_entry("r2", "5"),
            _make_rss_entry("r3", "1"),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"], sort=Sort.RATING)

        ratings = [r.rating for r in result]
        assert ratings == sorted(ratings, reverse=True)

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_limit(self, mock_get: Any) -> None:
        """Limit caps the number of returned reviews."""
        entries = [_make_rss_entry(f"r{i}") for i in range(5)]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"], limit=2)

        assert len(result) == 2

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_chained_filter_sort_limit(self, mock_get: Any) -> None:
        """Full pipeline: fetch → filter → sort → limit."""
        entries = [
            _make_rss_entry("r1", "5", updated="2024-01-01T00:00:00+00:00"),
            _make_rss_entry("r2", "5", updated="2024-03-01T00:00:00+00:00"),
            _make_rss_entry("r3", "5", updated="2024-06-01T00:00:00+00:00"),
            _make_rss_entry("r4", "3", updated="2024-07-01T00:00:00+00:00"),
            _make_rss_entry("r5", "5", updated="2024-09-01T00:00:00+00:00"),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch(
            "12345",
            countries=["us"],
            ratings=[5],
            sort=Sort.OLDEST,
            limit=2,
        )

        # 4 five-star reviews, sorted oldest first, limited to 2
        assert len(result) == 2
        assert all(r.rating == 5 for r in result)
        assert result.reviews[0].created_at < result.reviews[1].created_at


class TestAppStoreErrorHandling:
    """Partial and total failure scenarios."""

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_partial_failure_keeps_successful_reviews(self, mock_get: Any) -> None:
        """One country fails, the other succeeds; reviews and errors both present."""

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/gb/" in url:
                return HttpResponse(status=500, body="internal error")
            if "/page=1/" in url:
                return _rss_page([_make_rss_entry("us-1")])
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us", "gb"])

        assert len(result.reviews) == 1
        assert result.reviews[0].country == "us"
        assert len(result.errors) == 1
        assert result.errors[0].country == "gb"
        assert [e.country for e in result.errors] == ["gb"]

        # Still exportable
        text = export_json(result.reviews)
        assert json.loads(text)

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_total_failure_all_countries(self, mock_get: Any) -> None:
        """All countries fail: empty reviews, errors for each country."""
        mock_get.return_value = HttpResponse(status=500, body="error")

        result = AppStoreReviews().fetch("12345", countries=["us", "gb", "de"])

        assert len(result.reviews) == 0
        assert len(result.errors) == 3
        assert set([e.country for e in result.errors]) == {"us", "gb", "de"}
        assert not result  # bool(FetchResult) is False when no reviews

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_empty_feed_returns_empty_result(self, mock_get: Any) -> None:
        """RSS feed with no entries returns FetchResult with no reviews."""
        mock_get.return_value = _rss_empty()

        result = AppStoreReviews().fetch("12345", countries=["us"])

        assert len(result) == 0
        assert len(result.errors) == 0
        assert not result

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_no_countries_returns_empty_result(self, mock_get: Any) -> None:
        """Fetch with empty country list returns empty result."""
        mock_get.return_value = _rss_empty()
        result = AppStoreReviews().fetch("12345", countries=[])

        assert len(result) == 0


# ===================================================================
# Google Play E2E tests
# ===================================================================


class TestGooglePlayFetchAndExport:
    """Full fetch-to-export flow for the Google Play batchexecute scraper."""

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_single_country_json(self, mock_post: Any) -> None:
        """Fetch Google Play reviews → JSON export."""
        reviews_data = [
            _make_gp_review("gp-1", "Alice", 5, "Fantastic", 1717200000),
            _make_gp_review("gp-2", "Bob", 2, "Buggy", 1717300000),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            return _gp_response(reviews_data)

        mock_post.side_effect = handler
        result = GooglePlayReviews().fetch("com.example.app", countries=["us"])

        assert len(result) == 2
        assert all(isinstance(r, Review) for r in result)
        assert all(r.store == "googleplay" for r in result)
        assert all(r.source == "googleplay_scraper" for r in result)

        text = export_json(result.reviews)
        parsed = json.loads(text)
        assert len(parsed) == 2
        assert parsed[0]["store"] == "googleplay"
        assert parsed[0]["app_id"] == "com.example.app"

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_single_country_jsonl(self, mock_post: Any) -> None:
        """Google Play → JSONL export."""
        reviews_data = [
            _make_gp_review("gp-1", rating=4),
            _make_gp_review("gp-2", rating=3),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            return _gp_response(reviews_data)

        mock_post.side_effect = handler
        result = GooglePlayReviews().fetch("com.test", countries=["us"])

        text = export_jsonl(result.reviews)
        lines = [ln for ln in text.strip().split("\n") if ln]
        assert len(lines) == 2
        for line in lines:
            obj = json.loads(line)
            assert obj["store"] == "googleplay"

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_single_country_csv(self, mock_post: Any) -> None:
        """Google Play → CSV export."""
        reviews_data = [_make_gp_review("gp-1", "Tester", 5, "Great")]

        def handler(url: str, **kw: Any) -> HttpResponse:
            return _gp_response(reviews_data)

        mock_post.side_effect = handler
        result = GooglePlayReviews().fetch("com.test", countries=["us"])

        text = export_csv(result.reviews)
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["rating"] == "5"
        assert rows[0]["source"] == "googleplay_scraper"

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_multiple_countries(self, mock_post: Any) -> None:
        """Google Play fetches per-country; reviews from both appear."""
        call_count = {"n": 0}

        def handler(url: str, **kw: Any) -> HttpResponse:
            call_count["n"] += 1
            if "gl=us" in url:
                return _gp_response([_make_gp_review("us-1", rating=5)])
            if "gl=gb" in url:
                return _gp_response([_make_gp_review("gb-1", rating=3)])
            return _gp_empty()

        mock_post.side_effect = handler
        result = GooglePlayReviews().fetch("com.test", countries=["us", "gb"])

        assert len(result) == 2

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_pagination(self, mock_post: Any) -> None:
        """Google Play pagination: first page has token, second doesn't."""
        call_urls: list[str] = []

        def handler(url: str, **kw: Any) -> HttpResponse:
            call_urls.append(url)
            body = kw.get("body", "")
            if "page_token_abc" in body:
                return _gp_response([_make_gp_review("p2-1")])
            return _gp_response(
                [_make_gp_review("p1-1"), _make_gp_review("p1-2")],
                page_token="page_token_abc",
            )

        mock_post.side_effect = handler
        result = GooglePlayReviews().fetch("com.test", countries=["us"])

        assert len(result) == 3


class TestGooglePlayFiltering:
    """Filter, sort, and limit for Google Play."""

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_filter_by_ratings(self, mock_post: Any) -> None:
        reviews_data = [
            _make_gp_review("gp-1", rating=5),
            _make_gp_review("gp-2", rating=1),
            _make_gp_review("gp-3", rating=5),
        ]
        mock_post.return_value = _gp_response(reviews_data)

        result = GooglePlayReviews().fetch("com.test", countries=["us"], ratings=[1])

        assert len(result) == 1
        assert result.reviews[0].rating == 1

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_sort_and_limit(self, mock_post: Any) -> None:
        """Sort by rating descending, then limit."""
        reviews_data = [
            _make_gp_review("gp-1", rating=2, created_ts=1717100000),
            _make_gp_review("gp-2", rating=5, created_ts=1717200000),
            _make_gp_review("gp-3", rating=4, created_ts=1717300000),
            _make_gp_review("gp-4", rating=1, created_ts=1717400000),
        ]
        mock_post.return_value = _gp_response(reviews_data)

        result = GooglePlayReviews().fetch(
            "com.test",
            countries=["us"],
            sort=Sort.RATING,
            limit=2,
        )

        assert len(result) == 2
        assert result.reviews[0].rating == 5
        assert result.reviews[1].rating == 4


class TestGooglePlayErrorHandling:
    """Google Play failure scenarios."""

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_partial_failure(self, mock_post: Any) -> None:
        """One country 500s, other succeeds."""

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "gl=de" in url:
                return HttpResponse(status=500, body="error")
            return _gp_response([_make_gp_review("ok-1")])

        mock_post.side_effect = handler
        result = GooglePlayReviews().fetch("com.test", countries=["us", "de"])

        assert len(result.reviews) == 1
        assert len(result.errors) == 1
        assert result.errors[0].country == "de"

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_total_failure(self, mock_post: Any) -> None:
        mock_post.return_value = HttpResponse(status=500, body="boom")

        result = GooglePlayReviews().fetch("com.test", countries=["us", "gb"])

        assert len(result.reviews) == 0
        assert len(result.errors) == 2
        assert not result


# ===================================================================
# FetchResult protocol tests (iteration, len, bool, to_dicts)
# ===================================================================


class TestFetchResultProtocol:
    """Verify FetchResult behaves as a collection."""

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_iteration(self, mock_get: Any) -> None:
        """FetchResult is iterable over reviews."""
        entries = [_make_rss_entry("r1"), _make_rss_entry("r2")]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"])

        collected = list(result)
        assert len(collected) == 2
        assert all(isinstance(r, Review) for r in collected)

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_bool_truthy(self, mock_get: Any) -> None:
        """FetchResult is truthy when it has reviews."""
        entries = [_make_rss_entry("r1")]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"])

        assert result
        assert bool(result) is True

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_bool_falsy_empty(self, mock_get: Any) -> None:
        """FetchResult is falsy when empty."""
        mock_get.return_value = _rss_empty()
        result = AppStoreReviews().fetch("12345", countries=["us"])
        assert not result

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_to_dicts(self, mock_get: Any) -> None:
        """to_dicts returns plain dicts with all fields."""
        entries = [_make_rss_entry("r1", "4", "Title", "Body", "Alice", "1.0")]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"])

        dicts = result.to_dicts()
        assert len(dicts) == 1
        d = dicts[0]
        assert isinstance(d, dict)
        assert d["store"] == "appstore"
        assert d["app_id"] == "12345"
        assert d["rating"] == 4
        assert d["title"] == "Title"
        assert d["body"] == "Body"
        assert d["author_name"] == "Alice"
        assert d["app_version"] == "1.0"


# ===================================================================
# FetchResult non-destructive operations
# ===================================================================


class TestFetchResultImmutability:
    """filter/sort/limit return new FetchResult, don't mutate original."""

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_filter_does_not_mutate_original(self, mock_get: Any) -> None:
        entries = [
            _make_rss_entry("r1", "5"),
            _make_rss_entry("r2", "1"),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"])
        filtered = result.filter(ratings=[5])

        assert len(result) == 2  # original unchanged
        assert len(filtered) == 1

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_sort_does_not_mutate_original(self, mock_get: Any) -> None:
        entries = [
            _make_rss_entry("r1", updated="2024-01-01T00:00:00+00:00"),
            _make_rss_entry("r2", updated="2024-08-01T00:00:00+00:00"),
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"])
        original_order = [r.id for r in result]
        sorted_result = result.sort(Sort.OLDEST)

        assert [r.id for r in result] == original_order
        assert len(sorted_result) == 2

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_limit_does_not_mutate_original(self, mock_get: Any) -> None:
        entries = [_make_rss_entry(f"r{i}") for i in range(5)]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us"])
        limited = result.limit(2)

        assert len(result) == 5
        assert len(limited) == 2

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_errors_preserved_through_filter(self, mock_get: Any) -> None:
        """Errors from failed countries survive filter/sort/limit."""

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/gb/" in url:
                return HttpResponse(status=500, body="err")
            if "/page=1/" in url:
                return _rss_page([_make_rss_entry("us-1", "5")])
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("12345", countries=["us", "gb"])
        filtered = result.filter(ratings=[5]).sort(Sort.NEWEST).limit(10)

        assert len(filtered.errors) == 1
        assert filtered.errors[0].country == "gb"


# ===================================================================
# Empty / edge-case exports
# ===================================================================


class TestEmptyExports:
    """Export functions handle empty review lists gracefully."""

    def test_empty_json_export(self) -> None:
        text = export_json([])
        assert json.loads(text) == []

    def test_empty_jsonl_export(self) -> None:
        text = export_jsonl([])
        assert text == ""

    def test_empty_csv_export(self) -> None:
        text = export_csv([])
        assert text == ""


# ===================================================================
# Cross-store comparison: same flow, both stores
# ===================================================================


class TestCrossStoreConsistency:
    """Verify both stores produce structurally identical output."""

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_both_stores_produce_same_export_shape(
        self,
        mock_get: Any,
        mock_post: Any,
    ) -> None:
        """JSON export from both stores has the same keys."""
        rss_entries = [_make_rss_entry("as-1", "4")]

        def rss_handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(rss_entries)
            return _rss_empty()

        mock_get.side_effect = rss_handler

        gp_reviews = [_make_gp_review("gp-1", rating=4)]
        mock_post.return_value = _gp_response(gp_reviews)

        as_result = AppStoreReviews().fetch("12345", countries=["us"])
        gp_result = GooglePlayReviews().fetch("com.test", countries=["us"])

        as_json = json.loads(export_json(as_result.reviews))
        gp_json = json.loads(export_json(gp_result.reviews))

        # Both produce same set of top-level keys
        assert set(as_json[0].keys()) == set(gp_json[0].keys())

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_both_stores_csv_same_columns(
        self,
        mock_get: Any,
        mock_post: Any,
    ) -> None:
        """CSV output from both stores uses the same column headers."""
        rss_entries = [_make_rss_entry("as-1")]

        def rss_handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(rss_entries)
            return _rss_empty()

        mock_get.side_effect = rss_handler
        mock_post.return_value = _gp_response([_make_gp_review("gp-1")])

        as_csv = export_csv(AppStoreReviews().fetch("12345", countries=["us"]).reviews)
        gp_csv = export_csv(
            GooglePlayReviews().fetch("com.test", countries=["us"]).reviews,
        )

        as_reader = csv.DictReader(io.StringIO(as_csv))
        gp_reader = csv.DictReader(io.StringIO(gp_csv))
        assert as_reader.fieldnames == gp_reader.fieldnames


# ===================================================================
# Review field validation
# ===================================================================


class TestReviewFieldIntegrity:
    """Verify review fields are correctly populated end-to-end."""

    @patch("app_reviews.providers.appstore.scraper.http_get")
    def test_appstore_review_fields(self, mock_get: Any) -> None:
        entries = [
            _make_rss_entry(
                "abc123",
                "4",
                "Good app",
                "Works well",
                "TestUser",
                "5.2",
                updated="2024-07-15T08:30:00+00:00",
            )
        ]

        def handler(url: str, **kw: Any) -> HttpResponse:
            if "/page=1/" in url:
                return _rss_page(entries)
            return _rss_empty()

        mock_get.side_effect = handler
        result = AppStoreReviews().fetch("67890", countries=["de"])

        r = result.reviews[0]
        assert r.id == "appstore_scraper-abc123"
        assert r.store == "appstore"
        assert r.app_id == "67890"
        assert r.country == "de"
        assert r.rating == 4
        assert r.title == "Good app"
        assert r.body == "Works well"
        assert r.author_name == "TestUser"
        assert r.app_version == "5.2"
        assert r.source == "appstore_scraper"
        assert r.created_at == datetime(2024, 7, 15, 8, 30, tzinfo=UTC)
        assert r.fetched_at is not None

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_googleplay_review_fields(self, mock_post: Any) -> None:
        reviews_data = [
            _make_gp_review(
                "xyz789",
                "Reviewer1",
                3,
                "Decent app",
                1717200000,
                app_version="10.1",
            )
        ]
        mock_post.return_value = _gp_response(reviews_data)

        result = GooglePlayReviews().fetch("com.example", countries=["us"])

        r = result.reviews[0]
        assert r.id == "googleplay_scraper-xyz789"
        assert r.store == "googleplay"
        assert r.app_id == "com.example"
        assert r.rating == 3
        assert r.body == "Decent app"
        assert r.author_name == "Reviewer1"
        assert r.app_version == "10.1"
        assert r.source == "googleplay_scraper"
        assert r.created_at == datetime(2024, 6, 1, 0, 0, tzinfo=UTC)
        assert r.fetched_at is not None
