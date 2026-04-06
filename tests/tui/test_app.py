"""Integration tests for the TUI app."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from app_reviews.models.result import FetchResult, FetchStats
from app_reviews.models.review import Review
from app_reviews.tui.app import ReviewApp


def _make_review(id: str = "scraper-123", rating: int = 5) -> Review:
    return Review(
        store="appstore",
        id=id,
        app_id="12345",
        country="us",
        rating=rating,
        title="Great app",
        body="Love it",
        author_name="Alice",
        created_at=datetime(2024, 3, 15, tzinfo=UTC),
        source="appstore_scraper",
        fetched_at=datetime(2024, 3, 16, tzinfo=UTC),
    )


def _mock_result() -> FetchResult:
    return FetchResult(
        reviews=[_make_review("r1", 5), _make_review("r2", 1)],
        stats=FetchStats(total_reviews=2, total_countries=1),
    )


class TestReviewApp:
    @pytest.mark.asyncio
    async def test_app_launches_country_select(self) -> None:
        app = ReviewApp(app_id="12345")
        async with app.run_test(size=(80, 40)):
            sel_list = app.screen.query_one("SelectionList")
            assert "Select Countries" in sel_list.border_title

    @pytest.mark.asyncio
    @patch("app_reviews.tui.screens.fetching.lookup_metadata", return_value=None)
    @patch("app_reviews.tui.screens.fetching.execute_fetch")
    async def test_app_skips_country_select_when_countries_provided(
        self, mock_fetch: MagicMock, mock_lookup: MagicMock
    ) -> None:
        mock_fetch.return_value = _mock_result()
        app = ReviewApp(app_id="12345", countries=["us"])
        async with app.run_test(size=(80, 40)) as pilot:
            # Wait for screens to settle
            await pilot.pause()
            await pilot.pause()
            # Should have ended up on the review browser, not country select
            from app_reviews.tui.screens.country_select import (
                CountrySelectScreen,
            )

            assert not isinstance(app.screen, CountrySelectScreen)
