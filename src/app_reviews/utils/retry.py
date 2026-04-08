"""HTTP retry policy."""

from app_reviews.models.retry import RetryConfig


class RetryPolicy:
    """Determines whether a failed HTTP request should be retried."""

    def __init__(self, config: RetryConfig) -> None:
        self._config = config
        self._retryable = frozenset(config.retry_on)

    def should_retry(self, attempt: int, status_code: int) -> bool:
        """True if status is retryable and attempts remain."""
        if self._config.max_retries == 0:
            return False
        if attempt >= self._config.max_retries:
            return False
        return status_code in self._retryable

    def get_delay(self, attempt: int) -> float:
        """Exponential backoff: backoff_factor * 2^attempt seconds."""
        return float(self._config.backoff_factor * (2**attempt))
