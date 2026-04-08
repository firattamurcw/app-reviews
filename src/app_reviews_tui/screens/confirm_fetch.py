"""Confirmation screen showing app info before fetching."""

from __future__ import annotations

import contextlib

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, LoadingIndicator

from app_reviews.models.metadata import AppMetadata
from app_reviews.utils.metadata import lookup_metadata
from app_reviews_tui.screens.fetch_options import FetchOptions


class ConfirmFetchScreen(Screen[bool]):
    """Show app info and ask for confirmation before fetching reviews."""

    BINDINGS = [  # noqa: RUF012
        Binding("enter", "confirm", "Fetch reviews", priority=True),
        Binding("escape", "cancel", "Back"),
    ]

    DEFAULT_CSS = """
    ConfirmFetchScreen {
        align: center middle;
    }
    #confirm-container {
        width: 60;
        height: auto;
        padding: 2 4;
        border: tall $primary;
        background: $surface;
    }
    #confirm-container Label {
        width: 100%;
        margin: 0 0 1 0;
    }
    #app-name {
        text-style: bold;
    }
    #loading {
        height: 3;
        width: 100%;
    }
    #actions-hint {
        text-align: center;
        margin: 1 0 0 0;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        app_id: str,
        countries: list[str],
        fetch_options: FetchOptions | None = None,
    ) -> None:
        super().__init__()
        self._app_id = app_id
        self._countries = countries
        self._fetch_options = fetch_options or FetchOptions()
        self._app_metadata: AppMetadata | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Center(), Vertical(id="confirm-container"):
            yield Label("Looking up app...", id="app-name")
            yield LoadingIndicator(id="loading")
            yield Label("", id="app-details")
            yield Label("", id="fetch-summary")
            yield Label(
                "[dim]press [bold]enter[/bold] to fetch"
                "  \u00b7  [bold]esc[/bold] to go back[/]",
                id="actions-hint",
            )
        yield Footer()

    def on_mount(self) -> None:
        self._lookup_metadata()

    @work(thread=True)
    def _lookup_metadata(self) -> None:
        """Look up app info in background."""
        app_info: AppMetadata | None = None
        with contextlib.suppress(Exception):
            app_info = lookup_metadata(self._app_id)
        self._app_metadata = app_info
        self.app.call_from_thread(self._show_info)

    def _show_info(self) -> None:
        """Display app info on the main thread."""
        self.query_one("#loading", LoadingIndicator).display = False

        name_label = self.query_one("#app-name", Label)
        details_label = self.query_one("#app-details", Label)
        summary_label = self.query_one("#fetch-summary", Label)

        if self._app_metadata:
            info = self._app_metadata
            n = round(info.rating)
            stars = "[yellow]\u2605[/]" * n + "[dim]\u2606[/]" * (5 - n)
            name_label.update(f"[bold]{info.name}[/]")
            details_label.update(
                f"{info.developer}\n"
                f"{stars} {info.rating:.1f}  \u00b7  "
                f"{info.category}  \u00b7  {info.price}\n"
                f"v{info.version}"
            )
        else:
            name_label.update(f"[bold]App {self._app_id}[/]")
            details_label.update("[dim]Could not load app details[/]")

        countries_str = ", ".join(c.upper() for c in self._countries)
        opts = self._fetch_options
        limit_str = str(opts.limit) if opts.limit else "all"
        summary_label.update(
            f"\nFetching reviews from: [bold]{countries_str}[/]\n"
            f"Sort: [bold]{opts.sort_order}[/]  ·  "
            f"Limit: [bold]{limit_str}[/]"
        )

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
