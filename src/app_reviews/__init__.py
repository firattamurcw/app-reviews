"""app-reviews: Python package for App Store and Google Play reviews."""

from importlib.metadata import version

from app_reviews.client import AppStoreReviews, GooglePlayReviews
from app_reviews.models.auth import AppStoreAuth, GooglePlayAuth
from app_reviews.models.callback import FetchCallback
from app_reviews.models.country import Country
from app_reviews.models.result import CountryStatus, FetchResult, FetchStats
from app_reviews.models.retry import RetryConfig
from app_reviews.models.review import Review
from app_reviews.models.sort import Sort
from app_reviews.scraper import AppStoreScraper, GooglePlayScraper

__version__ = version("app-reviews")

__all__ = [
    # Clients
    "AppStoreReviews",
    "GooglePlayReviews",
    # Auth
    "AppStoreAuth",
    "GooglePlayAuth",
    # Config
    "RetryConfig",
    # Enums
    "Country",
    "Sort",
    # Results
    "FetchResult",
    "FetchStats",
    "CountryStatus",
    "Review",
    # Callbacks
    "FetchCallback",
    # Backwards compat (deprecated)
    "AppStoreScraper",
    "GooglePlayScraper",
    # Meta
    "__version__",
]
