# Installation

## Requirements

- **Python 3.11** or higher

---

## Install from PyPI

```bash
pip install app-reviews
```

This gives you the Python API and the CLI. No extra configuration needed.

---

## Install with the TUI

The interactive terminal UI is an optional extra. It uses the [Textual](https://textual.textualize.io/) library, which is not installed by default.

```bash
pip install app-reviews[tui]
```

---

## Install from Source

If you want to work with the latest code or contribute:

```bash
git clone https://github.com/firattamurcw/appstore-reviews.git
cd appstore-reviews
uv sync
```

This uses [uv](https://docs.astral.sh/uv/) as the package manager. It installs all dependencies and sets up the project in development mode.

To also install the development tools (testing, linting, type checking):

```bash
uv sync --group dev
```

---

## Verify the Installation

After installing, check that it works:

```bash
python -c "from app_reviews import AppStoreReviews; print('OK')"
```

Or check the CLI:

```bash
app-reviews --help
```

If either command fails, make sure you are using Python 3.11+ (`python --version`) and that the package installed without errors.

---

## Dependencies

The package has **one runtime dependency**:

| Package | Purpose |
|---------|---------|
| `cryptography` | JWT signing for authenticated API access (App Store Connect and Google Play Developer API) |

The TUI extra adds one more:

| Package | Purpose |
|---------|---------|
| `textual` | Powers the interactive terminal UI |

All HTTP requests use Python's built-in `urllib`. No `requests` or `httpx` needed.
