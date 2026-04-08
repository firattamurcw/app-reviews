"""Literal type aliases for store, provider, and source identifiers."""

from typing import Literal

Store = Literal["appstore", "googleplay"]
ProviderName = Literal["scraper", "official"]
Source = Literal[
    "appstore_scraper",
    "appstore_official",
    "googleplay_scraper",
    "googleplay_official",
]
