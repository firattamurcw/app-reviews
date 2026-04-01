# How It Works

This page explains what happens under the hood when you call `scraper.fetch()`. It covers provider selection, each data source in detail, the deduplication algorithm, and known limitations.

---

## The Fetch Pipeline

When you call `fetch()`, the package runs through these steps in order:

1. **Validate inputs.** Check that you provided `app_id` or `app_ids` (not both, not neither). Normalize country codes.
2. **Select a provider.** Decide which data source to use based on the `provider` parameter and whether credentials are present.
3. **Fetch from each country.** Send HTTP requests to the chosen data source for each country in your list. Each country is fetched independently.
4. **Deduplicate.** The same review can appear in multiple country feeds. The package removes duplicates using a two-pass algorithm.
5. **Sort.** Reviews are sorted newest-first by `created_at`.
6. **Return.** Package everything into a `FetchResult` with the reviews, any failures, warnings, and statistics.

---

## Provider Selection

The `provider` parameter controls which data source the package uses. There are three values: `"auto"`, `"scraper"`, and `"official"`.

### How "auto" works

`"auto"` is the default. The package checks whether you provided authentication credentials:

- **Apple App Store:** If `key_id`, `issuer_id`, and `key_path` are all provided, it uses the official API (App Store Connect). If any one is missing, it falls back to the scraper (RSS feed).
- **Google Play:** If `service_account_path` is provided, it uses the official API (Developer API). Otherwise, it falls back to the scraper (web scraping).

### Forcing a provider

If you set `provider="scraper"`, the package always uses the free scraper, even if you provided credentials. This is useful for testing or when you want to avoid API quota usage.

If you set `provider="official"`, the package uses the authenticated API. If the required credentials are missing, it raises a `ValueError` immediately rather than silently falling back.

---

## Providers Overview

The package has four data sources -- two per store. Here is a comparison:

| | Apple App Store | Google Play |
|---|---|---|
| **Scraper (free)** | RSS feed. Public, no auth. Max ~500 recent reviews per app. | Web scraper. Public, no auth. Rate-limited by Google. |
| **Official (authenticated)** | App Store Connect API. Requires Apple Developer account + API key. Higher limits, more metadata. | Google Play Developer API. Requires Google Cloud service account. Structured pagination. |
| **Source value on Review** | `appstore_scraper` or `appstore_official` | `googleplay_scraper` or `googleplay_official` |

---

## Data Sources in Detail

### Apple App Store -- Scraper (RSS Feed)

**What it is:** Apple provides a public RSS feed that returns recent reviews for any app. No authentication required.

**Endpoint:** `https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/page={page}/json`

**How it works step by step:**

1. The package builds a URL for each country you specified.
2. It sends an HTTP GET request to the RSS feed endpoint.
3. The response is JSON containing up to 50 reviews per page.
4. The package paginates through all available pages by following the feed's pagination links.
5. Each review is parsed into a `Review` object with `source="appstore_scraper"`.

**What data you get:** Review ID, star rating (1-5), title, body text, author name, app version, and timestamps (created, updated).

**Rate limits:** Apple does not document rate limits for this endpoint. In practice, it is generous and rarely throttled.

**Limitations:**

- Returns only the most recent reviews. There is no way to request reviews from a specific date range.
- Maximum of roughly 500 reviews per app per country. For apps with thousands of reviews, you will only get the newest ones.
- No historical data. If a review was posted a year ago and has since been pushed out by newer reviews, you cannot retrieve it through this endpoint.

!!! warning "When to use"
    Use the scraper when you want a quick look at recent reviews, do not have an Apple Developer account, or do not want to deal with authentication setup. It is the simplest option and works for any app.

### Apple App Store -- Official API (App Store Connect)

**What it is:** Apple's authenticated REST API for app developers. Gives you access to customer reviews for apps you own or manage.

**Endpoint:** `https://api.appstoreconnect.apple.com/v1/apps/{app_id}/customerReviews`

**How it works step by step:**

1. The package reads your `.p8` private key file.
2. It builds a JWT with your Key ID and Issuer ID in the header, and signs it using the ES256 algorithm (ECDSA with P-256 and SHA-256).
3. The JWT is sent as a `Authorization: Bearer {token}` header.
4. The API returns paginated results. The package follows the `next` link in each response until all pages are consumed.
5. Each review is parsed into a `Review` object with `source="appstore_official"`.

**What data you get:** Everything the scraper provides, plus territory information and more reliable pagination.

**Rate limits:** Apple enforces rate limits on the Connect API (currently around 450 requests per minute). The package does not do anything special to handle this -- if you hit the limit, the request will fail and appear in `result.failures`.

**Limitations:**

- Requires an Apple Developer Program membership ($99/year).
- You can only access reviews for apps that belong to your developer account. You cannot use this to fetch reviews for other people's apps.
- Setup requires generating an API key in App Store Connect. See [Authentication](../guide/authentication.md).

!!! tip "When to use"
    Use the official API when you own the app and need more complete review data, higher limits, or more reliable pagination than the RSS feed provides.

### Google Play -- Scraper (Web)

**What it is:** The package sends requests to Google Play's internal batch endpoint, the same one the Google Play website uses to load reviews. No authentication required.

**Endpoint:** `https://play.google.com/_/PlayStoreUi/data/batchexecute`

**How it works step by step:**

1. The package builds a POST request with an RPC-encoded payload that requests reviews for the given app and country.
2. Google Play returns up to 200 reviews per request, along with a continuation token.
3. The package follows continuation tokens to paginate through more reviews.
4. If Google returns a rate-limit error (`PlayGatewayError`), the package backs off with exponential delays starting at 5 seconds and retries.
5. Each review is parsed into a `Review` object with `source="googleplay_scraper"`.

**What data you get:** Review ID, star rating (1-5), body text, author name, timestamps, app version, and language.

**Rate limits:** Google rate-limits this endpoint aggressively. The package handles this with automatic exponential backoff, but heavy usage (many apps, many countries, rapid fetching) may still hit walls.

**Limitations:**

- This is an **undocumented internal endpoint**. Google can change it at any time without notice, which would break the scraper until the package is updated.
- Rate limiting can slow down large fetches significantly. Fetching from many countries for a popular app might take minutes due to backoff delays.
- Google Play reviews do not have titles (unlike App Store reviews). The `title` field will be empty.
- Sort options are limited to what Google's internal API supports: newest, most relevant, or by rating.

!!! warning "When to use"
    Use the scraper when you want reviews for any app without authentication. Be aware that it depends on an undocumented endpoint and may break or be slow under heavy use.

### Google Play -- Official API (Developer API)

**What it is:** Google's authenticated REST API for app developers. Part of the Google Play Developer API (v3).

**Endpoint:** `https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{app_id}/reviews`

**How it works step by step:**

1. The package reads your service account JSON file and extracts the RSA private key.
2. It builds a JWT requesting the `https://www.googleapis.com/auth/androidpublisher` scope and signs it using RS256 (RSA with SHA-256).
3. The JWT is POSTed to `https://oauth2.googleapis.com/token` to exchange it for an OAuth2 access token.
4. The access token is sent as a `Authorization: Bearer {token}` header in requests to the reviews endpoint.
5. The API returns paginated results. The package follows pagination tokens until all pages are consumed.
6. Each review is parsed into a `Review` object with `source="googleplay_official"`.

**What data you get:** Review ID, star rating, body text, author name, timestamps, and language.

**Rate limits:** Google enforces quota limits on the Developer API. The default quota is generous for most use cases.

**Limitations:**

- Requires a Google Cloud account and a Google Play Developer account.
- You can only access reviews for apps that belong to your developer account.
- Setup involves creating a service account, enabling the API, and linking the account in Google Play Console. See [Authentication](../guide/authentication.md).
- After granting permissions in Google Play Console, it can take up to 24 hours for them to take effect.

!!! tip "When to use"
    Use the official API when you own the app and want structured, reliable access without depending on web scraping.

---

## Deduplication

When you fetch from multiple countries, the same review often appears in more than one country's results. The package removes duplicates using a two-pass algorithm.

### Pass 1: Exact Key Match

Every review has a `canonical_key` field formatted as `{store}:{source_review_id}`. Two reviews with the same canonical key are the same review. When duplicates are found, the package keeps the one from the higher-priority source.

**Source priority (lower number wins):**

| Priority | Source | Description |
|----------|--------|-------------|
| 1 | `appstore_official` | App Store Connect API |
| 2 | `googleplay_official` | Google Play Developer API |
| 3 | `appstore_scraper` | App Store RSS feed |
| 4 | `googleplay_scraper` | Google Play web scraper |

Official sources are preferred because they tend to have more complete and reliable data.

### Pass 2: Fuzzy Match

Sometimes the same review has different IDs across sources (e.g., if the same review is fetched via both the scraper and the official API). The package catches these by checking if all four of these conditions match:

- Same `app_id`
- Same `author_name`
- Same `rating`
- `created_at` timestamps within **60 seconds** of each other

If all four match, the reviews are considered duplicates and the higher-priority source is kept.

### After Deduplication

Reviews are sorted **newest first** by `created_at`. The final list is what you get in `result.reviews`.

---

## Authentication Flow

### App Store Connect (ES256)

1. Read the `.p8` private key file from disk.
2. Build a JWT payload with the Key ID in the header and Issuer ID in the claims.
3. Sign the JWT with ES256 (ECDSA using P-256 and SHA-256).
4. Attach the signed token as `Authorization: Bearer {token}` on each API request.
5. A fresh token is generated for each fetch operation. No caching or refresh logic.

### Google Play Developer API (RS256)

1. Read the service account JSON file from disk.
2. Extract the RSA private key from the `private_key` field.
3. Build a JWT requesting the `https://www.googleapis.com/auth/androidpublisher` scope.
4. Sign the JWT with RS256 (RSA using SHA-256).
5. POST the signed JWT to `https://oauth2.googleapis.com/token` to exchange it for an OAuth2 access token.
6. Attach the access token as `Authorization: Bearer {token}` on each API request.
7. A fresh token is generated for each fetch operation. No caching or refresh logic.

In both cases, your private keys never leave your machine. They are only used locally to sign tokens.

---

## HTTP Layer

All HTTP requests use Python's built-in `urllib` module. There are no third-party HTTP dependencies (`requests`, `httpx`, etc.).

The package provides:

- **Retries** with configurable exponential backoff for transient failures.
- **Timeouts** to prevent requests from hanging indefinitely.
- **Proxy support** via standard HTTP proxy environment variables.

---

## Metadata Lookup

The `lookup_metadata()` function fetches app information without fetching reviews. It is used by the TUI to display app details before fetching, and you can use it directly.

**Apple App Store:** Calls the iTunes Lookup API (`https://itunes.apple.com/lookup?id={app_id}`). Returns structured JSON with the app's name, developer, category, price, version, rating, and URL.

**Google Play:** Fetches the app's store page (`https://play.google.com/store/apps/details?id={app_id}`) and parses the HTML to extract metadata. This is less reliable than the Apple endpoint since it depends on Google's page structure.

**Store auto-detection:** The store is detected from the ID format:

- Numeric IDs (like `123456789`) are treated as Apple App Store.
- Package names (like `com.example.app`) are treated as Google Play.
- You can also specify the store explicitly with the `store` parameter.
