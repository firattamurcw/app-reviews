"""App metadata lookup utilities for Apple and Google Play stores."""

from __future__ import annotations

import contextlib
import json

from app_reviews.models.metadata import AppMetadata
from app_reviews.models.types import Store
from app_reviews.utils.http import http_get

ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup"
GOOGLE_PLAY_URL = "https://play.google.com/store/apps/details"


def _lookup_apple(app_id: str) -> AppMetadata:
    """Fetch app metadata from the iTunes Lookup API."""
    resp = http_get(ITUNES_LOOKUP_URL, params={"id": app_id}, timeout=10.0)

    if resp.status != 200:
        raise RuntimeError(f"HTTP {resp.status} from iTunes Lookup API")

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
    from html.parser import HTMLParser

    resp = http_get(
        GOOGLE_PLAY_URL,
        params={"id": app_id, "hl": "en", "gl": "us"},
        timeout=10.0,
    )

    if resp.status == 404:
        raise ValueError(f"App ID {app_id!r} not found on Google Play.")
    if resp.status != 200:
        raise RuntimeError(f"HTTP {resp.status} from Google Play")

    html = resp.body

    # Simple HTML parser to extract metadata
    class MetadataParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.name = "Unknown"
            self.developer = "Unknown"
            self.category = "Unknown"
            self.rating = 0.0
            self._in_h1 = False
            self._in_dev_link = False
            self._in_cat_link = False
            self._h1_found = False
            self._dev_found = False
            self._cat_found = False

        def handle_starttag(
            self, tag: str, attrs: list[tuple[str, str | None]]
        ) -> None:
            attr_dict = dict(attrs)
            if tag == "h1" and not self._h1_found:
                self._in_h1 = True
            elif tag == "a" and not self._dev_found:
                href = attr_dict.get("href", "")
                if href and "/store/apps/dev" in href:
                    self._in_dev_link = True
            elif tag == "a" and not self._cat_found:
                href = attr_dict.get("href", "")
                if href and "/store/apps/category/" in href:
                    self._in_cat_link = True
                    # Extract category from URL slug (links often lack text)
                    slug = href.rsplit("/", 1)[-1]
                    if slug and slug != "FAMILY":
                        self.category = slug.replace("_", " ").title()
                        self._cat_found = True
            # Rating from aria-label like "Rated 4.7 stars out of five stars"
            aria = attr_dict.get("aria-label", "")
            if aria and "Rated" in aria and not self.rating:
                import re

                m = re.search(r"Rated\s+([\d.]+)", aria)
                if m:
                    with contextlib.suppress(ValueError):
                        self.rating = float(m.group(1))

        def handle_endtag(self, tag: str) -> None:
            if tag == "h1":
                self._in_h1 = False
            if tag == "a":
                self._in_dev_link = False
                self._in_cat_link = False

        def handle_data(self, data: str) -> None:
            if self._in_h1 and not self._h1_found:
                self.name = data.strip()
                self._h1_found = True
            elif self._in_dev_link and not self._dev_found:
                self.developer = data.strip()
                self._dev_found = True
            elif self._in_cat_link and not self._cat_found:
                self.category = data.strip()
                self._cat_found = True

    parser = MetadataParser()
    parser.feed(html)

    return AppMetadata(
        app_id=app_id,
        store="googleplay",
        name=parser.name,
        developer=parser.developer,
        category=parser.category,
        price="Unknown",
        version="Unknown",
        rating=parser.rating,
        rating_count=0,
        url=f"https://play.google.com/store/apps/details?id={app_id}",
    )


def lookup_metadata(app_id: str, store: Store | None = None) -> AppMetadata:
    """Fetch app metadata, auto-detecting store if not provided."""
    if store is None:
        from app_reviews.core.inputs import detect_store

        store = detect_store(app_id)

    if store == "appstore":
        return _lookup_apple(app_id)
    return _lookup_google(app_id)
