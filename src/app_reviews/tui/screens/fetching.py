"""Fetching progress screen."""

from __future__ import annotations

import contextlib

from textual import work
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, LoadingIndicator

from app_reviews.core.execution import execute_fetch
from app_reviews.models.config import ReviewConfig
from app_reviews.models.metadata import AppMetadata
from app_reviews.models.result import FetchResult
from app_reviews.utils.metadata import lookup_metadata


class FetchData:
    """Container for fetch results and app info."""

    def __init__(self, result: FetchResult, app_metadata: AppMetadata | None) -> None:
        self.result = result
        self.app_metadata = app_metadata


class FetchingScreen(Screen[FetchData]):
    """Screen showing fetch progress with a spinner."""

    DEFAULT_CSS = """
    FetchingScreen {
        align: center middle;
    }
    FetchingScreen #status-container {
        width: 50;
        height: auto;
        padding: 2 4;
        border: tall $primary;
        background: $surface;
    }
    FetchingScreen Label {
        width: 100%;
        text-align: center;
        margin: 1 0;
    }
    FetchingScreen LoadingIndicator {
        width: 100%;
        height: 3;
    }
    """

    def __init__(self, config: ReviewConfig) -> None:
        super().__init__()
        self._config = config

    def compose(self) -> ComposeResult:
        yield Header()
        with Center(), Vertical(id="status-container"):
            yield Label("[bold]Fetching reviews...[/]")
            yield Label(
                f"App: {', '.join(self._config.app_ids)}\n"
                f"Countries: {', '.join(self._config.countries)}"
            )
            yield LoadingIndicator()
            yield Label("", id="result-label")
        yield Footer()

    def on_mount(self) -> None:
        self._do_fetch()

    @work(thread=True)
    def _do_fetch(self) -> None:
        """Run fetch and app info lookup in a background thread."""
        try:
            result = execute_fetch(self._config)
        except Exception as exc:
            self.app.call_from_thread(self._on_fetch_error, str(exc))
            return
        app_metadata: AppMetadata | None = None
        with contextlib.suppress(Exception):
            app_metadata = lookup_metadata(self._config.app_ids[0])
        data = FetchData(result=result, app_metadata=app_metadata)
        self.app.call_from_thread(self._on_fetch_complete, data)

    def _on_fetch_error(self, error: str) -> None:
        """Show error message when fetch fails."""
        label = self.query_one("#result-label", Label)
        label.update(f"[bold red]Fetch failed: {error}[/]")
        loading = self.query_one(LoadingIndicator)
        loading.display = False

    def _on_fetch_complete(self, data: FetchData) -> None:
        """Handle fetch completion on the main thread."""
        count = len(data.result.reviews)
        failures = len(data.result.failures)
        label = self.query_one("#result-label", Label)
        name = data.app_metadata.name if data.app_metadata else "App"
        msg = f"[bold green]\u2713 {name}: {count} reviews fetched[/]"
        if failures:
            msg += f"  [bold red]({failures} failed)[/]"
        label.update(msg)
        self.dismiss(data)
