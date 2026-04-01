# App Reviews

Fetch app reviews from the **Apple App Store** and **Google Play Store** with a single Python package.

[![PyPI](https://img.shields.io/pypi/v/app-reviews.svg)](https://pypi.org/project/app-reviews)
[![Python](https://img.shields.io/pypi/pyversions/app-reviews.svg)](https://pypi.org/project/app-reviews)
[![Downloads](https://img.shields.io/pypi/dm/app-reviews.svg)](https://pypistats.org/packages/app-reviews)
[![License](https://img.shields.io/github/license/firattamurcw/app-reviews)](LICENSE)

[![CI](https://github.com/firattamurcw/app-reviews/actions/workflows/ci.yml/badge.svg)](https://github.com/firattamurcw/app-reviews/actions/workflows/ci.yml)
[![Scheduled E2E](https://github.com/firattamurcw/app-reviews/actions/workflows/scheduled_e2e_test.yml/badge.svg)](https://github.com/firattamurcw/app-reviews/actions/workflows/scheduled_e2e_test.yml)
[![Docs](https://github.com/firattamurcw/app-reviews/actions/workflows/docs.yml/badge.svg)](https://firattamurcw.github.io/app-reviews/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## Why App Reviews?

Fetching app reviews should be simple. In practice, it is not:

- Apple and Google use completely different APIs, formats, and auth methods
- Getting reviews from multiple countries means handling deduplication
- Google rate-limits aggressively, Apple requires JWT signing
- Most existing tools only support one store

**App Reviews** handles all of this behind a single `scraper.fetch()` call. It works out of the box with no API keys, and optionally supports authenticated APIs for more data.

## Install

```bash
pip install app-reviews
```

## Quick Start

```python
from app_reviews import AppStoreScraper, GooglePlayScraper

# Apple App Store – Spotify
apple = AppStoreScraper(app_id="324684580", countries=["us", "gb"])
result = apple.fetch()

for review in result.reviews:
    print(f"[{review.country}] {review.rating}★ {review.title}")

# Google Play Store – Instagram
google = GooglePlayScraper(app_id="com.instagram.android", countries=["us", "gb"])
result = google.fetch()

for review in result.reviews:
    print(f"[{review.country}] {review.rating}★ {review.body[:80]}")
```

## Features

- **Both stores** -- Apple App Store and Google Play in one package
- **No API keys required** -- works out of the box using public endpoints
- **175+ countries** -- fetch and deduplicate across regions in a single call
- **Official API support** -- optionally use App Store Connect or Google Play Developer API
- **Python API, CLI, and interactive TUI** -- use it however you prefer
- **4 export formats** -- table, JSON, JSONL, CSV
- **Minimal dependencies** -- just `cryptography` for JWT signing, stdlib `urllib` for HTTP

## Documentation

**[Read the full documentation](https://firattamurcw.github.io/app-reviews/)**

- [Installation](https://firattamurcw.github.io/app-reviews/getting-started/installation/) -- all install methods
- [Quick Start](https://firattamurcw.github.io/app-reviews/getting-started/quickstart/) -- first reviews in 2 minutes
- [Python API](https://firattamurcw.github.io/app-reviews/guide/python-api/) -- full reference with all parameters
- [CLI](https://firattamurcw.github.io/app-reviews/guide/cli/) -- command-line usage
- [Interactive TUI](https://firattamurcw.github.io/app-reviews/guide/tui/) -- browse reviews in your terminal
- [Authentication](https://firattamurcw.github.io/app-reviews/guide/authentication/) -- set up official APIs
- [How It Works](https://firattamurcw.github.io/app-reviews/reference/how-it-works/) -- providers, limitations, internals

## Contributing

```bash
git clone https://github.com/firattamurcw/app-reviews.git
cd app-reviews
uv sync --group dev
make test
```

See the [Contributing Guide](https://firattamurcw.github.io/app-reviews/contributing/) for details.

## License

[MIT](LICENSE)
