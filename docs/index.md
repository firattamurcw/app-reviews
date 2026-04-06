# App Reviews

Fetch app reviews from the **Apple App Store** and **Google Play Store** with a single Python package.

---

## Why App Reviews?

Fetching app reviews sounds simple until you try to do it. Each store has a different API, different authentication, and different data formats. The Apple App Store uses an RSS feed (public) or the App Store Connect API (authenticated). Google Play uses an undocumented internal endpoint (public) or the Google Play Developer API (authenticated). If you want reviews from multiple countries, you have to make separate requests for each one and then deduplicate the results, because the same review often appears in multiple country feeds.

App Reviews handles all of this for you. One interface, both stores, 175+ countries, automatic deduplication.

**What makes it different:**

- **Zero-config start.** Works without any API keys or developer accounts. Just install and fetch.
- **Both stores, one API.** `AppStoreReviews` and `GooglePlayReviews` follow the same pattern. Learn one, you know both.
- **Multi-country with deduplication.** Fetch from dozens of countries in a single call. The package removes duplicate reviews automatically using a two-pass algorithm (exact ID match, then fuzzy match).
- **Optional authenticated access.** When you need more data or higher limits, plug in your App Store Connect or Google Play Developer API credentials via `AppStoreAuth` or `GooglePlayAuth`. The package auto-selects the best provider.
- **Minimal dependencies.** One runtime dependency (`cryptography` for JWT signing). All HTTP uses Python's built-in `urllib`.
- **Three interfaces.** Python API, CLI, and an interactive terminal UI.

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

Both return a `FetchResult` object containing deduplicated reviews, any failures, warnings, and timing statistics. `FetchResult` is iterable — you can loop over it directly to get `Review` objects.

---

## What You Get

- Fetches reviews from both the **Apple App Store** and **Google Play Store**
- Supports **175+ countries** in a single call with automatic deduplication
- Works **without any API keys** out of the box
- Optionally uses authenticated APIs for more data and higher limits
- Provides a **Python API**, a **CLI**, and an **interactive terminal UI**
- Exports to **table**, **JSON**, **JSONL**, and **CSV**
- Handles retries, timeouts, and proxies
- Strictly typed with mypy and tested with 75%+ coverage

---

## Limitations

Being upfront about what this package can and cannot do:

- **The free scrapers have limits.** The App Store RSS feed returns at most ~500 reviews per app (most recent only). The Google Play web scraper is rate-limited by Google and can break if Google changes their internal API.
- **No historical data.** Neither scraper gives you the complete history of all reviews ever written. You get what the public endpoints provide, which is typically the most recent reviews.
- **Authenticated APIs require developer accounts.** The official APIs give you more data, but you need an Apple Developer Program membership ($99/year) or a Google Play Developer account ($25 one-time).

For details, see [How It Works](reference/how-it-works.md).

---

## Next Steps

- [Installation](getting-started/installation.md) -- install the package
- [Quick Start](getting-started/quickstart.md) -- get your first reviews in 2 minutes
- [Python API](guide/python-api.md) -- full API reference with all parameters
- [CLI](guide/cli.md) -- command-line usage
- [Interactive TUI](guide/tui.md) -- browse reviews in your terminal
- [How It Works](reference/how-it-works.md) -- what happens under the hood
