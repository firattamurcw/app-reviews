"""HTTP utility functions using urllib (stdlib)."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

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
) -> HttpResponse:
    """Perform a GET request."""
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    h = {"User-Agent": _DEFAULT_USER_AGENT}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return HttpResponse(status=resp.status, body=resp.read().decode())
    except urllib.error.HTTPError as e:
        return HttpResponse(status=e.code, body=e.read().decode())


def http_post(
    url: str,
    *,
    body: str,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> HttpResponse:
    """Perform a POST request."""
    h = {"User-Agent": _DEFAULT_USER_AGENT}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=body.encode(), headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return HttpResponse(status=resp.status, body=resp.read().decode())
    except urllib.error.HTTPError as e:
        return HttpResponse(status=e.code, body=e.read().decode())
