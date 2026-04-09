"""Tests for AppMetadata icon_url field."""

from app_reviews.models.metadata import AppMetadata


class TestAppMetadataIconUrl:
    def test_icon_url_defaults_to_none(self):
        meta = AppMetadata(
            app_id="123",
            store="appstore",
            name="Test",
            developer="Dev",
            category="Utils",
            price="Free",
            version="1.0",
            rating=4.5,
            rating_count=100,
            url="https://example.com",
        )
        assert meta.icon_url is None

    def test_icon_url_can_be_set(self):
        meta = AppMetadata(
            app_id="123",
            store="appstore",
            name="Test",
            developer="Dev",
            category="Utils",
            price="Free",
            version="1.0",
            rating=4.5,
            rating_count=100,
            url="https://example.com",
            icon_url="https://example.com/icon.png",
        )
        assert meta.icon_url == "https://example.com/icon.png"
