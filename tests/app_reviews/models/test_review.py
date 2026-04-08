"""Tests for Review model validation."""

from datetime import UTC, datetime

import pytest

from app_reviews.models.review import Review


def _make_review(**overrides):
    defaults = {
        "store": "appstore",
        "app_id": "12345",
        "country": "us",
        "rating": 4,
        "title": "Great",
        "body": "Love it",
        "author_name": "Tester",
        "created_at": datetime(2024, 1, 1, tzinfo=UTC),
        "source": "appstore_scraper",
    }
    return Review(**(defaults | overrides))


class TestReviewRatingValidation:
    def test_valid_rating_1(self):
        review = _make_review(rating=1)
        assert review.rating == 1

    def test_valid_rating_5(self):
        review = _make_review(rating=5)
        assert review.rating == 5

    def test_rating_0_raises(self):
        with pytest.raises(ValueError, match="rating must be 1-5"):
            _make_review(rating=0)

    def test_rating_6_raises(self):
        with pytest.raises(ValueError, match="rating must be 1-5"):
            _make_review(rating=6)

    def test_negative_rating_raises(self):
        with pytest.raises(ValueError, match="rating must be 1-5"):
            _make_review(rating=-1)
