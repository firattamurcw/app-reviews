# Export Formats

App Reviews supports three export formats: **JSON**, **JSONL**, and **CSV**.

---

## Formats at a Glance

| Format | Best For |
|--------|----------|
| **JSON** | Programmatic use, API responses, structured data |
| **JSONL** | Streaming, large datasets, line-by-line processing |
| **CSV** | Spreadsheets, data analysis, importing into other tools |

---

## JSON

Exports reviews as a JSON array.

```python
from app_reviews import AppStoreReviews
from app_reviews.exporters.json import export_json

client = AppStoreReviews()
result = client.fetch("123456789")

# Get JSON string
json_text = export_json(result.reviews)

# Write to file
export_json(result.reviews, output="reviews.json")

# Overwrite existing file
export_json(result.reviews, output="reviews.json", overwrite=True)

# Include raw API payload
export_json(result.reviews, output="reviews.json", include_raw=True)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reviews` | `list[Review]` | Required | Reviews to export. |
| `output` | `str`, `Path`, or `None` | `None` | File path. If `None`, only returns the string. |
| `overwrite` | `bool` | `False` | Overwrite if file exists. |
| `include_raw` | `bool` | `False` | Include raw API response per review. |

### Output Structure

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

Exports reviews as newline-delimited JSON. Each line is one review. Useful for streaming and large datasets.

```python
from app_reviews import AppStoreReviews
from app_reviews.exporters.jsonl import export_jsonl

client = AppStoreReviews()
result = client.fetch("123456789")

# Get JSONL string
jsonl_text = export_jsonl(result.reviews)

# Write to file
export_jsonl(result.reviews, output="reviews.jsonl")

# Include raw API payload
export_jsonl(result.reviews, output="reviews.jsonl", include_raw=True)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reviews` | `list[Review]` | Required | Reviews to export. |
| `output` | `str`, `Path`, or `None` | `None` | File path. If `None`, only returns the string. |
| `overwrite` | `bool` | `False` | Overwrite if file exists. |
| `include_raw` | `bool` | `False` | Include raw API response per review. |

### Output Structure

```
{"store": "appstore", "id": "12345", "rating": 5, "title": "Great app", ...}
{"store": "appstore", "id": "12346", "rating": 3, "title": "OK", ...}
```

---

## CSV

Exports reviews as a standard CSV file with headers.

```python
from app_reviews import AppStoreReviews
from app_reviews.exporters.csv import export_csv

client = AppStoreReviews()
result = client.fetch("123456789")

# Get CSV string
csv_text = export_csv(result.reviews)

# Write to file
export_csv(result.reviews, output="reviews.csv")
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reviews` | `list[Review]` | Required | Reviews to export. |
| `output` | `str`, `Path`, or `None` | `None` | File path. If `None`, only returns the string. |
| `overwrite` | `bool` | `False` | Overwrite if file exists. |

### CSV Columns

`id`, `app_id`, `country`, `language`, `rating`, `title`, `body`, `author_name`, `app_version`, `created_at`, `updated_at`, `is_edited`, `source`, `fetched_at`

!!! note
    CSV does not support `include_raw`. The raw API payload is excluded because it contains nested JSON that doesn't fit the flat CSV format.
