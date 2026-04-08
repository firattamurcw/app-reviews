"""App metadata lookup utilities for Apple and Google Play stores."""

from __future__ import annotations

import contextlib
import json
import re

from app_reviews.errors import HttpError
from app_reviews.models.metadata import AppMetadata
from app_reviews.models.types import Store
from app_reviews.utils.http import http_get

ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup"
GOOGLE_PLAY_URL = "https://play.google.com/store/apps/details"

_RE_H1 = re.compile(r"<h1[^>]*>([^<]+)</h1>", re.IGNORECASE)
_RE_DEV_LINK = re.compile(r'<a[^>]*href="[^"]*/store/apps/dev[^"]*"[^>]*>([^<]+)</a>')
_RE_CAT_LINK = re.compile(r'<a[^>]*href="[^"]*/store/apps/category/([^"]+)"')
_RE_RATING = re.compile(r'aria-label="[^"]*Rated\s+([\d.]+)')


def _parse_google_play_html(app_id: str, html: str) -> AppMetadata:
    """Parse a Google Play store page into an AppMetadata object."""
    name = m.group(1).strip() if (m := _RE_H1.search(html)) else "Unknown"
    developer = m.group(1).strip() if (m := _RE_DEV_LINK.search(html)) else "Unknown"

    category = "Unknown"
    if m := _RE_CAT_LINK.search(html):
        slug = m.group(1).rsplit("/", 1)[-1]
        if slug and slug != "FAMILY":
            category = slug.replace("_", " ").title()

    rating = 0.0
    if m := _RE_RATING.search(html):
        with contextlib.suppress(ValueError):
            rating = float(m.group(1))

    return AppMetadata(
        app_id=app_id,
        store="googleplay",
        name=name,
        developer=developer,
        category=category,
        price="Unknown",
        version="Unknown",
        rating=rating,
        rating_count=0,
        url=f"https://play.google.com/store/apps/details?id={app_id}",
    )


def _lookup_apple(app_id: str) -> AppMetadata:
    """Fetch app metadata from the iTunes Lookup API."""
    resp = http_get(ITUNES_LOOKUP_URL, params={"id": app_id}, timeout=10.0)

    if resp.status != 200:
        raise HttpError(f"HTTP {resp.status} from iTunes Lookup API")

    data = json.loads(resp.body)

    if data.get("resultCount", 0) == 0:
        raise ValueError(f"App ID {app_id!r} not found on the App Store.")

    result = data["results"][0]
    return AppMetadata(
        app_id=app_id,
        store="appstore",
        name=result.get("trackName", "Unknown"),
        developer=result.get("artistName", "Unknown"),
        category=result.get("primaryGenreName", "Unknown"),
        price=result.get("formattedPrice", "Unknown"),
        version=result.get("version", "Unknown"),
        rating=result.get("averageUserRating", 0.0),
        rating_count=result.get("userRatingCount", 0),
        url=result.get("trackViewUrl", f"https://apps.apple.com/app/id{app_id}"),
    )


def _lookup_google(app_id: str) -> AppMetadata:
    """Fetch app metadata from the Google Play store page."""
    resp = http_get(
        GOOGLE_PLAY_URL,
        params={"id": app_id, "hl": "en", "gl": "us"},
        timeout=10.0,
    )

    if resp.status == 404:
        raise ValueError(f"App ID {app_id!r} not found on Google Play.")
    if resp.status != 200:
        raise HttpError(f"HTTP {resp.status} from Google Play")

    return _parse_google_play_html(app_id, resp.body)


def lookup_metadata(app_id: str, store: Store | None = None) -> AppMetadata:
    """Fetch app metadata, auto-detecting store if not provided."""
    if store is None:
        from app_reviews.utils.parsing import detect_store

        store = detect_store(app_id)

    if store == "appstore":
        return _lookup_apple(app_id)
    return _lookup_google(app_id)
