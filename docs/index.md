# App Reviews

Fetch app reviews from the **Apple App Store** and **Google Play Store** with a single Python package.

---

## Why App Reviews?

Each store has a different API, authentication and data format. This package puts
both behind one interface.

- **No credentials to start.** The default sources are public endpoints.
- **Both stores, one API.** `AppStoreReviews` and `GooglePlayReviews` follow the same pattern.
- **Multi-country fetch.** Fetch from dozens of countries in a single call.
- **Optional authenticated access.** Plug in App Store Connect or Google Play Developer API credentials for more data and higher limits.
- **Minimal dependencies.** `cryptography` for JWT signing and `httpx` for transport.
- **Real async.** Every entry point has an async twin (`afetch`, `aiter_reviews`, `aiter_pages`, `asearch`, ...) using `httpx.AsyncClient`, not a thread-pool wrapper. See [Async](guide/async.md).
- **Streams or buffers, your choice.** `fetch()` sorts and filters the whole corpus; `iter_reviews()` yields reviews as they arrive so a 155-storefront walk never has to fit in memory. See [Paging and cursors](guide/paging.md).
- **Pooled connections.** Each client holds one `httpx` connection pool, so a multi-page walk costs one TLS handshake, not one per page.
- **Retries, timeouts and proxies.** Configured per client through `RetryConfig` and `proxy=`.
- **JSON-ready output.** `to_dicts()` returns plain dicts for `json` or `csv`; the package ships no exporters.
- **Typed and tested.** Strict mypy, and coverage held at 85% or above.

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

# No countries= here: Connect is a global API. One request covers every
# territory, and each review carries its own.
result = client.fetch("123456789")

for review in result:
    print(f"[{review.country}] {review.rating}* {review.title}")
```

**Google Play Store:**

```python
from app_reviews import GooglePlayReviews, Country

client = GooglePlayReviews()

# Play has one global review corpus, so there is no country to fan out over.
result = client.fetch("com.example.app")

for review in result:
    print(f"[{review.country}] {review.rating}* {review.body[:80]}")
```

Both return a `FetchResult` containing reviews and any per-country errors. `FetchResult` is iterable: loop over it directly to get `Review` objects.

---

## Limitations

- **How far back you can reach differs by source**
    - `appstore_scraper`: ~500 most recent reviews per storefront
    - `googleplay_official`: **the last 7 days only**; full history needs a Play Console CSV export, which this package does not read
    - `appstore_official`, `googleplay_scraper`: unbounded
- **The Google Play web endpoint is undocumented** and rate-limited, and can change without notice
- **Authenticated APIs require developer accounts**
    - Apple Developer Program: $99/year
    - Google Play Developer account: $25 one-time

Per-source detail: [How the sources differ](reference/capabilities.md).

---

## Next Steps

- [Installation](getting-started/installation.md): install the package
- [Quick Start](getting-started/quickstart.md): your first fetch, both stores
- [Python API](guide/python-api.md): full API reference
- [How It Works](reference/how-it-works.md): what the fetch pipeline does
