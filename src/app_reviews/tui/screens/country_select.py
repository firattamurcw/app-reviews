"""Country selection screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, SelectionList
from textual.widgets.selection_list import Selection

from app_reviews.core.inputs import ALL_COUNTRIES, COUNTRIES

_COMMON_COUNTRIES = ["us", "gb", "de", "fr", "jp", "au", "ca"]


class CountrySelectScreen(Screen[list[str]]):
    """Screen for selecting countries to fetch reviews from."""

    BINDINGS = [  # noqa: RUF012
        Binding("enter", "confirm", "Fetch", priority=True),
        Binding("a", "select_all", "Select all"),
        Binding("n", "select_none", "Select none"),
    ]

    DEFAULT_CSS = """
    CountrySelectScreen {
        align: center middle;
    }
    CountrySelectScreen SelectionList {
        width: 60;
        height: 80%;
        border: tall $primary;
        border-title-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        ordered = _COMMON_COUNTRIES + [
            c for c in ALL_COUNTRIES if c not in _COMMON_COUNTRIES
        ]
        selections = [Selection(COUNTRIES[c].label, c, c == "us") for c in ordered]
        sel_list = SelectionList[str](*selections)
        sel_list.border_title = "Select Countries"
        yield sel_list
        yield Footer()

    def action_confirm(self) -> None:
        """Confirm selection and proceed."""
        sel_list = self.query_one(SelectionList)
        selected = list(sel_list.selected)
        if not selected:
            selected = ["us"]
        self.dismiss(selected)

    def action_select_all(self) -> None:
        self.query_one(SelectionList).select_all()

    def action_select_none(self) -> None:
        self.query_one(SelectionList).deselect_all()
