"""Tests for Google Play Developer API provider."""

import json
from typing import Any
from unittest.mock import patch

from app_reviews.providers.googleplay.official import (
    GoogleDeveloperApiProvider,
    _map_entry,
)
from app_reviews.utils.http import HttpResponse

_SAMPLE_ENTRY = {
    "reviewId": "abc123",
    "authorName": "TestUser",
    "comments": [
        {
            "userComment": {
                "text": "Amazing app!",
                "starRating": 5,
                "appVersionName": "3.0.1",
                "lastModified": {"seconds": 1700000000, "nanos": 0},
            }
        }
    ],
}

_SAMPLE_API_RESPONSE = {
    "reviews": [_SAMPLE_ENTRY],
}

_PAGINATED_RESPONSE_PAGE1 = {
    "reviews": [_SAMPLE_ENTRY],
    "tokenPagination": {"nextPageToken": "page2token"},
}

_PAGINATED_RESPONSE_PAGE2 = {
    "reviews": [
        {
            "reviewId": "def456",
            "authorName": "User2",
            "comments": [
                {
                    "userComment": {
                        "text": "Good",
                        "starRating": 4,
                        "lastModified": {"seconds": 1700100000},
                    }
                }
            ],
        }
    ],
}


class TestMapEntry:
    def test_maps_valid_entry(self) -> None:
        review = _map_entry(_SAMPLE_ENTRY, "com.example")
        assert review.store == "googleplay"
        assert review.source == "googleplay_official"
        assert review.rating == 5
        assert review.body == "Amazing app!"
        assert review.author_name == "TestUser"
        assert review.app_version == "3.0.1"


class TestGoogleDeveloperApiProvider:
    @patch("app_reviews.providers.googleplay.official.http_get")
    def test_fetch_success(self, mock_get: Any) -> None:
        mock_get.return_value = HttpResponse(
            status=200, body=json.dumps(_SAMPLE_API_RESPONSE)
        )

        provider = GoogleDeveloperApiProvider(auth_header="Bearer token")
        result = provider.fetch("com.example")

        assert len(result.reviews) == 1
        assert result.reviews[0].store == "googleplay"
        assert result.reviews[0].source == "googleplay_official"

    @patch("app_reviews.providers.googleplay.official.http_get")
    def test_fetch_pagination(self, mock_get: Any) -> None:
        mock_get.side_effect = [
            HttpResponse(status=200, body=json.dumps(_PAGINATED_RESPONSE_PAGE1)),
            HttpResponse(status=200, body=json.dumps(_PAGINATED_RESPONSE_PAGE2)),
        ]

        provider = GoogleDeveloperApiProvider(auth_header="Bearer token")
        result = provider.fetch("com.example")

        assert len(result.reviews) == 2

    @patch("app_reviews.providers.googleplay.official.http_get")
    def test_fetch_http_error(self, mock_get: Any) -> None:
        import urllib.error

        mock_get.side_effect = urllib.error.URLError("timeout")

        provider = GoogleDeveloperApiProvider(auth_header="Bearer token")
        result = provider.fetch("com.example")

        assert len(result.reviews) == 0
        assert len(result.failures) == 1

    @patch("app_reviews.providers.googleplay.official.http_get")
    def test_fetch_non_200(self, mock_get: Any) -> None:
        mock_get.return_value = HttpResponse(status=403, body="Forbidden")

        provider = GoogleDeveloperApiProvider(auth_header="Bearer token")
        result = provider.fetch("com.example")

        assert len(result.reviews) == 0
        assert len(result.failures) == 1
