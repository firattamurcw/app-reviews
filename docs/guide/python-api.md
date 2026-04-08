# Python API

Two main classes: `AppStoreReviews` and `GooglePlayReviews`. Both follow the same pattern -- create a client, then call `fetch()`.

---

## AppStoreReviews

```python
from app_reviews import AppStoreReviews, AppStoreAuth
```

### Constructor

```python
client = AppStoreReviews(
    auth=None,       # AppStoreAuth | None -- credentials for App Store Connect API
    proxy=None,      # str | None -- HTTP proxy URL
    retry=None,      # RetryConfig | None -- retry settings
)
```

Without `auth`, uses the public RSS feed. With `auth`, uses the App Store Connect API.

### fetch()

```python
result = client.fetch(
    app_id,          # str -- App Store ID (numeric)
    countries=None,  # list[str] | None -- country codes (default: ["us"])
    since=None,      # date | None -- only reviews on or after this date
    until=None,      # date | None -- only reviews on or before this date
    ratings=None,    # list[int] | None -- filter to specific star ratings
    sort=Sort.NEWEST,# Sort -- sort order
    limit=None,      # int | None -- max reviews to return
)
```

### AppStoreAuth

```python
auth = AppStoreAuth(
    key_id="ABC123DEF4",
    issuer_id="12345678-1234-1234-1234-123456789012",
    key_path="/path/to/AuthKey_ABC123DEF4.p8",
)
```

### Examples

```python
# No auth (public RSS feed)
client = AppStoreReviews()
result = client.fetch("123456789")

# Multiple countries
from app_reviews import Country
result = client.fetch("123456789", countries=[Country.US, Country.GB, Country.DE])

# With auth
client = AppStoreReviews(
    auth=AppStoreAuth(
        key_id="ABC123DEF4",
        issuer_id="12345678-1234-1234-1234-123456789012",
        key_path="/path/to/AuthKey.p8",
    )
)
result = client.fetch("123456789", countries=[Country.US, Country.GB])

# Reuse client
spotify = client.fetch("324684580", countries=[Country.US, Country.GB])
instagram = client.fetch("389801252", countries=[Country.US])
twitter = client.fetch("333903271", ratings=[1, 2])

# Filter by date and rating
from datetime import date
result = client.fetch("123456789", ratings=[1, 2], since=date(2025, 1, 1))
```

---

## GooglePlayReviews

```python
from app_reviews import GooglePlayReviews, GooglePlayAuth
```

### Constructor

```python
client = GooglePlayReviews(
    auth=None,       # GooglePlayAuth | None -- credentials for Developer API
    proxy=None,      # str | None -- HTTP proxy URL
    retry=None,      # RetryConfig | None -- retry settings
)
```

Without `auth`, uses the public web endpoint. With `auth`, uses the Google Play Developer API.

### fetch()

Same parameters as `AppStoreReviews.fetch()`, except `app_id` is a package name (e.g. `"com.example.app"`).

### GooglePlayAuth

```python
auth = GooglePlayAuth(
    service_account_path="/path/to/service-account.json",
)
```

### Examples

```python
# No auth
client = GooglePlayReviews()
result = client.fetch("com.example.app")

# With auth
from app_reviews import Sort
client = GooglePlayReviews(
    auth=GooglePlayAuth(service_account_path="/path/to/service-account.json")
)
result = client.fetch("com.example.app", countries=[Country.US], sort=Sort.NEWEST, limit=100)
```

---

## Country Enum

`Country` is a `StrEnum` -- values are two-letter country codes.

```python
from app_reviews import Country

Country.US   # "us"
Country.GB   # "gb"
Country.DE   # "de"
```

**Region groups:**

| Group | Description |
|-------|-------------|
| `Country.ALL` | All 155 supported countries |
| `Country.EUROPE` | European countries |
| `Country.AMERICAS` | North and South America |
| `Country.ASIA_PACIFIC` | Asia-Pacific region |
| `Country.MIDDLE_EAST` | Middle East and North Africa |
| `Country.ENGLISH_SPEAKING` | English-speaking countries |

Plain strings also work: `countries=["us", "gb"]`.

---

## Sort Enum

```python
from app_reviews import Sort

Sort.NEWEST   # most recent first (default)
Sort.OLDEST   # oldest first
Sort.RATING   # highest rated first
```

---

## Working with Results

### Iterate, count, and check

```python
result = client.fetch("123456789")

for review in result:
    print(review.title)

print(f"Reviews: {len(result)}")

if result:
    print("Got reviews!")
```

### Filter after fetching

```python
from datetime import date

bad_recent = result.filter(ratings=[1, 2], since=date(2025, 1, 1))
```

### Check errors

```python
if result.errors:
    for err in result.errors:
        print(f"Failed: {err.country} -- {err.message}")
```

### Export

```python
# List of plain dicts
records = result.to_dicts()
```

### Review fields

```python
for review in result:
    review.id            # unique identifier
    review.store         # "appstore" or "googleplay"
    review.app_id        # app ID or package name
    review.country       # two-letter country code
    review.rating        # 1 to 5
    review.title         # may be empty for Google Play
    review.body          # review text
    review.author_name   # display name
    review.app_version   # may be None
    review.created_at    # datetime
    review.updated_at    # datetime or None
    review.is_edited     # bool
    review.source        # e.g. "appstore_scraper"
    review.language      # e.g. "en" or None
    review.fetched_at    # datetime or None
    review.raw           # raw API payload or None
```

### Error handling

`fetch()` does not raise on partial failures. Check `result.errors`:

```python
result = client.fetch("123456789")

if not result and result.errors:
    print("All fetches failed:")
    for err in result.errors:
        print(f"  {err.country}: {err.message}")
elif result.errors:
    print(f"Got {len(result)} reviews, but some countries failed:")
    for err in result.errors:
        print(f"  {err.country}: {err.message}")
```

---

## Look Up App Metadata

```python
from app_reviews.utils.metadata import lookup_metadata

metadata = lookup_metadata("123456789")  # auto-detects store

metadata.name          # app name
metadata.developer     # developer name
metadata.category      # primary category
metadata.price         # "Free" or "$4.99"
metadata.version       # current version
metadata.rating        # average star rating
metadata.rating_count  # total ratings
metadata.url           # store page URL
```

Specify store explicitly:

```python
metadata = lookup_metadata("com.example.app", store="googleplay")
```
