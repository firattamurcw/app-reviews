"""appstore-reviews: The go-to Python package for App Store review extraction."""

from importlib.metadata import version

from appstore_reviews.models import (
    FetchFailure,
    FetchResult,
    FetchStats,
    FetchWarning,
    Review,
)
from appstore_reviews.scraper import AppStoreScraper, AsyncAppStoreScraper

__version__ = version("appstore-reviews")

__all__ = [
    "AppStoreScraper",
    "AsyncAppStoreScraper",
    "FetchFailure",
    "FetchResult",
    "FetchStats",
    "FetchWarning",
    "Review",
    "__version__",
]
