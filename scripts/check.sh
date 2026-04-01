#!/usr/bin/env bash
# Run all checks locally before pushing.
# Usage: ./scripts/check.sh

set -euo pipefail

echo "==> Lint..."
uv run ruff check .
uv run ruff format --check .

echo "==> Typecheck..."
uv run mypy src/

echo "==> Test..."
uv run pytest --cov --cov-report=term-missing

echo "==> Build..."
uv build

echo ""
echo "All checks passed."
