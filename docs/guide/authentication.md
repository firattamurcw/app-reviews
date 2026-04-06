# Authentication

Both stores work **without any authentication**. The default providers use public endpoints and require no setup.

If you need higher rate limits or more complete data, you can set up authenticated access using the official store APIs. This page walks through the setup for each store.

---

## Apple App Store Connect API

The official API gives you access to all reviews with higher rate limits and more metadata than the public RSS feed.

### What You Need

- An [Apple Developer Program](https://developer.apple.com/programs/) membership ($99/year)
- An API key from App Store Connect
- Three pieces of information: **Key ID**, **Issuer ID**, and a **`.p8` private key file**

### Step-by-Step Setup

**Step 1: Open App Store Connect**

Go to [App Store Connect](https://appstoreconnect.apple.com/) and sign in with your Apple Developer account.

**Step 2: Navigate to API Keys**

Go to **Users and Access** in the top menu, then click the **Keys** tab. If you don't see this tab, you may need the Admin or Account Holder role.

**Step 3: Generate a New Key**

Click the **+** button to create a new API key. Give it a name (like "App Reviews") and select the appropriate access level.

After creating the key, you will see two values on the page:

- **Key ID** -- a short alphanumeric string (like `ABC123DEF4`)
- **Issuer ID** -- a UUID (like `12345678-1234-1234-1234-123456789012`)

Copy both of these. You will need them.

**Step 4: Download the Private Key**

Click **Download API Key** to get the `.p8` file. This file contains your private key.

!!! warning "Download it now"
    You can only download the `.p8` file **once**. If you lose it, you will need to create a new key.

Save it somewhere safe, like `~/.appstore-keys/AuthKey_ABC123DEF4.p8`.

**Step 5: Use the Credentials**

Pass the credentials to `AppStoreReviews` via `AppStoreAuth`:

```python
from app_reviews import AppStoreReviews, AppStoreAuth, Country

client = AppStoreReviews(
    auth=AppStoreAuth(
        key_id="ABC123DEF4",
        issuer_id="12345678-1234-1234-1234-123456789012",
        key_path="/path/to/AuthKey_ABC123DEF4.p8",
    )
)

result = client.fetch("123456789", countries=[Country.US, Country.GB])
```

### No Auth (Public RSS Feed)

If you do not provide `auth`, the client automatically uses the public RSS feed:

```python
from app_reviews import AppStoreReviews

# No auth — uses public RSS feed
client = AppStoreReviews()
result = client.fetch("123456789")
```

### How It Works

The package uses your `.p8` private key to sign a JWT (JSON Web Token) using the ES256 algorithm. This token is sent as a Bearer token in the `Authorization` header of each request to the App Store Connect API.

Tokens are short-lived and generated fresh for each fetch operation. Your private key never leaves your machine.

---

## Google Play Developer API

The official API gives you access to reviews through Google's authenticated endpoint, with pagination support and structured data.

### What You Need

- A [Google Cloud](https://console.cloud.google.com/) account
- A Google Play Developer account linked to your Google Cloud project
- A **service account JSON key file**

### Step-by-Step Setup

**Step 1: Open Google Cloud Console**

Go to [Google Cloud Console](https://console.cloud.google.com/) and select your project (or create a new one).

**Step 2: Enable the Google Play Developer API**

Go to **APIs & Services** > **Library**, search for "Google Play Android Developer API", and click **Enable**.

**Step 3: Create a Service Account**

Go to **APIs & Services** > **Credentials**, click **Create Credentials** > **Service Account**.

Give it a name (like "app-reviews") and click through the wizard. You do not need to grant it any Google Cloud roles -- the permissions come from the Google Play Console side.

**Step 4: Download the Key File**

After creating the service account, click on it, go to the **Keys** tab, and click **Add Key** > **Create New Key** > **JSON**.

This downloads a JSON file. Save it somewhere safe, like `~/.google-keys/service-account.json`.

**Step 5: Link to Google Play Console**

Go to the [Google Play Console](https://play.google.com/console/), then **Settings** > **API access**. Find your service account and click **Grant access**. Give it at least **View app information and download bulk reports** permission.

!!! note "Propagation delay"
    After granting access, it can take up to 24 hours for the permissions to take effect.

**Step 6: Use the Credentials**

Pass the credentials to `GooglePlayReviews` via `GooglePlayAuth`:

```python
from app_reviews import GooglePlayReviews, GooglePlayAuth, Country

client = GooglePlayReviews(
    auth=GooglePlayAuth(
        service_account_path="/path/to/service-account.json",
    )
)

result = client.fetch("com.example.app", countries=[Country.US, Country.GB])
```

### No Auth (Public Web Endpoint)

If you do not provide `auth`, the client automatically uses the public web endpoint:

```python
from app_reviews import GooglePlayReviews

# No auth — uses public web endpoint
client = GooglePlayReviews()
result = client.fetch("com.example.app")
```

### How It Works

The package reads your service account JSON file, extracts the RSA private key, and signs a JWT using the RS256 algorithm. This JWT is exchanged for an OAuth2 access token via Google's token endpoint.

The access token is then used as a Bearer token in requests to the Google Play Developer API. Tokens are generated fresh for each fetch operation. Your private key never leaves your machine.
