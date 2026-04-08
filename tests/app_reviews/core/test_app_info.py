"""Tests for metadata lookup."""

import json
from typing import Any
from unittest.mock import patch

import pytest

from app_reviews.utils.http import HttpResponse
from app_reviews.utils.metadata import lookup_metadata

_SAMPLE_RESPONSE = {
    "resultCount": 1,
    "results": [
        {
            "trackName": "Facebook",
            "artistName": "Meta Platforms, Inc.",
            "primaryGenreName": "Social Networking",
            "formattedPrice": "Free",
            "version": "450.0",
            "averageUserRating": 2.2,
            "userRatingCount": 4100000,
            "trackViewUrl": "https://apps.apple.com/us/app/facebook/id284882215",
        }
    ],
}


class TestLookupMetadata:
    @patch("app_reviews.utils.metadata.http_get")
    def test_returns_metadata(self, mock_get: Any) -> None:
        mock_get.return_value = HttpResponse(
            status=200, body=json.dumps(_SAMPLE_RESPONSE)
        )

        metadata = lookup_metadata("284882215")

        assert metadata.name == "Facebook"
        assert metadata.developer == "Meta Platforms, Inc."
        assert metadata.category == "Social Networking"
        assert metadata.price == "Free"
        assert metadata.version == "450.0"
        assert metadata.rating == 2.2
        assert metadata.rating_count == 4100000
        assert metadata.store == "appstore"
        assert "284882215" in metadata.url

    @patch("app_reviews.utils.metadata.http_get")
    def test_not_found_raises(self, mock_get: Any) -> None:
        mock_get.return_value = HttpResponse(
            status=200,
            body=json.dumps({"resultCount": 0, "results": []}),
        )

        with pytest.raises(ValueError, match="not found"):
            lookup_metadata("9999999999")

    @patch("app_reviews.utils.metadata.http_get")
    def test_http_error_raises(self, mock_get: Any) -> None:
        import urllib.error

        mock_get.side_effect = urllib.error.URLError("connection failed")

        with pytest.raises(urllib.error.URLError):
            lookup_metadata("284882215")


class TestLookupGoogleMetadata:
    @patch("app_reviews.utils.metadata.http_get")
    def test_returns_google_metadata(self, mock_get: Any) -> None:
        html = """
        <html><body>
        <h1>WhatsApp Messenger</h1>
        <a href="/store/apps/dev?id=123">WhatsApp LLC</a>
        <a href="/store/apps/category/COMMUNICATION">Communication</a>
        <div aria-label="Rated 4.2 out of 5 stars">4.2</div>
        </body></html>
        """
        mock_get.return_value = HttpResponse(status=200, body=html)

        metadata = lookup_metadata("com.whatsapp", store="googleplay")

        assert metadata.store == "googleplay"
        assert metadata.name == "WhatsApp Messenger"
        assert metadata.developer == "WhatsApp LLC"
        assert metadata.category == "Communication"
        assert metadata.rating == 4.2
        assert "com.whatsapp" in metadata.url

    @patch("app_reviews.utils.metadata.http_get")
    def test_store_autodetect_google(self, mock_get: Any) -> None:
        html = "<html><body><h1>App</h1></body></html>"
        mock_get.return_value = HttpResponse(status=200, body=html)

        metadata = lookup_metadata("com.example.app")
        assert metadata.store == "googleplay"
