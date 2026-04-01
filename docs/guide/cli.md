# CLI Reference

The `app-reviews` command-line tool has two commands: `fetch` and `info`.

---

## fetch

Fetches reviews for an app and outputs them in the format you choose.

```bash
app-reviews fetch [APP_ID] [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `APP_ID` | An App Store ID (like `123456789`), a Google Play package name (like `com.example.app`), or a full store URL. The store is auto-detected from the format. |

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--country` | `-c` | Country code to fetch from. Can be repeated to fetch from multiple countries. | `us` |
| `--format` | `-f` | Output format: `table`, `json`, `jsonl`, or `csv`. | `table` |
| `--rating` | `-r` | Filter reviews by rating: `all`, `1-2`, `3`, or `4-5`. | `all` |
| `--sort` | `-s` | Sort order: `newest`, `oldest`, `highest`, or `lowest`. | `newest` |
| `--limit` | `-l` | Maximum number of reviews to return. | No limit |
| `--output` | `-o` | Write output to a file instead of printing to the terminal. | Prints to stdout |
| `--overwrite` | | Overwrite the output file if it already exists. | `false` |
| `--include-raw` | | Include the raw API response in each review (JSON and JSONL only). | `false` |
| `--no-interactive` | | Disable the interactive TUI. Always output directly. | `false` |

### Examples

**Fetch reviews with default settings (table format, US only):**

```bash
app-reviews fetch 123456789
```

**Fetch from multiple countries:**

```bash
app-reviews fetch 123456789 -c us -c gb -c de -c fr
```

**Output as JSON:**

```bash
app-reviews fetch 123456789 -f json
```

**Filter to only 1-star and 2-star reviews:**

```bash
app-reviews fetch 123456789 -r 1-2
```

**Sort by oldest first and limit to 50:**

```bash
app-reviews fetch 123456789 -s oldest -l 50
```

**Save to a CSV file:**

```bash
app-reviews fetch 123456789 -f csv -o reviews.csv
```

**Overwrite an existing file:**

```bash
app-reviews fetch 123456789 -f csv -o reviews.csv --overwrite
```

**Include raw API response in JSON output:**

```bash
app-reviews fetch 123456789 -f json --include-raw
```

**Use a full App Store URL instead of an ID:**

```bash
app-reviews fetch "https://apps.apple.com/us/app/example/id123456789"
```

**Use a Google Play URL:**

```bash
app-reviews fetch "https://play.google.com/store/apps/details?id=com.example.app"
```

### Interactive TUI

When you run `fetch` without the `--format`, `--output`, or `--no-interactive` flags, the interactive TUI launches automatically (if installed). See the [TUI guide](tui.md) for details.

---

## info

Looks up metadata for an app and prints it. This does not fetch reviews -- it only shows app information.

```bash
app-reviews info APP_ID
```

### Arguments

| Argument | Description |
|----------|-------------|
| `APP_ID` | An App Store ID, a Google Play package name, or a full store URL. |

### Output

The command prints:

- **Name** -- the app's display name
- **Developer** -- the developer or publisher
- **Category** -- the app's primary category
- **Price** -- the app's price (or "Free")
- **Version** -- the current version number
- **Rating** -- the average star rating
- **Rating Count** -- the total number of ratings
- **URL** -- the app's store page URL

### Examples

**Look up an App Store app:**

```bash
app-reviews info 123456789
```

**Look up a Google Play app:**

```bash
app-reviews info com.example.app
```

**Use a full URL:**

```bash
app-reviews info "https://apps.apple.com/us/app/example/id123456789"
```
