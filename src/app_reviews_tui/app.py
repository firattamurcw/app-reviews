"""Main Textual app for app-reviews."""

from __future__ import annotations

from textual.app import App

from app_reviews_tui.screens.app_id_input import AppIdInputScreen
from app_reviews_tui.screens.confirm_fetch import ConfirmFetchScreen
from app_reviews_tui.screens.country_select import CountrySelectScreen
from app_reviews_tui.screens.fetch_options import FetchOptions, FetchOptionsScreen
from app_reviews_tui.screens.fetching import FetchData, FetchingScreen
from app_reviews_tui.screens.review_browser import ReviewBrowserScreen
from app_reviews_tui.sorting import sort_reviews


class ReviewApp(App[None]):
    """Interactive app review browser."""

    TITLE = "App Reviews"

    CSS = """
    Screen {
        background: $background;
    }
    """

    def __init__(
        self,
        app_id: str | None = None,
        countries: list[str] | None = None,
        store: str | None = None,
    ) -> None:
        super().__init__()
        self._app_id = app_id
        self._countries = countries
        self._store = store
        self._fetch_options = FetchOptions()

    def on_mount(self) -> None:
        """Start the screen flow."""
        if not self._app_id:
            self.push_screen(
                AppIdInputScreen(),
                callback=self._on_app_id_entered,
            )
        elif not self._countries:
            self.push_screen(
                CountrySelectScreen(),
                callback=self._on_countries_selected,
            )
        else:
            self._show_options()

    def _on_app_id_entered(self, app_id: str | None) -> None:
        self._app_id = app_id
        # Try to auto-detect store if not already set
        if not self._store and app_id:
            try:
                from app_reviews.utils.parsing import detect_store

                self._store = detect_store(app_id)
            except ValueError:
                from app_reviews_tui.screens.store_select import (
                    StoreSelectScreen,
                )

                self.push_screen(
                    StoreSelectScreen(),
                    callback=self._on_store_selected,
                )
                return
        self.push_screen(
            CountrySelectScreen(),
            callback=self._on_countries_selected,
        )

    def _on_store_selected(self, store: str | None) -> None:
        self._store = store or "appstore"
        self.push_screen(
            CountrySelectScreen(),
            callback=self._on_countries_selected,
        )

    def _on_countries_selected(self, countries: list[str] | None) -> None:
        self._countries = countries
        self._show_options()

    def _show_options(self) -> None:
        """Show fetch options (sort, limit) before confirmation."""
        self.push_screen(
            FetchOptionsScreen(),
            callback=self._on_options_selected,
        )

    def _on_options_selected(self, options: FetchOptions | None) -> None:
        if options is not None:
            self._fetch_options = options
        self._show_confirm()

    def _show_confirm(self) -> None:
        """Show app info confirmation before fetching."""
        self.push_screen(
            ConfirmFetchScreen(
                self._app_id or "",
                self._countries or ["us"],
                self._fetch_options,
            ),
            callback=self._on_confirm,
        )

    def _on_confirm(self, confirmed: bool | None) -> None:
        if confirmed:
            self._start_fetch(self._countries or ["us"])
        else:
            # Go back to fetch options
            self._show_options()

    def _start_fetch(self, countries: list[str]) -> None:
        self.push_screen(
            FetchingScreen(
                app_id=self._app_id or "",
                countries=countries,
                store=self._store or "appstore",
            ),
            callback=self._on_fetch_complete,
        )

    def _on_fetch_complete(self, data: FetchData | None) -> None:
        if data is None:
            return
        # Apply sort and limit from fetch options
        reviews = sort_reviews(data.result.reviews, self._fetch_options.sort_order)
        if self._fetch_options.limit:
            reviews = reviews[: self._fetch_options.limit]

        from app_reviews.models.result import FetchResult

        result = FetchResult(
            reviews=reviews,
            errors=data.result.errors,
        )

        self.push_screen(
            ReviewBrowserScreen(
                result,
                self._countries or ["us"],
                app_metadata=data.app_metadata,
            )
        )
