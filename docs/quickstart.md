# Quickstart

## Installation

```bash
pip install appstore-reviews
```

Or with uv:

```bash
uv add appstore-reviews
```

## Fetch reviews (Python)

```python
from appstore_reviews import AppStoreScraper

scraper = AppStoreScraper(
    app_id="123456789",
    countries=["us", "gb", "de"],
)

result = scraper.fetch()

print(f"Fetched {result.stats.total_reviews} reviews")

for review in result.reviews:
    print(f"[{review.country}] {review.rating}* {review.title}")
    print(f"  {review.body[:80]}")
```

## Async usage

```python
from appstore_reviews import AsyncAppStoreScraper

scraper = AsyncAppStoreScraper(app_id="123456789", countries=["us", "gb"])
result = await scraper.fetch()

for review in result.reviews:
    print(review.title)
```

## Multiple apps

Pass `app_ids` to fetch reviews for multiple apps at once:

```python
scraper = AppStoreScraper(
    app_ids=["123456789", "987654321"],
    countries=["us"],
)
result = scraper.fetch()
```

## Handling failures

Failed requests are captured in `result.failures` instead of raising exceptions:

```python
result = scraper.fetch()

for failure in result.failures:
    print(f"Failed: {failure.app_id}/{failure.country} - {failure.error}")
```

## CLI

Fetch reviews from the command line:

```bash
# Pretty table output (default)
appstore-reviews fetch --app-id 123456789

# Multiple countries
appstore-reviews fetch --app-id 123456789 --country us --country gb

# Export as JSON
appstore-reviews fetch --app-id 123456789 --format json

# Save to file
appstore-reviews fetch --app-id 123456789 --format csv -o reviews.csv
```

See the [CLI reference](cli.md) for all options.
