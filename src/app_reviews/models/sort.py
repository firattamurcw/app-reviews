"""Sort order enum."""

from enum import StrEnum


class Sort(StrEnum):
    NEWEST = "newest"
    OLDEST = "oldest"
    RATING = "rating"
