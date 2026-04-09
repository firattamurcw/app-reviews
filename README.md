<div align="center">

# App Reviews

**Fetch reviews, search apps, and look up metadata from the Apple App Store and Google Play Store.**

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

Apple and Google use completely different APIs, formats, and auth methods. **App Reviews** handles all of this behind a simple Python API -- no API keys required.

```python
from app_reviews import AppStoreSearch, GooglePlayReviews, Country

# Search for apps
results = AppStoreSearch().search("whatsapp", country=Country.US, limit=5)
print(results[0].name, results[0].icon_url)

# Fetch reviews
reviews = GooglePlayReviews().fetch("com.whatsapp", countries=[Country.US])
for review in reviews:
    print(f"{review.rating}* {review.body[:80]}")
```

### Highlights

| | |
|---|---|
| **Both stores** | Apple App Store + Google Play in one package |
| **Search & lookup** | Find apps by keyword, look up metadata by ID |
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
result: FetchResult = client.fetch("com.instagram.android", countries=[Country.US])

for review in result:
    print(f"[{review.country}] {review.rating}* {review.body[:80]}")
```

### Review

`fetch()` returns a `FetchResult` containing `Review` objects:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique review identifier |
| `store` | `Store` | `"appstore"` or `"googleplay"` |
| `app_id` | `str` | App Store ID or package name |
| `country` | `str` | Two-letter country code |
| `rating` | `int` | Star rating (1 -- 5) |
| `title` | `str` | Review title (may be empty for Google Play) |
| `body` | `str` | Review text |
| `author_name` | `str` | Reviewer display name |
| `app_version` | `str \| None` | App version at time of review |
| `created_at` | `datetime` | When the review was posted |
| `updated_at` | `datetime \| None` | When the review was last edited |
| `is_edited` | `bool` | Whether the review was edited |
| `source` | `Source` | Provider (e.g. `"appstore_scraper"`, `"googleplay_official"`) |
| `language` | `str \| None` | Review language code |
| `fetched_at` | `datetime \| None` | When the review was fetched |

---

## Search & Lookup

Find apps by keyword and look up app metadata -- no authentication required.

### Search

```python
from app_reviews import AppStoreSearch, GooglePlaySearch, Country, AppMetadata

# App Store -- returns list[AppMetadata]
results: list[AppMetadata] = AppStoreSearch().search("fitness tracker", country=Country.US, limit=10)
for app in results:
    print(f"{app.name} by {app.developer} ({app.rating}*)")

# Google Play -- returns list[AppMetadata]
results: list[AppMetadata] = GooglePlaySearch().search("fitness tracker", country=Country.US, limit=10)
for app in results:
    print(f"{app.name} by {app.developer}")
```

### Lookup

```python
# Look up by bundle ID (App Store) or package name (Google Play)
# Returns AppMetadata | None
app = AppStoreSearch().lookup("com.burbn.instagram")
if app:
    print(f"{app.name} - {app.icon_url}")

app = GooglePlaySearch().lookup("com.whatsapp")
if app:
    print(f"{app.name} - {app.rating}*")
```

### AppMetadata

Both `search()` and `lookup()` return `AppMetadata` objects:

| Field | Type | Description |
|-------|------|-------------|
| `app_id` | `str` | Bundle ID (App Store) or package name (Google Play) |
| `name` | `str` | App display name |
| `developer` | `str` | Developer or publisher name |
| `category` | `str` | Primary category (e.g. "Social Networking") |
| `price` | `str` | Formatted price (e.g. "Free", "$4.99") |
| `version` | `str` | Current version string |
| `rating` | `float` | Average star rating (0.0 -- 5.0) |
| `rating_count` | `int` | Total number of ratings |
| `url` | `str` | Store page URL |
| `icon_url` | `str \| None` | App icon image URL |

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

## Acknowledgements

The Google Play scraping logic (parsing `AF_initDataCallback` datasets, field index paths) is based on the work done in [google-play-scraper](https://github.com/JoMingyu/google-play-scraper) by JoMingyu. We re-implemented it on top of our own HTTP layer to support retries and proxies, but the data-structure knowledge originates from that project.

---

## License

[MIT](LICENSE)
