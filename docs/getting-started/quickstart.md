# Quick Start

This page gets you from zero to fetching reviews in under 2 minutes.

---

## Fetch Apple App Store Reviews

```python
from app_reviews import AppStoreScraper

# Create a scraper for an App Store app
scraper = AppStoreScraper(app_id="123456789")

# Fetch reviews (hits the public RSS feed, no auth needed)
result = scraper.fetch()

# Print each review
for review in result.reviews:
    print(f"{review.rating}* {review.title}")
    print(f"  {review.body[:100]}")
    print(f"  -- {review.author_name}, {review.country}")
    print()
```

Replace `"123456789"` with a real App Store ID. You can find the ID in the app's App Store URL -- it is the number after `/id`.

For example, in `https://apps.apple.com/us/app/example/id123456789`, the ID is `123456789`.

!!! note "What happens behind the scenes"
    When you call `scraper.fetch()`, the package sends HTTP requests to Apple's public RSS feed for each country you specified (default: US only). It parses the JSON response, normalizes each review into a common `Review` object, deduplicates across countries, and returns everything in a `FetchResult`.

---

## Fetch Google Play Store Reviews

```python
from app_reviews import GooglePlayScraper

# Create a scraper for a Google Play app
scraper = GooglePlayScraper(app_id="com.example.app")

# Fetch reviews (scrapes Google Play's web endpoint, no auth needed)
result = scraper.fetch()

# Print each review
for review in result.reviews:
    print(f"{review.rating}* {review.body[:100]}")
    print(f"  -- {review.author_name}, {review.country}")
    print()
```

Replace `"com.example.app"` with a real package name. You can find it in the Google Play URL -- it is the `id` parameter.

For example, in `https://play.google.com/store/apps/details?id=com.example.app`, the package name is `com.example.app`.

---

## Fetch from Multiple Countries

Both scrapers can fetch reviews from multiple countries at once. The package automatically deduplicates reviews that appear in more than one country's feed.

```python
from app_reviews import AppStoreScraper

scraper = AppStoreScraper(
    app_id="123456789",
    countries=["us", "gb", "de", "fr", "jp"],
)

result = scraper.fetch()

print(f"Fetched {len(result.reviews)} unique reviews")
print(f"From {result.stats.total_countries} countries")
print(f"In {result.stats.duration_seconds:.1f} seconds")
```

!!! tip
    The same review can appear in multiple country feeds. When you fetch from 5 countries, you might get 200 raw reviews but only 150 unique ones after deduplication. The `result.reviews` list always contains only unique reviews.

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

Every `scraper.fetch()` call returns a `FetchResult` object. This is what you get back:

| Property | What it contains |
|----------|-----------------|
| `result.reviews` | A list of `Review` objects, deduplicated and sorted newest-first. |
| `result.failures` | A list of fetch attempts that failed (e.g., a country that returned an error). |
| `result.warnings` | Non-fatal issues (e.g., unexpected data format in one response). |
| `result.stats` | Summary: total reviews, total countries, total failures, duration in seconds. |

Here is how to inspect it:

```python
result = scraper.fetch()

# The reviews
print(f"Reviews: {len(result.reviews)}")

# Any countries that failed
if result.failures:
    for f in result.failures:
        print(f"Failed: {f.country} -- {f.error}")

# Any non-fatal warnings
if result.warnings:
    for w in result.warnings:
        print(f"Warning: {w.message}")

# Timing and counts
print(f"Total countries: {result.stats.total_countries}")
print(f"Duration: {result.stats.duration_seconds:.1f}s")
```

A fetch can partially succeed. For example, if you request 5 countries and 1 fails, you still get reviews from the other 4. Check `result.failures` to see what went wrong.

---

## Next Steps

- [Python API](../guide/python-api.md) -- all parameters and options
- [CLI](../guide/cli.md) -- full command-line reference
- [Interactive TUI](../guide/tui.md) -- terminal UI walkthrough
- [Authentication](../guide/authentication.md) -- set up authenticated APIs for more data
- [Export Formats](../guide/export.md) -- JSON, JSONL, CSV export
