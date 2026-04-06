"""Tests for enriched FetchResult."""

from datetime import UTC, date, datetime

from app_reviews.models.result import CountryStatus, FetchResult, FetchStats

# Import make_review from conftest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from conftest import make_review


def test_fetch_result_iter():
    r1 = make_review(id="1", rating=5)
    r2 = make_review(id="2", rating=3)
    result = FetchResult(reviews=[r1, r2], stats=FetchStats(total_reviews=2))
    assert list(result) == [r1, r2]


def test_fetch_result_len():
    result = FetchResult(
        reviews=[make_review(id="1"), make_review(id="2")],
        stats=FetchStats(total_reviews=2),
    )
    assert len(result) == 2


def test_fetch_result_bool_truthy():
    result = FetchResult(reviews=[make_review()], stats=FetchStats(total_reviews=1))
    assert bool(result) is True


def test_fetch_result_bool_falsy():
    result = FetchResult()
    assert bool(result) is False


def test_fetch_result_cursor():
    result = FetchResult(cursor="abc123")
    assert result.cursor == "abc123"


def test_fetch_result_cursor_default_none():
    result = FetchResult()
    assert result.cursor is None


def test_country_status_fields():
    status = CountryStatus(
        country="us",
        state="success",
        review_count=42,
        duration_seconds=1.5,
    )
    assert status.country == "us"
    assert status.state == "success"
    assert status.review_count == 42
    assert status.error is None
    assert status.status_code is None
    assert status.duration_seconds == 1.5


def test_fetch_result_countries_dict():
    status = CountryStatus(country="us", state="success", review_count=10)
    result = FetchResult(countries={"us": status})
    assert result.countries["us"].review_count == 10


def test_fetch_result_succeeded_and_failed():
    ok = CountryStatus(country="us", state="success", review_count=10)
    fail = CountryStatus(country="gb", state="failed", error="HTTP 500")
    empty = CountryStatus(country="de", state="empty")
    result = FetchResult(countries={"us": ok, "gb": fail, "de": empty})
    assert result.succeeded == ["us"]
    assert result.failed == ["gb"]


def test_fetch_result_filter_by_ratings():
    r1 = make_review(id="1", rating=5)
    r2 = make_review(id="2", rating=2)
    r3 = make_review(id="3", rating=3)
    result = FetchResult(reviews=[r1, r2, r3], stats=FetchStats(total_reviews=3))
    filtered = result.filter(ratings=[4, 5])
    assert len(filtered) == 1
    assert list(filtered)[0].rating == 5


def test_fetch_result_filter_by_since():
    old = make_review(id="1", created_at=datetime(2024, 1, 1, tzinfo=UTC))
    new = make_review(id="2", created_at=datetime(2025, 6, 1, tzinfo=UTC))
    result = FetchResult(reviews=[old, new], stats=FetchStats(total_reviews=2))
    filtered = result.filter(since=date(2025, 1, 1))
    assert len(filtered) == 1


def test_fetch_result_filter_by_until():
    old = make_review(id="1", created_at=datetime(2024, 1, 1, tzinfo=UTC))
    new = make_review(id="2", created_at=datetime(2025, 6, 1, tzinfo=UTC))
    result = FetchResult(reviews=[old, new], stats=FetchStats(total_reviews=2))
    filtered = result.filter(until=date(2025, 1, 1))
    assert len(filtered) == 1
    assert list(filtered)[0].id == "1"


def test_fetch_result_filter_is_non_destructive():
    r1 = make_review(id="1", rating=5)
    r2 = make_review(id="2", rating=2)
    result = FetchResult(reviews=[r1, r2], stats=FetchStats(total_reviews=2))
    filtered = result.filter(ratings=[5])
    assert len(result) == 2
    assert len(filtered) == 1


def test_fetch_result_to_dicts():
    r = make_review(id="1", rating=4, title="Nice", body="Good app")
    result = FetchResult(reviews=[r], stats=FetchStats(total_reviews=1))
    dicts = result.to_dicts()
    assert len(dicts) == 1
    assert dicts[0]["rating"] == 4
    assert dicts[0]["title"] == "Nice"
    assert dicts[0]["id"] == "1"
