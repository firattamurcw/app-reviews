# Python API

The Python API provides two main classes: `AppStoreReviews` for the Apple App Store and `GooglePlayReviews` for the Google Play Store. Both follow the same pattern: create a client with connection configuration, then call `fetch()` with the app ID and query parameters. The client is reusable — you can call `fetch()` multiple times for different apps.

---

## AppStoreReviews

Fetches reviews from the Apple App Store.

### Import

```python
from app_reviews import AppStoreReviews, AppStoreAuth
```

### Constructor

```python
client = AppStoreReviews(
    auth=None,
    proxy=None,
    retry=None,
    debug=False,
    callbacks=None,
    on_review=None,
)
```

The constructor takes **connection configuration only** — no app ID, no query parameters. This lets you create the client once and reuse it for many `fetch()` calls.

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `auth` | `AppStoreAuth` or `None` | `None` | Authentication credentials. If `None`, uses the public RSS feed. If provided, uses the App Store Connect API. |
| `proxy` | `str` or `None` | `None` | HTTP proxy URL. Applied to all requests made by this client. |
| `retry` | `RetryConfig` or `None` | `None` | Retry configuration. If `None`, uses the default retry settings. |
| `debug` | `bool` | `False` | If `True`, prints debug information for each request. |
| `callbacks` | `list[FetchCallback]` or `None` | `None` | Lifecycle callbacks invoked at fetch start, per-review, and fetch end. |
| `on_review` | `callable` or `None` | `None` | Shorthand for a single per-review callback. Called with each `Review` as it is fetched. |

### fetch() Method

```python
result = client.fetch(
    app_id,
    countries=None,
    since=None,
    until=None,
    ratings=None,
    sort=None,
    limit=None,
    cursor=None,
)
```

### fetch() Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app_id` | `str` | Required (positional) | The App Store ID to fetch reviews for (the numeric ID from the app's URL). |
| `countries` | `list[Country \| str]` or `None` | `[Country.US]` | Countries to fetch from. Accepts `Country` enum values or two-letter strings. Reviews are fetched from each country and deduplicated. |
| `since` | `date` or `None` | `None` | Only return reviews posted on or after this date. |
| `until` | `date` or `None` | `None` | Only return reviews posted on or before this date. |
| `ratings` | `list[int]` or `None` | `None` | Filter to specific star ratings. Example: `[1, 2]` returns only 1- and 2-star reviews. |
| `sort` | `Sort` or `None` | `None` | Sort order. One of `Sort.NEWEST`, `Sort.OLDEST`, `Sort.RATING`. |
| `limit` | `int` or `None` | `None` | Maximum number of reviews to return. |
| `cursor` | `str` or `None` | `None` | Resume a paginated fetch from a previous result's `cursor`. |

### AppStoreAuth

```python
from app_reviews import AppStoreAuth

auth = AppStoreAuth(
    key_id="ABC123DEF4",
    issuer_id="12345678-1234-1234-1234-123456789012",
    key_path="/path/to/AuthKey_ABC123DEF4.p8",
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `key_id` | `str` | Your App Store Connect API key ID. |
| `issuer_id` | `str` | Your App Store Connect issuer ID. |
| `key_path` | `str` | Path to your `.p8` private key file. |

### Examples

**Basic usage (no auth, public RSS feed):**

```python
from app_reviews import AppStoreReviews

client = AppStoreReviews()
result = client.fetch("123456789")

for review in result:
    print(f"{review.rating}* {review.title}")
```

**Multiple countries:**

```python
from app_reviews import AppStoreReviews, Country

client = AppStoreReviews()
result = client.fetch(
    "123456789",
    countries=[Country.US, Country.GB, Country.DE, Country.FR, Country.JP],
)
print(f"{len(result)} unique reviews from 5 countries")
```

**With App Store Connect authentication:**

```python
from app_reviews import AppStoreReviews, AppStoreAuth, Country

client = AppStoreReviews(
    auth=AppStoreAuth(
        key_id="ABC123DEF4",
        issuer_id="12345678-1234-1234-1234-123456789012",
        key_path="/path/to/AuthKey_ABC123DEF4.p8",
    )
)

result = client.fetch("123456789", countries=[Country.US, Country.GB])
```

**Reuse client for multiple apps:**

```python
spotify = client.fetch("324684580", countries=[Country.US, Country.GB])
instagram = client.fetch("389801252", countries=[Country.US])
twitter = client.fetch("333903271", ratings=[1, 2])
```

**Filter by date and rating:**

```python
from datetime import date
from app_reviews import AppStoreReviews, Country

client = AppStoreReviews()
result = client.fetch(
    "123456789",
    countries=[Country.US],
    ratings=[1, 2],
    since=date(2025, 1, 1),
)
```

---

## GooglePlayReviews

Fetches reviews from the Google Play Store.

### Import

```python
from app_reviews import GooglePlayReviews, GooglePlayAuth
```

### Constructor

```python
client = GooglePlayReviews(
    auth=None,
    proxy=None,
    retry=None,
    debug=False,
    callbacks=None,
    on_review=None,
)
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `auth` | `GooglePlayAuth` or `None` | `None` | Authentication credentials. If `None`, uses the public web endpoint. If provided, uses the Google Play Developer API. |
| `proxy` | `str` or `None` | `None` | HTTP proxy URL. Applied to all requests made by this client. |
| `retry` | `RetryConfig` or `None` | `None` | Retry configuration. If `None`, uses the default retry settings. |
| `debug` | `bool` | `False` | If `True`, prints debug information for each request. |
| `callbacks` | `list[FetchCallback]` or `None` | `None` | Lifecycle callbacks invoked at fetch start, per-review, and fetch end. |
| `on_review` | `callable` or `None` | `None` | Shorthand for a single per-review callback. Called with each `Review` as it is fetched. |

### fetch() Method

```python
result = client.fetch(
    app_id,
    countries=None,
    since=None,
    until=None,
    ratings=None,
    sort=None,
    limit=None,
    cursor=None,
)
```

### fetch() Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app_id` | `str` | Required (positional) | The Google Play package name (e.g. `"com.example.app"`). |
| `countries` | `list[Country \| str]` or `None` | `[Country.US]` | Countries to fetch from. |
| `since` | `date` or `None` | `None` | Only return reviews posted on or after this date. |
| `until` | `date` or `None` | `None` | Only return reviews posted on or before this date. |
| `ratings` | `list[int]` or `None` | `None` | Filter to specific star ratings. |
| `sort` | `Sort` or `None` | `None` | Sort order. One of `Sort.NEWEST`, `Sort.OLDEST`, `Sort.RATING`. |
| `limit` | `int` or `None` | `None` | Maximum number of reviews to return. |
| `cursor` | `str` or `None` | `None` | Resume a paginated fetch from a previous result's `cursor`. |

### GooglePlayAuth

```python
from app_reviews import GooglePlayAuth

auth = GooglePlayAuth(
    service_account_path="/path/to/service-account.json",
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `service_account_path` | `str` | Path to a Google service account JSON key file. |

### Examples

**Basic usage (no auth):**

```python
from app_reviews import GooglePlayReviews

client = GooglePlayReviews()
result = client.fetch("com.example.app")

for review in result:
    print(f"{review.rating}* {review.body[:100]}")
```

**Multiple countries:**

```python
from app_reviews import GooglePlayReviews, Country

client = GooglePlayReviews()
result = client.fetch(
    "com.example.app",
    countries=[Country.US, Country.GB, Country.DE, Country.FR, Country.JP],
)
print(f"{len(result)} unique reviews from 5 countries")
```

**With Google Play Developer API authentication:**

```python
from app_reviews import GooglePlayReviews, GooglePlayAuth, Country, Sort

client = GooglePlayReviews(
    auth=GooglePlayAuth(
        service_account_path="/path/to/service-account.json",
    )
)

result = client.fetch(
    "com.example.app",
    countries=[Country.US, Country.GB],
    sort=Sort.NEWEST,
    limit=100,
)
```

---

## Country Enum

`Country` is a `StrEnum` — values are two-letter country codes but can be used anywhere a string is expected.

```python
from app_reviews import Country

# Individual countries
Country.US   # "us"
Country.GB   # "gb"
Country.DE   # "de"
Country.FR   # "fr"
Country.JP   # "jp"

# Convenience groups
Country.EUROPE   # all European countries
Country.ALL      # all 175+ supported countries
```

You can also pass plain strings: `countries=["us", "gb"]` works the same as `countries=[Country.US, Country.GB]`.

---

## Sort Enum

```python
from app_reviews import Sort

Sort.NEWEST   # most recent reviews first (default)
Sort.OLDEST   # oldest reviews first
Sort.RATING   # highest rated first
```

---

## Working with Results

Both clients return a `FetchResult` object. See the [Models](../reference/models.md) page for full field documentation.

### Iterate, count, and check

```python
result = client.fetch("123456789")

# Iterate directly
for review in result:
    print(review.title)

# Count
print(f"Reviews: {len(result)}")

# Check if any results
if result:
    print("Got reviews!")
```

### Filter after fetching

```python
from datetime import date

# Filter without making another network request
bad_recent = result.filter(ratings=[1, 2], since=date(2025, 1, 1))

for review in bad_recent:
    print(f"{review.rating}* {review.body[:80]}")
```

### Check succeeded and failed countries

```python
print(f"Succeeded: {[cs.country for cs in result.succeeded]}")

if result.failed:
    for cs in result.failed:
        print(f"Failed: {cs.country} -- {cs.error}")
```

### Export to dicts or DataFrame

```python
# List of plain dicts
records = result.to_dicts()

# pandas DataFrame (requires pandas)
df = result.to_df()
print(df[["rating", "title", "country"]].head())
```

### Access review fields

```python
for review in result:
    print(f"ID:       {review.id}")
    print(f"Store:    {review.store}")       # "appstore" or "googleplay"
    print(f"App:      {review.app_id}")
    print(f"Country:  {review.country}")
    print(f"Rating:   {review.rating}")      # 1 to 5
    print(f"Title:    {review.title}")       # may be empty for Google Play
    print(f"Body:     {review.body}")
    print(f"Author:   {review.author_name}")
    print(f"Version:  {review.app_version}") # may be None
    print(f"Date:     {review.created_at}")
    print(f"Edited:   {review.is_edited}")
    print(f"Source:   {review.source}")      # e.g. "appstore_scraper"
    print(f"Raw:      {review.raw}")         # raw API payload, if requested
    print()
```

### Error handling

The `fetch()` method does not raise exceptions for partial failures. If some countries fail and others succeed, you get the successful reviews plus a list of failures in `result.failed`.

```python
result = client.fetch("123456789")

if not result and result.failed:
    # Everything failed
    print("All fetches failed:")
    for cs in result.failed:
        print(f"  {cs.country}: {cs.error}")
elif result.failed:
    # Partial success
    print(f"Got {len(result)} reviews, but some countries failed:")
    for cs in result.failed:
        print(f"  {cs.country}: {cs.error}")
else:
    # Full success
    print(f"Got {len(result)} reviews")
```

If you pass invalid configuration (e.g., malformed auth credentials), the client raises a `ValueError` immediately.

---

## Callbacks

Use callbacks to react to reviews as they are fetched, without waiting for the entire operation to complete.

```python
from app_reviews import AppStoreReviews, Review

def handle_review(review: Review) -> None:
    print(f"Got review: {review.rating}* {review.title}")

client = AppStoreReviews(on_review=handle_review)
result = client.fetch("123456789")
```

For more control, implement the `FetchCallback` protocol:

```python
from app_reviews import FetchCallback, Review

class MyCallback:
    def on_start(self, app_id: str) -> None:
        print(f"Starting fetch for {app_id}")

    def on_review(self, review: Review) -> None:
        print(f"  {review.rating}* {review.title}")

    def on_end(self, app_id: str, total: int) -> None:
        print(f"Done: {total} reviews for {app_id}")

client = AppStoreReviews(callbacks=[MyCallback()])
result = client.fetch("123456789")
```

---

## Look Up App Metadata

You can look up app metadata without fetching reviews:

```python
from app_reviews.utils.metadata import lookup_metadata

# Auto-detects store from the ID format
metadata = lookup_metadata("123456789")

print(f"Name:      {metadata.name}")
print(f"Developer: {metadata.developer}")
print(f"Category:  {metadata.category}")
print(f"Price:     {metadata.price}")
print(f"Version:   {metadata.version}")
print(f"Rating:    {metadata.rating}")
print(f"Ratings:   {metadata.rating_count}")
print(f"URL:       {metadata.url}")
```

You can also specify the store explicitly:

```python
metadata = lookup_metadata("com.example.app", store="googleplay")
```

---

## Legacy API

The old class names still work but emit a deprecation warning. Update your code when convenient.

```python
# Deprecated — use AppStoreReviews instead
from app_reviews import AppStoreScraper
scraper = AppStoreScraper(app_id="123456789", countries=["us"])
result = scraper.fetch()

# Deprecated — use GooglePlayReviews instead
from app_reviews import GooglePlayScraper
scraper = GooglePlayScraper(app_id="com.example.app")
result = scraper.fetch()
```
