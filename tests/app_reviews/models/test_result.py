"""Tests for FetchResult."""

import os
import sys
from datetime import UTC, date, datetime

from app_reviews.models.result import FetchError, FetchResult
from app_reviews.models.sort import Sort

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from conftest import make_review


def test_fetch_result_default_empty():
    result = FetchResult()
    assert result.reviews == []
    assert result.errors == []


def test_fetch_result_iter():
    r1 = make_review(id="1")
    r2 = make_review(id="2")
    result = FetchResult(reviews=[r1, r2])
    assert list(result) == [r1, r2]


def test_fetch_result_len():
    result = FetchResult(reviews=[make_review(id="1"), make_review(id="2")])
    assert len(result) == 2


def test_fetch_result_bool_truthy():
    assert bool(FetchResult(reviews=[make_review()])) is True


def test_fetch_result_bool_falsy():
    assert bool(FetchResult()) is False


def test_filter_by_ratings():
    r1 = make_review(id="1", rating=5)
    r2 = make_review(id="2", rating=2)
    result = FetchResult(reviews=[r1, r2]).filter(ratings=[4, 5])
    assert len(result) == 1
    assert next(iter(result)).rating == 5


def test_filter_by_since():
    old = make_review(id="1", created_at=datetime(2024, 1, 1, tzinfo=UTC))
    new = make_review(id="2", created_at=datetime(2025, 6, 1, tzinfo=UTC))
    result = FetchResult(reviews=[old, new]).filter(since=date(2025, 1, 1))
    assert len(result) == 1


def test_filter_by_until():
    old = make_review(id="1", created_at=datetime(2024, 1, 1, tzinfo=UTC))
    new = make_review(id="2", created_at=datetime(2025, 6, 1, tzinfo=UTC))
    result = FetchResult(reviews=[old, new]).filter(until=date(2025, 1, 1))
    assert len(result) == 1
    assert next(iter(result)).id == "1"


def test_filter_preserves_errors():
    err = FetchError(country="gb", message="fail")
    r1 = make_review(id="1", rating=5)
    r2 = make_review(id="2", rating=1)
    result = FetchResult(reviews=[r1, r2], errors=[err]).filter(ratings=[5])
    assert result.errors == [err]


def test_filter_is_non_destructive():
    r1 = make_review(id="1", rating=5)
    r2 = make_review(id="2", rating=2)
    original = FetchResult(reviews=[r1, r2])
    filtered = original.filter(ratings=[5])
    assert len(original) == 2
    assert len(filtered) == 1


def test_sort_newest():
    old = make_review(id="1", created_at=datetime(2024, 1, 1, tzinfo=UTC))
    new = make_review(id="2", created_at=datetime(2025, 6, 1, tzinfo=UTC))
    result = FetchResult(reviews=[old, new]).sort(Sort.NEWEST)
    assert next(iter(result)).id == "2"


def test_sort_oldest():
    old = make_review(id="1", created_at=datetime(2024, 1, 1, tzinfo=UTC))
    new = make_review(id="2", created_at=datetime(2025, 6, 1, tzinfo=UTC))
    result = FetchResult(reviews=[old, new]).sort(Sort.OLDEST)
    assert next(iter(result)).id == "1"


def test_sort_rating():
    low = make_review(id="1", rating=1)
    high = make_review(id="2", rating=5)
    result = FetchResult(reviews=[low, high]).sort(Sort.RATING)
    assert next(iter(result)).rating == 5


def test_limit_truncates():
    reviews = [make_review(id=str(i)) for i in range(10)]
    result = FetchResult(reviews=reviews).limit(3)
    assert len(result) == 3


def test_limit_none_is_noop():
    reviews = [make_review(id=str(i)) for i in range(5)]
    result = FetchResult(reviews=reviews).limit(None)
    assert len(result) == 5


def test_limit_larger_than_count_is_noop():
    reviews = [make_review(id=str(i)) for i in range(3)]
    result = FetchResult(reviews=reviews).limit(100)
    assert len(result) == 3


def test_chain_filter_sort_limit():
    reviews = [
        make_review(id="1", rating=5, created_at=datetime(2025, 1, 1, tzinfo=UTC)),
        make_review(id="2", rating=1, created_at=datetime(2025, 6, 1, tzinfo=UTC)),
        make_review(id="3", rating=5, created_at=datetime(2024, 1, 1, tzinfo=UTC)),
    ]
    result = FetchResult(reviews=reviews).filter(ratings=[5]).sort(Sort.NEWEST).limit(1)
    assert len(result) == 1
    assert next(iter(result)).id == "1"


def test_to_dicts():
    r = make_review(id="1", rating=4, title="Nice", body="Good app")
    dicts = FetchResult(reviews=[r]).to_dicts()
    assert len(dicts) == 1
    assert dicts[0]["rating"] == 4
    assert dicts[0]["title"] == "Nice"
