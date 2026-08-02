"""Tests for PageResult."""

from app_reviews.models.page import PageResult
from app_reviews.models.result import FetchError


class TestPageResult:
    def test_defaults(self):
        page = PageResult()
        assert page.reviews == []
        assert page.next_cursor is None
        assert page.error is None
        assert page.stopped_because is None

    def test_carries_stop_reason(self):
        page = PageResult(stopped_because="since")
        assert page.stopped_because == "since"

    def test_carries_error(self):
        page = PageResult(
            error=FetchError(country="us", message="boom", kind="server", status=503)
        )
        assert page.error.kind == "server"
