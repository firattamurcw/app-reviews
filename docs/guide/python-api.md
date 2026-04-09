# Python API

Four main classes -- two for reviews, two for search and lookup. All follow the same pattern: create a client, call a method.

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

### Review

`fetch()` returns a `FetchResult` containing `Review` objects -- frozen dataclasses with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique review identifier |
| `store` | `Store` | `"appstore"` or `"googleplay"` |
| `app_id` | `str` | App Store ID or package name |
| `country` | `str` | Two-letter country code |
| `rating` | `int` | Star rating (`1` -- `5`) |
| `title` | `str` | Review title (may be empty for Google Play) |
| `body` | `str` | Review text |
| `author_name` | `str` | Reviewer display name |
| `app_version` | `str \| None` | App version at time of review |
| `created_at` | `datetime` | When the review was posted |
| `updated_at` | `datetime \| None` | When the review was last edited |
| `is_edited` | `bool` | Whether the review was edited |
| `source` | `Source` | Provider (e.g. `"appstore_scraper"`, `"googleplay_official"`) |
| `language` | `str \| None` | Review language code |
| `fetched_at` | `datetime \| None` | When the review was fetched |
| `raw` | `dict \| None` | Raw API response payload |

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

## App Search & Lookup

Search for apps by keyword and look up app metadata by ID. No authentication required.

### AppStoreSearch

```python
from app_reviews import AppStoreSearch, Country
```

```python
client = AppStoreSearch(
    proxy=None,      # str | None -- HTTP proxy URL
    retry=None,      # RetryConfig | None -- retry settings
)
```

#### search()

```python
results = client.search(
    "fitness tracker",       # str -- search query
    country=Country.US,      # Country -- store region (default: US)
    limit=50,                # int -- max results (default: 50)
)
# returns list[AppMetadata]
```

#### lookup()

```python
app = client.lookup(
    "com.whatsapp.WhatsApp", # str -- bundle ID
    country=Country.US,      # Country -- store region (default: US)
)
# returns AppMetadata | None
```

### GooglePlaySearch

```python
from app_reviews import GooglePlaySearch, Country
```

```python
client = GooglePlaySearch(
    proxy=None,      # str | None -- HTTP proxy URL
    retry=None,      # RetryConfig | None -- retry settings
)
```

Same `search()` and `lookup()` methods as `AppStoreSearch`. For lookup, pass a package name (e.g. `"com.whatsapp"`).

### AppMetadata

Both `search()` and `lookup()` return `AppMetadata` -- a frozen dataclass with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `app_id` | `str` | Bundle ID (App Store) or package name (Google Play) |
| `store` | `Store` | `"appstore"` or `"googleplay"` |
| `name` | `str` | App display name |
| `developer` | `str` | Developer or publisher name |
| `category` | `str` | Primary category (e.g. `"Social Networking"`) |
| `price` | `str` | Formatted price (e.g. `"Free"`, `"$4.99"`) |
| `version` | `str` | Current version string |
| `rating` | `float` | Average star rating (`0.0` -- `5.0`) |
| `rating_count` | `int` | Total number of ratings |
| `url` | `str` | Store page URL |
| `icon_url` | `str \| None` | App icon image URL |

> **Note:** Google Play search results may have `"Unknown"` for `category`, `price`, `version` and `0` for `rating_count` since these aren't available from the search endpoint. Use `lookup()` for full metadata.

### Examples

```python
from app_reviews import AppStoreSearch, GooglePlaySearch, Country

# Search App Store
results = AppStoreSearch().search("weather", country=Country.GB, limit=5)
for app in results:
    print(f"{app.name} by {app.developer} ({app.rating}*)")

# Search Google Play
results = GooglePlaySearch().search("weather", country=Country.US, limit=5)
for app in results:
    print(f"{app.name} -- {app.icon_url}")

# Look up a specific app, then fetch its reviews
from app_reviews import GooglePlayReviews
app = GooglePlaySearch().lookup("com.whatsapp")
if app:
    reviews = GooglePlayReviews().fetch(app.app_id, countries=[Country.US])
    print(f"{app.name}: {len(reviews)} reviews")
```

---

## Legacy Metadata Lookup

The `lookup_metadata` utility is still available for quick lookups:

```python
from app_reviews.utils.metadata import lookup_metadata

metadata = lookup_metadata("123456789")  # auto-detects store
metadata = lookup_metadata("com.example.app", store="googleplay")
```

For new code, prefer `AppStoreSearch.lookup()` and `GooglePlaySearch.lookup()` which return richer data including `icon_url`.
