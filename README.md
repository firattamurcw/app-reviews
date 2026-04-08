<div align="center">

# App Reviews

**Fetch app reviews from the Apple App Store and Google Play Store with a single Python package.**

[![PyPI](https://img.shields.io/pypi/v/app-reviews.svg)](https://pypi.org/project/app-reviews)
[![Python](https://img.shields.io/pypi/pyversions/app-reviews.svg)](https://pypi.org/project/app-reviews)
[![Downloads](https://img.shields.io/pypi/dm/app-reviews.svg)](https://pypistats.org/packages/app-reviews)
[![License](https://img.shields.io/github/license/firattamurcw/app-reviews)](LICENSE)

[![CI](https://github.com/firattamurcw/app-reviews/actions/workflows/ci.yml/badge.svg)](https://github.com/firattamurcw/app-reviews/actions/workflows/ci.yml)
[![Docs](https://github.com/firattamurcw/app-reviews/actions/workflows/docs.yml/badge.svg)](https://firattamurcw.github.io/app-reviews/)

[Documentation](https://firattamurcw.github.io/app-reviews/) · [PyPI](https://pypi.org/project/app-reviews/) · [Contributing](https://firattamurcw.github.io/app-reviews/contributing/)

</div>

---

## Why App Reviews?

Apple and Google use completely different APIs, formats, and auth methods. Getting reviews across multiple countries means juggling separate requests, rate limits, and JWT signing.

**App Reviews** handles all of this behind a single `client.fetch()` call -- no API keys required.

```python
from app_reviews import AppStoreReviews, Country

client = AppStoreReviews()
result = client.fetch("324684580", countries=[Country.US, Country.GB])

for review in result:
    print(f"[{review.country}] {review.rating}* {review.title}")
```

### Highlights

| | |
|---|---|
| **Both stores** | Apple App Store + Google Play in one package |
| **No API keys** | Works out of the box using public endpoints |
| **155 countries** | Fetch across regions in a single call |
| **Official APIs** | Optionally use App Store Connect or Google Play Developer API |
| **Interactive TUI** | Browse reviews in the terminal |
| **Export** | JSON, JSONL, CSV |
| **Minimal deps** | Just `cryptography` for JWT + stdlib `urllib` |

---

## Install

```bash
pip install app-reviews
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add app-reviews
```

---

## Quick Start

### Apple App Store

```python
from app_reviews import AppStoreReviews, Country

client = AppStoreReviews()
result = client.fetch("324684580", countries=[Country.US, Country.GB])

for review in result:
    print(f"[{review.country}] {review.rating}* {review.title}")
```

### Google Play Store

```python
from app_reviews import GooglePlayReviews, Country

client = GooglePlayReviews()
result = client.fetch("com.instagram.android", countries=[Country.US])

for review in result:
    print(f"[{review.country}] {review.rating}* {review.body[:80]}")
```

---

## Authentication (Optional)

For higher limits and more data, use the official APIs with your developer credentials.

<summary><b>Apple App Store Connect</b></summary>

Requires an [Apple Developer Program](https://developer.apple.com/programs/) membership ($99/year).

```python
from app_reviews import AppStoreReviews, AppStoreAuth, Country

auth = AppStoreAuth(
    key_id="ABC123DEF4",
    issuer_id="12345678-1234-1234-1234-123456789012",
    key_path="/path/to/AuthKey.p8",
)

client = AppStoreReviews(auth=auth)
result = client.fetch("324684580", countries=[Country.US, Country.GB])
```

<summary><b>Google Play Developer API</b></summary>

Requires a [Google Play Developer](https://play.google.com/console/) account ($25 one-time).

```python
from app_reviews import GooglePlayReviews, GooglePlayAuth, Country

auth = GooglePlayAuth(service_account_path="/path/to/service-account.json")

client = GooglePlayReviews(auth=auth)
result = client.fetch("com.instagram.android", countries=[Country.US])
```

---

## Advanced Usage

<summary><b>Retry and proxy</b></summary>

```python
from app_reviews import AppStoreReviews, RetryConfig

retry = RetryConfig(
    max_retries=5,       # default: 3
    backoff_factor=1.0,  # default: 0.5
    timeout=60.0,        # default: 30.0
    retry_on=[429, 503], # default: [500, 502, 503, 504, 429]
)

client = AppStoreReviews(retry=retry, proxy="http://proxy.example.com:8080")
result = client.fetch("324684580", countries=["us"])
```

<summary><b>Export results</b></summary>

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

<summary><b>Interactive TUI</b></summary>

Browse reviews in the terminal with the built-in TUI:

```bash
pip install app-reviews[tui]
app-reviews
```

---

## Limitations

- **Free scrapers have limits**:
    - App Store RSS: ~500 most recent reviews.
    - Google Play scraper: rate-limited and may not return all reviews.

- **No historical data**:
    - Only the most recent reviews from public endpoints

- **Official APIs require developer accounts**:
    - Apple ($99/year), Google ($25 one-time)

---

## Documentation

**[Read the full docs](https://firattamurcw.github.io/app-reviews/)** includes guides on the Python API, TUI, authentication, export formats, and architecture.

---

## Contributing

```bash
git clone https://github.com/firattamurcw/app-reviews.git
cd app-reviews
uv sync --group dev
make test
```

See the [Contributing Guide](https://firattamurcw.github.io/app-reviews/contributing/) · [Code of Conduct](CODE_OF_CONDUCT.md) · [Security Policy](SECURITY.md)

---

## License

[MIT](LICENSE)
