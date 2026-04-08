# App Reviews

Fetch app reviews from the **Apple App Store** and **Google Play Store** with a single Python package.

---

## Why App Reviews?

Each store has a different API, authentication, and data format. App Reviews handles all of this for you. One interface, both stores, 155 countries.

- **Zero-config start.** Works without any API keys. Just install and fetch.
- **Both stores, one API.** `AppStoreReviews` and `GooglePlayReviews` follow the same pattern.
- **Multi-country fetch.** Fetch from dozens of countries in a single call.
- **Optional authenticated access.** Plug in App Store Connect or Google Play Developer API credentials for more data and higher limits.
- **Minimal dependencies.** One runtime dependency (`cryptography` for JWT). All HTTP uses Python's built-in `urllib`.
- **Two interfaces.** Python API and an interactive terminal UI.

---

## Quick Example

**Apple App Store:**

```python
from app_reviews import AppStoreReviews, AppStoreAuth, Country

client = AppStoreReviews(
    auth=AppStoreAuth(
        key_id="ABC123DEF4",
        issuer_id="12345678-1234-1234-1234-123456789012",
        key_path="/path/to/AuthKey.p8",
    )
)

result = client.fetch("123456789", countries=[Country.US, Country.GB, Country.DE])

for review in result:
    print(f"[{review.country}] {review.rating}* {review.title}")
```

**Google Play Store:**

```python
from app_reviews import GooglePlayReviews, Country

client = GooglePlayReviews()

result = client.fetch("com.example.app", countries=[Country.US, Country.GB])

for review in result:
    print(f"[{review.country}] {review.rating}* {review.body[:80]}")
```

Both return a `FetchResult` containing reviews and any per-country errors. `FetchResult` is iterable -- loop over it directly to get `Review` objects.

---

## What You Get

- Fetches reviews from both the **Apple App Store** and **Google Play Store**
- Supports **155 countries** in a single call
- Works **without any API keys** out of the box
- Optionally uses authenticated APIs for more data and higher limits
- Provides a **Python API** and an **interactive terminal UI**
- Exports to **JSON**, **JSONL**, and **CSV**
- Handles retries, timeouts, and proxies
- Strictly typed with mypy and tested with 75%+ coverage

---

## Limitations

- **Free scrapers have limits**
    - App Store RSS feed: ~500 most recent reviews per app
    - Google Play web scraper: rate-limited, depends on undocumented internal API
- **No historical data** -- you get what the public endpoints provide (most recent reviews only)
- **Authenticated APIs require developer accounts**
    - Apple Developer Program: $99/year
    - Google Play Developer account: $25 one-time

For details, see [How It Works](reference/how-it-works.md).

---

## Next Steps

- [Installation](getting-started/installation.md) -- install the package
- [Quick Start](getting-started/quickstart.md) -- get your first reviews in 2 minutes
- [Python API](guide/python-api.md) -- full API reference
- [Interactive TUI](guide/tui.md) -- browse reviews in your terminal
- [How It Works](reference/how-it-works.md) -- what happens under the hood
