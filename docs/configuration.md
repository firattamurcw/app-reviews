# Configuration

## Scraper options

Both `AppStoreScraper` and `AsyncAppStoreScraper` accept the same constructor parameters:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `app_id` | `str` | `None` | Single app ID to fetch reviews for |
| `app_ids` | `list[str]` | `None` | Multiple app IDs to fetch reviews for |
| `countries` | `list[str]` | `["us"]` | ISO country codes to query |
| `provider` | `str` | `"auto"` | Provider to use: `auto`, `rss`, or `connect` |

Use either `app_id` (single) or `app_ids` (multiple), not both.

## Providers

### RSS (default)

The RSS provider fetches reviews from Apple's public RSS feed. No authentication required.

```python
scraper = AppStoreScraper(app_id="123456789", provider="rss")
```

### App Store Connect

The Connect provider uses the App Store Connect API. Requires authentication credentials.

```python
scraper = AppStoreScraper(app_id="123456789", provider="connect")
```

### Auto (default)

When `provider="auto"`, the library selects the best available provider based on your configuration.

## Result structure

### FetchResult

The `fetch()` method returns a `FetchResult` with:

| Field | Type | Description |
|---|---|---|
| `reviews` | `list[Review]` | Deduplicated review list |
| `failures` | `list[FetchFailure]` | Failed fetch attempts |
| `warnings` | `list[FetchWarning]` | Non-fatal warnings |
| `stats` | `FetchStats` | Summary statistics |

### Review

Each `Review` contains:

| Field | Type | Description |
|---|---|---|
| `review_id` | `str` | Unique review identifier |
| `app_id` | `str` | App Store app ID |
| `country` | `str` | Country code |
| `rating` | `int` | Star rating (1-5) |
| `title` | `str` | Review title |
| `body` | `str` | Review body text |
| `author_name` | `str` | Author display name |
| `app_version` | `str \| None` | App version at time of review |
| `created_at` | `datetime` | When the review was posted |
| `updated_at` | `datetime \| None` | When the review was last edited |
| `is_edited` | `bool` | Whether the review was edited |
| `source` | `str` | Provider: `"rss"` or `"connect"` |

### FetchStats

| Field | Type | Description |
|---|---|---|
| `total_reviews` | `int` | Number of reviews fetched |
| `total_countries` | `int` | Number of countries queried |
| `total_failures` | `int` | Number of failed requests |
| `duration_seconds` | `float` | Total fetch duration |
