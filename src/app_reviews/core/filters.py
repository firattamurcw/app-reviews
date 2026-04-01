"""Review filtering and sorting utilities."""

from __future__ import annotations

from app_reviews.models.review import Review

_RATING_RANGES: dict[str, tuple[int, int]] = {
    "all": (1, 5),
    "1-2": (1, 2),
    "3": (3, 3),
    "4-5": (4, 5),
}

_SORT_KEYS = {
    "newest": lambda r: r.created_at,
    "oldest": lambda r: r.created_at,
    "highest": lambda r: r.rating,
    "lowest": lambda r: r.rating,
}

_SORT_REVERSE = {"newest": True, "oldest": False, "highest": True, "lowest": False}


def filter_by_rating(reviews: list[Review], rating_filter: str) -> list[Review]:
    """Filter reviews by rating range."""
    if rating_filter not in _RATING_RANGES:
        raise ValueError(
            f"Invalid rating filter {rating_filter!r}. "
            f"Choose from: {', '.join(_RATING_RANGES)}"
        )
    lo, hi = _RATING_RANGES[rating_filter]
    return [r for r in reviews if lo <= r.rating <= hi]


def sort_reviews(reviews: list[Review], sort_order: str) -> list[Review]:
    """Sort reviews by the given order."""
    if sort_order not in _SORT_KEYS:
        raise ValueError(
            f"Invalid sort {sort_order!r}. Choose from: {', '.join(_SORT_KEYS)}"
        )
    return sorted(
        reviews, key=_SORT_KEYS[sort_order], reverse=_SORT_REVERSE[sort_order]
    )
