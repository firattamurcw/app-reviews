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
| `review_id` | `str` | Required | A unique identifier for this review. |
| `canonical_key` | `str` | Required | A key used for deduplication across providers. Format: `{store}:{source_review_id}`. |
| `app_id` | `str` | Required | The app's ID (numeric for App Store, package name for Google Play). |
| `app_input` | `str` | Required | The original input value you passed to the scraper. This preserves what you gave it, even if it was a URL that got resolved to an ID. |
| `country` | `str` | Required | Two-letter country code (like `"us"`, `"gb"`, `"de"`). |
| `rating` | `int` | Required | Star rating from 1 to 5. Validated on creation -- values outside this range raise `ValueError`. |
| `title` | `str` | Required | The review's title. May be empty for Google Play reviews (Google Play reviews do not have titles). |
| `body` | `str` | Required | The review's body text. |
| `author_name` | `str` | Required | The display name of the review author. |
| `created_at` | `datetime` | Required | When the review was originally posted. |
| `source` | `str` | Required | Which data source provided this review. One of: `appstore_scraper`, `appstore_official`, `googleplay_scraper`, `googleplay_official`. |
| `source_review_id` | `str` | Required | The raw review ID as returned by the source. |
| `fetched_at` | `datetime` | Required | When this review was fetched by the scraper. |
| `locale` | `str` or `None` | `None` | The locale of the review (like `"en_US"`), if available. |
| `language` | `str` or `None` | `None` | The language of the review (like `"en"`), if available. |
| `app_version` | `str` or `None` | `None` | The app version that was reviewed (like `"2.1.0"`), if available. Not all sources provide this. |
| `updated_at` | `datetime` or `None` | `None` | When the review was last edited, if it was edited. |
| `is_edited` | `bool` | `False` | `True` if the review has been edited by the author. |
| `source_payload` | `dict` or `None` | `None` | The raw response from the API for this review. Only populated when `include_raw=True` is used during export. |

---

## FetchResult

The return value of `scraper.fetch()`. Contains everything from a fetch operation: the reviews, any failures, warnings, statistics, and checkpoint state.

```python
from app_reviews import FetchResult
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `reviews` | `list[Review]` | `[]` | The deduplicated list of reviews, sorted newest-first by default. |
| `failures` | `list[FetchFailure]` | `[]` | A list of fetch attempts that failed. Each failure records which app, country, and provider failed, and what the error was. |
| `warnings` | `list[FetchWarning]` | `[]` | A list of non-fatal issues that happened during the fetch. These do not stop the fetch but may indicate problems. |
| `stats` | `FetchStats` | `FetchStats()` | Summary statistics for the fetch operation. |
| `checkpoint` | `dict[str, str]` | `{}` | State for resuming an interrupted fetch. Can be passed back to continue where you left off. |

!!! note
    A fetch can partially succeed. If 3 out of 5 countries succeed, `result.reviews` contains the reviews from those 3 countries, and `result.failures` contains the 2 that failed. Always check `result.failures` if you need to know whether everything succeeded.

---

## FetchFailure

Records a single failed fetch attempt.

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

You can create a `FetchFailure` with an automatic timestamp:

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
