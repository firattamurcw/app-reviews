"""Tests for the CLI fetch command."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from appstore_reviews.cli import main
from appstore_reviews.models.result import FetchResult, FetchStats
from appstore_reviews.models.review import Review


def _make_review(review_id: str = "rss-123") -> Review:
    return Review(
        review_id=review_id,
        canonical_key=f"12345-{review_id}",
        app_id="12345",
        app_input="12345",
        country="us",
        rating=5,
        title="Great",
        body="Love it",
        author_name="Alice",
        created_at=datetime(2024, 3, 15, tzinfo=UTC),
        source="rss",
        source_review_id="123",
        fetched_at=datetime(2024, 3, 16, tzinfo=UTC),
    )


class TestFetchCommand:
    def test_fetch_requires_app_id(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["fetch"])
        assert result.exit_code != 0

    @patch("appstore_reviews.cli.execute_fetch")
    def test_fetch_outputs_table_by_default(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = FetchResult(
            reviews=[_make_review()],
            stats=FetchStats(total_reviews=1, total_countries=1),
        )
        runner = CliRunner()
        result = runner.invoke(main, ["fetch", "--app-id", "12345"])
        assert result.exit_code == 0
        assert "1 reviews fetched" in result.output
        assert "Great" in result.output

    @patch("appstore_reviews.cli.execute_fetch")
    def test_fetch_json_format(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = FetchResult(
            reviews=[_make_review()],
            stats=FetchStats(total_reviews=1, total_countries=1),
        )
        runner = CliRunner()
        result = runner.invoke(main, ["fetch", "--app-id", "12345", "--format", "json"])
        assert result.exit_code == 0
        assert "[" in result.output  # JSON array

    @patch("appstore_reviews.cli.execute_fetch")
    def test_fetch_csv_format(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = FetchResult(
            reviews=[_make_review()],
            stats=FetchStats(total_reviews=1, total_countries=1),
        )
        runner = CliRunner()
        result = runner.invoke(main, ["fetch", "--app-id", "12345", "--format", "csv"])
        assert result.exit_code == 0
        assert "review_id" in result.output  # CSV header

    @patch("appstore_reviews.cli.execute_fetch")
    def test_fetch_with_country(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = FetchResult(reviews=[], stats=FetchStats())
        runner = CliRunner()
        result = runner.invoke(main, ["fetch", "--app-id", "12345", "--country", "gb"])
        assert result.exit_code == 0
        call_config = mock_fetch.call_args[0][0]
        assert "gb" in call_config.countries

    @patch("appstore_reviews.cli.execute_fetch")
    def test_fetch_to_output_file(self, mock_fetch: MagicMock, tmp_path: Path) -> None:
        mock_fetch.return_value = FetchResult(
            reviews=[_make_review()],
            stats=FetchStats(total_reviews=1, total_countries=1),
        )
        out = tmp_path / "out.jsonl"
        runner = CliRunner()
        result = runner.invoke(
            main, ["fetch", "--app-id", "12345", "--output", str(out)]
        )
        assert result.exit_code == 0
        assert out.exists()
