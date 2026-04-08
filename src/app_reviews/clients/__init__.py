"""Reusable client classes for fetching reviews."""

from app_reviews.clients.appstore import AppStoreReviews
from app_reviews.clients.googleplay import GooglePlayReviews

__all__ = ["AppStoreReviews", "GooglePlayReviews"]
