"""Tests for Google Play web scraper provider."""

import json
from unittest.mock import patch

from app_reviews.providers.googleplay.scraper import GoogleScraperProvider
from app_reviews.utils.http import HttpResponse

# A realistic review entry matching oCPfdb response format
_REVIEW_ENTRY = [
    "review-id-123",
    ["TestUser", [None, 2, None, [None, None, "https://avatar.url"]]],
    4,
    None,
    "Great app, love it!",
    [1700000000, 1700100000],
    42,
    None,
    None,
    None,
    "2.1.0",
]

_BATCH_PAYLOAD = json.dumps([[_REVIEW_ENTRY], [None, "next-page-token"], [None]])
_RAW_RESPONSE = ")]}'\n\n" + json.dumps(
    [["wrb.fr", "oCPfdb", _BATCH_PAYLOAD, None, None]]
)

_BATCH_PAYLOAD_LAST = json.dumps([[_REVIEW_ENTRY], None, [None]])
_RAW_RESPONSE_LAST = ")]}'\n\n" + json.dumps(
    [["wrb.fr", "oCPfdb", _BATCH_PAYLOAD_LAST, None, None]]
)

# Responses that exercise edge cases through the public fetch_page interface
_EMPTY_OUTER = ")]}'\n\n[]"
_NULL_INNER = ")]}'\n\n" + json.dumps([["wrb.fr", "oCPfdb", None, None, None]])
_LIST_TOKEN_PAYLOAD = json.dumps([[_REVIEW_ENTRY], [None, ["not-a-token"]], [None]])
_LIST_TOKEN_RESPONSE = ")]}'\n\n" + json.dumps(
    [["wrb.fr", "oCPfdb", _LIST_TOKEN_PAYLOAD, None, None]]
)
_INVALID_ENTRY = [[], None, None, None, None, None]
_INVALID_ENTRY_PAYLOAD = json.dumps([[_INVALID_ENTRY], None, [None]])
_INVALID_ENTRY_RESPONSE = ")]}'\n\n" + json.dumps(
    [["wrb.fr", "oCPfdb", _INVALID_ENTRY_PAYLOAD, None, None]]
)


class TestGoogleScraperProviderReviewParsing:
    """Tests that valid/invalid review data is correctly handled through fetch_page."""

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_valid_entry_produces_review_with_correct_fields(self, mock_post):
        mock_post.return_value = HttpResponse(status=200, body=_RAW_RESPONSE_LAST)
        provider = GoogleScraperProvider()
        page = provider.fetch_page("com.example", "us", cursor=None)
        assert len(page.reviews) == 1
        review = page.reviews[0]
        assert review.store == "googleplay"
        assert review.source == "googleplay_scraper"
        assert review.rating == 4
        assert review.body == "Great app, love it!"
        assert review.author_name == "TestUser"
        assert review.app_version == "2.1.0"
        assert review.app_id == "com.example"

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_invalid_entry_is_skipped(self, mock_post):
        mock_post.return_value = HttpResponse(status=200, body=_INVALID_ENTRY_RESPONSE)
        provider = GoogleScraperProvider()
        page = provider.fetch_page("com.example", "us", cursor=None)
        assert len(page.reviews) == 0
        assert page.error is None

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_empty_outer_response_returns_no_reviews(self, mock_post):
        mock_post.return_value = HttpResponse(status=200, body=_EMPTY_OUTER)
        provider = GoogleScraperProvider()
        page = provider.fetch_page("com.example", "us", cursor=None)
        assert len(page.reviews) == 0
        assert page.error is None

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_null_inner_payload_returns_no_reviews(self, mock_post):
        mock_post.return_value = HttpResponse(status=200, body=_NULL_INNER)
        provider = GoogleScraperProvider()
        page = provider.fetch_page("com.example", "us", cursor=None)
        assert len(page.reviews) == 0
        assert page.error is None

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_list_token_means_no_next_page(self, mock_post):
        mock_post.return_value = HttpResponse(status=200, body=_LIST_TOKEN_RESPONSE)
        provider = GoogleScraperProvider()
        page = provider.fetch_page("com.example", "us", cursor=None)
        assert len(page.reviews) == 1
        assert page.next_cursor is None


class TestGoogleScraperProviderCountries:
    def test_returns_all_requested_countries(self):
        provider = GoogleScraperProvider(lang="en")
        assert provider.countries(["us", "gb", "de"]) == ["us", "gb", "de"]

    def test_returns_empty_for_empty_requested(self):
        provider = GoogleScraperProvider()
        assert provider.countries([]) == []


class TestGoogleScraperProviderFetchPage:
    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_first_page_no_cursor(self, mock_post):
        mock_post.return_value = HttpResponse(status=200, body=_RAW_RESPONSE_LAST)
        provider = GoogleScraperProvider()
        page = provider.fetch_page("com.example", "us", cursor=None)
        assert page.error is None
        assert len(page.reviews) == 1
        assert page.reviews[0].store == "googleplay"

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_returns_next_cursor_when_token_present(self, mock_post):
        mock_post.return_value = HttpResponse(status=200, body=_RAW_RESPONSE)
        provider = GoogleScraperProvider()
        page = provider.fetch_page("com.example", "us", cursor=None)
        assert page.next_cursor == "next-page-token"

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_returns_no_cursor_on_last_page(self, mock_post):
        mock_post.return_value = HttpResponse(status=200, body=_RAW_RESPONSE_LAST)
        provider = GoogleScraperProvider()
        page = provider.fetch_page("com.example", "us", cursor=None)
        assert page.next_cursor is None

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_cursor_passed_as_page_token(self, mock_post):
        """Cursor from previous page is passed to next request body."""
        mock_post.return_value = HttpResponse(status=200, body=_RAW_RESPONSE_LAST)
        provider = GoogleScraperProvider()
        provider.fetch_page("com.example", "us", cursor="some-token")
        body_arg = mock_post.call_args[1]["body"]
        assert "some-token" in body_arg

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_http_error_returns_fetch_error(self, mock_post):
        import urllib.error

        mock_post.side_effect = urllib.error.URLError("timeout")
        provider = GoogleScraperProvider()
        page = provider.fetch_page("com.example", "us", cursor=None)
        assert page.error is not None
        assert len(page.reviews) == 0

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_non_200_returns_fetch_error(self, mock_post):
        mock_post.return_value = HttpResponse(status=503, body="error")
        provider = GoogleScraperProvider()
        page = provider.fetch_page("com.example", "us", cursor=None)
        assert page.error is not None

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_empty_response_no_reviews_no_error(self, mock_post):
        mock_post.return_value = HttpResponse(status=200, body=")]}'\n\n[]")
        provider = GoogleScraperProvider()
        page = provider.fetch_page("com.example", "us", cursor=None)
        assert len(page.reviews) == 0
        assert page.error is None

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_passes_hl_gl_params(self, mock_post):
        mock_post.return_value = HttpResponse(status=200, body=_RAW_RESPONSE_LAST)
        provider = GoogleScraperProvider(lang="de")
        provider.fetch_page("com.example", "de", cursor=None)
        url = mock_post.call_args[0][0]
        assert "hl=de" in url
        assert "gl=de" in url
