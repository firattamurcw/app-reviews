"""Behavioral tests for checkpoint state management.

Tests verify: checkpoints track what was fetched and survive save/load cycles.
"""

from pathlib import Path

from app_reviews.core.checkpoints import Checkpoint


class TestCheckpoint:
    def test_save_load_round_trip(self, tmp_path: Path) -> None:
        """Smoke test: data survives a save/load cycle."""
        cp = Checkpoint(tmp_path / "cp.json")
        cp.mark_fetched("app1", "us", "scraper")
        cp.save(cp.load())

        cp2 = Checkpoint(tmp_path / "cp.json")
        assert cp2.is_fetched("app1", "us", "scraper") is True

    def test_marks_app_country_provider_as_fetched(self, tmp_path: Path) -> None:
        """After marking a combination, is_fetched returns True."""
        cp = Checkpoint(tmp_path / "cp.json")
        assert cp.is_fetched("app1", "us", "scraper") is False

        cp.mark_fetched("app1", "us", "scraper")

        assert cp.is_fetched("app1", "us", "scraper") is True
        # Different combination is still not fetched
        assert cp.is_fetched("app1", "gb", "scraper") is False
        assert cp.is_fetched("app1", "us", "official") is False

    def test_clear_removes_all_state(self, tmp_path: Path) -> None:
        """After clear, nothing is marked as fetched."""
        cp = Checkpoint(tmp_path / "cp.json")
        cp.mark_fetched("app1", "us", "scraper")
        cp.clear()

        assert cp.is_fetched("app1", "us", "scraper") is False

    def test_missing_file_returns_empty_state(self, tmp_path: Path) -> None:
        """A fresh checkpoint with no file on disk has no fetched entries."""
        cp = Checkpoint(tmp_path / "nonexistent.json")
        assert cp.load() == {}
        assert cp.is_fetched("any", "any", "any") is False
