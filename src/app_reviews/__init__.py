"""app-reviews: Python package for App Store and Google Play reviews."""

import logging
from importlib.metadata import version

from app_reviews.clients import AppStoreReviews, GooglePlayReviews
from app_reviews.models.auth import AppStoreAuth, GooglePlayAuth
from app_reviews.models.country import Country
from app_reviews.models.result import FetchError, FetchResult
from app_reviews.models.retry import RetryConfig
from app_reviews.models.review import Review
from app_reviews.models.sort import Sort

logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = version("app-reviews")

__all__ = [
    "AppStoreAuth",
    "AppStoreReviews",
    "Country",
    "FetchError",
    "FetchResult",
    "GooglePlayAuth",
    "GooglePlayReviews",
    "RetryConfig",
    "Review",
    "Sort",
    "__version__",
]
