"""Tests for text processing utilities."""

from app_reviews.utils.text import clean_text


class TestCleanText:
    def test_strips_whitespace(self):
        assert clean_text("  hello  ") == "hello"

    def test_normalizes_crlf(self):
        assert clean_text("a\r\nb") == "a\nb"

    def test_normalizes_cr(self):
        assert clean_text("a\rb") == "a\nb"

    def test_mixed_line_endings(self):
        assert clean_text("a\r\nb\rc\nd") == "a\nb\nc\nd"

    def test_empty_string(self):
        assert clean_text("") == ""

    def test_whitespace_only(self):
        assert clean_text("   \n\r\n  ") == ""

    def test_already_clean(self):
        assert clean_text("hello world") == "hello world"
