"""Literal type aliases for store, provider, and source identifiers."""

from typing import Literal

Store = Literal["appstore", "googleplay"]
AppStoreProvider = Literal["scraper", "official"]
GooglePlayProvider = Literal["scraper", "official"]
Provider = Literal["auto", "scraper", "official"]
Source = Literal[
    "appstore_scraper",
    "appstore_official",
    "googleplay_scraper",
    "googleplay_official",
]
