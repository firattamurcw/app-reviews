"""Rating distribution bar chart widget."""

from __future__ import annotations

from textual.widgets import Static

from app_reviews.models.metadata import AppMetadata
from app_reviews.models.review import Review


def _stars(rating: float) -> str:
    """Render star rating with filled yellow and dim empty stars."""
    n = round(rating)
    filled = "[yellow]\u2605[/]" * n
    empty = "[dim]\u2606[/]" * (5 - n)
    return filled + empty


class RatingBar(Static):
    """Displays app info header and rating distribution bar chart."""

    DEFAULT_CSS = """
    RatingBar {
        width: 100%;
        height: auto;
        padding: 1 2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._reviews: list[Review] = []
        self._active_ratings: set[int] = {1, 2, 3, 4, 5}
        self._app_metadata: AppMetadata | None = None

    def set_app_metadata(self, app_metadata: AppMetadata | None) -> None:
        """Set app metadata for the header."""
        self._app_metadata = app_metadata
        self.refresh()

    def update_reviews(self, reviews: list[Review], active_ratings: set[int]) -> None:
        """Update the displayed reviews and active rating filters."""
        self._reviews = reviews
        self._active_ratings = active_ratings
        self.refresh()

    def render(self) -> str:
        lines: list[str] = []

        # App info header
        if self._app_metadata:
            info = self._app_metadata
            lines.append(f"[bold]{info.name}[/]")
            lines.append(f"[dim]{info.developer}[/]")
            lines.append(
                f"{_stars(info.rating)} {info.rating:.1f}  [dim]v{info.version}[/]"
            )
            lines.append("")

        if not self._reviews:
            lines.append("No reviews")
            return "\n".join(lines)

        dist = [0, 0, 0, 0, 0]
        for r in self._reviews:
            dist[r.rating - 1] += 1

        total = len(self._reviews)
        avg = sum(r.rating for r in self._reviews) / total

        lines.append(f"{_stars(avg)} {avg:.1f}  \u00b7  [bold]{total}[/] reviews")
        lines.append("")

        max_count = max(dist) if dist else 1
        for i in range(5, 0, -1):
            count = dist[i - 1]
            bar_w = int((count / max_count) * 16) if max_count else 0
            bar = "\u2588" * bar_w
            active = i in self._active_ratings
            style = "yellow" if active else "dim"
            label_style = "bold" if active else "dim"
            lines.append(f"[{label_style}]{i}\u2605[/] [{style}]{bar}[/] {count}")

        return "\n".join(lines)
