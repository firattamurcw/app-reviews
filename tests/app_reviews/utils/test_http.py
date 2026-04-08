"""Tests for HTTP utility with retry support."""

from unittest.mock import MagicMock, patch

from app_reviews.models.retry import RetryConfig
from app_reviews.utils.http import http_get, http_post


class TestHttpGetRetry:
    @patch("app_reviews.utils.http.urllib.request.urlopen")
    def test_retries_on_500(self, mock_open):
        """500 response is retried up to max_retries times."""
        fail_resp = MagicMock()
        fail_resp.status = 500
        fail_resp.read.return_value = b"error"
        fail_resp.__enter__ = lambda s: s
        fail_resp.__exit__ = MagicMock(return_value=False)

        ok_resp = MagicMock()
        ok_resp.status = 200
        ok_resp.read.return_value = b"ok"
        ok_resp.__enter__ = lambda s: s
        ok_resp.__exit__ = MagicMock(return_value=False)

        mock_open.side_effect = [fail_resp, ok_resp]

        result = http_get(
            "http://example.com",
            retry=RetryConfig(max_retries=2, backoff_factor=0),
        )
        assert result.status == 200
        assert mock_open.call_count == 2

    @patch("app_reviews.utils.http.time.sleep")
    @patch("app_reviews.utils.http.urllib.request.urlopen")
    def test_backoff_delay_between_retries(self, mock_open, mock_sleep):
        """Exponential backoff delay is applied between retries."""
        fail_resp = MagicMock()
        fail_resp.status = 503
        fail_resp.read.return_value = b"error"
        fail_resp.__enter__ = lambda s: s
        fail_resp.__exit__ = MagicMock(return_value=False)

        ok_resp = MagicMock()
        ok_resp.status = 200
        ok_resp.read.return_value = b"ok"
        ok_resp.__enter__ = lambda s: s
        ok_resp.__exit__ = MagicMock(return_value=False)

        mock_open.side_effect = [fail_resp, ok_resp]

        http_get(
            "http://example.com",
            retry=RetryConfig(max_retries=2, backoff_factor=1.0),
        )
        mock_sleep.assert_called_once_with(1.0)

    @patch("app_reviews.utils.http.urllib.request.urlopen")
    def test_no_retry_on_404(self, mock_open):
        """404 is not retried — client errors are permanent."""
        resp = MagicMock()
        resp.status = 404
        resp.read.return_value = b"not found"
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)

        mock_open.return_value = resp

        result = http_get(
            "http://example.com",
            retry=RetryConfig(max_retries=3, backoff_factor=0),
        )
        assert result.status == 404
        assert mock_open.call_count == 1

    @patch("app_reviews.utils.http.urllib.request.urlopen")
    def test_no_retry_config_means_single_attempt(self, mock_open):
        """Without retry config, only one attempt is made."""
        resp = MagicMock()
        resp.status = 500
        resp.read.return_value = b"error"
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)

        mock_open.return_value = resp

        result = http_get("http://example.com", retry=None)
        assert result.status == 500
        assert mock_open.call_count == 1

    @patch("app_reviews.utils.http.urllib.request.urlopen")
    def test_returns_last_response_after_exhausting_retries(self, mock_open):
        """After all retries fail, returns the last error response."""
        resp = MagicMock()
        resp.status = 502
        resp.read.return_value = b"bad gateway"
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)

        mock_open.return_value = resp

        result = http_get(
            "http://example.com",
            retry=RetryConfig(max_retries=2, backoff_factor=0),
        )
        assert result.status == 502
        assert mock_open.call_count == 3  # initial + 2 retries


class TestHttpPostRetry:
    @patch("app_reviews.utils.http.urllib.request.urlopen")
    def test_retries_on_503(self, mock_open):
        """POST also retries on server errors."""
        fail_resp = MagicMock()
        fail_resp.status = 503
        fail_resp.read.return_value = b"error"
        fail_resp.__enter__ = lambda s: s
        fail_resp.__exit__ = MagicMock(return_value=False)

        ok_resp = MagicMock()
        ok_resp.status = 200
        ok_resp.read.return_value = b"ok"
        ok_resp.__enter__ = lambda s: s
        ok_resp.__exit__ = MagicMock(return_value=False)

        mock_open.side_effect = [fail_resp, ok_resp]

        result = http_post(
            "http://example.com",
            body="data",
            retry=RetryConfig(max_retries=2, backoff_factor=0),
        )
        assert result.status == 200
        assert mock_open.call_count == 2
