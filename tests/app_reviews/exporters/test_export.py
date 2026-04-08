"""Behavioral tests for exporters: round-trip fidelity.

Tests verify: exported reviews can be parsed back without data loss.
"""

import csv
import io
import json
from datetime import UTC, datetime

from app_reviews.exporters.csv import export_csv
from app_reviews.exporters.json import export_json
from app_reviews.exporters.jsonl import export_jsonl
from app_reviews.models.review import Review


def _make_review(id: str = "1") -> Review:
    """A fully-populated review for round-trip testing."""
    return Review(
        store="appstore",
        id=f"scraper-{id}",
        app_id="12345",
        country="us",
        language="en",
        rating=4,
        title="Great app",
        body="Really enjoyed using this",
        author_name="TestUser",
        app_version="2.0",
        created_at=datetime(2024, 3, 15, 10, 0, 0, tzinfo=UTC),
        updated_at=datetime(2024, 3, 16, 12, 0, 0, tzinfo=UTC),
        is_edited=True,
        source="appstore_scraper",
        raw={"raw": "data"},
        fetched_at=datetime(2024, 3, 17, 8, 0, 0, tzinfo=UTC),
    )


class TestJsonExportRoundTrip:
    def test_exported_data_parses_back_correctly(self) -> None:
        """JSON export preserves all review fields."""
        reviews = [_make_review("1"), _make_review("2")]
        text = export_json(reviews, include_raw=True)
        parsed = json.loads(text)

        assert len(parsed) == 2
        for i, row in enumerate(parsed):
            original = reviews[i]
            assert row["id"] == original.id
            assert row["app_id"] == original.app_id
            assert row["country"] == original.country
            assert row["rating"] == original.rating
            assert row["title"] == original.title
            assert row["body"] == original.body
            assert row["author_name"] == original.author_name
            assert row["app_version"] == original.app_version
            assert row["source"] == original.source
            assert row["raw"] == original.raw

    def test_raw_excluded_by_default(self) -> None:
        """Default export strips raw payload for cleaner output."""
        text = export_json([_make_review()])
        parsed = json.loads(text)
        assert "raw" not in parsed[0]

    def test_empty_list_produces_empty_array(self) -> None:
        text = export_json([])
        assert json.loads(text) == []


class TestJsonlExportRoundTrip:
    def test_exported_data_parses_back_correctly(self) -> None:
        """Each JSONL line is a complete review."""
        reviews = [_make_review("1"), _make_review("2")]
        text = export_jsonl(reviews, include_raw=True)
        lines = text.strip().split("\n")

        assert len(lines) == 2
        for i, line in enumerate(lines):
            row = json.loads(line)
            original = reviews[i]
            assert row["id"] == original.id
            assert row["rating"] == original.rating
            assert row["title"] == original.title
            assert row["body"] == original.body
            assert row["raw"] == original.raw

    def test_raw_excluded_by_default(self) -> None:
        text = export_jsonl([_make_review()])
        row = json.loads(text.strip())
        assert "raw" not in row

    def test_empty_list_produces_empty_string(self) -> None:
        assert export_jsonl([]) == ""


class TestCsvExportRoundTrip:
    def test_exported_data_parses_back_correctly(self) -> None:
        """CSV export preserves key review fields."""
        reviews = [_make_review("1"), _make_review("2")]
        text = export_csv(reviews)
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)

        assert len(rows) == 2
        for i, row in enumerate(rows):
            original = reviews[i]
            assert row["id"] == original.id
            assert row["app_id"] == original.app_id
            assert row["country"] == original.country
            assert row["rating"] == str(original.rating)
            assert row["title"] == original.title
            assert row["body"] == original.body
            assert row["author_name"] == original.author_name
            assert row["source"] == original.source

    def test_empty_list_produces_empty_string(self) -> None:
        assert export_csv([]) == ""
