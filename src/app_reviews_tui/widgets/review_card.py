"""Review card widget for displaying a single review."""

from __future__ import annotations

from textual.widgets import Static

from app_reviews.models.review import Review
from app_reviews.utils.parsing import COUNTRIES


def _stars(rating: int) -> str:
    """Render star rating with filled yellow and dim empty stars."""
    filled = "[yellow]\u2605[/]" * rating
    empty = "[dim]\u2606[/]" * (5 - rating)
    return filled + empty


class ReviewCard(Static):
    """Displays a single review as a styled card."""

    DEFAULT_CSS = """
    ReviewCard {
        width: 1fr;
        height: auto;
        padding: 1 2;
        margin: 0 0 1 0;
        background: $surface;
        border: tall $primary-background;
    }
    ReviewCard:hover {
        background: $surface-lighten-1;
    }
    """

    def __init__(self, review: Review) -> None:
        super().__init__()
        self._review = review

    def render(self) -> str:
        r = self._review
        date_str = r.created_at.strftime("%Y-%m-%d")
        version = f" \u00b7 v{r.app_version}" if r.app_version else ""
        body = r.body.replace("\n", " ").strip()
        if len(body) > 200:
            body = body[:199] + "\u2026"

        country = COUNTRIES.get(r.country)
        country_display = country.label if country else r.country.upper()

        return (
            f"{_stars(r.rating)}  [bold]{r.title}[/]\n"
            f"[dim]{r.author_name} \u00b7 {country_display}"
            f" \u00b7 {date_str}{version}[/]\n"
            f"{body}"
        )
