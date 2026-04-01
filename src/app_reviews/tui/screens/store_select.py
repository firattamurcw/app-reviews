"""Store selection screen."""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, OptionList
from textual.widgets.option_list import Option


class StoreSelectScreen(Screen[str]):
    """Screen for selecting the app store."""

    BINDINGS: ClassVar[list[BindingType]] = [
        ("escape", "app.pop_screen", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Center(), Vertical():
            yield Label("Select App Store", classes="title")
            yield OptionList(
                Option("Apple App Store", id="appstore"),
                Option("Google Play Store", id="googleplay"),
            )
        yield Footer()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option.id or "appstore")
