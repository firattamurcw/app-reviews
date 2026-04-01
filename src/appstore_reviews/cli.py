"""CLI entry point for appstore-reviews."""

from __future__ import annotations

import sys

import click

from appstore_reviews.config.models import AppStoreConfig
from appstore_reviews.core.execution import execute_fetch
from appstore_reviews.core.inputs import normalize_app_id, normalize_countries
from appstore_reviews.exporters.csv import export_csv
from appstore_reviews.exporters.json import export_json
from appstore_reviews.exporters.jsonl import export_jsonl
from appstore_reviews.models.result import FetchResult


@click.group()
@click.version_option(package_name="appstore-reviews")
def main() -> None:
    """The go-to CLI for App Store review extraction."""


@main.command()
@click.option("--app-id", required=True, help="App Store app ID or URL.")
@click.option(
    "--country",
    multiple=True,
    default=["us"],
    help="Country code(s). Repeat for multiple.",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "jsonl", "json", "csv"]),
    default="table",
    help="Output format (default: table for terminal, jsonl when piped).",
)
@click.option("--output", "-o", default=None, help="Output file path.")
@click.option("--overwrite", is_flag=True, help="Overwrite existing output file.")
@click.option("--include-raw", is_flag=True, help="Include raw source payload.")
def fetch(
    app_id: str,
    country: tuple[str, ...],
    fmt: str,
    output: str | None,
    overwrite: bool,
    include_raw: bool,
) -> None:
    """Fetch App Store reviews for an app."""
    config = AppStoreConfig(
        app_ids=[app_id],
        countries=list(country),
        provider="auto",
    )
    # Auto-detect: use table for interactive terminal, jsonl when piped
    if fmt == "table" and output:
        fmt = "jsonl"

    result = execute_fetch(config)

    if fmt == "table":
        _print_table(result)
        return

    if fmt == "jsonl":
        text = export_jsonl(result.reviews, include_raw=include_raw)
    elif fmt == "json":
        text = export_json(result.reviews, include_raw=include_raw)
    elif fmt == "csv":
        text = export_csv(result.reviews)
    else:
        text = ""

    if output:
        from pathlib import Path

        p = Path(output)
        if p.exists() and not overwrite:
            click.echo(f"Error: file already exists: {output}", err=True)
            sys.exit(1)
        p.write_text(text)
        click.echo(f"Wrote {len(result.reviews)} reviews to {output}", err=True)
    else:
        click.echo(text, nl=False)


def _stars(rating: int) -> str:
    return click.style("★" * rating, fg="yellow") + click.style(
        "☆" * (5 - rating), dim=True
    )


def _truncate(text: str, width: int) -> str:
    text = text.replace("\n", " ").strip()
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


def _print_table(result: FetchResult) -> None:
    reviews = result.reviews
    failures = result.failures

    # Header
    click.echo()
    click.echo(
        click.style(f"  {len(reviews)} reviews fetched", bold=True)
        + (click.style(f"  ({len(failures)} failed)", fg="red") if failures else "")
    )
    click.echo()

    if not reviews:
        click.echo("  No reviews found.")
        return

    # Rating distribution
    dist = [0, 0, 0, 0, 0]
    for r in reviews:
        dist[r.rating - 1] += 1
    avg = sum(r.rating for r in reviews) / len(reviews)

    click.echo(f"  Average: {_stars(round(avg))} {avg:.1f}")
    for i in range(5, 0, -1):
        bar = "█" * dist[i - 1]
        click.echo(
            click.style(f"  {i}★ ", dim=True)
            + click.style(bar, fg="yellow")
            + f" {dist[i - 1]}"
        )
    click.echo()

    # Reviews
    for r in reviews:
        date_str = r.created_at.strftime("%Y-%m-%d")
        header = (
            f"  {_stars(r.rating)}  "
            + click.style(r.title, bold=True)
            + click.style(f"  — {r.author_name}", dim=True)
        )
        meta = click.style(
            f"  {r.country.upper()} · {date_str}"
            + (f" · v{r.app_version}" if r.app_version else ""),
            dim=True,
        )
        click.echo(header)
        click.echo(f"  {_truncate(r.body, 120)}")
        click.echo(meta)
        click.echo()


@main.command()
@click.option("--app-id", required=True, help="App Store app ID or URL.")
def inspect(app_id: str) -> None:
    """Show information about an app ID."""
    try:
        normalized = normalize_app_id(app_id)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    click.echo(f"App ID: {normalized}")
    click.echo(f"Input:  {app_id}")
    click.echo(
        f"RSS URL: https://itunes.apple.com/us/rss/customerreviews/id={normalized}/json"
    )


@main.group()
def config() -> None:
    """Configuration utilities."""


@config.command()
@click.option("--app-id", required=True, help="App Store app ID.")
@click.option("--country", multiple=True, default=["us"], help="Country code(s).")
def validate(app_id: str, country: tuple[str, ...]) -> None:
    """Validate configuration parameters."""
    errors: list[str] = []

    try:
        normalize_app_id(app_id)
    except ValueError as exc:
        errors.append(str(exc))

    try:
        normalize_countries(list(country))
    except ValueError as exc:
        errors.append(str(exc))

    if errors:
        for err in errors:
            click.echo(f"Error: {err}", err=True)
        sys.exit(1)

    click.echo("Configuration is valid.")


if __name__ == "__main__":  # pragma: no cover
    main()
