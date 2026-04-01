"""Filter, sort, and search controls widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Input, Label, Static

_SORT_OPTIONS = ["newest", "oldest", "highest", "lowest"]


class FilterBar(Static):
    """Filter and sort controls for the review browser."""

    DEFAULT_CSS = """
    FilterBar {
        dock: top;
        width: 100%;
        height: auto;
        padding: 0;
        border-bottom: tall $primary-background;
    }
    FilterBar Vertical {
        height: auto;
    }
    #filter-row {
        height: auto;
        width: 100%;
        padding: 1 2;
    }
    .filter-label {
        width: auto;
        padding: 0 2;
    }
    .filter-sep {
        width: 1;
        color: $text-muted;
    }
    #search-input {
        width: 100%;
        margin: 1 2;
    }
    """

    class FiltersChanged(Message):
        """Emitted when any filter/sort/search changes."""

        def __init__(
            self,
            active_ratings: set[int],
            sort_order: str,
            search_query: str,
        ) -> None:
            super().__init__()
            self.active_ratings = active_ratings
            self.sort_order = sort_order
            self.search_query = search_query

    def __init__(self) -> None:
        super().__init__()
        self._active_ratings: set[int] = {1, 2, 3, 4, 5}
        self._sort_index: int = 0
        self._search_query: str = ""

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="filter-row"):
                yield Label(
                    self._ratings_label(),
                    classes="filter-label",
                    id="rating-label",
                )
                yield Label("\u2502", classes="filter-sep")
                yield Label(
                    self._sort_label(),
                    classes="filter-label",
                    id="sort-label",
                )
            yield Input(
                placeholder="Search reviews...",
                id="search-input",
            )

    def _ratings_label(self) -> str:
        parts = []
        for i in range(1, 6):
            if i in self._active_ratings:
                parts.append(f"[bold yellow]{i}\u2605[/]")
            else:
                parts.append(f"[dim]{i}\u2606[/]")
        return "Rating: " + "  ".join(parts)

    def _sort_label(self) -> str:
        return f"Sort: [bold]{_SORT_OPTIONS[self._sort_index]}[/]"

    def toggle_rating(self, rating: int) -> None:
        """Toggle a rating filter on/off."""
        if rating in self._active_ratings:
            if len(self._active_ratings) > 1:
                self._active_ratings.discard(rating)
        else:
            self._active_ratings.add(rating)
        self.query_one("#rating-label", Label).update(self._ratings_label())
        self._emit_change()

    def cycle_sort(self) -> None:
        """Cycle to the next sort order."""
        self._sort_index = (self._sort_index + 1) % len(_SORT_OPTIONS)
        self.query_one("#sort-label", Label).update(self._sort_label())
        self._emit_change()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        self._search_query = event.value
        self._emit_change()

    def focus_search(self) -> None:
        """Focus the search input."""
        self.query_one("#search-input", Input).focus()

    def _emit_change(self) -> None:
        self.post_message(
            self.FiltersChanged(
                active_ratings=set(self._active_ratings),
                sort_order=_SORT_OPTIONS[self._sort_index],
                search_query=self._search_query,
            )
        )

    @property
    def active_ratings(self) -> set[int]:
        return set(self._active_ratings)

    @property
    def current_sort_order(self) -> str:
        return _SORT_OPTIONS[self._sort_index]
