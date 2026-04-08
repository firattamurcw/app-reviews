# How It Works

What happens under the hood when you call `client.fetch()`.

---

## The Fetch Pipeline

1. **Resolve countries.** Normalize country codes to the provider's expected format.
2. **Select a provider.** If auth credentials are provided, use the official API. Otherwise, use the free scraper.
3. **Fetch from each country.** Send HTTP requests for each country in parallel using threads.
4. **Paginate.** Follow pagination cursors until all available pages are consumed.
5. **Filter and sort.** Apply date, rating, and sort filters to the collected reviews.
6. **Return.** Package everything into a `FetchResult` with reviews and any per-country errors.

---

## Provider Selection

The provider is selected automatically based on whether you provide auth credentials:

- **With auth** -- uses the official API (App Store Connect or Google Play Developer API).
- **Without auth** -- uses the free scraper (RSS feed or web scraper).

There is no manual provider override. If you pass credentials, you get the official API.

---

## Providers Overview

| | Apple App Store | Google Play |
|---|---|---|
| **Scraper (free)** | RSS feed. Public, no auth. Max ~500 recent reviews. | Web scraper. Public, no auth. Rate-limited by Google. |
| **Official (auth)** | App Store Connect API. Requires Apple Developer account + API key. | Google Play Developer API. Requires service account. |
| **Source value** | `appstore_scraper` / `appstore_official` | `googleplay_scraper` / `googleplay_official` |

---

## Data Sources

### Apple App Store -- RSS Feed (Scraper)

Public JSON feed. No authentication.

**Endpoint:** `https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/page={page}/json`

- Up to 50 reviews per page, paginates through all available pages.
- Returns: review ID, rating, title, body, author, app version, timestamps.
- **Limit:** ~500 most recent reviews per app per country.
- Rate limits are generous.

### Apple App Store -- App Store Connect API (Official)

Authenticated REST API for app developers.

**Endpoint:** `https://api.appstoreconnect.apple.com/v1/apps/{app_id}/customerReviews`

- Signs a JWT using your `.p8` private key (ES256).
- Higher limits and more metadata than the RSS feed.
- You can only access reviews for apps you own.
- Requires Apple Developer Program membership ($99/year).
- Rate limit: ~450 requests/minute.

### Google Play -- Web Scraper

Sends requests to Google Play's internal batch endpoint.

**Endpoint:** `https://play.google.com/_/PlayStoreUi/data/batchexecute`

- Up to 200 reviews per request, follows continuation tokens.
- Automatic exponential backoff on rate limits.
- Returns: review ID, rating, body, author, timestamps, app version, language.
- **Undocumented endpoint** -- can break if Google changes their internal API.
- Google Play reviews do not have titles.

### Google Play -- Developer API (Official)

Authenticated REST API (v3).

**Endpoint:** `https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{app_id}/reviews`

- Signs a JWT using service account key (RS256), exchanges for OAuth2 token.
- Structured pagination.
- You can only access reviews for apps you own.
- Requires Google Cloud + Google Play Developer account.
- Permissions can take up to 24 hours to propagate.

---

## Authentication Flow

### App Store Connect (ES256)

1. Read `.p8` private key.
2. Build JWT with Key ID and Issuer ID.
3. Sign with ES256.
4. Send as `Authorization: Bearer {token}`.
5. Fresh token per fetch operation.

### Google Play Developer API (RS256)

1. Read service account JSON, extract RSA private key.
2. Build JWT with `androidpublisher` scope.
3. Sign with RS256.
4. Exchange JWT for OAuth2 access token at `https://oauth2.googleapis.com/token`.
5. Send access token as `Authorization: Bearer {token}`.
6. Fresh token per fetch operation.

Private keys never leave your machine.

---

## HTTP Layer

All HTTP uses Python's built-in `urllib`. No third-party HTTP dependencies.

- **Retries** with configurable exponential backoff.
- **Timeouts** to prevent hanging requests.
- **Proxy support** via constructor parameter.

---

## Metadata Lookup

`lookup_metadata()` fetches app info without fetching reviews.

- **Apple:** iTunes Lookup API (`https://itunes.apple.com/lookup?id={app_id}`).
- **Google:** Parses the Google Play store page HTML.
- **Auto-detection:** Numeric IDs -> App Store, package names -> Google Play.
