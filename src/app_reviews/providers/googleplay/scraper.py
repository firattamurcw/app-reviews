"""Google Play web scraper provider for reviews."""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.parse
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app_reviews.models.result import FetchError
from app_reviews.models.review import Review
from app_reviews.providers.base import PageResult
from app_reviews.utils.http import http_post

if TYPE_CHECKING:
    from app_reviews.models.retry import RetryConfig

_PROVIDER = "scraper"
_LOG = logging.getLogger(__name__)

_BATCHEXECUTE_URL = "https://play.google.com/_/PlayStoreUi/data/batchexecute"
_RPC_ID = "oCPfdb"

SORT_NEWEST = 2
SORT_RELEVANT = 1
SORT_RATING = 3

_RESPONSE_PREFIX_RE = re.compile(r"\)]}'\n\n([\s\S]+)")
_MAX_BATCH_SIZE = 200


def _build_body(
    app_id: str,
    count: int = _MAX_BATCH_SIZE,
    sort: int = SORT_NEWEST,
    page_token: str | None = None,
    lang: str = "en",
    country: str = "us",
) -> tuple[str, str]:
    """Build POST body and URL for one review fetch RPC. Returns (url, encoded_body)."""
    pagination = [count, None, page_token] if page_token else [count]
    filters = [None] * 9
    inner = json.dumps([None, [2, sort, pagination, None, filters], [app_id, 7]])
    payload = json.dumps([[[_RPC_ID, inner, None, "generic"]]])
    url = (
        f"{_BATCHEXECUTE_URL}"
        f"?hl={urllib.parse.quote(lang)}"
        f"&gl={urllib.parse.quote(country)}"
    )
    body = urllib.parse.urlencode({"f.req": payload})
    return url, body


def _parse_response(raw: str) -> tuple[list[list[Any]], str | None]:
    """Parse batchexecute response -> (review_entries, page_token | None)."""
    match = _RESPONSE_PREFIX_RE.search(raw)
    if not match:
        _LOG.warning("Google Play response missing expected prefix")
        return [], None
    try:
        outer = json.loads(match.group(1))
    except json.JSONDecodeError:
        _LOG.warning("Google Play response body is not valid JSON")
        return [], None

    for item in outer:
        if not isinstance(item, list) or len(item) < 3:
            continue
        if item[0] != "wrb.fr" or item[1] != _RPC_ID:
            continue
        if item[2] is None:
            return [], None
        try:
            data = json.loads(item[2])
        except json.JSONDecodeError:
            return [], None

        reviews = data[0] if data and data[0] else []
        token: str | None = None
        if len(data) > 1 and data[-2]:
            tok = data[-2][-1]
            if isinstance(tok, str):
                token = tok
        return reviews, token

    return [], None


# Indices into the batchexecute review array structure.
_IDX_REVIEW_ID = 0
_IDX_AUTHOR_INFO = 1
_IDX_AUTHOR_NAME = 0
_IDX_RATING = 2
_IDX_BODY = 4
_IDX_TIMESTAMPS = 5
_IDX_CREATED_TS = 0
_IDX_UPDATED_TS = 1
_IDX_APP_VERSION = 10


def _to_review(entry: list[Any], app_id: str) -> Review | None:
    """Parse a single review array into a Review."""
    try:
        review_id = entry[_IDX_REVIEW_ID]
        author_name = entry[_IDX_AUTHOR_INFO][_IDX_AUTHOR_NAME]
        rating = int(entry[_IDX_RATING])
        body = entry[_IDX_BODY] or ""
        timestamps = entry[_IDX_TIMESTAMPS]
        created_at = datetime.fromtimestamp(timestamps[_IDX_CREATED_TS], tz=UTC)
        updated_ts = (
            timestamps[_IDX_UPDATED_TS] if len(timestamps) > _IDX_UPDATED_TS else None
        )
        updated_at = datetime.fromtimestamp(updated_ts, tz=UTC) if updated_ts else None
        app_version = (
            str(entry[_IDX_APP_VERSION])
            if len(entry) > _IDX_APP_VERSION and entry[_IDX_APP_VERSION]
            else None
        )

        return Review(
            store="googleplay",
            app_id=app_id,
            country="",
            rating=rating,
            title="",
            body=body,
            author_name=author_name,
            app_version=app_version,
            created_at=created_at,
            updated_at=updated_at,
            source="googleplay_scraper",
            raw=None,
            fetched_at=datetime.now(tz=UTC),
            id=f"googleplay_scraper-{review_id}",
        )
    except (IndexError, TypeError, ValueError):
        _LOG.warning("Failed to parse review entry for app %s: %r", app_id, entry[:3])
        return None


class GoogleScraperProvider:
    """Fetches one page from Google Play via batchexecute RPC."""

    def __init__(
        self,
        count: int = _MAX_BATCH_SIZE,
        timeout: float = 30.0,
        lang: str = "en",
        proxy: str | None = None,
        retry: RetryConfig | None = None,
    ) -> None:
        self._count = min(count, _MAX_BATCH_SIZE)
        self._timeout = timeout
        self._lang = lang
        self._proxy = proxy
        self._retry = retry

    def countries(self, requested: list[str]) -> list[str]:
        """Google scraper supports per-country requests — return all requested."""
        return requested if requested else []

    def fetch_page(self, app_id: str, country: str, cursor: str | None) -> PageResult:
        """Fetch one page. cursor is the page token from the previous response."""
        url, body = _build_body(
            app_id,
            count=self._count,
            page_token=cursor,
            lang=self._lang,
            country=country or "us",
        )

        try:
            resp = http_post(
                url,
                body=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=self._timeout,
                proxy=self._proxy,
                retry=self._retry,
            )
        except urllib.error.URLError as exc:
            return PageResult(error=FetchError(country=country, message=str(exc)))

        if resp.status != 200:
            return PageResult(
                error=FetchError(country=country, message=f"HTTP {resp.status}")
            )

        entries, next_token = _parse_response(resp.body)
        reviews = [r for e in entries if (r := _to_review(e, app_id)) is not None]
        return PageResult(reviews=reviews, next_cursor=next_token)
