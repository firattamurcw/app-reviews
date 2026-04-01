# Contributing

Thanks for your interest in contributing to App Reviews.

---

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/firattamurcw/appstore-reviews.git
cd appstore-reviews
```

### Install Dependencies

Install all dependencies including development tools:

```bash
uv sync --group dev
```

This installs:

- **pytest** -- test runner
- **pytest-cov** -- code coverage reporting
- **pytest-asyncio** -- async test support
- **mypy** -- static type checker (strict mode)
- **ruff** -- linter and code formatter
- **pre-commit** -- git pre-commit hooks
- **textual** -- TUI library (for TUI tests)

### Set Up Pre-Commit Hooks

```bash
pre-commit install
```

This runs linting and formatting checks automatically before each commit.

---

## Development Commands

The project uses a `Makefile` for common tasks:

| Command | What It Does |
|---------|-------------|
| `make install` | Install all dependencies (`uv sync --group dev`) |
| `make test` | Run the test suite with coverage reporting |
| `make lint` | Check code style with ruff (no auto-fix) |
| `make format` | Auto-fix code style and formatting with ruff |
| `make typecheck` | Run mypy in strict mode |
| `make build` | Build the package |
| `make docs` | Build the documentation site |
| `make docs-serve` | Start a local docs preview server at `http://localhost:8000` |
| `make clean` | Remove build artifacts |
| `make all` | Run lint + typecheck + test + build (the full check) |

### Run Tests

```bash
make test
```

This runs pytest with coverage reporting. The minimum coverage threshold is **75%**. If coverage drops below this, the test run fails.

### Check Code Style

```bash
make lint
```

This runs ruff to check for style issues, import ordering, and common mistakes. It does not modify files.

To auto-fix issues:

```bash
make format
```

### Type Checking

```bash
make typecheck
```

This runs mypy in **strict mode**. All code must pass strict type checking with no errors.

### Run Everything

```bash
make all
```

This runs lint, typecheck, test, and build in order. If any step fails, it stops. Run this before opening a pull request.

---

## Project Structure

```
src/app_reviews/
├── __init__.py             # Public API exports
├── scraper.py              # AppStoreScraper & GooglePlayScraper
├── core/                   # Orchestration and utilities
│   ├── execution.py        # Main fetch orchestration
│   ├── provider_selection.py
│   ├── inputs.py           # App ID / country normalization
│   ├── dedupe.py           # Deduplication logic
│   ├── filters.py          # Rating filters and sorting
│   ├── checkpoints.py      # Fetch resumption
│   └── json_store.py       # State persistence
├── providers/              # Data source implementations
│   ├── base.py             # ReviewProvider protocol
│   ├── appstore/
│   │   ├── rss.py          # Public RSS feed
│   │   └── connect.py      # App Store Connect API
│   └── googleplay/
│       ├── scraper.py       # Web scraper
│       └── developer_api.py # Google Play Developer API
├── auth/                   # Authentication
│   ├── appstore/
│   │   └── connect.py      # JWT (ES256) for App Store
│   └── googleplay/
│       └── service_account.py  # JWT (RS256) for Google
├── exporters/              # Export formats
│   ├── json.py
│   ├── jsonl.py
│   └── csv.py
├── models/                 # Data models (dataclasses)
│   ├── review.py
│   ├── result.py
│   ├── config.py
│   ├── auth.py
│   ├── types.py
│   └── ...
├── utils/                  # Shared utilities
│   ├── http.py             # HTTP client (stdlib urllib)
│   ├── jwt.py              # JWT encoding
│   ├── metadata.py         # App metadata lookup
│   ├── retry.py            # Retry logic
│   └── text.py             # Text cleaning
└── tui/                    # Interactive terminal UI
    ├── __init__.py
    ├── app.py
    ├── screens/
    └── widgets/
```

---

## Code Standards

- **Python 3.11+** -- use modern syntax (type unions with `|`, `match` statements, etc.)
- **Strict mypy** -- all code must pass `mypy --strict`
- **Ruff** -- code must pass ruff linting and formatting
- **75%+ test coverage** -- coverage must not drop below 75%
- **Frozen dataclasses** -- all models use `@dataclass(frozen=True, slots=True)`
- **Stdlib HTTP** -- no third-party HTTP libraries. Use `urllib` via `utils/http.py`
- **One runtime dependency** -- `cryptography` for JWT. Keep dependencies minimal.

---

## Submitting Changes

1. **Open an issue first** for large changes so we can discuss the approach
2. **Create a branch** from `main`
3. **Make your changes** and add tests for new functionality.
4. **Run `make all`** to check lint, types, and tests.
5. **Open a pull request** against `main`.

For small fixes (typos, docs, minor bugs), you can skip the issue and go straight to a PR.
