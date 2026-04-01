"""Textual TUI for app-reviews."""

from __future__ import annotations


def main() -> None:
    """Entry point — launch the TUI app."""
    from app_reviews.tui.app import ReviewApp

    ReviewApp().run()
