# Quick Start

Get from zero to fetching reviews in under 2 minutes.

---

## Fetch Apple App Store Reviews

```python
from app_reviews import AppStoreReviews

client = AppStoreReviews()
result = client.fetch("123456789")

for review in result:
    print(f"{review.rating}* {review.title}")
    print(f"  {review.body[:100]}")
    print(f"  -- {review.author_name}, {review.country}")
```

Replace `"123456789"` with a real App Store ID (the number after `/id` in the app's URL).

---

## Fetch Google Play Store Reviews

```python
from app_reviews import GooglePlayReviews

client = GooglePlayReviews()
result = client.fetch("com.example.app")

for review in result:
    print(f"{review.rating}* {review.body[:100]}")
    print(f"  -- {review.author_name}, {review.country}")
```

Replace `"com.example.app"` with a real package name (the `id` parameter in the Google Play URL).

---

## Fetch from Multiple Countries

```python
from app_reviews import AppStoreReviews, Country

client = AppStoreReviews()
result = client.fetch(
    "123456789",
    countries=[Country.US, Country.GB, Country.DE, Country.FR, Country.JP],
)

print(f"Fetched {len(result)} reviews")
```

---

## Reuse the Client

The client holds connection config (auth, proxy, retry). Reuse it for multiple apps:

```python
from app_reviews import AppStoreReviews, AppStoreAuth, Country

client = AppStoreReviews(
    auth=AppStoreAuth(
        key_id="ABC123DEF4",
        issuer_id="12345678-1234-1234-1234-123456789012",
        key_path="/path/to/AuthKey.p8",
    )
)

spotify = client.fetch("324684580", countries=[Country.US, Country.GB])
instagram = client.fetch("389801252", countries=[Country.US])
twitter = client.fetch("333903271", ratings=[1, 2])
```

---

## Filter Results

```python
from datetime import date

result = client.fetch("123456789", countries=[Country.US, Country.GB, Country.DE])

bad_recent = result.filter(ratings=[1, 2], since=date(2025, 1, 1))

for review in bad_recent:
    print(f"{review.rating}* {review.body[:80]}")
```

---

## Launch the Interactive TUI

If you installed with `pip install app-reviews[tui]`:

```bash
app-reviews
```

This launches an interactive terminal UI that walks you through selecting an app, countries, and browsing results.

---

## Understanding the Result

Every `client.fetch()` call returns a `FetchResult`. It is iterable and supports `len()` and `bool()`.

| Property / Method | Description |
|-------------------|-------------|
| `for r in result` | Iterate over `Review` objects. |
| `len(result)` | Number of reviews. |
| `bool(result)` | `True` if there is at least one review. |
| `result.reviews` | The list of `Review` objects. |
| `result.errors` | List of `FetchError` objects for countries that failed. |
| `result.filter(...)` | Returns a new filtered `FetchResult`. |
| `result.sort(...)` | Returns a new sorted `FetchResult`. |
| `result.limit(n)` | Returns a new `FetchResult` truncated to `n` reviews. |
| `result.to_dicts()` | Convert reviews to a list of plain dicts. |

```python
result = client.fetch("123456789")

print(f"Reviews: {len(result)}")

if result.errors:
    for err in result.errors:
        print(f"Failed: {err.country} -- {err.message}")
```

A fetch can partially succeed. If 3 out of 5 countries succeed, you get reviews from those 3 and errors for the other 2.

---

## Next Steps

- [Python API](../guide/python-api.md) -- all parameters and options
- [Interactive TUI](../guide/tui.md) -- terminal UI walkthrough
- [Authentication](../guide/authentication.md) -- set up authenticated APIs
- [Export Formats](../guide/export.md) -- JSON, JSONL, CSV export
