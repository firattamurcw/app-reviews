# appstore-reviews

The go-to Python package for App Store review extraction.

[![CI](https://github.com/firattamur/appstore-reviews/actions/workflows/ci.yml/badge.svg)](https://github.com/firattamur/appstore-reviews/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/appstore-reviews)](https://pypi.org/project/appstore-reviews/)
[![Python](https://img.shields.io/pypi/pyversions/appstore-reviews)](https://pypi.org/project/appstore-reviews/)
[![License](https://img.shields.io/github/license/firattamur/appstore-reviews)](LICENSE)

## Features

- Fetch reviews via RSS feeds or the App Store Connect API
- Multi-country fan-out with automatic deduplication
- Sync and async Python APIs
- CLI with JSON, JSONL, and CSV export
- Smart provider selection and retry handling

## Installation

```bash
pip install appstore-reviews
```

## Usage

### Python

```python
from appstore_reviews import AppStoreScraper

scraper = AppStoreScraper(
    app_id="123456789",
    countries=["us", "gb", "de"],
)

result = scraper.fetch()

for review in result.reviews:
    print(f"[{review.country}] {review.rating}* {review.title}")
```

### Async

```python
from appstore_reviews import AsyncAppStoreScraper

scraper = AsyncAppStoreScraper(app_id="123456789")
result = await scraper.fetch()
```

### CLI

```bash
appstore-reviews fetch --app-id 123456789 --country us
```

## Documentation

[https://firattamur.github.io/appstore-reviews](https://firattamur.github.io/appstore-reviews)

## License

[MIT](LICENSE)
