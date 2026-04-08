"""App input and country normalization utilities."""

import re
from dataclasses import dataclass

from app_reviews.models.types import Store

_APP_STORE_URL_PATTERN = re.compile(r"/id(\d+)")
_GOOGLE_PLAY_URL_PATTERN = re.compile(r"[?&]id=([\w.]+)")
_PACKAGE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)+$")


def _flag(code: str) -> str:
    """Convert a 2-letter country code to its flag emoji."""
    return "".join(chr(0x1F1E6 + ord(c) - ord("a")) for c in code.lower())


@dataclass(frozen=True, slots=True)
class Country:
    """An iTunes-supported country."""

    code: str
    name: str
    flag: str

    @property
    def label(self) -> str:
        """Display label: flag + name (e.g. '🇺🇸 United States of America')."""
        return f"{self.flag} {self.name}"


COUNTRIES: dict[str, Country] = {
    code: Country(code=code, name=name, flag=_flag(code))
    for code, name in {
        "ae": "United Arab Emirates",
        "ag": "Antigua and Barbuda",
        "ai": "Anguilla",
        "al": "Albania",
        "am": "Armenia",
        "ao": "Angola",
        "ar": "Argentina",
        "at": "Austria",
        "au": "Australia",
        "az": "Azerbaijan",
        "bb": "Barbados",
        "be": "Belgium",
        "bf": "Burkina-Faso",
        "bg": "Bulgaria",
        "bh": "Bahrain",
        "bj": "Benin",
        "bm": "Bermuda",
        "bn": "Brunei Darussalam",
        "bo": "Bolivia",
        "br": "Brazil",
        "bs": "Bahamas",
        "bt": "Bhutan",
        "bw": "Botswana",
        "by": "Belarus",
        "bz": "Belize",
        "ca": "Canada",
        "cg": "Democratic Republic of the Congo",
        "ch": "Switzerland",
        "cl": "Chile",
        "cn": "China",
        "co": "Colombia",
        "cr": "Costa Rica",
        "cv": "Cape Verde",
        "cy": "Cyprus",
        "cz": "Czech Republic",
        "de": "Germany",
        "dk": "Denmark",
        "dm": "Dominica",
        "do": "Dominican Republic",
        "dz": "Algeria",
        "ec": "Ecuador",
        "ee": "Estonia",
        "eg": "Egypt",
        "es": "Spain",
        "fi": "Finland",
        "fj": "Fiji",
        "fm": "Federated States of Micronesia",
        "fr": "France",
        "gb": "Great Britain",
        "gd": "Grenada",
        "gh": "Ghana",
        "gm": "Gambia",
        "gr": "Greece",
        "gt": "Guatemala",
        "gw": "Guinea Bissau",
        "gy": "Guyana",
        "hk": "Hong Kong",
        "hn": "Honduras",
        "hr": "Croatia",
        "hu": "Hungary",
        "id": "Indonesia",
        "ie": "Ireland",
        "il": "Israel",
        "in": "India",
        "is": "Iceland",
        "it": "Italy",
        "jm": "Jamaica",
        "jo": "Jordan",
        "jp": "Japan",
        "ke": "Kenya",
        "kg": "Kyrgyzstan",
        "kh": "Cambodia",
        "kn": "Saint Kitts and Nevis",
        "kr": "South Korea",
        "kw": "Kuwait",
        "ky": "Cayman Islands",
        "kz": "Kazakhstan",
        "la": "Laos",
        "lb": "Lebanon",
        "lc": "Saint Lucia",
        "lk": "Sri Lanka",
        "lr": "Liberia",
        "lt": "Lithuania",
        "lu": "Luxembourg",
        "lv": "Latvia",
        "md": "Moldova",
        "mg": "Madagascar",
        "mk": "Macedonia",
        "ml": "Mali",
        "mn": "Mongolia",
        "mo": "Macau",
        "mr": "Mauritania",
        "ms": "Montserrat",
        "mt": "Malta",
        "mu": "Mauritius",
        "mw": "Malawi",
        "mx": "Mexico",
        "my": "Malaysia",
        "mz": "Mozambique",
        "na": "Namibia",
        "ne": "Niger",
        "ng": "Nigeria",
        "ni": "Nicaragua",
        "nl": "Netherlands",
        "np": "Nepal",
        "no": "Norway",
        "nz": "New Zealand",
        "om": "Oman",
        "pa": "Panama",
        "pe": "Peru",
        "pg": "Papua New Guinea",
        "ph": "Philippines",
        "pk": "Pakistan",
        "pl": "Poland",
        "pt": "Portugal",
        "pw": "Palau",
        "py": "Paraguay",
        "qa": "Qatar",
        "ro": "Romania",
        "ru": "Russia",
        "sa": "Saudi Arabia",
        "sb": "Solomon Islands",
        "sc": "Seychelles",
        "se": "Sweden",
        "sg": "Singapore",
        "si": "Slovenia",
        "sk": "Slovakia",
        "sl": "Sierra Leone",
        "sn": "Senegal",
        "sr": "Suriname",
        "st": "Sao Tome e Principe",
        "sv": "El Salvador",
        "sz": "Swaziland",
        "tc": "Turks and Caicos Islands",
        "td": "Chad",
        "th": "Thailand",
        "tj": "Tajikistan",
        "tm": "Turkmenistan",
        "tn": "Tunisia",
        "tr": "Turkey",
        "tt": "Trinidad and Tobago",
        "tw": "Taiwan",
        "tz": "Tanzania",
        "ua": "Ukraine",
        "ug": "Uganda",
        "us": "United States of America",
        "uy": "Uruguay",
        "uz": "Uzbekistan",
        "vc": "Saint Vincent and the Grenadines",
        "ve": "Venezuela",
        "vg": "British Virgin Islands",
        "vn": "Vietnam",
        "ye": "Yemen",
        "za": "South Africa",
        "zw": "Zimbabwe",
    }.items()
}

ALL_COUNTRIES: list[str] = list(COUNTRIES.keys())


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


def detect_store(raw: str) -> Store:
    """Detect which store an app ID or URL belongs to."""
    if _APP_STORE_URL_PATTERN.search(raw):
        return "appstore"
    if "play.google.com" in raw:
        return "googleplay"
    if raw.isdigit():
        return "appstore"
    if _PACKAGE_NAME_PATTERN.match(raw):
        return "googleplay"
    raise ValueError(
        f"Cannot detect store for {raw!r}. Use --store apple or --store google."
    )


def normalize_google_app_id(raw: str) -> str:
    """Normalize a Google Play app ID from URL or package name."""
    match = _GOOGLE_PLAY_URL_PATTERN.search(raw)
    if match:
        return match.group(1)
    if _PACKAGE_NAME_PATTERN.match(raw):
        return raw
    raise ValueError(f"Invalid Google Play app ID: {raw!r}")


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
