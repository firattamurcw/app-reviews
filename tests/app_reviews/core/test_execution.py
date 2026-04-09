"""Tests for BaseReviews fetch orchestration."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock

from conftest import make_review

from app_reviews.clients.base_reviews import BaseReviews
from app_reviews.models.result import FetchError
from app_reviews.providers.base import PageResult


def _make_provider(
    pages: list[PageResult],
    countries_list: list[str] | None = None,
) -> MagicMock:
    """Build a mock provider that returns pages in sequence."""
    provider = MagicMock()
    provider.countries.return_value = countries_list or ["us"]
    provider.fetch_page.side_effect = pages
    return provider


class TestFetchCountry:
    def test_single_page_no_cursor(self):
        reviews = [make_review(id="1"), make_review(id="2")]
        provider = _make_provider([PageResult(reviews=reviews, next_cursor=None)])
        result, error = BaseReviews._fetch_country(provider, "app123", "us", None)
        assert error is None
        assert len(result) == 2

    def test_paginates_until_no_cursor(self):
        r1 = make_review(id="1")
        r2 = make_review(id="2")
        provider = _make_provider(
            [
                PageResult(reviews=[r1], next_cursor="page2"),
                PageResult(reviews=[r2], next_cursor=None),
            ]
        )
        result, error = BaseReviews._fetch_country(provider, "app123", "us", None)
        assert error is None
        assert len(result) == 2

    def test_error_on_first_page_returns_empty_reviews(self):
        err = FetchError(country="us", message="HTTP 503")
        provider = _make_provider([PageResult(error=err)])
        result, error = BaseReviews._fetch_country(provider, "app123", "us", None)
        assert result == []
        assert error == err

    def test_error_mid_pagination_keeps_partial_reviews(self):
        r1 = make_review(id="1")
        err = FetchError(country="us", message="timeout")
        provider = _make_provider(
            [
                PageResult(reviews=[r1], next_cursor="page2"),
                PageResult(error=err),
            ]
        )
        result, error = BaseReviews._fetch_country(provider, "app123", "us", None)
        assert len(result) == 1
        assert error is None
