# Quick Start

This page gets you from zero to fetching reviews in under 2 minutes.

---

## Fetch Apple App Store Reviews

```python
from app_reviews import AppStoreReviews

# Create a client (no auth = uses public RSS feed)
client = AppStoreReviews()

# Fetch reviews for an app by its App Store ID
result = client.fetch("123456789")

# FetchResult is iterable — loop directly over it
for review in result:
    print(f"{review.rating}* {review.title}")
    print(f"  {review.body[:100]}")
    print(f"  -- {review.author_name}, {review.country}")
    print()
```

Replace `"123456789"` with a real App Store ID. You can find the ID in the app's App Store URL -- it is the number after `/id`.

For example, in `https://apps.apple.com/us/app/example/id123456789`, the ID is `123456789`.

!!! note "What happens behind the scenes"
    When you call `client.fetch("123456789")`, the package sends HTTP requests to Apple's public RSS feed for each country you specified (default: US only). It parses the JSON response, normalizes each review into a common `Review` object, deduplicates across countries, and returns everything in a `FetchResult`.

---

## Fetch Google Play Store Reviews

```python
from app_reviews import GooglePlayReviews

# Create a client (no auth = uses public web endpoint)
client = GooglePlayReviews()

# Fetch reviews for an app by its package name
result = client.fetch("com.example.app")

# Loop directly over the result
for review in result:
    print(f"{review.rating}* {review.body[:100]}")
    print(f"  -- {review.author_name}, {review.country}")
    print()
```

Replace `"com.example.app"` with a real package name. You can find it in the Google Play URL -- it is the `id` parameter.

For example, in `https://play.google.com/store/apps/details?id=com.example.app`, the package name is `com.example.app`.

---

## Fetch from Multiple Countries

Both clients can fetch reviews from multiple countries at once. The package automatically deduplicates reviews that appear in more than one country's feed.

```python
from app_reviews import AppStoreReviews, Country

client = AppStoreReviews()

result = client.fetch(
    "123456789",
    countries=[Country.US, Country.GB, Country.DE, Country.FR, Country.JP],
)

print(f"Fetched {len(result)} unique reviews")
print(f"From {result.stats.total_countries} countries")
print(f"In {result.stats.duration_seconds:.1f} seconds")
```

!!! tip
    The same review can appear in multiple country feeds. When you fetch from 5 countries, you might get 200 raw reviews but only 150 unique ones after deduplication. Iterating over `result` always yields only unique reviews.

---

## Reuse the Client for Multiple Apps

The client holds connection configuration (auth, proxy, retry settings). You can reuse it to fetch multiple apps without recreating the connection setup each time.

```python
from app_reviews import AppStoreReviews, AppStoreAuth, Country

client = AppStoreReviews(
    auth=AppStoreAuth(
        key_id="ABC123DEF4",
        issuer_id="12345678-1234-1234-1234-123456789012",
        key_path="/path/to/AuthKey.p8",
    )
)

# Fetch different apps with the same client
spotify = client.fetch("324684580", countries=[Country.US, Country.GB])
instagram = client.fetch("389801252", countries=[Country.US])
twitter = client.fetch("333903271", ratings=[1, 2])  # only 1 and 2 star reviews
```

---

## Filter Results After Fetching

Use `result.filter()` to narrow down results without making another network request.

```python
from datetime import date

result = client.fetch("123456789", countries=[Country.US, Country.GB, Country.DE])

# Only 1 and 2 star reviews posted since the start of 2025
bad_recent = result.filter(ratings=[1, 2], since=date(2025, 1, 1))

for review in bad_recent:
    print(f"{review.rating}* {review.body[:80]}")
```

---

## Use the CLI

Fetch reviews from the command line:

```bash
# Table output (default)
app-reviews fetch 123456789

# JSON output
app-reviews fetch 123456789 -f json

# Fetch from specific countries
app-reviews fetch 123456789 -c us -c gb -c de

# Save to a file
app-reviews fetch 123456789 -f csv -o reviews.csv
```

---

## Launch the Interactive TUI

If you installed with `pip install app-reviews[tui]`, you can browse reviews in an interactive terminal interface:

```bash
app-reviews fetch
```

Running `fetch` without format or output flags launches the TUI. It walks you through selecting an app, choosing countries, fetching, and browsing the results.

---

## Understanding the Result

Every `client.fetch()` call returns a `FetchResult` object. It is iterable and supports `len()` and `bool()`.

| Property / Method | What it contains |
|-------------------|-----------------|
| `for r in result` | Iterate over deduplicated `Review` objects, sorted newest-first. |
| `len(result)` | Number of unique reviews. |
| `bool(result)` | `True` if there is at least one review. |
| `result.filter(...)` | Returns a new `FetchResult` filtered by ratings, date range, etc. |
| `result.succeeded` | List of countries that were fetched successfully. |
| `result.failed` | List of countries that failed (as `CountryStatus` objects). |
| `result.stats` | Summary: total reviews, total countries, total failures, duration in seconds. |
| `result.cursor` | Cursor for resuming a paginated fetch. |
| `result.to_dicts()` | Convert reviews to a list of plain dicts. |
| `result.to_df()` | Convert reviews to a pandas DataFrame (requires pandas). |

Here is how to inspect it:

```python
result = client.fetch("123456789")

# The reviews
print(f"Reviews: {len(result)}")

# Any countries that failed
if result.failed:
    for cs in result.failed:
        print(f"Failed: {cs.country} -- {cs.error}")

# Timing and counts
print(f"Total countries: {result.stats.total_countries}")
print(f"Duration: {result.stats.duration_seconds:.1f}s")
```

A fetch can partially succeed. For example, if you request 5 countries and 1 fails, you still get reviews from the other 4. Check `result.failed` to see what went wrong.

---

## Next Steps

- [Python API](../guide/python-api.md) -- all parameters and options
- [CLI](../guide/cli.md) -- full command-line reference
- [Interactive TUI](../guide/tui.md) -- terminal UI walkthrough
- [Authentication](../guide/authentication.md) -- set up authenticated APIs for more data
- [Export Formats](../guide/export.md) -- JSON, JSONL, CSV export
