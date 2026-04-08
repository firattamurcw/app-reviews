"""Review sorting for the TUI."""

from __future__ import annotations

from app_reviews.models.review import Review

_SORT_KEYS = {
    "newest": lambda r: r.created_at,
    "oldest": lambda r: r.created_at,
    "highest": lambda r: r.rating,
    "lowest": lambda r: r.rating,
}

_SORT_REVERSE = {"newest": True, "oldest": False, "highest": True, "lowest": False}


def sort_reviews(reviews: list[Review], sort_order: str) -> list[Review]:
    """Sort reviews by the given order.

    Args:
        reviews: List of Review objects to sort.
        sort_order: One of "newest", "oldest", "highest", "lowest".

    Returns:
        A new sorted list.

    Raises:
        ValueError: If sort_order is not recognized.
    """
    if sort_order not in _SORT_KEYS:
        raise ValueError(
            f"Invalid sort {sort_order!r}. Choose from: {', '.join(_SORT_KEYS)}"
        )
    return sorted(
        reviews, key=_SORT_KEYS[sort_order], reverse=_SORT_REVERSE[sort_order]
    )
