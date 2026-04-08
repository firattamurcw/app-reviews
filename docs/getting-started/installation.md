# Installation

## Requirements

- **Python 3.11** or higher

---

## Install with pip

```bash
pip install app-reviews
```

## Install with uv

```bash
uv add app-reviews
```

---

## Install with the TUI

The interactive terminal UI requires the [Textual](https://textual.textualize.io/) library:

```bash
pip install app-reviews[tui]
```

Or with uv:

```bash
uv add "app-reviews[tui]"
```

---

## Install from Source

```bash
git clone https://github.com/firattamurcw/app-reviews.git
cd app-reviews
uv sync
```

To also install development tools:

```bash
uv sync --group dev
```

---

## Verify the Installation

```bash
python -c "from app_reviews import AppStoreReviews; print('OK')"
```

---

## Dependencies

One runtime dependency:

| Package | Purpose |
|---------|---------|
| `cryptography` | JWT signing for authenticated API access |

The TUI extra adds:

| Package | Purpose |
|---------|---------|
| `textual` | Powers the interactive terminal UI |

All HTTP requests use Python's built-in `urllib`.
