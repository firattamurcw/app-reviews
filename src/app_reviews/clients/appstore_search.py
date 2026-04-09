"""Client for searching and looking up App Store apps."""

from __future__ import annotations

import json
import logging
from typing import Any

from app_reviews.clients.base_search import BaseSearch
from app_reviews.errors import HttpError
from app_reviews.models.country import Country
from app_reviews.models.metadata import AppMetadata
from app_reviews.utils.http import http_get

_LOG = logging.getLogger(__name__)

_ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
_ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup"


def _to_app_metadata(result: dict[str, Any]) -> AppMetadata:
    """Map an iTunes API result dict to AppMetadata."""
    return AppMetadata(
        app_id=result.get("bundleId", str(result.get("trackId", ""))),
        store="appstore",
        name=result.get("trackName", "Unknown"),
        developer=result.get("artistName", "Unknown"),
        category=result.get("primaryGenreName", "Unknown"),
        price=result.get("formattedPrice", "Unknown"),
        version=result.get("version", "Unknown"),
        rating=result.get("averageUserRating", 0.0),
        rating_count=result.get("userRatingCount", 0),
        url=result.get(
            "trackViewUrl",
            f"https://apps.apple.com/app/id{result.get('trackId', '')}",
        ),
        icon_url=result.get("artworkUrl512"),
    )


class AppStoreSearch(BaseSearch):
    """Search and lookup for App Store apps via iTunes APIs."""

    def search(
        self,
        query: str,
        *,
        country: Country = Country.US,
        limit: int = 50,
    ) -> list[AppMetadata]:
        resp = http_get(
            _ITUNES_SEARCH_URL,
            params={
                "term": query,
                "entity": "software",
                "country": str(country),
                "limit": str(limit),
            },
            timeout=self._retry.timeout,
            retry=self._retry,
            proxy=self._proxy,
        )
        if resp.status != 200:
            raise HttpError(f"HTTP {resp.status} from iTunes Search API")

        try:
            data = json.loads(resp.body)
        except json.JSONDecodeError:
            _LOG.warning("Malformed JSON from iTunes Search API")
            return []
        return [_to_app_metadata(r) for r in data.get("results", [])]

    def lookup(
        self,
        app_id: str,
        *,
        country: Country = Country.US,
    ) -> AppMetadata | None:
        resp = http_get(
            _ITUNES_LOOKUP_URL,
            params={
                "bundleId": app_id,
                "country": str(country),
            },
            timeout=self._retry.timeout,
            retry=self._retry,
            proxy=self._proxy,
        )
        if resp.status != 200:
            raise HttpError(f"HTTP {resp.status} from iTunes Lookup API")

        try:
            data = json.loads(resp.body)
        except json.JSONDecodeError:
            _LOG.warning("Malformed JSON from iTunes Lookup API")
            return None
        results = data.get("results", [])
        if not results:
            return None
        return _to_app_metadata(results[0])
