# Contributing

---

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/firattamurcw/app-reviews.git
cd app-reviews
```

### Install Dependencies

```bash
uv sync --group dev
```

### Set Up Pre-Commit Hooks

```bash
pre-commit install
```

---

## Development Commands

| Command | What It Does |
|---------|-------------|
| `make install` | Install all dependencies |
| `make test` | Run tests with coverage |
| `make lint` | Check code style with ruff |
| `make format` | Auto-fix style and formatting |
| `make typecheck` | Run mypy strict |
| `make build` | Build the package |
| `make docs` | Build documentation |
| `make docs-serve` | Preview docs at `http://localhost:8000` |
| `make clean` | Remove build artifacts |
| `make all` | Run lint + typecheck + test + build |

---

## Project Structure

```
src/app_reviews/
├── __init__.py             # Public API exports
├── errors.py               # Typed exceptions
├── clients/                # Store clients
│   ├── base.py             # Base client (pagination, threading)
│   ├── appstore.py         # AppStoreReviews
│   └── googleplay.py       # GooglePlayReviews
├── providers/              # Data source implementations
│   ├── base.py             # ReviewProvider protocol
│   ├── appstore/
│   │   ├── official.py     # App Store Connect API
│   │   └── scraper.py      # Public RSS feed
│   └── googleplay/
│       ├── official.py     # Google Play Developer API
│       └── scraper.py      # Web scraper
├── auth/                   # Authentication
│   ├── appstore/
│   │   └── connect.py      # JWT (ES256)
│   └── googleplay/
│       └── service_account.py  # JWT (RS256)
├── exporters/              # Export formats
│   ├── json.py
│   ├── jsonl.py
│   └── csv.py
├── models/                 # Data models (frozen dataclasses)
│   ├── auth.py             # Auth credentials
│   ├── country.py          # Country enum + region groups
│   ├── metadata.py         # AppMetadata
│   ├── result.py           # FetchResult, FetchError
│   ├── retry.py            # RetryConfig
│   ├── review.py           # Review
│   ├── sort.py             # Sort enum
│   └── types.py            # Literal type aliases
└── utils/                  # Shared utilities
    ├── http.py             # HTTP client (stdlib urllib)
    ├── jwt.py              # JWT encoding
    ├── metadata.py         # App metadata lookup
    ├── parsing.py          # Input parsing and store detection
    ├── retry.py            # Retry logic
    └── text.py             # Text cleaning
```

---

## Code Standards

- **Python 3.11+** -- use modern syntax (`|` unions, etc.)
- **Strict mypy** -- all code must pass `mypy --strict`
- **Ruff** -- code must pass ruff linting and formatting
- **75%+ test coverage**
- **Frozen dataclasses** -- `@dataclass(frozen=True, slots=True)`
- **Stdlib HTTP** -- `urllib` only, no third-party HTTP libraries
- **One runtime dependency** -- `cryptography` for JWT

---

## Submitting Changes

1. **Open an issue first** for large changes
2. **Create a branch** from `main`
3. **Make your changes** and add tests
4. **Run `make all`**
5. **Open a pull request** against `main`

For small fixes, go straight to a PR.
