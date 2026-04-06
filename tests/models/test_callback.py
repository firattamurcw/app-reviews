"""Tests for FetchCallback protocol."""

from app_reviews.models.callback import FetchCallback
from app_reviews.models.result import CountryStatus, FetchFailure, FetchResult
from app_reviews.models.review import Review

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from conftest import make_review


class _FullCallback:
    """Callback implementing all methods."""

    def __init__(self) -> None:
        self.events: list[str] = []

    def on_fetch_start(self, app_id: str, provider: str) -> None:
        self.events.append(f"start:{app_id}")

    def on_review(self, review: Review) -> None:
        self.events.append(f"review:{review.id}")

    def on_country_done(self, country: str, status: CountryStatus) -> None:
        self.events.append(f"country:{country}")

    def on_fetch_done(self, result: FetchResult) -> None:
        self.events.append("done")

    def on_error(self, error: FetchFailure) -> None:
        self.events.append(f"error:{error.error}")


class _PartialCallback:
    """Callback implementing only on_review."""

    def __init__(self) -> None:
        self.reviews: list[str] = []

    def on_review(self, review: Review) -> None:
        self.reviews.append(review.id)


def test_full_callback_satisfies_protocol():
    cb = _FullCallback()
    assert isinstance(cb, FetchCallback)


def test_partial_callback_satisfies_protocol():
    cb = _PartialCallback()
    assert isinstance(cb, FetchCallback)


def test_full_callback_records_events():
    cb = _FullCallback()
    cb.on_fetch_start("123", "scraper")
    cb.on_review(make_review(id="r1"))
    assert cb.events == ["start:123", "review:r1"]
