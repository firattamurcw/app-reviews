# Contributing

Thanks for helping out. Bug reports, fixes, and new store support are all welcome.

## Setup

```bash
git clone https://github.com/firattamurcw/app-reviews.git
cd app-reviews
make install
pre-commit install
```

## Commands

| Command | What it does |
|---------|--------------|
| `make all` | lint + typecheck + test + build — run this before pushing |
| `make test` | tests with coverage |
| `make format` | auto-fix style |
| `make docs-serve` | preview docs at `localhost:8000` |

Live tests hit real store endpoints and are skipped by default. Run them with `make test ARGS="-m live"` or `uv run pytest -m live`.

## Standards

- Python 3.11+, `mypy --strict`, and ruff must all pass
- Stdlib `urllib` for HTTP — no third-party HTTP libraries
- `cryptography` is the only runtime dependency; keep it that way
- Models are `@dataclass(frozen=True, slots=True)`
- Coverage stays at or above 75%

## Pull requests

Branch from `main`, add tests, run `make all`, open the PR. For anything large, open an issue first so we can agree on the approach. Small fixes can go straight to a PR.

## Security

Please don't file public issues for vulnerabilities — see [SECURITY.md](SECURITY.md).
