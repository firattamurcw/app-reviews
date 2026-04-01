# AppStore Reviews

The go-to Python package for App Store review extraction.

## Why AppStore Reviews

- **Multiple providers** -- fetch reviews via RSS feeds or the App Store Connect API
- **Multi-country fan-out** -- query multiple countries in one call with automatic deduplication
- **Sync and async** -- use `AppStoreScraper` or `AsyncAppStoreScraper` depending on your needs
- **CLI included** -- export reviews as table, JSON, JSONL, or CSV from the command line
- **Structured results** -- Pydantic models with stats, failures, and warnings

## Installation

```bash
pip install appstore-reviews
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add appstore-reviews
```

## Quick example

```python
from appstore_reviews import AppStoreScraper

scraper = AppStoreScraper(app_id="123456789", countries=["us", "gb"])
result = scraper.fetch()

for review in result.reviews:
    print(f"[{review.country}] {review.rating}* {review.title}")
```

## Requirements

- Python 3.11+
