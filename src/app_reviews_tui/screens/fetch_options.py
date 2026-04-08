"""Fetch options screen for configuring limit and sort before fetching."""

from __future__ import annotations

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label, Select

_SORT_OPTIONS: list[tuple[str, str]] = [
    ("Newest first", "newest"),
    ("Oldest first", "oldest"),
    ("Highest rated", "highest"),
    ("Lowest rated", "lowest"),
]


@dataclass
class FetchOptions:
    """User-selected fetch options."""

    sort_order: str = "newest"
    limit: int | None = None


class FetchOptionsScreen(Screen[FetchOptions]):
    """Screen for configuring how reviews are fetched."""

    BINDINGS = [  # noqa: RUF012
        Binding("enter", "confirm", "Continue", priority=True),
        Binding("escape", "cancel", "Back"),
    ]

    DEFAULT_CSS = """
    FetchOptionsScreen {
        align: center middle;
    }
    #options-container {
        width: 60;
        height: auto;
        padding: 2 4;
        border: tall $primary;
        background: $surface;
    }
    #options-container Label {
        width: 100%;
        margin: 0 0 1 0;
    }
    #options-title {
        text-style: bold;
        text-align: center;
    }
    #options-container Select {
        width: 100%;
        margin: 0 0 1 0;
    }
    #options-container Input {
        width: 100%;
        margin: 0 0 1 0;
    }
    #actions-hint {
        text-align: center;
        margin: 1 0 0 0;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Center(), Vertical(id="options-container"):
            yield Label("Fetch Options", id="options-title")
            yield Label("Sort order")
            yield Select[str](_SORT_OPTIONS, value="newest", id="sort-select")
            yield Label("Max reviews [dim](leave empty for all)[/]")
            yield Input(
                placeholder="e.g. 50, 100, 500",
                id="limit-input",
            )
            yield Label(
                "[dim]press [bold]enter[/bold] to continue"
                "  ·  [bold]esc[/bold] to go back[/]",
                id="actions-hint",
            )
        yield Footer()

    def action_confirm(self) -> None:
        sort_select = self.query_one("#sort-select", Select)
        sort_order = str(sort_select.value) if sort_select.value else "newest"

        limit_input = self.query_one("#limit-input", Input)
        limit: int | None = None
        if limit_input.value.strip():
            try:
                limit = int(limit_input.value.strip())
                if limit <= 0:
                    limit = None
            except ValueError:
                limit = None

        self.dismiss(FetchOptions(sort_order=sort_order, limit=limit))

    def action_cancel(self) -> None:
        self.dismiss(FetchOptions())
