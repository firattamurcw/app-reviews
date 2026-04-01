"""Tests for Google Play web scraper provider."""

import json
from typing import Any
from unittest.mock import patch

from app_reviews.providers.googleplay.scraper import (
    GoogleScraperProvider,
    _parse_response,
    _to_review,
)
from app_reviews.utils.http import HttpResponse

# A realistic review entry matching oCPfdb response format
_REVIEW_ENTRY = [
    "review-id-123",
    ["TestUser", [None, 2, None, [None, None, "https://avatar.url"]]],
    4,
    None,
    "Great app, love it!",
    [1700000000, 1700100000],
    42,  # thumbs up
    None,
    None,
    None,
    "2.1.0",
]

# oCPfdb response structure: [reviews, [None, token], metadata]
_BATCH_PAYLOAD = json.dumps([[_REVIEW_ENTRY], [None, "next-page-token"], [None]])

_RAW_RESPONSE = ")]}'\n\n" + json.dumps(
    [["wrb.fr", "oCPfdb", _BATCH_PAYLOAD, None, None]]
)

# Last-page response: token slot is None
_BATCH_PAYLOAD_LAST = json.dumps([[_REVIEW_ENTRY], None, [None]])

_RAW_RESPONSE_LAST = ")]}'\n\n" + json.dumps(
    [["wrb.fr", "oCPfdb", _BATCH_PAYLOAD_LAST, None, None]]
)


class TestToReview:
    def test_parses_valid_entry(self) -> None:
        review = _to_review(_REVIEW_ENTRY, "com.example", "com.example")
        assert review is not None
        assert review.store == "googleplay"
        assert review.source == "googleplay_scraper"
        assert review.rating == 4
        assert review.body == "Great app, love it!"
        assert review.author_name == "TestUser"
        assert review.app_version == "2.1.0"
        assert review.app_id == "com.example"

    def test_returns_none_for_invalid_entry(self) -> None:
        result = _to_review([], "com.example", "com.example")
        assert result is None


class TestParseResponse:
    def test_parses_valid_response(self) -> None:
        entries, token = _parse_response(_RAW_RESPONSE)
        assert len(entries) == 1
        assert token == "next-page-token"

    def test_parses_last_page(self) -> None:
        entries, token = _parse_response(_RAW_RESPONSE_LAST)
        assert len(entries) == 1
        assert token is None

    def test_empty_response(self) -> None:
        entries, token = _parse_response(")]}'\n\n[]")
        assert entries == []
        assert token is None

    def test_list_token_means_end(self) -> None:
        """oCPfdb returns a list (not string) token when no more pages."""
        payload = json.dumps([[_REVIEW_ENTRY], [None, ["not-a-token"]], [None]])
        raw = ")]}'\n\n" + json.dumps([["wrb.fr", "oCPfdb", payload, None, None]])
        entries, token = _parse_response(raw)
        assert len(entries) == 1
        assert token is None

    def test_null_inner_payload(self) -> None:
        raw = ")]}'\n\n" + json.dumps([["wrb.fr", "oCPfdb", None, None, None]])
        entries, token = _parse_response(raw)
        assert entries == []
        assert token is None


class TestGoogleScraperProvider:
    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_fetch_success(self, mock_post: Any) -> None:
        mock_post.return_value = HttpResponse(status=200, body=_RAW_RESPONSE_LAST)

        provider = GoogleScraperProvider()
        result = provider.fetch("com.example", "com.example")

        assert len(result.reviews) == 1
        assert result.reviews[0].store == "googleplay"
        assert result.reviews[0].source == "googleplay_scraper"
        assert len(result.failures) == 0

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_fetch_paginates(self, mock_post: Any) -> None:
        """Two pages then stops on missing token."""
        mock_post.side_effect = [
            HttpResponse(status=200, body=_RAW_RESPONSE),
            HttpResponse(status=200, body=_RAW_RESPONSE_LAST),
        ]

        provider = GoogleScraperProvider()
        result = provider.fetch("com.example", "com.example")

        assert len(result.reviews) == 2
        assert mock_post.call_count == 2

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_fetch_http_error(self, mock_post: Any) -> None:
        import urllib.error

        mock_post.side_effect = urllib.error.URLError("timeout")

        provider = GoogleScraperProvider(max_retries=1)
        result = provider.fetch("com.example", "com.example")

        assert len(result.reviews) == 0
        assert len(result.failures) == 1

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_fetch_non_200(self, mock_post: Any) -> None:
        mock_post.return_value = HttpResponse(status=503, body="error")

        provider = GoogleScraperProvider(max_retries=1)
        result = provider.fetch("com.example", "com.example")

        assert len(result.reviews) == 0
        assert len(result.failures) == 1

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_fetch_empty_response(self, mock_post: Any) -> None:
        mock_post.return_value = HttpResponse(status=200, body=")]}'\n\n[]")

        provider = GoogleScraperProvider()
        result = provider.fetch("com.example", "com.example")

        assert len(result.reviews) == 0
        assert len(result.failures) == 0

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    @patch("app_reviews.providers.googleplay.scraper.time.sleep")
    def test_rate_limit_backoff(self, mock_sleep: Any, mock_post: Any) -> None:
        """Rate-limit response triggers sleep then retry."""
        rate_body = ")]}'\n\n" + json.dumps(
            [
                [
                    "wrb.fr",
                    "oCPfdb",
                    "PlayGatewayError",
                    None,
                ]
            ]
        )
        mock_post.side_effect = [
            HttpResponse(status=200, body=rate_body),
            HttpResponse(status=200, body=_RAW_RESPONSE_LAST),
        ]

        provider = GoogleScraperProvider(max_retries=2)
        result = provider.fetch("com.example", "com.example")

        assert len(result.reviews) == 1
        mock_sleep.assert_called_once_with(5.0)

    @patch("app_reviews.providers.googleplay.scraper.http_post")
    def test_passes_hl_gl_params(self, mock_post: Any) -> None:
        mock_post.return_value = HttpResponse(status=200, body=_RAW_RESPONSE_LAST)

        provider = GoogleScraperProvider(lang="de", country="de")
        provider.fetch("com.example", "com.example")

        call_url = mock_post.call_args[0][0]
        assert "hl=de" in call_url
        assert "gl=de" in call_url
