"""Tests for app metadata lookup utilities."""

import json
from unittest.mock import patch

import pytest

from app_reviews.errors import HttpError
from app_reviews.models.metadata import AppMetadata
from app_reviews.utils.http import HttpResponse
from app_reviews.utils.metadata import lookup_metadata

_ITUNES_RESPONSE = json.dumps(
    {
        "resultCount": 1,
        "results": [
            {
                "trackName": "TestApp",
                "artistName": "TestDev",
                "primaryGenreName": "Utilities",
                "formattedPrice": "Free",
                "version": "1.2.3",
                "averageUserRating": 4.5,
                "userRatingCount": 1000,
                "trackViewUrl": "https://apps.apple.com/app/id12345",
            }
        ],
    }
)

_GOOGLE_PLAY_HTML = """\
<html>
<head><title>TestApp</title></head>
<body>
<h1>Google Test App</h1>
<a href="/store/apps/dev?id=123">Google Dev</a>
<a href="/store/apps/category/TOOLS">Tools</a>
<div aria-label="Rated 4.2 out of 5 stars">4.2</div>
</body>
</html>
"""

_GOOGLE_PLAY_HTML_MINIMAL = """\
<html><body>
<h1>Minimal App</h1>
</body></html>
"""


class TestLookupApple:
    @patch("app_reviews.utils.metadata.http_get")
    def test_returns_correct_metadata(self, mock_get):
        mock_get.return_value = HttpResponse(status=200, body=_ITUNES_RESPONSE)
        result = lookup_metadata("12345", store="appstore")
        assert isinstance(result, AppMetadata)
        assert result.name == "TestApp"
        assert result.developer == "TestDev"
        assert result.category == "Utilities"
        assert result.rating == 4.5
        assert result.rating_count == 1000
        assert result.store == "appstore"

    @patch("app_reviews.utils.metadata.http_get")
    def test_not_found_raises_value_error(self, mock_get):
        mock_get.return_value = HttpResponse(
            status=200, body=json.dumps({"resultCount": 0, "results": []})
        )
        with pytest.raises(ValueError, match="not found"):
            lookup_metadata("99999", store="appstore")

    @patch("app_reviews.utils.metadata.http_get")
    def test_http_error_raises(self, mock_get):
        mock_get.return_value = HttpResponse(status=500, body="error")
        with pytest.raises(HttpError, match="500"):
            lookup_metadata("12345", store="appstore")


class TestLookupGoogle:
    @patch("app_reviews.utils.metadata.http_get")
    def test_returns_correct_metadata(self, mock_get):
        mock_get.return_value = HttpResponse(status=200, body=_GOOGLE_PLAY_HTML)
        result = lookup_metadata("com.example.app", store="googleplay")
        assert isinstance(result, AppMetadata)
        assert result.name == "Google Test App"
        assert result.developer == "Google Dev"
        assert result.category == "Tools"
        assert result.rating == 4.2
        assert result.store == "googleplay"

    @patch("app_reviews.utils.metadata.http_get")
    def test_missing_fields_default_to_unknown(self, mock_get):
        mock_get.return_value = HttpResponse(status=200, body=_GOOGLE_PLAY_HTML_MINIMAL)
        result = lookup_metadata("com.example.app", store="googleplay")
        assert result.name == "Minimal App"
        assert result.developer == "Unknown"
        assert result.rating == 0.0

    @patch("app_reviews.utils.metadata.http_get")
    def test_404_raises_value_error(self, mock_get):
        mock_get.return_value = HttpResponse(status=404, body="not found")
        with pytest.raises(ValueError, match="not found"):
            lookup_metadata("com.bad.app", store="googleplay")

    @patch("app_reviews.utils.metadata.http_get")
    def test_http_error_raises(self, mock_get):
        mock_get.return_value = HttpResponse(status=503, body="error")
        with pytest.raises(HttpError, match="503"):
            lookup_metadata("com.example.app", store="googleplay")


class TestLookupMetadataAutoDetect:
    @patch("app_reviews.utils.metadata.http_get")
    def test_numeric_id_detected_as_appstore(self, mock_get):
        mock_get.return_value = HttpResponse(status=200, body=_ITUNES_RESPONSE)
        result = lookup_metadata("12345")
        assert result.store == "appstore"

    @patch("app_reviews.utils.metadata.http_get")
    def test_package_name_detected_as_googleplay(self, mock_get):
        mock_get.return_value = HttpResponse(status=200, body=_GOOGLE_PLAY_HTML)
        result = lookup_metadata("com.example.app")
        assert result.store == "googleplay"
