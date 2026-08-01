<div align="center">

# App Reviews

**Fetch reviews, search apps, and look up metadata from the Apple App Store and Google Play Store.**

[![PyPI](https://img.shields.io/pypi/v/app-reviews.svg)](https://pypi.org/project/app-reviews)
[![Python](https://img.shields.io/pypi/pyversions/app-reviews.svg)](https://pypi.org/project/app-reviews)
[![Downloads](https://img.shields.io/pypi/dm/app-reviews.svg)](https://pypistats.org/packages/app-reviews)
[![License](https://img.shields.io/github/license/firattamurcw/app-reviews)](LICENSE)

[![CI](https://github.com/firattamurcw/app-reviews/actions/workflows/ci.yml/badge.svg)](https://github.com/firattamurcw/app-reviews/actions/workflows/ci.yml)
[![E2E](https://github.com/firattamurcw/app-reviews/actions/workflows/scheduled_e2e_test.yml/badge.svg)](https://github.com/firattamurcw/app-reviews/actions/workflows/scheduled_e2e_test.yml)
[![Docs](https://github.com/firattamurcw/app-reviews/actions/workflows/docs.yml/badge.svg)](https://firattamurcw.github.io/app-reviews/)

[Documentation](https://firattamurcw.github.io/app-reviews/) · [PyPI](https://pypi.org/project/app-reviews/) · [Contributing](CONTRIBUTING.md)

</div>

---

## Why App Reviews?

Apple and Google use different APIs, formats and auth. This package puts both behind one Python API, with no API keys required.

```python
from app_reviews import AppStoreSearch, GooglePlayReviews, Country

# Search for apps
results = AppStoreSearch().search("whatsapp", country=Country.US, limit=5)
print(results[0].name, results[0].icon_url)

# Fetch reviews
reviews = GooglePlayReviews().fetch("com.whatsapp")
for review in reviews:
    print(f"{review.rating}* {review.body[:80]}")
```

### Highlights

| | |
|---|---|
| **Both stores** | Apple App Store + Google Play in one package |
| **Search & lookup** | Find apps by keyword, look up metadata by ID |
| **No API keys** | The default sources are public endpoints |
| **155 countries** | Fetch across regions in a single call |
| **Official APIs** | Optionally use App Store Connect or Google Play Developer API |
| **Async** | Every entry point has a real async twin, not a thread-pool wrapper |
| **Own the loop** | `fetch_page` / `iter_pages` / `iter_reviews`: resumable cursors, streaming |
| **Typed errors** | `ErrorKind` on every failure, and per-country outcomes |
| **Pooled** | One connection per client, not one per request |
| **Minimal deps** | Just `cryptography` for JWT and `httpx` for transport |

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
from app_reviews import GooglePlayReviews

client = GooglePlayReviews()
result = client.fetch("com.instagram.android")

for review in result:
    print(f"{review.rating}* {review.body[:80]}")
```

No `countries` here on purpose: Google Play has a single global review corpus, so
`review.country` is `None` and passing a country list collapses to one request
either way. The App Store RSS feed above is the one source where storefront
genuinely partitions the results.

### Review

`fetch()` returns a `FetchResult` containing `Review` objects:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Raw identifier assigned by the source ([see below](#review-ids)) |
| `store` | `Store` | `"appstore"` or `"googleplay"` |
| `app_id` | `str` | App Store ID or package name |
| `country` | `str \| None` | Storefront queried, not the reviewer's location. `None` when the source does not report one |
| `rating` | `int` | Star rating (1-5) |
| `title` | `str \| None` | Review title. `None` for sources with no title concept (Google Play) |
| `body` | `str` | Review text |
| `author_name` | `str` | Reviewer display name |
| `app_version` | `str \| None` | App version at time of review |
| `created_at` | `datetime \| None` | When written. `None` on sources that only report a modification time |
| `updated_at` | `datetime \| None` | Last modified. `None` on sources that only report a creation time |
| `source` | `Source` | Provider (e.g. `"appstore_scraper"`, `"googleplay_official"`) |
| `language` | `str \| None` | Review language code |
| `fetched_at` | `datetime \| None` | When the review was fetched |
| `raw` | `dict \| list \| None` | The provider's own payload, passed through unchanged. A list from Play, whose endpoints send positional arrays rather than objects |

**Exactly one of `created_at` / `updated_at` is set by every source here**, and it is the timestamp
that source orders by; no store reports both. `review.dated_at` returns whichever
one is there, and `sort`, `since` and `until` all use it. App Store Connect
reports creation; the RSS feed and the Play Developer API report last-modified;
the Play web feed reports creation to millisecond precision.

Not every other source fills every field either, and a blank is permanent rather
than occasional: `app_version` is always `None` on `appstore_official`, `title` and
`country` are always `None` on both Google Play sources, and `language` is never
populated by anything. See
[what each source fills](https://firattamurcw.github.io/app-reviews/reference/models/)
before writing code against a field.

`None` means "this source does not report it", never "this review has no value",
so a `None` `country` and a `None` `title` are honest rather than an empty-string
stand-in. Every source populates `raw`, which is what makes a fetch reprocessable
later. See
[how the sources differ](https://firattamurcw.github.io/app-reviews/reference/capabilities/).
`to_dicts()` leaves it out unless you pass `include_raw=True`.

#### Review IDs

`id` is the raw identifier assigned by the source, passed through unchanged. Treat it as unique within a `(store, source)` pair rather than globally, use `source` to tell provenance apart, and key any deduplication on `(store, source, id)`.

Ids are not necessarily comparable across sources. On the App Store they definitely differ: RSS ids are numeric while Connect ids are opaque, with no mapping between them, so the same review fetched via `appstore_scraper` and `appstore_official` carries two different ids. Google Play appears to use a single identifier space for both providers.

For App Store Connect specifically, `customerReviewResponses` requires a Connect `customerReviews.id`, so an `appstore_scraper` id cannot be used to reply.

---

## Search & Lookup

Find apps by keyword and look up app metadata. No authentication required.

### Search

```python
from app_reviews import AppStoreSearch, GooglePlaySearch, Country, AppMetadata

# App Store: returns list[AppMetadata]
results: list[AppMetadata] = AppStoreSearch().search("fitness tracker", country=Country.US, limit=10)
for app in results:
    print(f"{app.name} by {app.developer} ({app.rating}*)")

# Google Play: returns list[AppMetadata]
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
| `store` | `"appstore"` \| `"googleplay"` | Which store |
| `name` | `str` | App display name |
| `developer` | `str` | Developer or publisher name |
| `category` | `str` | Primary category (e.g. "Social Networking") |
| `price` | `str` | Formatted price (e.g. "Free", "$4.99") |
| `version` | `str` | Current version. `"Varies with device"` on Google Play for an app shipping per-device variants, and for any search hit; `lookup()` returns the real one when published |
| `rating` | `float` | Average star rating (0.0-5.0) |
| `rating_count` | `int` | Total number of ratings. `0` for a regular Google Play *search* hit; use `lookup()` |
| `url` | `str` | Store page URL |
| `icon_url` | `str \| None` | App icon image URL |
| `current_version_release_date` | `datetime \| None` | When the current version shipped. Real timestamp on the App Store; midnight UTC on Google Play, which publishes only the day |
| `first_release_date` | `datetime \| None` | When the app first appeared on the store. Same precision caveat |

Both dates are `None` when the store does not publish them, and a Google Play
*search* hit never carries either; use `lookup()`.

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
result = client.fetch("com.instagram.android")  # Play is global
```

---

## Advanced Usage

<summary><b>Own the loop: the four-rung ladder</b></summary>

`fetch()` walks every page and buffers the result so it can filter and sort
across countries. Drop a rung when you want the cursor, or when the corpus is too
big to hold.

```python
from app_reviews import AppStoreReviews, Sort

client = AppStoreReviews()

# rung 1: one request. Persist next_cursor and resume later, even in
# another process.
page = client.fetch_page("324684580", country="us")
save(page.next_cursor)
page = client.fetch_page("324684580", country="us", cursor=load())

# rung 2: one country, paginated. The last page carries stopped_because.
for page in client.iter_pages("324684580", country="us", since=since):
    store(page.reviews)
    checkpoint(page.next_cursor)

# rung 3: reviews, streamed across countries, one page held at a time
for review in client.iter_reviews("324684580", countries=["us", "gb"]):
    handle(review)

# rung 4: everything, filtered and sorted
result = client.fetch("324684580", countries=["us", "gb"], sort=Sort.RATING)
```

`since` reduces requests rather than just filtering: the walk stops once a page's
oldest review predates it, on sources that guarantee newest-first ordering.

Every rung has an `a`-prefixed async twin.

<summary><b>Errors are data, or exceptions: one vocabulary</b></summary>

```python
result = client.fetch("324684580", countries=["us", "gb"])

for outcome in result.outcomes:
    # "exhausted" means no more data. "limit"/"since"/"cycle"/"stalled"/
    # "max_pages"/"error" all mean there may be more
    print(outcome.country, outcome.pages, outcome.reviews_fetched,
          outcome.stopped_because)

for err in result.errors:            # derived from outcomes, always in sync
    if err.kind == "rate_limited":   # auth | not_found | server | transport | parse
        back_off()
```

`fetch()` never raises on a partial failure: a country that fails still reports
its reviews, its `stopped_because == "error"`, and its `FetchError`. Search and
lookup are single requests with a single outcome, so they raise `HttpError`
instead. The class *is* the classification, so catch what you want to react to:

```python
from app_reviews import AppStoreSearch, AuthError, RateLimitError, HttpError

try:
    apps = AppStoreSearch().search("fitness tracker")
except RateLimitError as err:
    back_off(err.status)
except AuthError:
    alert_a_human()                 # never worth retrying
except HttpError as err:            # the catch-all for a failed request
    log(type(err).__name__, err.status)
```

`RateLimitError`, `NotFoundError`, `ServerError`, `TransportError` and
`ParseError` all subclass `HttpError`; `AuthError` sits beside it, because a bad
key file is an auth failure with no HTTP in it. `AppReviewsError` is the base for
everything.

<summary><b>Know which source you are talking to</b></summary>

```python
client = GooglePlayReviews()
client.source                        # "googleplay_scraper"
client.resolve_countries(["us","gb"]) # [""]: global, so one request, not two
```

The four sources differ in ways that change how you call them: only the App
Store RSS feed is per-storefront, only the Play Developer API is unordered and
capped at seven days of history, and the RSS feed tops out near 500 reviews per
storefront. All of it is in
[how the sources differ](https://firattamurcw.github.io/app-reviews/reference/capabilities/).

<summary><b>Connection pooling and concurrency</b></summary>

Each client owns one HTTP connection pool, so a multi-page walk costs one TLS
handshake rather than one per page. The sockets outlive a request, so close the
client when you are done:

```python
with AppStoreReviews() as client:          # or `async with`, plus close()/aclose()
    result = client.fetch("324684580")
```

`concurrency` bounds the cross-country fan-out; pass `1` to make it sequential
when you are rate-limiting a source yourself:

```python
result = client.fetch("324684580", countries=[...], concurrency=1)
```

To share one pool between clients, set a proxy in one place, or inject a
transport in tests, build it yourself:

```python
from app_reviews import AppStoreReviews, AppStoreSearch, HttpClient

pool = HttpClient(proxy="http://proxy.example.com:8080")
reviews, search = AppStoreReviews(http=pool), AppStoreSearch(http=pool)
```

<summary><b>Retry and proxy</b></summary>

```python
from app_reviews import AppStoreReviews, RetryConfig

retry = RetryConfig(
    max_retries=5,       # default: 3
    backoff_factor=1.0,  # default: 0.5
    timeout=60.0,        # default: 30.0
    retry_on=[429, 503], # default: [500, 502, 503, 504, 429]
    max_backoff=30.0,    # default: 60.0, ceiling on any one wait
)

# A server's `Retry-After` overrides the backoff schedule, capped at max_backoff.

client = AppStoreReviews(retry=retry, proxy="http://proxy.example.com:8080")
result = client.fetch("324684580", countries=["us"])
```

<summary><b>Serialise the results</b></summary>

`to_dicts()` returns JSON-safe plain dicts: ISO 8601 timestamps, and the
provider payload (`raw`) omitted unless you ask. The standard library handles the
rest; this package ships no exporters.

```python
import csv, json
from app_reviews import GooglePlayReviews

result = GooglePlayReviews().fetch("com.instagram.android")

json.dumps(result.to_dicts(), indent=2)                # JSON
"\n".join(json.dumps(d) for d in result.to_dicts())    # JSONL

rows = result.to_dicts()
with open("reviews.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
```

Pass `include_raw=True` to keep the provider payload, useful if you want the
fetch to stay reprocessable later.

---

## Limitations

Full reference:
[how the sources differ](https://firattamurcw.github.io/app-reviews/reference/capabilities/).

- **How far back you can reach**:
    - `appstore_scraper`: ~500 most recent per country (the RSS feed serves 10 pages).
    - `googleplay_official`: **only the last 7 days.** Google documents this;
      full history needs a Play Console CSV export, which this package does not read.
    - `appstore_official`, `googleplay_scraper`: unbounded.

- **Country is not always a real axis**:
    - Only `appstore_scraper` partitions by storefront. Google Play has one global
      review corpus, and both official APIs are global: passing more countries
      there costs nothing extra, because it collapses to a single request.

- **Replies need official ids** (not implemented here):
    - Reply APIs only accept identifiers their own list endpoint minted, so a
      scraper-sourced review is permanently non-repliable.

- **Ordering is not always guaranteed**:
    - `googleplay_official` documents none, so the `since`/`limit` early stop
      never applies to it and every fetch walks to exhaustion.

- **Scrapers are unofficial**: the Google Play web endpoint is undocumented and
  rate-limited, and can change without notice.

- **Official APIs require developer accounts**: Apple ($99/year), Google ($25 one-time).

---

## Documentation

**[Read the full docs](https://firattamurcw.github.io/app-reviews/)**: the Python API, paging and cursors, async, authentication, the models, and how the four sources differ.

---

## Contributing

```bash
git clone https://github.com/firattamurcw/app-reviews.git
cd app-reviews
uv sync --group dev
make test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) · [Security Policy](SECURITY.md)

---

## Acknowledgements

The Google Play scraping logic (parsing `AF_initDataCallback` datasets, field index paths) is based on the work done in [google-play-scraper](https://github.com/JoMingyu/google-play-scraper) by JoMingyu. We re-implemented it on top of our own HTTP layer to support retries and proxies, but the data-structure knowledge originates from that project.

---

## License

[MIT](LICENSE)
