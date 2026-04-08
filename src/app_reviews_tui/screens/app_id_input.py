"""App ID input screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label


class AppIdInputScreen(Screen[str]):
    """Screen for entering an App Store app ID or URL."""

    BINDINGS = [  # noqa: RUF012
        Binding("escape", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
    AppIdInputScreen {
        align: center middle;
    }
    #input-container {
        width: 64;
        height: auto;
        padding: 2 4;
        border: tall $primary;
        background: $surface;
    }
    #input-container Label {
        width: 100%;
        margin: 0 0 1 0;
    }
    #input-container Input {
        width: 100%;
        margin: 1 0;
    }
    #hint {
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Center(), Vertical(id="input-container"):
            yield Label("[bold]Enter App Store App ID[/]")
            yield Input(
                placeholder="e.g. 284882215 or App Store URL",
                id="app-id-input",
            )
            yield Label(
                "[dim]Paste a numeric ID or an App Store URL, then press Enter[/]",
                id="hint",
            )
        yield Footer()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle enter in the input."""
        value = event.value.strip()
        if value:
            self.dismiss(value)

    def action_quit(self) -> None:
        self.app.exit()
