"""Main review browser screen."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import Footer, Header, Input, Label, Select

from app_reviews.core.filters import sort_reviews
from app_reviews.exporters.csv import export_csv
from app_reviews.exporters.json import export_json
from app_reviews.exporters.jsonl import export_jsonl
from app_reviews.models.metadata import AppMetadata
from app_reviews.models.result import FetchResult
from app_reviews.models.review import Review
from app_reviews.tui.widgets.filter_bar import FilterBar
from app_reviews.tui.widgets.rating_bar import RatingBar
from app_reviews.tui.widgets.review_card import ReviewCard


class ExportModal(ModalScreen[str | None]):
    """Modal for exporting reviews."""

    DEFAULT_CSS = """
    ExportModal {
        align: center middle;
    }
    ExportModal #export-container {
        width: 50;
        height: auto;
        padding: 2 4;
        border: tall $primary;
        background: $surface;
    }
    ExportModal Label {
        margin: 1 0;
    }
    ExportModal Select {
        width: 100%;
        margin: 0 0 1 0;
    }
    ExportModal Input {
        width: 100%;
        margin: 0 0 1 0;
    }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]  # noqa: RUF012

    def __init__(self, reviews: list[Review]) -> None:
        super().__init__()
        self._reviews = reviews

    def compose(self) -> ComposeResult:
        with Vertical(id="export-container"):
            yield Label(f"[bold]Export {len(self._reviews)} reviews[/]")
            yield Select[str](
                [("JSON", "json"), ("JSONL", "jsonl"), ("CSV", "csv")],
                value="json",
                id="format-select",
            )
            yield Input(
                value="reviews.json",
                id="file-input",
                placeholder="File path",
            )
            yield Label("", id="export-status")

    def on_select_changed(self, event: Select.Changed) -> None:
        """Update file extension when format changes."""
        fmt = event.value
        inp = self.query_one("#file-input", Input)
        stem = Path(inp.value).stem if inp.value else "reviews"
        inp.value = f"{stem}.{fmt}"

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Export on enter in the file input."""
        self._do_export()

    def _do_export(self) -> None:
        fmt = self.query_one("#format-select", Select).value
        file_path = self.query_one("#file-input", Input).value

        if fmt == "json":
            text = export_json(self._reviews)
        elif fmt == "jsonl":
            text = export_jsonl(self._reviews)
        elif fmt == "csv":
            text = export_csv(self._reviews)
        else:
            text = ""

        try:
            path = Path(file_path)
            path.write_text(text)
            self.dismiss(
                f"\u2713 Exported {len(self._reviews)} reviews to {path.resolve()}"
            )
        except OSError as exc:
            status = self.query_one("#export-status", Label)
            status.update(f"[bold red]\u2717 Failed: {exc}[/]")

    def action_cancel(self) -> None:
        self.dismiss(None)


class ReviewBrowserScreen(Screen[None]):
    """Main screen for browsing reviews with filter/sort/search."""

    BINDINGS = [  # noqa: RUF012
        Binding("q", "quit", "Quit"),
        Binding("1", "toggle_1", "1\u2605"),
        Binding("2", "toggle_2", "2\u2605"),
        Binding("3", "toggle_3", "3\u2605"),
        Binding("4", "toggle_4", "4\u2605"),
        Binding("5", "toggle_5", "5\u2605"),
        Binding("s", "cycle_sort", "Sort"),
        Binding("slash", "search", "Search"),
        Binding("escape", "blur_search", show=False),
        Binding("e", "export", "Export"),
    ]

    DEFAULT_CSS = """
    ReviewBrowserScreen {
        layout: vertical;
    }
    #browser-body {
        width: 100%;
        height: 1fr;
    }
    #sidebar {
        width: 32;
        height: auto;
        max-height: 100%;
        border-right: tall $primary-background;
        padding: 1 0;
    }
    #review-list {
        width: 1fr;
        height: 100%;
    }
    """

    def __init__(
        self,
        result: FetchResult,
        countries: list[str],
        app_metadata: AppMetadata | None = None,
    ) -> None:
        super().__init__()
        self._result = result
        self._all_reviews = result.reviews
        self._countries = countries
        self._app_metadata = app_metadata
        self._filtered_reviews: list[Review] = list(result.reviews)

    def compose(self) -> ComposeResult:
        yield Header()
        yield FilterBar()
        with Horizontal(id="browser-body"):
            with Vertical(id="sidebar"):
                yield RatingBar()
            yield VerticalScroll(id="review-list")
        yield Footer()

    def on_mount(self) -> None:
        # Pass app info to the rating bar
        rating_bar = self.query_one(RatingBar)
        rating_bar.set_app_metadata(self._app_metadata)

        self._apply_filters(
            active_ratings={1, 2, 3, 4, 5},
            sort_order="newest",
            search_query="",
        )

    def on_filter_bar_filters_changed(self, event: FilterBar.FiltersChanged) -> None:
        """Respond to filter/sort/search changes."""
        self._apply_filters(
            active_ratings=event.active_ratings,
            sort_order=event.sort_order,
            search_query=event.search_query,
        )

    def _apply_filters(
        self,
        active_ratings: set[int],
        sort_order: str,
        search_query: str,
    ) -> None:
        """Filter, sort, and re-render the review list."""
        reviews = [r for r in self._all_reviews if r.rating in active_ratings]

        if search_query:
            q = search_query.lower()
            reviews = [
                r
                for r in reviews
                if q in r.title.lower()
                or q in r.body.lower()
                or q in r.author_name.lower()
            ]

        reviews = sort_reviews(reviews, sort_order)
        self._filtered_reviews = reviews

        # Update rating bar
        rating_bar = self.query_one(RatingBar)
        rating_bar.update_reviews(self._all_reviews, active_ratings)

        # Update review list
        review_list = self.query_one("#review-list", VerticalScroll)
        review_list.remove_children()
        if reviews:
            for r in reviews:
                review_list.mount(ReviewCard(r))
        else:
            review_list.mount(Label("No reviews match filters."))

    def action_toggle_1(self) -> None:
        self.query_one(FilterBar).toggle_rating(1)

    def action_toggle_2(self) -> None:
        self.query_one(FilterBar).toggle_rating(2)

    def action_toggle_3(self) -> None:
        self.query_one(FilterBar).toggle_rating(3)

    def action_toggle_4(self) -> None:
        self.query_one(FilterBar).toggle_rating(4)

    def action_toggle_5(self) -> None:
        self.query_one(FilterBar).toggle_rating(5)

    def action_cycle_sort(self) -> None:
        self.query_one(FilterBar).cycle_sort()

    def action_search(self) -> None:
        self.query_one(FilterBar).focus_search()

    def action_blur_search(self) -> None:
        self.set_focus(None)

    def action_export(self) -> None:
        self.app.push_screen(
            ExportModal(self._filtered_reviews),
            callback=self._on_export_done,
        )

    def _on_export_done(self, message: str | None) -> None:
        if message:
            self.notify(message, severity="information", timeout=5)

    def action_quit(self) -> None:
        self.app.exit()
