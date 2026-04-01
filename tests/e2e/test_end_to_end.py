"""End-to-end tests covering the full fetch-to-export flow."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
from click.testing import CliRunner

from appstore_reviews import AppStoreScraper, AsyncAppStoreScraper, FetchResult, Review
from appstore_reviews.cli import main
from appstore_reviews.exporters.csv import export_csv
from appstore_reviews.exporters.json import export_json
from appstore_reviews.exporters.jsonl import export_jsonl


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


def _rss_handler(request: httpx.Request) -> httpx.Response:
    """Return different reviews per country."""
    url = str(request.url)
    if "/us/" in url:
        entries = [_make_entry("us-1"), _make_entry("us-2", "4")]
    elif "/gb/" in url:
        entries = [_make_entry("gb-1", "3")]
    else:
        entries = []
    body = {"feed": {"entry": entries}} if entries else {"feed": {}}
    return httpx.Response(200, json=body)


class TestEndToEndSync:
    def test_scraper_fetch_and_export_json(self) -> None:
        """Full flow: scraper → fetch → JSON export."""
        client = httpx.Client(transport=httpx.MockTransport(_rss_handler))
        scraper = AppStoreScraper(app_id="99999", countries=["us", "gb"])
        result = scraper.fetch(sync_client=client)

        assert isinstance(result, FetchResult)
        assert len(result.reviews) == 3
        assert result.stats.total_reviews == 3
        assert all(isinstance(r, Review) for r in result.reviews)

        # Export to JSON
        text = export_json(result.reviews)
        parsed = json.loads(text)
        assert len(parsed) == 3

    def test_scraper_fetch_and_export_jsonl(self) -> None:
        client = httpx.Client(transport=httpx.MockTransport(_rss_handler))
        scraper = AppStoreScraper(app_id="99999", countries=["us"])
        result = scraper.fetch(sync_client=client)

        text = export_jsonl(result.reviews)
        lines = [line for line in text.strip().split("\n") if line]
        assert len(lines) == 2
        for line in lines:
            obj = json.loads(line)
            assert obj["app_id"] == "99999"

    def test_scraper_fetch_and_export_csv(self) -> None:
        client = httpx.Client(transport=httpx.MockTransport(_rss_handler))
        scraper = AppStoreScraper(app_id="99999", countries=["us"])
        result = scraper.fetch(sync_client=client)

        text = export_csv(result.reviews)
        assert "review_id" in text
        assert "99999" in text

    def test_partial_failure_flow(self) -> None:
        """Partial failures don't crash the pipeline."""

        def handler(request: httpx.Request) -> httpx.Response:
            if "/gb/" in str(request.url):
                return httpx.Response(500, text="error")
            return httpx.Response(200, json={"feed": {"entry": [_make_entry("ok-1")]}})

        client = httpx.Client(transport=httpx.MockTransport(handler))
        scraper = AppStoreScraper(app_id="99999", countries=["us", "gb"])
        result = scraper.fetch(sync_client=client)

        assert len(result.reviews) == 1
        assert len(result.failures) == 1

        # Export still works with partial data
        text = export_json(result.reviews)
        assert json.loads(text)


class TestEndToEndAsync:
    async def test_async_scraper_fetch(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return _rss_handler(request)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        scraper = AsyncAppStoreScraper(app_id="99999", countries=["us", "gb"])
        result = await scraper.fetch(async_client=client)

        assert len(result.reviews) == 3
        assert result.stats.total_reviews == 3


class TestEndToEndCli:
    @patch("appstore_reviews.cli.execute_fetch")
    def test_cli_fetch_produces_output(self, mock_fetch: MagicMock) -> None:
        """CLI fetch command produces JSONL output to stdout."""
        from datetime import UTC, datetime

        reviews = [
            Review(
                review_id="rss-1",
                canonical_key="99999-1",
                app_id="99999",
                app_input="99999",
                country="us",
                rating=5,
                title="CLI test",
                body="Works great",
                author_name="Tester",
                created_at=datetime(2024, 6, 1, tzinfo=UTC),
                source="rss",
                source_review_id="1",
                fetched_at=datetime(2024, 6, 2, tzinfo=UTC),
            )
        ]
        from appstore_reviews.models.result import FetchStats

        mock_fetch.return_value = FetchResult(
            reviews=reviews,
            stats=FetchStats(total_reviews=1, total_countries=1),
        )

        runner = CliRunner()
        result = runner.invoke(
            main, ["fetch", "--app-id", "99999", "--format", "jsonl"]
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output.strip())
        assert parsed["app_id"] == "99999"
