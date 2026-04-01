"""Tests for smart dedupe and canonical ordering."""

from datetime import UTC, datetime

from app_reviews.core.dedupe import dedupe_reviews, sort_reviews_newest_first
from app_reviews.models.review import Review

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_DT = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)


def _dt(offset_seconds: int = 0) -> datetime:
    from datetime import timedelta

    return _BASE_DT + timedelta(seconds=offset_seconds)


def _make_review(
    *,
    review_id: str = "r1",
    canonical_key: str = "app1::scraper::r1",
    app_id: str = "app1",
    app_input: str = "app1",
    country: str = "us",
    rating: int = 5,
    title: str = "Great",
    body: str = "Loved it",
    author_name: str = "Alice",
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    source: str = "appstore_scraper",
    source_review_id: str = "r1",
    fetched_at: datetime | None = None,
) -> Review:
    return Review(
        store="appstore",
        review_id=review_id,
        canonical_key=canonical_key,
        app_id=app_id,
        app_input=app_input,
        country=country,
        rating=rating,
        title=title,
        body=body,
        author_name=author_name,
        created_at=created_at or _BASE_DT,
        updated_at=updated_at,
        source=source,
        source_review_id=source_review_id,
        fetched_at=fetched_at or _BASE_DT,
    )


# ---------------------------------------------------------------------------
# sort_reviews_newest_first
# ---------------------------------------------------------------------------


class TestSortReviewsNewestFirst:
    def test_empty_returns_empty(self) -> None:
        assert sort_reviews_newest_first([]) == []

    def test_single_review_returned(self) -> None:
        r = _make_review()
        assert sort_reviews_newest_first([r]) == [r]

    def test_sorted_descending_by_created_at(self) -> None:
        r1 = _make_review(review_id="r1", source_review_id="r1", created_at=_dt(0))
        r2 = _make_review(review_id="r2", source_review_id="r2", created_at=_dt(100))
        r3 = _make_review(review_id="r3", source_review_id="r3", created_at=_dt(50))
        result = sort_reviews_newest_first([r1, r2, r3])
        assert result == [r2, r3, r1]

    def test_already_sorted_unchanged(self) -> None:
        r1 = _make_review(review_id="r1", source_review_id="r1", created_at=_dt(200))
        r2 = _make_review(review_id="r2", source_review_id="r2", created_at=_dt(100))
        assert sort_reviews_newest_first([r1, r2]) == [r1, r2]

    def test_does_not_mutate_original_list(self) -> None:
        r1 = _make_review(review_id="r1", source_review_id="r1", created_at=_dt(0))
        r2 = _make_review(review_id="r2", source_review_id="r2", created_at=_dt(100))
        original = [r1, r2]
        sort_reviews_newest_first(original)
        assert original == [r1, r2]


# ---------------------------------------------------------------------------
# dedupe_reviews — empty / single
# ---------------------------------------------------------------------------


class TestDedupeReviewsEdgeCases:
    def test_empty_input_returns_empty(self) -> None:
        assert dedupe_reviews([]) == []

    def test_single_review_returned(self) -> None:
        r = _make_review()
        assert dedupe_reviews([r]) == [r]


# ---------------------------------------------------------------------------
# dedupe_reviews — no duplicates pass through
# ---------------------------------------------------------------------------


class TestDedupeNoopOnUniqueCanonicaKeys:
    def test_unique_keys_pass_through_unchanged_and_sorted(self) -> None:
        # Use distinct authors so the heuristic does NOT merge these reviews.
        r1 = _make_review(
            review_id="r1",
            canonical_key="app1::scraper::r1",
            source_review_id="r1",
            author_name="Alice",
            created_at=_dt(0),
        )
        r2 = _make_review(
            review_id="r2",
            canonical_key="app1::scraper::r2",
            source_review_id="r2",
            author_name="Bob",
            created_at=_dt(100),
        )
        r3 = _make_review(
            review_id="r3",
            canonical_key="app1::scraper::r3",
            source_review_id="r3",
            author_name="Carol",
            created_at=_dt(50),
        )
        result = dedupe_reviews([r1, r2, r3])
        assert len(result) == 3
        assert result == [r2, r3, r1]


# ---------------------------------------------------------------------------
# dedupe_reviews — exact canonical_key dedupe
# ---------------------------------------------------------------------------


class TestDedupeExactCanonicalKey:
    def test_keeps_latest_updated_at_for_same_key(self) -> None:
        key = "app1::scraper::r1"
        older = _make_review(
            review_id="r1-us",
            canonical_key=key,
            source_review_id="r1",
            country="us",
            created_at=_dt(0),
            updated_at=_dt(10),
        )
        newer = _make_review(
            review_id="r1-gb",
            canonical_key=key,
            source_review_id="r1",
            country="gb",
            created_at=_dt(0),
            updated_at=_dt(200),
        )
        result = dedupe_reviews([older, newer])
        assert len(result) == 1
        assert result[0] == newer

    def test_falls_back_to_created_at_when_no_updated_at(self) -> None:
        key = "app1::scraper::r1"
        older = _make_review(
            review_id="r1-us",
            canonical_key=key,
            source_review_id="r1",
            country="us",
            created_at=_dt(0),
        )
        newer = _make_review(
            review_id="r1-gb",
            canonical_key=key,
            source_review_id="r1",
            country="gb",
            created_at=_dt(100),
        )
        result = dedupe_reviews([older, newer])
        assert len(result) == 1
        assert result[0] == newer

    def test_three_same_key_keeps_latest(self) -> None:
        key = "app1::scraper::r1"
        reviews = [
            _make_review(
                review_id=f"r1-{c}",
                canonical_key=key,
                source_review_id="r1",
                country=c,
                created_at=_dt(i * 10),
            )
            for i, c in enumerate(["us", "gb", "au"])
        ]
        result = dedupe_reviews(reviews)
        assert len(result) == 1
        assert result[0].country == "au"


# ---------------------------------------------------------------------------
# dedupe_reviews — cross-provider: official preferred over scraper
# ---------------------------------------------------------------------------


class TestDedupeOfficialPreferredOverScraper:
    def test_official_preferred_for_same_canonical_key(self) -> None:
        key = "app1::shared::r1"
        scraper_review = _make_review(
            review_id="r1-scraper",
            canonical_key=key,
            source_review_id="r1",
            source="appstore_scraper",
            created_at=_dt(0),
        )
        official_review = _make_review(
            review_id="r1-official",
            canonical_key=key,
            source_review_id="r1",
            source="appstore_official",
            created_at=_dt(0),
        )
        result = dedupe_reviews([scraper_review, official_review])
        assert len(result) == 1
        assert result[0].source == "appstore_official"

    def test_official_preferred_regardless_of_order(self) -> None:
        key = "app1::shared::r1"
        official_review = _make_review(
            review_id="r1-official",
            canonical_key=key,
            source_review_id="r1",
            source="appstore_official",
            created_at=_dt(0),
        )
        scraper_review = _make_review(
            review_id="r1-scraper",
            canonical_key=key,
            source_review_id="r1",
            source="appstore_scraper",
            created_at=_dt(200),
        )
        # scraper has newer created_at but official should still win
        result = dedupe_reviews([official_review, scraper_review])
        assert len(result) == 1
        assert result[0].source == "appstore_official"


# ---------------------------------------------------------------------------
# dedupe_reviews — content-time heuristic
# ---------------------------------------------------------------------------


class TestDedupeContentTimeHeuristic:
    def _make_pair(
        self,
        *,
        dt_offset_a: int = 0,
        dt_offset_b: int = 0,
        rating_a: int = 5,
        rating_b: int = 5,
        author_a: str = "Alice",
        author_b: str = "Alice",
        app_id_a: str = "app1",
        app_id_b: str = "app1",
        source_a: str = "appstore_scraper",
        source_b: str = "appstore_scraper",
    ) -> tuple[Review, Review]:
        a = _make_review(
            review_id="ra",
            canonical_key="app1::scraper::ra",
            source_review_id="ra",
            app_id=app_id_a,
            app_input=app_id_a,
            author_name=author_a,
            rating=rating_a,
            created_at=_dt(dt_offset_a),
            source=source_a,
        )
        b = _make_review(
            review_id="rb",
            canonical_key="app1::scraper::rb",
            source_review_id="rb",
            app_id=app_id_b,
            app_input=app_id_b,
            author_name=author_b,
            rating=rating_b,
            created_at=_dt(dt_offset_b),
            source=source_b,
        )
        return a, b

    def test_same_author_rating_close_timestamp_treated_as_duplicate(self) -> None:
        a, b = self._make_pair(dt_offset_a=0, dt_offset_b=30)
        result = dedupe_reviews([a, b])
        assert len(result) == 1

    def test_exactly_60s_apart_is_duplicate(self) -> None:
        a, b = self._make_pair(dt_offset_a=0, dt_offset_b=60)
        result = dedupe_reviews([a, b])
        assert len(result) == 1

    def test_more_than_60s_apart_not_duplicate(self) -> None:
        a, b = self._make_pair(dt_offset_a=0, dt_offset_b=61)
        result = dedupe_reviews([a, b])
        assert len(result) == 2

    def test_different_rating_not_duplicate(self) -> None:
        a, b = self._make_pair(dt_offset_a=0, dt_offset_b=10, rating_a=4, rating_b=5)
        result = dedupe_reviews([a, b])
        assert len(result) == 2

    def test_different_author_not_duplicate(self) -> None:
        a, b = self._make_pair(
            dt_offset_a=0, dt_offset_b=10, author_a="Alice", author_b="Bob"
        )
        result = dedupe_reviews([a, b])
        assert len(result) == 2

    def test_different_app_id_not_duplicate(self) -> None:
        a, b = self._make_pair(
            dt_offset_a=0, dt_offset_b=10, app_id_a="app1", app_id_b="app2"
        )
        result = dedupe_reviews([a, b])
        assert len(result) == 2

    def test_heuristic_official_preferred_over_scraper(self) -> None:
        a, b = self._make_pair(
            dt_offset_a=0,
            dt_offset_b=10,
            source_a="appstore_scraper",
            source_b="appstore_official",
        )
        result = dedupe_reviews([a, b])
        assert len(result) == 1
        assert result[0].source == "appstore_official"


# ---------------------------------------------------------------------------
# dedupe_reviews — output always sorted newest-first
# ---------------------------------------------------------------------------


class TestDedupeOutputSortedNewestFirst:
    def test_output_sorted_descending(self) -> None:
        reviews = [
            _make_review(
                review_id=f"r{i}",
                canonical_key=f"app1::scraper::r{i}",
                source_review_id=f"r{i}",
                created_at=_dt(i * 100),
            )
            for i in range(5)
        ]
        result = dedupe_reviews(reviews)
        assert len(result) == 5
        for i in range(len(result) - 1):
            assert result[i].created_at >= result[i + 1].created_at
