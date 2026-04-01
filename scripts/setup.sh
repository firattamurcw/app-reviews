#!/usr/bin/env bash
# Setup development environment for new contributors.
# Usage: ./scripts/setup.sh

set -euo pipefail

echo "==> Installing dependencies..."
uv sync --group dev

echo "==> Installing pre-commit hooks..."
uv run pre-commit install

echo "==> Running checks to verify setup..."
uv run ruff check . --quiet
uv run mypy src/ --no-error-summary
uv run pytest -q --no-header

echo ""
echo "Done! Development environment is ready."
