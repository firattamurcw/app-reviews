"""Tests for AppStoreSearch."""

import json
from unittest.mock import patch

import pytest

from app_reviews.clients.search.appstore import AppStoreSearch
from app_reviews.errors import HttpError
from app_reviews.models.country import Country
from app_reviews.models.metadata import AppMetadata
from app_reviews.utils.http import HttpResponse

_SEARCH_RESPONSE = json.dumps(
    {
        "resultCount": 2,
        "results": [
            {
                "trackId": 310633997,
                "bundleId": "com.whatsapp.WhatsApp",
                "trackName": "WhatsApp Messenger",
                "artistName": "WhatsApp Inc.",
                "primaryGenreName": "Social Networking",
                "formattedPrice": "Free",
                "version": "24.10.79",
                "averageUserRating": 4.7,
                "userRatingCount": 5000000,
                "trackViewUrl": "https://apps.apple.com/us/app/whatsapp-messenger/id310633997",
                "artworkUrl512": "https://is1-ssl.mzstatic.com/image/512x512.jpg",
            },
            {
                "trackId": 485449038,
                "bundleId": "com.whatsapp.WhatsAppBusiness",
                "trackName": "WhatsApp Business",
                "artistName": "WhatsApp Inc.",
                "primaryGenreName": "Business",
                "formattedPrice": "Free",
                "version": "24.10.79",
                "averageUserRating": 4.5,
                "userRatingCount": 1000000,
                "trackViewUrl": "https://apps.apple.com/us/app/whatsapp-business/id485449038",
                "artworkUrl512": "https://is1-ssl.mzstatic.com/image/biz-512x512.jpg",
            },
        ],
    }
)

_EMPTY_RESPONSE = json.dumps({"resultCount": 0, "results": []})

_LOOKUP_RESPONSE = json.dumps(
    {
        "resultCount": 1,
        "results": [
            {
                "trackId": 310633997,
                "bundleId": "com.whatsapp.WhatsApp",
                "trackName": "WhatsApp Messenger",
                "artistName": "WhatsApp Inc.",
                "primaryGenreName": "Social Networking",
                "formattedPrice": "Free",
                "version": "24.10.79",
                "averageUserRating": 4.7,
                "userRatingCount": 5000000,
                "trackViewUrl": "https://apps.apple.com/us/app/whatsapp-messenger/id310633997",
                "artworkUrl512": "https://is1-ssl.mzstatic.com/image/512x512.jpg",
            }
        ],
    }
)


class TestAppStoreSearchConstruction:
    def test_default(self):
        client = AppStoreSearch()
        assert client is not None

    def test_with_proxy(self):
        client = AppStoreSearch(proxy="http://proxy:8080")
        assert client._proxy == "http://proxy:8080"


class TestAppStoreSearchSearch:
    @patch("app_reviews.clients.search.appstore.http_get")
    def test_returns_list_of_app_metadata(self, mock_get):
        mock_get.return_value = HttpResponse(status=200, body=_SEARCH_RESPONSE)
        results = AppStoreSearch().search("whatsapp")
        assert len(results) == 2
        assert all(isinstance(r, AppMetadata) for r in results)

    @patch("app_reviews.clients.search.appstore.http_get")
    def test_maps_fields_correctly(self, mock_get):
        mock_get.return_value = HttpResponse(status=200, body=_SEARCH_RESPONSE)
        results = AppStoreSearch().search("whatsapp")
        app = results[0]
        assert app.app_id == "310633997"
        assert app.store == "appstore"
        assert app.name == "WhatsApp Messenger"
        assert app.developer == "WhatsApp Inc."
        assert app.category == "Social Networking"
        assert app.price == "Free"
        assert app.version == "24.10.79"
        assert app.rating == 4.7
        assert app.rating_count == 5000000
        assert app.icon_url == "https://is1-ssl.mzstatic.com/image/512x512.jpg"

    @patch("app_reviews.clients.search.appstore.http_get")
    def test_passes_query_params(self, mock_get):
        mock_get.return_value = HttpResponse(status=200, body=_EMPTY_RESPONSE)
        AppStoreSearch().search("test", country=Country.GB, limit=10)
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["term"] == "test"
        assert params["country"] == "gb"
        assert params["limit"] == "10"
        assert params["entity"] == "software"

    @patch("app_reviews.clients.search.appstore.http_get")
    def test_empty_results_returns_empty_list(self, mock_get):
        mock_get.return_value = HttpResponse(status=200, body=_EMPTY_RESPONSE)
        results = AppStoreSearch().search("xyznonexistent")
        assert results == []

    @patch("app_reviews.clients.search.appstore.http_get")
    def test_http_error_raises(self, mock_get):
        mock_get.return_value = HttpResponse(status=503, body="error")
        with pytest.raises(HttpError):
            AppStoreSearch().search("whatsapp")


class TestAppStoreSearchLookup:
    @patch("app_reviews.clients.search.appstore.http_get")
    def test_returns_app_metadata(self, mock_get):
        mock_get.return_value = HttpResponse(status=200, body=_LOOKUP_RESPONSE)
        result = AppStoreSearch().lookup("com.whatsapp.WhatsApp")
        assert isinstance(result, AppMetadata)
        assert result.name == "WhatsApp Messenger"
        assert result.icon_url == "https://is1-ssl.mzstatic.com/image/512x512.jpg"

    @patch("app_reviews.clients.search.appstore.http_get")
    def test_not_found_returns_none(self, mock_get):
        mock_get.return_value = HttpResponse(status=200, body=_EMPTY_RESPONSE)
        result = AppStoreSearch().lookup("com.nonexistent.app")
        assert result is None

    @patch("app_reviews.clients.search.appstore.http_get")
    def test_passes_bundle_id_param(self, mock_get):
        mock_get.return_value = HttpResponse(status=200, body=_LOOKUP_RESPONSE)
        AppStoreSearch().lookup("com.whatsapp.WhatsApp", country=Country.JP)
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["bundleId"] == "com.whatsapp.WhatsApp"
        assert params["country"] == "jp"

    @patch("app_reviews.clients.search.appstore.http_get")
    def test_http_error_raises(self, mock_get):
        mock_get.return_value = HttpResponse(status=500, body="error")
        with pytest.raises(HttpError):
            AppStoreSearch().lookup("com.whatsapp.WhatsApp")
