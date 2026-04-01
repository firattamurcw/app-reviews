"""Tests for the CLI config validate command."""

from click.testing import CliRunner

from appstore_reviews.cli import main


class TestConfigValidateCommand:
    def test_validate_with_inline_args(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["config", "validate", "--app-id", "12345", "--country", "us"],
        )
        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_validate_invalid_country(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["config", "validate", "--app-id", "12345", "--country", "INVALID"],
        )
        # Should report an error or non-zero exit
        output = result.output.lower()
        assert result.exit_code != 0 or "invalid" in output or "error" in output
