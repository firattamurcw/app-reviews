#!/usr/bin/env bash
# Create a release: bump version, commit, tag, push.
# Usage: ./scripts/release.sh <major|minor|patch|X.Y.Z>

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <major|minor|patch|X.Y.Z>"
    exit 1
fi

BUMP="$1"
PYPROJECT="pyproject.toml"
CURRENT=$(grep -m1 '^version' "$PYPROJECT" | sed 's/version = "\(.*\)"/\1/')

IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

case "$BUMP" in
    major) NEW="$((MAJOR + 1)).0.0" ;;
    minor) NEW="${MAJOR}.$((MINOR + 1)).0" ;;
    patch) NEW="${MAJOR}.${MINOR}.$((PATCH + 1))" ;;
    *.*.*)  NEW="$BUMP" ;;
    *)
        echo "Error: argument must be major, minor, patch, or X.Y.Z"
        exit 1
        ;;
esac

echo "==> Bumping version: ${CURRENT} -> ${NEW}"
sed -i '' "s/^version = \"${CURRENT}\"/version = \"${NEW}\"/" "$PYPROJECT"

echo "==> Running checks..."
uv lock --quiet
uv run ruff check . --quiet
uv run mypy src/ --no-error-summary
uv run pytest -q --no-header

echo "==> Committing and tagging..."
git add "$PYPROJECT" uv.lock
git commit -m "release: v${NEW}"
git tag "v${NEW}"

echo "==> Pushing..."
git push origin main --tags

echo ""
echo "Released v${NEW}."
