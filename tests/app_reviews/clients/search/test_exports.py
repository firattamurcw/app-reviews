"""Tests that search classes are importable from the top-level package."""


def test_appstore_search_importable():
    from app_reviews import AppStoreSearch

    assert AppStoreSearch is not None


def test_googleplay_search_importable():
    from app_reviews import GooglePlaySearch

    assert GooglePlaySearch is not None


def test_clients_package_exports():
    from app_reviews.clients import AppStoreSearch, GooglePlaySearch

    assert AppStoreSearch is not None
    assert GooglePlaySearch is not None
