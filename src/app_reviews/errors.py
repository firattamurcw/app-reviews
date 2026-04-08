"""Typed exceptions for app-reviews."""


class AppReviewsError(Exception):
    """Base exception for all app-reviews errors."""


class AuthError(AppReviewsError):
    """Authentication or token exchange failure."""


class HttpError(AppReviewsError):
    """Network-level failure (timeout, connection refused, etc.)."""
