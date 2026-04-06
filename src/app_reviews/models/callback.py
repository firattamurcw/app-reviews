"""Callback protocol for fetch lifecycle hooks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, cast, runtime_checkable

if TYPE_CHECKING:
    from app_reviews.models.result import CountryStatus, FetchFailure, FetchResult
    from app_reviews.models.review import Review


@runtime_checkable
class FetchCallback(Protocol):
    """Lifecycle hooks for fetch operations.

    All methods are optional — implement only the hooks you need.
    The protocol is satisfied by any object that has at least ``on_review``;
    all other hooks are looked up at call time and silently skipped when absent.
    """

    def on_review(self, review: Review) -> None: ...

    def on_fetch_start(self, app_id: str, provider: str) -> None:
        """Called when a fetch operation begins."""

    def on_country_done(self, country: str, status: CountryStatus) -> None:
        """Called when a country's fetch completes."""

    def on_fetch_done(self, result: FetchResult) -> None:
        """Called when the entire fetch operation completes."""

    def on_error(self, error: FetchFailure) -> None:
        """Called when a non-fatal error occurs during fetching."""

    @classmethod
    def __subclasshook__(cls, C: Any) -> bool:
        if cls is FetchCallback:
            return hasattr(C, "on_review")
        return cast(bool, NotImplemented)
