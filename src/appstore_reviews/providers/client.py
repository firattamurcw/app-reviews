"""Thin factory functions for creating configured httpx clients."""

import httpx

_DEFAULT_USER_AGENT = "appstore-reviews"


def create_sync_client(
    *,
    timeout: float = 30.0,
    proxy_url: str | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Client:
    """Create a configured sync httpx.Client."""
    merged_headers: dict[str, str] = {"user-agent": _DEFAULT_USER_AGENT}
    if headers:
        merged_headers.update(headers)

    if proxy_url is not None:
        return httpx.Client(
            timeout=timeout,
            headers=merged_headers,
            proxy=proxy_url,
        )
    return httpx.Client(
        timeout=timeout,
        headers=merged_headers,
    )


def create_async_client(
    *,
    timeout: float = 30.0,
    proxy_url: str | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.AsyncClient:
    """Create a configured async httpx.AsyncClient."""
    merged_headers: dict[str, str] = {"user-agent": _DEFAULT_USER_AGENT}
    if headers:
        merged_headers.update(headers)

    if proxy_url is not None:
        return httpx.AsyncClient(
            timeout=timeout,
            headers=merged_headers,
            proxy=proxy_url,
        )
    return httpx.AsyncClient(
        timeout=timeout,
        headers=merged_headers,
    )
