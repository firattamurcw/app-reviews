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

**App Reviews** handles all of this behind a single `client.fetch()` call. It works out of the box with no API keys, and optionally supports authenticated APIs for more data.

## Install

```bash
pip install app-reviews
```

## Quick Start

### No authentication (public endpoints)

```python
from app_reviews import AppStoreReviews, Country

client = AppStoreReviews()
result = client.fetch("324684580", countries=[Country.US, Country.GB])

for review in result:
    print(f"[{review.country}] {review.rating}★ {review.title}")
```

```python
from app_reviews import GooglePlayReviews, Country

client = GooglePlayReviews()
result = client.fetch("com.instagram.android", countries=[Country.US])

for review in result:
    print(f"[{review.country}] {review.rating}★ {review.body[:80]}")
```

### With authentication (official APIs)

```python
from app_reviews import AppStoreReviews, AppStoreAuth, Country

auth = AppStoreAuth(
    key_id="ABC123DEF4",
    issuer_id="12345678-1234-1234-1234-123456789012",
    key_path="/path/to/AuthKey.p8",
)

client = AppStoreReviews(auth=auth)
spotify = client.fetch("324684580", countries=[Country.US, Country.GB])
instagram = client.fetch("389801252", countries=[Country.US])
```

```python
from app_reviews import GooglePlayReviews, GooglePlayAuth, Country

auth = GooglePlayAuth(service_account_path="/path/to/service-account.json")

client = GooglePlayReviews(auth=auth)
result = client.fetch("com.instagram.android", countries=[Country.US])
```

### Retry and proxy

```python
from app_reviews import AppStoreReviews, RetryConfig

retry = RetryConfig(
    max_retries=5,       # default: 3
    backoff_factor=1.0,  # wait 1s, 2s, 4s, ... between retries (default: 0.5)
    timeout=60.0,        # per-request timeout in seconds (default: 30.0)
    retry_on=[429, 503], # HTTP status codes to retry on (default: [429, 503])
)

client = AppStoreReviews(retry=retry, proxy="http://proxy.example.com:8080")
result = client.fetch("324684580", countries=["us"])
```

### Export results

```python
from app_reviews import GooglePlayReviews
from app_reviews.exporters.json import export_json
from app_reviews.exporters.csv import export_csv
from app_reviews.exporters.jsonl import export_jsonl

client = GooglePlayReviews()
result = client.fetch("com.instagram.android")

export_json(result.reviews)   # JSON array string
export_csv(result.reviews)    # CSV string with headers
export_jsonl(result.reviews)  # one JSON object per line
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

## Community

- **[Code of Conduct](CODE_OF_CONDUCT.md)** -- our standards for participation
- **[Security Policy](SECURITY.md)** -- how to report vulnerabilities
- **[Contributing](https://firattamurcw.github.io/app-reviews/contributing/)** -- how to submit changes

## License

[MIT](LICENSE)
