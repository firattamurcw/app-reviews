"""Tests for Sort enum."""

from app_reviews.models.types import Sort


def test_sort_default_is_newest():
    assert Sort("newest") == Sort.NEWEST
