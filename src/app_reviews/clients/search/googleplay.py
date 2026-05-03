"""Client for searching and looking up Google Play apps."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app_reviews.clients.search.base import BaseSearch
from app_reviews.errors import HttpError
from app_reviews.models.country import Country
from app_reviews.models.metadata import AppMetadata
from app_reviews.utils.http import http_get

_LOG = logging.getLogger(__name__)

_PLAY_SEARCH_URL = "https://play.google.com/store/search"
_PLAY_DETAIL_URL = "https://play.google.com/store/apps/details"

# Browser UA required — Google rejects non-browser requests
_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# Regex to extract individual AF_initDataCallback script blocks
_RE_SCRIPT = re.compile(r"AF_initDataCallback[\s\S]*?</script")
# Regex to extract the dataset key (e.g., "ds:4")
_RE_KEY = re.compile(r"(ds:\d+)'")
# Regex to locate the data value start (after "data:" and optional whitespace)
_RE_DATA_VALUE = re.compile(r"\bdata:\s*")


def _nested_lookup(source: Any, path: list[int]) -> Any:
    """Traverse nested lists by index path, returning None on any failure."""
    try:
        node = source
        for idx in path:
            node = node[idx]
        return node
    except (IndexError, TypeError, KeyError):
        return None


def _extract_datasets(html: str) -> dict[str, Any]:
    """Parse AF_initDataCallback script blocks into a {ds_key: data} dict.

    Google Play pages embed structured data in script blocks like::

        AF_initDataCallback({key: 'ds:4', ..., data:[...], sideChannel: {}});

    We extract each block, identify its ``ds:X`` key, and JSON-decode the
    data value using :meth:`json.JSONDecoder.raw_decode`.
    """
    datasets: dict[str, Any] = {}
    decoder = json.JSONDecoder()
    for match in _RE_SCRIPT.finditer(html):
        block = match.group(0)
        key_match = _RE_KEY.search(block)
        if not key_match:
            continue
        data_match = _RE_DATA_VALUE.search(block)
        if not data_match:
            continue
        try:
            value, _ = decoder.raw_decode(block, data_match.end())
        except (json.JSONDecodeError, ValueError):
            continue
        datasets[key_match.group(1)] = value
    return datasets


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_price(raw: Any) -> str:
    """Format a microcurrency price value."""
    if raw is None or raw == 0:
        return "Free"
    try:
        return f"${float(raw) / 1_000_000:.2f}"
    except (TypeError, ValueError):
        return "Unknown"


# ---------------------------------------------------------------------------
# Search result parsing
# ---------------------------------------------------------------------------


def _search_entry_to_metadata(entry: Any) -> AppMetadata | None:
    """Parse a regular search result entry.

    Field paths (relative to *entry*):

    ======== ============
    Field    Path
    ======== ============
    appId    [0][0][0]
    name     [0][3]
    developer [0][14]
    rating   [0][4][1]
    icon     [0][1][3][2]
    genre    [0][5]
    price    [0][8][1][0][0]
    ======== ============
    """
    app_data = _nested_lookup(entry, [0])
    if not isinstance(app_data, list):
        return None

    app_id = _nested_lookup(app_data, [0, 0])
    if not isinstance(app_id, str) or not app_id:
        return None

    return AppMetadata(
        app_id=app_id,
        store="googleplay",
        name=_nested_lookup(app_data, [3]) or "Unknown",
        developer=_nested_lookup(app_data, [14]) or "Unknown",
        category=_nested_lookup(app_data, [5]) or "Unknown",
        price=_format_price(_nested_lookup(app_data, [8, 1, 0, 0])),
        version="Unknown",
        rating=float(_nested_lookup(app_data, [4, 1]) or 0),
        rating_count=0,
        url=f"https://play.google.com/store/apps/details?id={app_id}",
        icon_url=_nested_lookup(app_data, [1, 3, 2]),
    )


def _top_result_to_metadata(entry: Any) -> AppMetadata | None:
    """Parse a featured/top search result (different layout).

    Field paths (relative to *entry*):

    ======== ======================
    Field    Path
    ======== ======================
    appId    [11][0][0]
    name     [2][0][0]
    developer [2][68][0]
    rating   [2][51][0][1]
    icon     [2][95][0][3][2]
    genre    [2][79][0][0][0]
    price    [2][57][0][0][0][0][1][0][0]
    ======== ======================
    """
    app_id = _nested_lookup(entry, [11, 0, 0])
    if not isinstance(app_id, str) or not app_id:
        return None

    detail = _nested_lookup(entry, [2])
    if not isinstance(detail, list):
        return None

    return AppMetadata(
        app_id=app_id,
        store="googleplay",
        name=_nested_lookup(detail, [0, 0]) or "Unknown",
        developer=_nested_lookup(detail, [68, 0]) or "Unknown",
        category=_nested_lookup(detail, [79, 0, 0, 0]) or "Unknown",
        price=_format_price(_nested_lookup(detail, [57, 0, 0, 0, 0, 1, 0, 0])),
        version="Unknown",
        rating=float(_nested_lookup(detail, [51, 0, 1]) or 0),
        rating_count=0,
        url=f"https://play.google.com/store/apps/details?id={app_id}",
        icon_url=_nested_lookup(detail, [95, 0, 3, 2]),
    )


def _parse_search_html(html: str) -> list[AppMetadata]:
    """Extract app search results from Google Play search page HTML."""
    datasets = _extract_datasets(html)
    if not datasets:
        _LOG.warning("Google Play search: no AF_initDataCallback data found")
        return []

    results: list[AppMetadata] = []
    seen: set[str] = set()

    # Search data lives in ds:4; try it first, then fall back to others.
    for key in sorted(datasets, key=lambda k: (k != "ds:4", k)):
        sections = _nested_lookup(datasets[key], [0, 1])
        if not isinstance(sections, list):
            continue

        for section in sections:
            if not isinstance(section, list):
                continue

            # Featured/top result at section[23][16]
            top = _nested_lookup(section, [23, 16])
            if top is not None:
                meta = _top_result_to_metadata(top)
                if meta and meta.app_id not in seen:
                    seen.add(meta.app_id)
                    results.append(meta)

            # Regular results: section[22] = list of groups
            groups = _nested_lookup(section, [22])
            if not isinstance(groups, list):
                continue
            for group in groups:
                if not isinstance(group, list):
                    continue
                for entry in group:
                    meta = _search_entry_to_metadata(entry)
                    if meta and meta.app_id not in seen:
                        seen.add(meta.app_id)
                        results.append(meta)

        if results:
            return results

    _LOG.warning("Google Play search: no app data found in response")
    return []


# ---------------------------------------------------------------------------
# App detail parsing
# ---------------------------------------------------------------------------


def _parse_detail_html(app_id: str, html: str) -> AppMetadata:
    """Parse a Google Play app detail page into AppMetadata.

    Detail data is in ``ds:5`` at path ``[1][2]``:

    ============ =====================
    Field        Path (relative to base)
    ============ =====================
    name         [0][0]
    developer    [68][0]
    genre        [79][0][0][0]
    rating       [51][0][1]
    rating_count [51][2][1]
    price        [57][0][0][0][0][1][0][0]
    version      [140][0][0][0]
    icon         [95][0][3][2]
    ============ =====================
    """
    datasets = _extract_datasets(html)
    url = f"https://play.google.com/store/apps/details?id={app_id}"

    # Detail data is typically in ds:5; try it first, then others.
    for key in sorted(datasets, key=lambda k: (k != "ds:5", k)):
        base = _nested_lookup(datasets[key], [1, 2])
        if not isinstance(base, list):
            continue

        # Verify this looks like a detail dataset
        name = _nested_lookup(base, [0, 0])
        if not isinstance(name, str):
            continue

        score = _nested_lookup(base, [51, 0, 1])
        rating_raw = _nested_lookup(base, [51, 2, 1])

        return AppMetadata(
            app_id=app_id,
            store="googleplay",
            name=name,
            developer=_nested_lookup(base, [68, 0]) or "Unknown",
            category=_nested_lookup(base, [79, 0, 0, 0]) or "Unknown",
            price=_format_price(_nested_lookup(base, [57, 0, 0, 0, 0, 1, 0, 0])),
            version=_nested_lookup(base, [140, 0, 0, 0]) or "Varies with device",
            rating=float(score) if score is not None else 0.0,
            rating_count=int(rating_raw) if rating_raw is not None else 0,
            url=url,
            icon_url=_nested_lookup(base, [95, 0, 3, 2]),
        )

    _LOG.warning("Google Play: no detail data found for %s", app_id)
    return AppMetadata(
        app_id=app_id,
        store="googleplay",
        name="Unknown",
        developer="Unknown",
        category="Unknown",
        price="Unknown",
        version="Unknown",
        rating=0.0,
        rating_count=0,
        url=url,
    )


# ---------------------------------------------------------------------------
# Public client
# ---------------------------------------------------------------------------


class GooglePlaySearch(BaseSearch):
    """Search and lookup for Google Play apps via scraping."""

    def search(
        self,
        query: str,
        *,
        country: Country = Country.US,
        limit: int = 50,
    ) -> list[AppMetadata]:
        resp = http_get(
            _PLAY_SEARCH_URL,
            params={"q": query, "c": "apps", "hl": "en", "gl": str(country)},
            headers={"User-Agent": _BROWSER_UA},
            timeout=self._retry.timeout,
            retry=self._retry,
            proxy=self._proxy,
        )
        if resp.status != 200:
            raise HttpError(f"HTTP {resp.status} from Google Play search")

        return _parse_search_html(resp.body)[:limit]

    def lookup(
        self,
        app_id: str,
        *,
        country: Country = Country.US,
    ) -> AppMetadata | None:
        resp = http_get(
            _PLAY_DETAIL_URL,
            params={"id": app_id, "hl": "en", "gl": str(country)},
            timeout=self._retry.timeout,
            retry=self._retry,
            proxy=self._proxy,
        )
        if resp.status == 404:
            return None
        if resp.status != 200:
            raise HttpError(f"HTTP {resp.status} from Google Play")

        return _parse_detail_html(app_id, resp.body)
