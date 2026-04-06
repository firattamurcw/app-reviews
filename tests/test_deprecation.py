"""Tests for backwards-compatibility aliases."""

import warnings


def test_appstore_scraper_alias_warns():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from app_reviews.scraper import AppStoreScraper

        scraper = AppStoreScraper(app_id="12345")
        assert scraper is not None
        assert any(issubclass(warning.category, DeprecationWarning) for warning in w)


def test_googleplay_scraper_alias_warns():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from app_reviews.scraper import GooglePlayScraper

        scraper = GooglePlayScraper(app_id="com.example")
        assert scraper is not None
        assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
