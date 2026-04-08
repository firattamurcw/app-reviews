"""Behavioral tests for retry policy."""

from app_reviews.models.retry import RetryConfig
from app_reviews.utils.retry import RetryPolicy


class TestRetryPolicy:
    """Tests verify WHEN retries happen, not HOW delays are calculated."""

    def test_retries_on_server_error(self) -> None:
        """A 500 on the first attempt should be retried."""
        policy = RetryPolicy(RetryConfig(max_retries=3))
        assert policy.should_retry(attempt=0, status_code=500) is True

    def test_retries_on_rate_limit(self) -> None:
        """A 429 rate-limit should be retried."""
        policy = RetryPolicy(RetryConfig(max_retries=3))
        assert policy.should_retry(attempt=0, status_code=429) is True

    def test_retries_on_bad_gateway(self) -> None:
        """502 and 503 are transient — should be retried."""
        policy = RetryPolicy(RetryConfig(max_retries=3))
        assert policy.should_retry(attempt=0, status_code=502) is True
        assert policy.should_retry(attempt=0, status_code=503) is True

    def test_does_not_retry_client_errors(self) -> None:
        """4xx client errors (except 429) are permanent — no retry."""
        policy = RetryPolicy(RetryConfig(max_retries=3))
        assert policy.should_retry(attempt=0, status_code=400) is False
        assert policy.should_retry(attempt=0, status_code=401) is False
        assert policy.should_retry(attempt=0, status_code=403) is False
        assert policy.should_retry(attempt=0, status_code=404) is False

    def test_gives_up_after_max_retries(self) -> None:
        """After exhausting all retries, stop even on retryable errors."""
        policy = RetryPolicy(RetryConfig(max_retries=2))
        assert policy.should_retry(attempt=0, status_code=500) is True
        assert policy.should_retry(attempt=1, status_code=500) is True
        assert policy.should_retry(attempt=2, status_code=500) is False

    def test_no_retries_when_disabled(self) -> None:
        """With max_retries=0, never retry anything."""
        policy = RetryPolicy(RetryConfig(max_retries=0))
        assert policy.should_retry(attempt=0, status_code=500) is False
        assert policy.should_retry(attempt=0, status_code=429) is False

    def test_delay_increases_with_each_attempt(self) -> None:
        """Later attempts wait longer than earlier ones."""
        policy = RetryPolicy(RetryConfig(backoff_factor=1.0))
        delays = [policy.get_delay(attempt=i) for i in range(3)]
        assert delays[0] < delays[1] < delays[2]


def test_retry_config_retry_on_defaults():
    config = RetryConfig()
    assert config.retry_on == [500, 502, 503, 504, 429]


def test_retry_config_retry_on_custom():
    config = RetryConfig(retry_on=[500, 502])
    assert config.retry_on == [500, 502]
