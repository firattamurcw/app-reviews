# Models

All models are Python dataclasses. They are frozen (immutable after creation) and use `__slots__` for memory efficiency.

---

## Review

A single app review, normalized to a common format across all stores and providers. Whether the review came from the App Store RSS feed or the Google Play Developer API, it has the same fields.

```python
from app_reviews import Review
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `store` | `"appstore"` or `"googleplay"` | Required | Which store the review came from. |
| `id` | `str` | Required | A unique identifier for this review. |
| `app_id` | `str` | Required | The app's ID (numeric for App Store, package name for Google Play). |
| `country` | `str` | Required | Two-letter country code (like `"us"`, `"gb"`, `"de"`). |
| `rating` | `int` | Required | Star rating from 1 to 5. Validated on creation -- values outside this range raise `ValueError`. |
| `title` | `str` | Required | The review's title. May be empty for Google Play reviews (Google Play reviews do not have titles). |
| `body` | `str` | Required | The review's body text. |
| `author_name` | `str` | Required | The display name of the review author. |
| `created_at` | `datetime` | Required | When the review was originally posted. |
| `source` | `str` | Required | Which data source provided this review. One of: `appstore_scraper`, `appstore_official`, `googleplay_scraper`, `googleplay_official`. |
| `fetched_at` | `datetime` | Required | When this review was fetched by the client. |
| `language` | `str` or `None` | `None` | The language of the review (like `"en"`), if available. |
| `app_version` | `str` or `None` | `None` | The app version that was reviewed (like `"2.1.0"`), if available. Not all sources provide this. |
| `updated_at` | `datetime` or `None` | `None` | When the review was last edited, if it was edited. |
| `is_edited` | `bool` | `False` | `True` if the review has been edited by the author. |
| `raw` | `dict` or `None` | `None` | The raw response from the API for this review. Only populated when `include_raw=True` is used during export. |

---

## FetchResult

The return value of `client.fetch()`. Contains everything from a fetch operation: the reviews, per-country status, statistics, and cursor state. `FetchResult` is iterable — you can loop over it directly to get `Review` objects.

```python
from app_reviews import FetchResult
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `countries` | `list[CountryStatus]` | Per-country fetch status. Each entry records whether that country succeeded or failed. |
| `stats` | `FetchStats` | Summary statistics for the fetch operation. |
| `cursor` | `str` or `None` | Cursor for resuming a paginated fetch. Pass to the next `fetch()` call to continue where you left off. |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `succeeded` | `list[CountryStatus]` | Countries that were fetched successfully. |
| `failed` | `list[CountryStatus]` | Countries that failed to fetch. |

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `__iter__()` | `Iterator[Review]` | Iterate over deduplicated reviews, sorted newest-first. |
| `__len__()` | `int` | Number of unique reviews. |
| `__bool__()` | `bool` | `True` if there is at least one review. |
| `filter(ratings, since, until)` | `FetchResult` | Return a new `FetchResult` with only reviews matching the given criteria. |
| `to_dicts(include_raw)` | `list[dict]` | Convert reviews to a list of plain dicts. |
| `to_df(include_raw)` | `DataFrame` | Convert reviews to a pandas DataFrame (requires pandas). |

!!! note
    A fetch can partially succeed. If 3 out of 5 countries succeed, iterating over the result yields the reviews from those 3 countries, and `result.failed` contains the 2 that failed. Always check `result.failed` if you need to know whether everything succeeded.

---

## CountryStatus

Records the fetch status for a single country.

```python
from app_reviews import CountryStatus
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `country` | `str` | Two-letter country code. |
| `succeeded` | `bool` | `True` if the fetch for this country succeeded. |
| `review_count` | `int` | Number of reviews fetched for this country (0 on failure). |
| `error` | `str` or `None` | Error message if the fetch failed. `None` on success. |
| `timestamp` | `datetime` | When the fetch attempt occurred. |

---

## FetchFailure

Records a single failed fetch attempt. Used internally and in legacy result objects.

```python
from app_reviews import FetchFailure
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `app_id` | `str` | The app ID that failed. |
| `country` | `str` | The country code that failed. May be empty if the failure was not country-specific. |
| `provider` | `str` | Which provider was being used when it failed. |
| `error` | `str` | A description of what went wrong. |
| `timestamp` | `datetime` | When the failure occurred. |

### Factory Method

```python
failure = FetchFailure.create(
    app_id="123456789",
    provider="scraper",
    error="HTTP 503 Service Unavailable",
    country="de",
)
```

---

## FetchWarning

A non-fatal issue encountered during a fetch. Warnings do not stop the fetch from completing.

```python
from app_reviews import FetchWarning
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `message` | `str` | Required | A description of the warning. |
| `context` | `dict[str, str]` | `{}` | Extra context about the warning (like which country or provider it relates to). |

---

## FetchStats

Summary statistics for a fetch operation.

```python
from app_reviews import FetchStats
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `total_reviews` | `int` | `0` | Total number of deduplicated reviews returned. |
| `total_countries` | `int` | `0` | Number of countries that were fetched from. |
| `total_failures` | `int` | `0` | Number of fetch attempts that failed. |
| `total_warnings` | `int` | `0` | Number of warnings generated. |
| `duration_seconds` | `float` | `0.0` | How long the entire fetch operation took, in seconds. |

---

## Country

`Country` is a `StrEnum` — values are two-letter country codes usable anywhere a string is expected.

```python
from app_reviews import Country
```

### Individual Countries

```python
Country.US    # "us"
Country.GB    # "gb"
Country.DE    # "de"
Country.FR    # "fr"
Country.JP    # "jp"
Country.CA    # "ca"
Country.AU    # "au"
# ... 175+ total
```

### Convenience Groups

| Group | Description |
|-------|-------------|
| `Country.EUROPE` | All European countries supported by the store. |
| `Country.ALL` | All 175+ supported countries. |

You can also pass plain strings: `countries=["us", "gb"]` works the same as `countries=[Country.US, Country.GB]`.

---

## Sort

Controls the order of reviews returned by `fetch()`.

```python
from app_reviews import Sort
```

| Value | Description |
|-------|-------------|
| `Sort.NEWEST` | Most recently posted reviews first (default). |
| `Sort.OLDEST` | Oldest reviews first. |
| `Sort.RATING` | Highest-rated reviews first. |

---

## RetryConfig

Controls retry behaviour for failed requests.

```python
from app_reviews import RetryConfig
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_attempts` | `int` | `3` | Maximum number of attempts per request (including the first). |
| `backoff_factor` | `float` | `1.0` | Multiplier applied to the wait time between retries. |
| `retry_on` | `list[int]` or `None` | `None` | HTTP status codes that should trigger a retry. If `None`, uses a sensible default set (e.g. 429, 500, 502, 503, 504). |

### Example

```python
from app_reviews import AppStoreReviews, RetryConfig

client = AppStoreReviews(
    retry=RetryConfig(max_attempts=5, backoff_factor=2.0, retry_on=[429, 503])
)
```

---

## FetchCallback

Protocol for lifecycle hooks. Implement any subset of the methods you need.

```python
from app_reviews import FetchCallback, Review
```

### Protocol Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `on_start` | `(app_id: str) -> None` | Called once when a fetch begins. |
| `on_review` | `(review: Review) -> None` | Called for each review as it is fetched, before deduplication. |
| `on_end` | `(app_id: str, total: int) -> None` | Called once when a fetch completes. `total` is the final deduplicated count. |

### Example

```python
from app_reviews import AppStoreReviews, FetchCallback, Review

class LoggingCallback:
    def on_start(self, app_id: str) -> None:
        print(f"Fetching {app_id}...")

    def on_review(self, review: Review) -> None:
        print(f"  [{review.country}] {review.rating}*")

    def on_end(self, app_id: str, total: int) -> None:
        print(f"Done: {total} reviews")

client = AppStoreReviews(callbacks=[LoggingCallback()])
result = client.fetch("123456789")
```

---

## AppMetadata

Metadata about an app, returned by `lookup_metadata()`.

```python
from app_reviews.utils.metadata import lookup_metadata

metadata = lookup_metadata("123456789")
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `app_id` | `str` | The app's ID or package name. |
| `store` | `"appstore"` or `"googleplay"` | Which store the app is on. |
| `name` | `str` | The app's display name. |
| `developer` | `str` | The developer or publisher name. |
| `category` | `str` | The app's primary category. |
| `price` | `str` | The app's price (like `"Free"` or `"$4.99"`). |
| `version` | `str` | The current version number. |
| `rating` | `float` | The average star rating. |
| `rating_count` | `int` | The total number of ratings. |
| `url` | `str` | The app's store page URL. |

---

## Type Aliases

These literal types are used throughout the package for type safety:

```python
from app_reviews.models.types import Store, Provider, Source
```

| Type | Values | Description |
|------|--------|-------------|
| `Store` | `"appstore"`, `"googleplay"` | Which store. |
| `Provider` | `"auto"`, `"scraper"`, `"official"` | Which data source to use. |
| `Source` | `"appstore_scraper"`, `"appstore_official"`, `"googleplay_scraper"`, `"googleplay_official"` | Which data source a review actually came from. |
