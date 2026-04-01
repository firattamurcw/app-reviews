"""Tests for the CLI inspect command."""

from click.testing import CliRunner

from appstore_reviews.cli import main


class TestInspectCommand:
    def test_inspect_requires_app_id(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["inspect"])
        assert result.exit_code != 0

    def test_inspect_shows_app_info(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["inspect", "--app-id", "12345"])
        assert result.exit_code == 0
        assert "12345" in result.output
