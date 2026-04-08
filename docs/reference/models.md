# Models

All models are frozen dataclasses with `__slots__`.

---

## Review

A single app review, normalized across all stores and providers.

```python
from app_reviews import Review
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `store` | `"appstore"` or `"googleplay"` | Required | Which store. |
| `app_id` | `str` | Required | App ID or package name. |
| `country` | `str` | Required | Two-letter country code. |
| `rating` | `int` | Required | Star rating 1-5. Validated on creation. |
| `title` | `str` | Required | Review title. May be empty for Google Play. |
| `body` | `str` | Required | Review body text. |
| `author_name` | `str` | Required | Author display name. |
| `created_at` | `datetime` | Required | When the review was posted. |
| `source` | `str` | Required | Data source: `appstore_scraper`, `appstore_official`, `googleplay_scraper`, or `googleplay_official`. |
| `app_version` | `str` or `None` | `None` | App version reviewed. |
| `updated_at` | `datetime` or `None` | `None` | Last edit time. |
| `language` | `str` or `None` | `None` | Review language. |
| `id` | `str` | `""` | Unique review identifier. |
| `fetched_at` | `datetime` or `None` | `None` | When the review was fetched. |
| `is_edited` | `bool` | `False` | Whether the review was edited. |
| `raw` | `dict` or `None` | `None` | Raw API payload. |

---

## FetchResult

The return value of `client.fetch()`. Contains reviews and any per-country errors. Iterable -- loop directly to get `Review` objects.

```python
from app_reviews import FetchResult
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `reviews` | `list[Review]` | The fetched reviews. |
| `errors` | `list[FetchError]` | Per-country fetch failures. |

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `__iter__()` | `Iterator[Review]` | Iterate over reviews. |
| `__len__()` | `int` | Number of reviews. |
| `__bool__()` | `bool` | `True` if there is at least one review. |
| `filter(ratings, since, until)` | `FetchResult` | Return a new filtered `FetchResult`. |
| `sort(order)` | `FetchResult` | Return a new sorted `FetchResult`. |
| `limit(n)` | `FetchResult` | Return a new `FetchResult` truncated to `n` reviews. |
| `to_dicts()` | `list[dict]` | Convert reviews to plain dicts. |

A fetch can partially succeed. Check `result.errors` to see which countries failed.

---

## FetchError

A per-country fetch failure.

```python
from app_reviews import FetchError
```

| Field | Type | Description |
|-------|------|-------------|
| `country` | `str` | Two-letter country code. |
| `message` | `str` | Error description. |

---

## Country

`StrEnum` with two-letter country codes.

```python
from app_reviews import Country
```

### Region Groups

| Group | Description |
|-------|-------------|
| `Country.ALL` | All 155 supported countries. |
| `Country.EUROPE` | European countries. |
| `Country.AMERICAS` | North and South America. |
| `Country.ASIA_PACIFIC` | Asia-Pacific region. |
| `Country.MIDDLE_EAST` | Middle East and North Africa. |
| `Country.ENGLISH_SPEAKING` | English-speaking countries. |

Plain strings also work: `countries=["us", "gb"]`.

---

## Sort

Controls review order.

```python
from app_reviews import Sort
```

| Value | Description |
|-------|-------------|
| `Sort.NEWEST` | Most recent first (default). |
| `Sort.OLDEST` | Oldest first. |
| `Sort.RATING` | Highest rated first. |

---

## RetryConfig

HTTP retry and timeout settings.

```python
from app_reviews import RetryConfig
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_retries` | `int` | `3` | Maximum number of retries per request. |
| `backoff_factor` | `float` | `0.5` | Multiplier for wait time between retries. |
| `timeout` | `float` | `30.0` | Per-request timeout in seconds. |
| `retry_on` | `list[int]` | `[500, 502, 503, 504, 429]` | HTTP status codes that trigger a retry. |

```python
from app_reviews import AppStoreReviews, RetryConfig

client = AppStoreReviews(
    retry=RetryConfig(max_retries=5, backoff_factor=1.0, retry_on=[429, 503])
)
```

---

## AppMetadata

Returned by `lookup_metadata()`.

```python
from app_reviews.utils.metadata import lookup_metadata

metadata = lookup_metadata("123456789")
```

| Field | Type | Description |
|-------|------|-------------|
| `app_id` | `str` | App ID or package name. |
| `store` | `"appstore"` or `"googleplay"` | Which store. |
| `name` | `str` | App display name. |
| `developer` | `str` | Developer or publisher. |
| `category` | `str` | Primary category. |
| `price` | `str` | Price or "Free". |
| `version` | `str` | Current version. |
| `rating` | `float` | Average star rating. |
| `rating_count` | `int` | Total number of ratings. |
| `url` | `str` | Store page URL. |

---

## Type Aliases

```python
from app_reviews.models.types import Store, ProviderName, Source
```

| Type | Values |
|------|--------|
| `Store` | `"appstore"`, `"googleplay"` |
| `ProviderName` | `"scraper"`, `"official"` |
| `Source` | `"appstore_scraper"`, `"appstore_official"`, `"googleplay_scraper"`, `"googleplay_official"` |
