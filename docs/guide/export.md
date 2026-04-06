# Export Formats

App Reviews supports four export formats: **table**, **JSON**, **JSONL**, and **CSV**. You can export from the CLI or from Python.

---

## Formats at a Glance

| Format | Best For | File Support |
|--------|----------|--------------|
| **Table** | Quick terminal viewing. Human-readable with a rating distribution summary. | Terminal only, not file export. |
| **JSON** | Programmatic use, API responses, storing structured data. | Yes |
| **JSONL** | Streaming, large datasets, line-by-line processing. | Yes |
| **CSV** | Spreadsheets, data analysis, importing into other tools. | Yes |

---

## Table

The default format. Prints a human-readable table with a rating distribution bar at the top.

### CLI

```bash
app-reviews fetch 123456789
app-reviews fetch 123456789 -f table
```

!!! note
    Table format is for terminal display only. It cannot be written to a file with `--output`. Use JSON, JSONL, or CSV for file export.

---

## JSON

Exports reviews as a JSON array. Each review is a JSON object.

### CLI

```bash
# Print to terminal
app-reviews fetch 123456789 -f json

# Save to file
app-reviews fetch 123456789 -f json -o reviews.json

# Include the raw API response in each review
app-reviews fetch 123456789 -f json --include-raw -o reviews.json
```

### Python

```python
from app_reviews import AppStoreReviews
from app_reviews.exporters.json import export_json

client = AppStoreReviews()
result = client.fetch("123456789")

# Get JSON as a string
json_text = export_json(list(result))
print(json_text)

# Write to a file
export_json(list(result), output="reviews.json")

# Overwrite an existing file
export_json(list(result), output="reviews.json", overwrite=True)

# Include the raw API response payload
export_json(list(result), output="reviews.json", include_raw=True)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reviews` | `list[Review]` | Required | The list of reviews to export. |
| `output` | `str`, `Path`, or `None` | `None` | File path to write to. If `None`, only returns the string. |
| `overwrite` | `bool` | `False` | If `True`, overwrite the file if it exists. If `False`, raise `FileExistsError`. |
| `include_raw` | `bool` | `False` | If `True`, include the `raw` field (the raw API response) in each review. |

### Output Structure

The output is a JSON array:

```json
[
  {
    "store": "appstore",
    "id": "12345",
    "app_id": "123456789",
    "country": "us",
    "rating": 5,
    "title": "Great app",
    "body": "Love this app!",
    "author_name": "John",
    "created_at": "2025-01-15 10:30:00",
    "source": "appstore_scraper",
    "fetched_at": "2025-01-20 08:00:00",
    "language": null,
    "app_version": "2.1.0",
    "updated_at": null,
    "is_edited": false
  }
]
```

---

## JSONL

Exports reviews as newline-delimited JSON. Each line is one review as a complete JSON object. This format is useful for streaming and processing large datasets line by line, since you do not need to parse the entire file into memory.

### CLI

```bash
# Print to terminal
app-reviews fetch 123456789 -f jsonl

# Save to file
app-reviews fetch 123456789 -f jsonl -o reviews.jsonl

# Include raw API response
app-reviews fetch 123456789 -f jsonl --include-raw -o reviews.jsonl
```

### Python

```python
from app_reviews import AppStoreReviews
from app_reviews.exporters.jsonl import export_jsonl

client = AppStoreReviews()
result = client.fetch("123456789")

# Get JSONL as a string
jsonl_text = export_jsonl(list(result))
print(jsonl_text)

# Write to a file
export_jsonl(list(result), output="reviews.jsonl")

# Overwrite an existing file
export_jsonl(list(result), output="reviews.jsonl", overwrite=True)

# Include raw API response
export_jsonl(list(result), output="reviews.jsonl", include_raw=True)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reviews` | `list[Review]` | Required | The list of reviews to export. |
| `output` | `str`, `Path`, or `None` | `None` | File path to write to. If `None`, only returns the string. |
| `overwrite` | `bool` | `False` | If `True`, overwrite the file if it exists. If `False`, raise `FileExistsError`. |
| `include_raw` | `bool` | `False` | If `True`, include the `raw` field in each review. |

### Output Structure

Each line is a complete JSON object:

```
{"store": "appstore", "id": "12345", "rating": 5, "title": "Great app", ...}
{"store": "appstore", "id": "12346", "rating": 3, "title": "OK", ...}
{"store": "appstore", "id": "12347", "rating": 1, "title": "Crashes", ...}
```

Returns an empty string if the review list is empty.

---

## CSV

Exports reviews as a standard CSV file with headers.

### CLI

```bash
# Print to terminal
app-reviews fetch 123456789 -f csv

# Save to file
app-reviews fetch 123456789 -f csv -o reviews.csv
```

### Python

```python
from app_reviews import AppStoreReviews
from app_reviews.exporters.csv import export_csv

client = AppStoreReviews()
result = client.fetch("123456789")

# Get CSV as a string
csv_text = export_csv(list(result))
print(csv_text)

# Write to a file
export_csv(list(result), output="reviews.csv")

# Overwrite an existing file
export_csv(list(result), output="reviews.csv", overwrite=True)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reviews` | `list[Review]` | Required | The list of reviews to export. |
| `output` | `str`, `Path`, or `None` | `None` | File path to write to. If `None`, only returns the string. |
| `overwrite` | `bool` | `False` | If `True`, overwrite the file if it exists. If `False`, raise `FileExistsError`. |

### CSV Columns

The CSV includes these columns in this order:

| Column | Description |
|--------|-------------|
| `id` | Unique review identifier |
| `app_id` | App ID or package name |
| `country` | Two-letter country code |
| `language` | Review language (if available) |
| `rating` | Star rating (1-5) |
| `title` | Review title |
| `body` | Review text |
| `author_name` | Author display name |
| `app_version` | App version reviewed (if available) |
| `created_at` | When the review was posted |
| `updated_at` | When the review was last edited (if available) |
| `is_edited` | Whether the review was edited (`True` or `False`) |
| `source` | Data source (`appstore_scraper`, `appstore_official`, `googleplay_scraper`, or `googleplay_official`) |
| `fetched_at` | When the review was fetched |

!!! note
    CSV does not support the `--include-raw` option. The raw API payload (`raw`) is excluded from CSV output because it contains nested JSON that does not fit the flat CSV format.
