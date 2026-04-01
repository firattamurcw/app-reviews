# CLI Reference

## fetch

Fetch App Store reviews for an app.

```bash
appstore-reviews fetch [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|---|---|---|---|
| `--app-id` | TEXT | *(required)* | App Store app ID or URL |
| `--country` | TEXT | `us` | Country code. Repeat for multiple countries |
| `--format` | CHOICE | `table` | Output format: `table`, `json`, `jsonl`, `csv` |
| `-o, --output` | PATH | stdout | Output file path |
| `--overwrite` | FLAG | `false` | Overwrite existing output file |
| `--include-raw` | FLAG | `false` | Include raw source payload in output |

### Examples

```bash
# Interactive table with rating distribution
appstore-reviews fetch --app-id 123456789

# Fetch from multiple countries
appstore-reviews fetch --app-id 123456789 --country us --country gb --country de

# Export as JSON to file
appstore-reviews fetch --app-id 123456789 --format json -o reviews.json

# Export as CSV
appstore-reviews fetch --app-id 123456789 --format csv -o reviews.csv

# JSONL for piping
appstore-reviews fetch --app-id 123456789 --format jsonl | jq '.rating'
```

When `--output` is specified with the default `table` format, the format automatically switches to `jsonl`.

## inspect

Show information about an app ID.

```bash
appstore-reviews inspect --app-id 123456789
```

Outputs the normalized app ID and its RSS URL. Useful for verifying an app ID or URL before fetching.

## config validate

Validate configuration parameters.

```bash
appstore-reviews config validate --app-id 123456789 --country us --country gb
```

Checks that the app ID and country codes are valid without making any network requests.
