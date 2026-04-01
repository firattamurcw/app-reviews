"""Google Play web scraper provider for reviews."""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import urllib.parse
from datetime import UTC, datetime
from typing import Any

from app_reviews.models.result import FetchFailure, FetchResult
from app_reviews.models.review import Review
from app_reviews.utils.http import http_post

_PROVIDER = "scraper"
_LOG = logging.getLogger(__name__)

# Google Play internal batchexecute RPC endpoint.
_BATCHEXECUTE_URL = "https://play.google.com/_/PlayStoreUi/data/batchexecute"

# Current RPC method for fetching reviews.
_RPC_ID = "oCPfdb"

# Sort orders supported by the RPC.
SORT_NEWEST = 2
SORT_RELEVANT = 1
SORT_RATING = 3

# Rate-limit detection string in Google's error responses.
_RATE_LIMIT_MARKER = "PlayGatewayError"

# Prefix Google prepends to batchexecute responses.
_RESPONSE_PREFIX_RE = re.compile(r"\)]}'\n\n([\s\S]+)")

# Default delay (seconds) multiplied by consecutive rate-limit hits.
_RATE_LIMIT_DELAY = 5.0

# Max reviews per single RPC call (Google accepts up to ~4500).
_MAX_BATCH_SIZE = 200


def _build_body(
    app_id: str,
    count: int = _MAX_BATCH_SIZE,
    sort: int = SORT_NEWEST,
    page_token: str | None = None,
    lang: str = "en",
    country: str = "us",
) -> tuple[str, str]:
    """Build the POST body and full URL for a review fetch RPC.

    Returns (url, encoded_body).
    """
    pagination = [count, None, page_token] if page_token else [count]
    # Filter array: [None, score_filter, ..., device_filter]
    # Leaving all None = no filtering.
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


def _parse_response(
    raw: str,
) -> tuple[list[list[Any]], str | None]:
    """Parse batchexecute response → (review_entries, page_token | None)."""
    match = _RESPONSE_PREFIX_RE.search(raw)
    if not match:
        return [], None

    try:
        outer = json.loads(match.group(1))
    except json.JSONDecodeError:
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
            # oCPfdb returns a plain string token;
            # list means end-of-results.
            if isinstance(tok, str):
                token = tok
        return reviews, token

    return [], None


def _to_review(entry: list[Any], app_id: str, app_input: str) -> Review | None:
    """Parse a single review array into a Review."""
    try:
        review_id = entry[0]
        author_name = entry[1][0]
        rating = int(entry[2])
        body = entry[4] or ""
        created_ts = entry[5][0]
        updated_ts = entry[5][1] if len(entry[5]) > 1 else None
        created_at = datetime.fromtimestamp(created_ts, tz=UTC)
        updated_at = datetime.fromtimestamp(updated_ts, tz=UTC) if updated_ts else None
        app_version = str(entry[10]) if len(entry) > 10 and entry[10] else None

        return Review(
            store="googleplay",
            review_id=f"googleplay_scraper-{review_id}",
            canonical_key=f"{app_id}-{review_id}",
            app_id=app_id,
            app_input=app_input,
            country="",
            rating=rating,
            title="",
            body=body,
            author_name=author_name,
            app_version=app_version,
            created_at=created_at,
            updated_at=updated_at,
            source="googleplay_scraper",
            source_review_id=review_id,
            source_payload=None,
            fetched_at=datetime.now(tz=UTC),
        )
    except (IndexError, TypeError, ValueError):
        return None


def _request(
    url: str,
    body: str,
    *,
    timeout: float,
    max_retries: int,
) -> str | None:
    """POST with retry and rate-limit back-off.

    Returns the response body, or None on unrecoverable failure.
    """
    rate_hits = 0
    last_error: str | None = None

    for attempt in range(1, max_retries + 1):
        try:
            resp = http_post(
                url,
                body=body,
                headers={
                    "Content-Type": ("application/x-www-form-urlencoded"),
                },
                timeout=timeout,
            )
        except urllib.error.URLError as exc:
            last_error = str(exc)
            _LOG.debug("attempt %d URLError: %s", attempt, exc)
            continue

        if resp.status != 200:
            last_error = f"HTTP {resp.status}"
            _LOG.debug("attempt %d status %d", attempt, resp.status)
            continue

        if _RATE_LIMIT_MARKER in resp.body:
            rate_hits += 1
            delay = _RATE_LIMIT_DELAY * rate_hits
            _LOG.warning(
                "rate-limited, backing off %.1fs (hit #%d)",
                delay,
                rate_hits,
            )
            time.sleep(delay)
            continue

        return resp.body

    _LOG.error("all %d attempts failed: %s", max_retries, last_error)
    return None


class GoogleScraperProvider:
    """Fetches reviews from Google Play via web scraping.

    Uses Google's internal batchexecute RPC (``oCPfdb``).
    Supports pagination, retry with back-off, and
    ``hl``/``gl`` locale params.
    """

    def __init__(
        self,
        count: int = _MAX_BATCH_SIZE,
        timeout: float = 30.0,
        max_retries: int = 3,
        max_reviews: int = 500,
        lang: str = "en",
        country: str = "us",
    ) -> None:
        self._count = min(count, _MAX_BATCH_SIZE)
        self._timeout = timeout
        self._max_retries = max_retries
        self._max_reviews = max_reviews
        self._lang = lang
        self._country = country

    def fetch(self, app_id: str, app_input: str) -> FetchResult:
        all_reviews: list[Review] = []
        all_failures: list[FetchFailure] = []
        page_token: str | None = None

        while len(all_reviews) < self._max_reviews:
            url, body = _build_body(
                app_id,
                count=self._count,
                page_token=page_token,
                lang=self._lang,
                country=self._country,
            )

            raw = _request(
                url,
                body,
                timeout=self._timeout,
                max_retries=self._max_retries,
            )
            if raw is None:
                all_failures.append(
                    FetchFailure.create(
                        app_id,
                        _PROVIDER,
                        "all retries exhausted",
                    )
                )
                break

            entries, next_token = _parse_response(raw)
            for entry in entries:
                review = _to_review(entry, app_id, app_input)
                if review:
                    all_reviews.append(review)

            if not entries or not next_token:
                break
            page_token = next_token

        return FetchResult(reviews=all_reviews, failures=all_failures)
