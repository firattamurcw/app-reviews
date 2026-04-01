"""Retry policy for HTTP requests."""

from appstore_reviews.config.models import RetryConfig

_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})


class RetryPolicy:
    """Determines whether a request should be retried."""

    def __init__(self, config: RetryConfig) -> None:
        self._config = config

    def should_retry(self, attempt: int, status_code: int) -> bool:
        """Retry on 429, 500, 502, 503, 504 if attempts remain."""
        if self._config.max_retries == 0:
            return False
        if attempt >= self._config.max_retries:
            return False
        return status_code in _RETRYABLE_STATUS_CODES

    def get_delay(self, attempt: int) -> float:
        """Exponential backoff: backoff_factor * (2 ** attempt)."""
        return float(self._config.backoff_factor * (2**attempt))
