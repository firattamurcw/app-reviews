# Python API

The Python API provides two main classes: `AppStoreScraper` for the Apple App Store and `GooglePlayScraper` for the Google Play Store. Both follow the same pattern: create a scraper, call `fetch()`, get results.

---

## AppStoreScraper

Fetches reviews from the Apple App Store.

### Import

```python
from app_reviews import AppStoreScraper
```

### Constructor

```python
scraper = AppStoreScraper(
    app_id="123456789",
    countries=["us", "gb", "de"],
    provider="auto",
    key_id=None,
    issuer_id=None,
    key_path=None,
)
```

All parameters are keyword-only.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app_id` | `str` or `None` | `None` | A single App Store ID. Use this or `app_ids`, not both. |
| `app_ids` | `list[str]` or `None` | `None` | A list of App Store IDs. Use this to fetch reviews for multiple apps in one call. |
| `countries` | `list[str]` or `None` | `["us"]` | List of two-letter country codes to fetch from. Reviews are fetched from each country and then deduplicated. |
| `provider` | `str` | `"auto"` | Which data source to use. See the provider table below. |
| `key_id` | `str` or `None` | `None` | Your App Store Connect API key ID. Required for the `official` provider. |
| `issuer_id` | `str` or `None` | `None` | Your App Store Connect issuer ID. Required for the `official` provider. |
| `key_path` | `str` or `None` | `None` | Path to your `.p8` private key file. Required for the `official` provider. |

### app_id vs app_ids

Use `app_id` when you are fetching reviews for a single app. This is the common case.

Use `app_ids` when you want to fetch reviews for multiple apps in one call. The result will contain reviews from all the apps mixed together. Each review has an `app_id` field so you can tell which app it belongs to.

You must provide exactly one of these. Passing both raises an error. Passing neither also raises an error.

### Providers

| Provider | Auth Required | Description |
|----------|---------------|-------------|
| `"auto"` | No | Uses the official API if `key_id`, `issuer_id`, and `key_path` are all provided. Otherwise falls back to the scraper. This is the default. |
| `"scraper"` | No | Fetches from the public iTunes RSS feed. No setup needed. Works for any app. Returns up to ~500 reviews (most recent only). |
| `"official"` | Yes | Uses the App Store Connect API. Requires `key_id`, `issuer_id`, and `key_path`. Returns more data and supports higher limits. See [Authentication](authentication.md) for setup. |

!!! warning "Scraper limitations"
    The RSS feed scraper returns only the most recent reviews. There is no way to fetch historical reviews through this endpoint. For most apps, you will get somewhere between 50 and 500 reviews per country. If you need more, use the `"official"` provider.

### Examples

**Basic usage:**

```python
from app_reviews import AppStoreScraper

scraper = AppStoreScraper(app_id="123456789")
result = scraper.fetch()

for review in result.reviews:
    print(f"{review.rating}* {review.title}")
```

**Multiple countries:**

```python
scraper = AppStoreScraper(
    app_id="123456789",
    countries=["us", "gb", "de", "fr", "jp"],
)
result = scraper.fetch()
print(f"{len(result.reviews)} unique reviews from 5 countries")
```

**Multiple apps:**

```python
scraper = AppStoreScraper(
    app_ids=["123456789", "987654321"],
    countries=["us"],
)
result = scraper.fetch()

# Reviews from both apps are in the same list
for review in result.reviews:
    print(f"[{review.app_id}] {review.rating}* {review.title}")
```

**With App Store Connect authentication:**

```python
scraper = AppStoreScraper(
    app_id="123456789",
    countries=["us", "gb"],
    provider="official",
    key_id="ABC123DEF4",
    issuer_id="12345678-1234-1234-1234-123456789012",
    key_path="/path/to/AuthKey_ABC123DEF4.p8",
)
result = scraper.fetch()
```

**Force scraper provider (skip authentication even if credentials are available):**

```python
scraper = AppStoreScraper(
    app_id="123456789",
    provider="scraper",
)
result = scraper.fetch()
```

---

## GooglePlayScraper

Fetches reviews from the Google Play Store.

### Import

```python
from app_reviews import GooglePlayScraper
```

### Constructor

```python
scraper = GooglePlayScraper(
    app_id="com.example.app",
    countries=["us", "gb"],
    provider="auto",
    service_account_path=None,
)
```

All parameters are keyword-only.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app_id` | `str` or `None` | `None` | A single Google Play package name. Use this or `app_ids`, not both. |
| `app_ids` | `list[str]` or `None` | `None` | A list of package names. Use this to fetch reviews for multiple apps in one call. |
| `countries` | `list[str]` or `None` | `["us"]` | List of two-letter country codes to fetch from. Reviews are fetched from each country and then deduplicated. |
| `provider` | `str` | `"auto"` | Which data source to use. See the provider table below. |
| `service_account_path` | `str` or `None` | `None` | Path to a Google service account JSON key file. Required for the `official` provider. |

### app_id vs app_ids

Same as App Store above. Use `app_id` for one app (common case), `app_ids` for multiple apps in one call. Provide exactly one.

### Providers

| Provider | Auth Required | Description |
|----------|---------------|-------------|
| `"auto"` | No | Uses the official API if `service_account_path` is provided. Otherwise falls back to the scraper. This is the default. |
| `"scraper"` | No | Scrapes the public Google Play website. No setup needed. Works for any app. Handles rate limiting with automatic exponential backoff. |
| `"official"` | Yes | Uses the Google Play Developer API. Requires a service account. See [Authentication](authentication.md) for setup. |

!!! warning "Scraper limitations"
    The Google Play web scraper uses an undocumented internal Google endpoint. It works well, but Google can rate-limit you or change the endpoint without notice, which would temporarily break scraping. The package handles rate limits with automatic backoff, but heavy usage may hit walls.

### Examples

**Basic usage:**

```python
from app_reviews import GooglePlayScraper

scraper = GooglePlayScraper(app_id="com.example.app")
result = scraper.fetch()

for review in result.reviews:
    print(f"{review.rating}* {review.body[:100]}")
```

**Multiple countries:**

```python
scraper = GooglePlayScraper(
    app_id="com.example.app",
    countries=["us", "gb", "de", "fr", "jp"],
)
result = scraper.fetch()
print(f"{len(result.reviews)} unique reviews from 5 countries")
```

**Multiple apps:**

```python
scraper = GooglePlayScraper(
    app_ids=["com.example.app", "com.another.app"],
    countries=["us"],
)
result = scraper.fetch()
```

**With Google Play Developer API authentication:**

```python
scraper = GooglePlayScraper(
    app_id="com.example.app",
    countries=["us", "gb"],
    provider="official",
    service_account_path="/path/to/service-account.json",
)
result = scraper.fetch()
```

**Force web scraping (skip authentication even if credentials are available):**

```python
scraper = GooglePlayScraper(
    app_id="com.example.app",
    provider="scraper",
)
result = scraper.fetch()
```

---

## Working with Results

Both scrapers return a `FetchResult` object. See the [Models](../reference/models.md) page for full field documentation.

### Inspect the result

```python
result = scraper.fetch()

# Number of reviews
print(f"Reviews: {len(result.reviews)}")

# Check for failures (countries that couldn't be fetched)
for failure in result.failures:
    print(f"Failed: {failure.country} -- {failure.error}")

# Check for warnings (non-fatal issues)
for warning in result.warnings:
    print(f"Warning: {warning.message}")

# Fetch statistics
print(f"Countries: {result.stats.total_countries}")
print(f"Failures: {result.stats.total_failures}")
print(f"Duration: {result.stats.duration_seconds:.1f}s")
```

### Access review fields

```python
for review in result.reviews:
    print(f"ID:       {review.review_id}")
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
    print()
```

### Error handling

The `fetch()` method does not raise exceptions for partial failures. If some countries fail and others succeed, you get the successful reviews plus a list of failures.

```python
result = scraper.fetch()

if not result.reviews and result.failures:
    # Everything failed
    print("All fetches failed:")
    for f in result.failures:
        print(f"  {f.country}: {f.error}")
elif result.failures:
    # Partial success
    print(f"Got {len(result.reviews)} reviews, but some countries failed:")
    for f in result.failures:
        print(f"  {f.country}: {f.error}")
else:
    # Full success
    print(f"Got {len(result.reviews)} reviews")
```

If you pass invalid configuration (e.g., `provider="official"` without credentials, or both `app_id` and `app_ids`), the scraper raises a `ValueError` immediately.

### Look up app metadata

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
