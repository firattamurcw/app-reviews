"""HTTP utility functions using urllib (stdlib)."""

from __future__ import annotations

import gzip
import json
import logging
import time
import typing
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import IO, TYPE_CHECKING

if TYPE_CHECKING:
    from app_reviews.models.retry import RetryConfig

_LOG = logging.getLogger(__name__)

_DEFAULT_USER_AGENT = "app-reviews"


@dataclass(frozen=True, slots=True)
class HttpResponse:
    """Simple HTTP response wrapper."""

    status: int
    body: str

    def json(self) -> object:
        """Parse body as JSON."""
        return json.loads(self.body)


def http_get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
    timeout: float = 30.0,
    retry: RetryConfig | None = None,
    proxy: str | None = None,
) -> HttpResponse:
    """Perform a GET request with optional retry and proxy."""
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    h = {"User-Agent": _DEFAULT_USER_AGENT}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    return _execute(req, timeout=timeout, retry=retry, proxy=proxy)


def http_post(
    url: str,
    *,
    body: str,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    retry: RetryConfig | None = None,
    proxy: str | None = None,
) -> HttpResponse:
    """Perform a POST request with optional retry and proxy."""
    h = {"User-Agent": _DEFAULT_USER_AGENT}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=body.encode(), headers=h, method="POST")
    return _execute(req, timeout=timeout, retry=retry, proxy=proxy)


def _read_body(resp: IO[bytes]) -> str:
    """Read response body, decompressing gzip if needed."""
    raw = resp.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", errors="replace")


def _execute(
    req: urllib.request.Request,
    *,
    timeout: float,
    retry: RetryConfig | None,
    proxy: str | None,
) -> HttpResponse:
    """Execute request with optional proxy and retry logic."""
    from app_reviews.utils.retry import RetryPolicy

    urlopen: typing.Callable[..., typing.Any]
    if proxy:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": proxy, "https": proxy})
        )
        urlopen = opener.open
    else:
        urlopen = urllib.request.urlopen

    policy = RetryPolicy(retry) if retry else None
    attempt = 0

    while True:
        _LOG.debug("%s %s (attempt %d)", req.get_method(), req.full_url, attempt + 1)
        try:
            with urlopen(req, timeout=timeout) as resp:
                response = HttpResponse(status=resp.status, body=_read_body(resp))
        except urllib.error.HTTPError as e:
            response = HttpResponse(status=e.code, body=_read_body(e))
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            response = HttpResponse(status=0, body=str(e))

        if policy and policy.should_retry(attempt, response.status):
            delay = policy.get_delay(attempt)
            _LOG.warning(
                "%s %s returned status %d, retrying in %.1fs (attempt %d)",
                req.get_method(),
                req.full_url,
                response.status,
                delay,
                attempt + 1,
            )
            time.sleep(delay)
            attempt += 1
            continue

        if response.status and response.status >= 400:
            _LOG.warning(
                "%s %s failed with status %d",
                req.get_method(),
                req.full_url,
                response.status,
            )

        return response
