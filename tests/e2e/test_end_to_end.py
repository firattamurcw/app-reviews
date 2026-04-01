"""End-to-end tests covering the full fetch-to-export flow."""

import json
from typing import Any
from unittest.mock import patch

from app_reviews import AppStoreScraper, FetchResult, Review
from app_reviews.exporters.csv import export_csv
from app_reviews.exporters.json import export_json
from app_reviews.exporters.jsonl import export_jsonl
from app_reviews.utils.http import HttpResponse


def _make_entry(review_id: str, rating: str = "5") -> dict[str, Any]:
    return {
        "id": {"label": review_id},
        "im:rating": {"label": rating},
        "title": {"label": f"Review {review_id}"},
        "content": {"label": f"Body for {review_id}"},
        "author": {"name": {"label": f"Author{review_id}"}},
        "im:version": {"label": "2.0"},
        "updated": {"label": "2024-06-01T12:00:00-07:00"},
    }


def _rss_response(url: str, **kwargs: Any) -> HttpResponse:
    """Return different reviews per country."""
    if "/us/" in url:
        entries = [_make_entry("us-1"), _make_entry("us-2", "4")]
    elif "/gb/" in url:
        entries = [_make_entry("gb-1", "3")]
    else:
        entries = []
    body = {"feed": {"entry": entries}} if entries else {"feed": {}}
    return HttpResponse(status=200, body=json.dumps(body))


class TestEndToEndSync:
    @patch("app_reviews.providers.appstore.rss.http_get")
    def test_scraper_fetch_and_export_json(self, mock_get: Any) -> None:
        """Full flow: scraper -> fetch -> JSON export."""
        mock_get.side_effect = _rss_response

        scraper = AppStoreScraper(app_id="99999", countries=["us", "gb"])
        result = scraper.fetch()

        assert isinstance(result, FetchResult)
        assert len(result.reviews) == 3
        assert result.stats.total_reviews == 3
        assert all(isinstance(r, Review) for r in result.reviews)

        text = export_json(result.reviews)
        parsed = json.loads(text)
        assert len(parsed) == 3

    @patch("app_reviews.providers.appstore.rss.http_get")
    def test_scraper_fetch_and_export_jsonl(self, mock_get: Any) -> None:
        mock_get.side_effect = _rss_response

        scraper = AppStoreScraper(app_id="99999", countries=["us"])
        result = scraper.fetch()

        text = export_jsonl(result.reviews)
        lines = [line for line in text.strip().split("\n") if line]
        assert len(lines) == 2
        for line in lines:
            obj = json.loads(line)
            assert obj["app_id"] == "99999"

    @patch("app_reviews.providers.appstore.rss.http_get")
    def test_scraper_fetch_and_export_csv(self, mock_get: Any) -> None:
        mock_get.side_effect = _rss_response

        scraper = AppStoreScraper(app_id="99999", countries=["us"])
        result = scraper.fetch()

        text = export_csv(result.reviews)
        assert "review_id" in text
        assert "99999" in text

    @patch("app_reviews.providers.appstore.rss.http_get")
    def test_partial_failure_flow(self, mock_get: Any) -> None:
        """Partial failures don't crash the pipeline."""

        def handler(url: str, **kwargs: Any) -> HttpResponse:
            if "/gb/" in url:
                return HttpResponse(status=500, body="error")
            body = {"feed": {"entry": [_make_entry("ok-1")]}}
            return HttpResponse(status=200, body=json.dumps(body))

        mock_get.side_effect = handler

        scraper = AppStoreScraper(app_id="99999", countries=["us", "gb"])
        result = scraper.fetch()

        assert len(result.reviews) == 1
        assert len(result.failures) == 1

        text = export_json(result.reviews)
        assert json.loads(text)
