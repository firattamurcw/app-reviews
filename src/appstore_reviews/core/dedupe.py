"""Smart dedupe and canonical ordering for reviews."""

from datetime import datetime, timedelta

from appstore_reviews.models.review import Review

# Sources ordered from least to most authoritative.
_SOURCE_PRIORITY: dict[str, int] = {"rss": 0, "connect": 1}

_HEURISTIC_WINDOW = timedelta(seconds=60)


def _effective_time(review: Review) -> datetime:
    """Return updated_at if present, otherwise created_at."""
    return review.updated_at if review.updated_at is not None else review.created_at


def _source_priority(review: Review) -> int:
    return _SOURCE_PRIORITY.get(review.source, 0)


def _best_of(a: Review, b: Review) -> Review:
    """Return the more authoritative / newer review between two candidates."""
    # Connect always beats rss.
    pa, pb = _source_priority(a), _source_priority(b)
    if pa != pb:
        return a if pa > pb else b
    # Same source authority: keep the one with the latest effective time.
    return a if _effective_time(a) >= _effective_time(b) else b


def dedupe_reviews(reviews: list[Review]) -> list[Review]:
    """Deduplicate reviews using smart strategy. Returns newest-first sorted list."""
    if not reviews:
        return []

    # --- Pass 1: exact canonical_key deduplication ---
    by_key: dict[str, Review] = {}
    for review in reviews:
        key = review.canonical_key
        if key in by_key:
            by_key[key] = _best_of(by_key[key], review)
        else:
            by_key[key] = review

    candidates = list(by_key.values())

    # --- Pass 2: content-time heuristic deduplication ---
    # For each pair with same app_id + author_name + rating and created_at
    # within 60 seconds, treat as duplicate and keep the more authoritative one.
    kept: list[Review] = []
    for review in candidates:
        merged = False
        for i, existing in enumerate(kept):
            if (
                existing.app_id == review.app_id
                and existing.author_name == review.author_name
                and existing.rating == review.rating
                and abs(existing.created_at - review.created_at) <= _HEURISTIC_WINDOW
            ):
                kept[i] = _best_of(existing, review)
                merged = True
                break
        if not merged:
            kept.append(review)

    return sort_reviews_newest_first(kept)


def sort_reviews_newest_first(reviews: list[Review]) -> list[Review]:
    """Sort reviews by created_at descending."""
    return sorted(reviews, key=lambda r: r.created_at, reverse=True)
