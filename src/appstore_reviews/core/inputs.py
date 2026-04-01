"""App input and country normalization utilities."""

import re

_APP_STORE_URL_PATTERN = re.compile(r"/id(\d+)")

ALL_COUNTRIES: list[str] = [
    "ae",
    "ar",
    "au",
    "at",
    "be",
    "bo",
    "br",
    "ca",
    "cl",
    "cn",
    "co",
    "cr",
    "cz",
    "dk",
    "ec",
    "eg",
    "fi",
    "fr",
    "de",
    "gh",
    "gt",
    "hk",
    "hu",
    "in",
    "id",
    "ie",
    "il",
    "it",
    "jp",
    "jo",
    "ke",
    "kr",
    "kw",
    "lb",
    "lt",
    "lu",
    "my",
    "mx",
    "nl",
    "nz",
    "ng",
    "no",
    "pk",
    "pa",
    "pe",
    "ph",
    "pl",
    "pt",
    "qa",
    "ro",
    "ru",
    "sa",
    "sg",
    "za",
    "es",
    "se",
    "ch",
    "tw",
    "th",
    "tr",
    "gb",
    "us",
    "uy",
    "ve",
    "vn",
]


def normalize_app_id(raw: str) -> str:
    """Normalize a raw app input (numeric ID or App Store URL) to a numeric ID."""
    if not raw:
        raise ValueError("App ID must not be empty.")

    # Try URL extraction first
    match = _APP_STORE_URL_PATTERN.search(raw)
    if match:
        return match.group(1)

    # If it looks like a URL but had no /id<digits>, reject it
    if raw.startswith("http://") or raw.startswith("https://"):
        raise ValueError(f"Could not extract a numeric app ID from URL: {raw!r}")

    # Accept a plain numeric string
    if raw.isdigit():
        return raw

    raise ValueError(
        f"Invalid app ID {raw!r}: expected a numeric ID or an App Store URL."
    )


def normalize_app_ids(raw_ids: list[str]) -> list[str]:
    """Normalize a list of raw app inputs. Raises ValueError on any invalid input."""
    return [normalize_app_id(r) for r in raw_ids]


def normalize_countries(raw: list[str]) -> list[str]:
    """Normalize country list. 'all' expands to ALL_COUNTRIES."""
    if raw == ["all"]:
        return list(ALL_COUNTRIES)

    seen: set[str] = set()
    result: list[str] = []
    for code in raw:
        if len(code) != 2 or not code.isalpha() or not code.islower():
            raise ValueError(
                f"Invalid country code {code!r}: expected a 2-letter lowercase"
                " ISO 3166-1 alpha-2 code."
            )
        if code not in seen:
            seen.add(code)
            result.append(code)
    return result
