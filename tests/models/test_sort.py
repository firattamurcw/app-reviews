"""Tests for Sort enum."""

from app_reviews.models.sort import Sort


def test_sort_is_str_enum():
    assert isinstance(Sort.NEWEST, str)
    assert Sort.NEWEST == "newest"
    assert Sort.OLDEST == "oldest"
    assert Sort.RATING == "rating"


def test_sort_has_exactly_three_members():
    assert len(Sort) == 3


def test_sort_default_is_newest():
    assert Sort("newest") == Sort.NEWEST
