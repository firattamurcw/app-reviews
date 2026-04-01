.DEFAULT_GOAL := all

.PHONY: install lint format typecheck test test-ci build docs docs-build clean all

install:
	uv sync --group dev --group docs

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy src/

test:
	uv run pytest --cov --cov-report=term-missing

test-ci:
	uv run pytest --cov --cov-report=xml --junitxml=junit.xml

build:
	uv build

docs:
	uv run mkdocs serve

docs-build:
	uv run mkdocs build

clean:
	rm -rf dist/ build/ .mypy_cache/ .pytest_cache/ .ruff_cache/ .coverage htmlcov/ site/ junit.xml coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +

all: lint typecheck test build
