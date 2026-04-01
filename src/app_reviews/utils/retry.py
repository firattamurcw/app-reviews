"""HTTP retry policy."""

from app_reviews.models.retry import RetryConfig

_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})


class RetryPolicy:
    """Determines whether a failed HTTP request should be retried.

    Args:
        config: Retry settings (max attempts, backoff factor).
    """

    def __init__(self, config: RetryConfig) -> None:
        self._config = config

    def should_retry(self, attempt: int, status_code: int) -> bool:
        """Check if a request should be retried.

        Args:
            attempt: Zero-based attempt number.
            status_code: HTTP status code from the failed response.

        Returns:
            ``True`` if the status code is retryable and attempts remain.
        """
        if self._config.max_retries == 0:
            return False
        if attempt >= self._config.max_retries:
            return False
        return status_code in _RETRYABLE_STATUS_CODES

    def get_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay for an attempt.

        Args:
            attempt: Zero-based attempt number.

        Returns:
            Delay in seconds: ``backoff_factor * 2^attempt``.
        """
        return float(self._config.backoff_factor * (2**attempt))
