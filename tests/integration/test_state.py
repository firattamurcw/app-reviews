"""Behavioral tests for cache and checkpoint state management.

Tests verify: checkpoints track what was fetched, cache stores and
retrieves reviews, and both survive save/load cycles.
"""

from pathlib import Path

from appstore_reviews.core.cache import ReviewCache
from appstore_reviews.core.checkpoints import Checkpoint


class TestCheckpoint:
    def test_save_load_round_trip(self, tmp_path: Path) -> None:
        """Smoke test: data survives a save/load cycle."""
        cp = Checkpoint(tmp_path / "cp.json")
        cp.mark_fetched("app1", "us", "rss")
        cp.save(cp.load())

        cp2 = Checkpoint(tmp_path / "cp.json")
        assert cp2.is_fetched("app1", "us", "rss") is True

    def test_marks_app_country_provider_as_fetched(self, tmp_path: Path) -> None:
        """After marking a combination, is_fetched returns True."""
        cp = Checkpoint(tmp_path / "cp.json")
        assert cp.is_fetched("app1", "us", "rss") is False

        cp.mark_fetched("app1", "us", "rss")

        assert cp.is_fetched("app1", "us", "rss") is True
        # Different combination is still not fetched
        assert cp.is_fetched("app1", "gb", "rss") is False
        assert cp.is_fetched("app1", "us", "connect") is False

    def test_clear_removes_all_state(self, tmp_path: Path) -> None:
        """After clear, nothing is marked as fetched."""
        cp = Checkpoint(tmp_path / "cp.json")
        cp.mark_fetched("app1", "us", "rss")
        cp.clear()

        assert cp.is_fetched("app1", "us", "rss") is False

    def test_missing_file_returns_empty_state(self, tmp_path: Path) -> None:
        """A fresh checkpoint with no file on disk has no fetched entries."""
        cp = Checkpoint(tmp_path / "nonexistent.json")
        assert cp.load() == {}
        assert cp.is_fetched("any", "any", "any") is False


class TestReviewCache:
    def test_save_load_round_trip(self, tmp_path: Path) -> None:
        """Smoke test: cached reviews survive a save/load cycle."""
        cache = ReviewCache(tmp_path / "cache.json")
        cache.put("key1", {"rating": 5, "title": "Great"})

        cache2 = ReviewCache(tmp_path / "cache.json")
        assert cache2.get("key1") == {"rating": 5, "title": "Great"}

    def test_stores_and_retrieves_by_canonical_key(self, tmp_path: Path) -> None:
        """Reviews are stored and looked up by canonical key."""
        cache = ReviewCache(tmp_path / "cache.json")
        cache.put("app1-review1", {"rating": 5})
        cache.put("app1-review2", {"rating": 3})

        assert cache.get("app1-review1") == {"rating": 5}
        assert cache.get("app1-review2") == {"rating": 3}
        assert cache.get("nonexistent") is None

    def test_put_many_stores_all_at_once(self, tmp_path: Path) -> None:
        """Batch put stores multiple reviews atomically."""
        cache = ReviewCache(tmp_path / "cache.json")
        cache.put_many(
            [
                ("key1", {"rating": 5}),
                ("key2", {"rating": 4}),
            ]
        )

        assert cache.size() == 2
        assert cache.get("key1") == {"rating": 5}
        assert cache.get("key2") == {"rating": 4}

    def test_overwrite_updates_existing_entry(self, tmp_path: Path) -> None:
        """Putting the same key again overwrites the old data."""
        cache = ReviewCache(tmp_path / "cache.json")
        cache.put("key1", {"rating": 3})
        cache.put("key1", {"rating": 5})

        assert cache.get("key1") == {"rating": 5}
        assert cache.size() == 1

    def test_clear_removes_all_entries(self, tmp_path: Path) -> None:
        """After clear, cache is empty."""
        cache = ReviewCache(tmp_path / "cache.json")
        cache.put("key1", {"rating": 5})
        cache.clear()

        assert cache.get("key1") is None
        assert cache.size() == 0

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        """A fresh cache with no file on disk returns None for any key."""
        cache = ReviewCache(tmp_path / "nonexistent.json")
        assert cache.get("any") is None
        assert cache.size() == 0
