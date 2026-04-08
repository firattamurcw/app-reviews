"""Tests for the review browser screen."""

from datetime import UTC, datetime

import pytest

from app_reviews.models.result import FetchResult
from app_reviews.models.review import Review
from app_reviews_tui.app import ReviewApp
from app_reviews_tui.screens.review_browser import ReviewBrowserScreen
from app_reviews_tui.widgets.filter_bar import FilterBar
from app_reviews_tui.widgets.review_card import ReviewCard


def _make_review(
    id: str = "scraper-123", rating: int = 5, title: str = "Great"
) -> Review:
    return Review(
        store="appstore",
        id=id,
        app_id="12345",
        country="us",
        rating=rating,
        title=title,
        body="Body text",
        author_name="Alice",
        created_at=datetime(2024, 3, 15, tzinfo=UTC),
        source="appstore_scraper",
        fetched_at=datetime(2024, 3, 16, tzinfo=UTC),
    )


def _make_result() -> FetchResult:
    return FetchResult(
        reviews=[
            _make_review("r1", 5, "Amazing"),
            _make_review("r2", 3, "Okay"),
            _make_review("r3", 1, "Terrible"),
        ],
    )


class TestReviewBrowserScreen:
    @pytest.mark.asyncio
    async def test_displays_all_reviews(self) -> None:
        result = _make_result()
        screen = ReviewBrowserScreen(result, ["us"])
        app = ReviewApp(app_id="12345", countries=["us"])
        async with app.run_test(size=(100, 50)) as pilot:
            app.switch_screen(screen)
            await pilot.pause()
            cards = app.screen.query(ReviewCard)
            assert len(cards) == 3

    @pytest.mark.asyncio
    async def test_rating_filter_hides_reviews(self) -> None:
        result = _make_result()
        screen = ReviewBrowserScreen(result, ["us"])
        app = ReviewApp(app_id="12345", countries=["us"])
        async with app.run_test(size=(100, 50)) as pilot:
            app.switch_screen(screen)
            await pilot.pause()
            # Use the FilterBar API directly to toggle ratings
            filter_bar = app.screen.query_one(FilterBar)
            filter_bar.toggle_rating(1)
            filter_bar.toggle_rating(3)
            await pilot.pause()
            cards = app.screen.query(ReviewCard)
            assert len(cards) == 1  # Only the 5-star review remains
