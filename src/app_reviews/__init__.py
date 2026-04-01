"""app-reviews: Python package for App Store and Google Play reviews."""

from importlib.metadata import version

from app_reviews.models import (
    FetchFailure,
    FetchResult,
    FetchStats,
    FetchWarning,
    Review,
)
from app_reviews.scraper import (
    AppStoreScraper,
    GooglePlayScraper,
)

__version__ = version("app-reviews")

__all__ = [
    "AppStoreScraper",
    "FetchFailure",
    "FetchResult",
    "FetchStats",
    "FetchWarning",
    "GooglePlayScraper",
    "Review",
    "__version__",
]
