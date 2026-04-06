"""Tests for review filtering and sorting."""

from datetime import UTC, datetime

import pytest

from app_reviews.core.filters import filter_by_rating, sort_reviews
from app_reviews.models.review import Review


def _review(rating: int, created_at: datetime | None = None) -> Review:
    ts = created_at or datetime(2024, 3, 15, tzinfo=UTC)
    return Review(
        store="appstore",
        id=f"scraper-{rating}-{ts.isoformat()}",
        app_id="12345",
        country="us",
        rating=rating,
        title=f"Rating {rating}",
        body="body",
        author_name="Alice",
        created_at=ts,
        source="appstore_scraper",
        fetched_at=datetime(2024, 3, 16, tzinfo=UTC),
    )


class TestFilterByRating:
    def test_all_returns_everything(self) -> None:
        reviews = [_review(1), _review(3), _review(5)]
        assert filter_by_rating(reviews, "all") == reviews

    def test_negative_returns_1_and_2(self) -> None:
        reviews = [_review(1), _review(2), _review(3), _review(4), _review(5)]
        result = filter_by_rating(reviews, "1-2")
        assert all(r.rating <= 2 for r in result)
        assert len(result) == 2

    def test_neutral_returns_3(self) -> None:
        reviews = [_review(1), _review(3), _review(5)]
        result = filter_by_rating(reviews, "3")
        assert all(r.rating == 3 for r in result)
        assert len(result) == 1

    def test_positive_returns_4_and_5(self) -> None:
        reviews = [_review(1), _review(3), _review(4), _review(5)]
        result = filter_by_rating(reviews, "4-5")
        assert all(r.rating >= 4 for r in result)
        assert len(result) == 2

    def test_invalid_filter_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid rating filter"):
            filter_by_rating([], "bad")


class TestSortReviews:
    def test_newest_first(self) -> None:
        old = _review(3, datetime(2024, 1, 1, tzinfo=UTC))
        new = _review(3, datetime(2024, 6, 1, tzinfo=UTC))
        result = sort_reviews([old, new], "newest")
        assert result[0].created_at > result[1].created_at

    def test_oldest_first(self) -> None:
        old = _review(3, datetime(2024, 1, 1, tzinfo=UTC))
        new = _review(3, datetime(2024, 6, 1, tzinfo=UTC))
        result = sort_reviews([old, new], "oldest")
        assert result[0].created_at < result[1].created_at

    def test_highest_rated_first(self) -> None:
        low = _review(1)
        high = _review(5)
        result = sort_reviews([low, high], "highest")
        assert result[0].rating == 5

    def test_lowest_rated_first(self) -> None:
        low = _review(1)
        high = _review(5)
        result = sort_reviews([low, high], "lowest")
        assert result[0].rating == 1

    def test_invalid_sort_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid sort"):
            sort_reviews([], "bad")
