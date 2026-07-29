"""Tests for app input and country normalization."""

import pytest

from app_reviews.utils.parsing import (
    ALL_COUNTRIES,
    detect_store,
    normalize_app_id,
    normalize_app_ids,
    normalize_countries,
    normalize_google_app_id,
)

# ---------------------------------------------------------------------------
# normalize_app_id
# ---------------------------------------------------------------------------


class TestNormalizeAppId:
    def test_numeric_id_passthrough(self) -> None:
        assert normalize_app_id("123456789") == "123456789"

    def test_numeric_id_different_length(self) -> None:
        assert normalize_app_id("9876543210") == "9876543210"

    def test_url_full_with_country_and_name(self) -> None:
        assert (
            normalize_app_id("https://apps.apple.com/us/app/example/id123456789")
            == "123456789"
        )

    def test_url_without_country(self) -> None:
        assert normalize_app_id("https://apps.apple.com/app/id123456789") == "123456789"

    def test_url_with_query_string(self) -> None:
        assert (
            normalize_app_id("https://apps.apple.com/us/app/example/id555000501?mt=8")
            == "555000501"
        )

    def test_url_different_country(self) -> None:
        assert (
            normalize_app_id("https://apps.apple.com/gb/app/myapp/id999111222")
            == "999111222"
        )

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            normalize_app_id("")

    def test_url_without_id_raises(self) -> None:
        with pytest.raises(ValueError):
            normalize_app_id("https://apps.apple.com/us/app/example/")

    def test_non_url_non_numeric_raises(self) -> None:
        with pytest.raises(ValueError):
            normalize_app_id("not-an-id")

    def test_alphabetic_string_raises(self) -> None:
        with pytest.raises(ValueError):
            normalize_app_id("myappname")

    def test_url_id_keyword_without_digits_raises(self) -> None:
        with pytest.raises(ValueError):
            normalize_app_id("https://apps.apple.com/us/app/example/id")


# ---------------------------------------------------------------------------
# normalize_app_ids
# ---------------------------------------------------------------------------


class TestNormalizeAppIds:
    def test_list_of_numeric_ids(self) -> None:
        assert normalize_app_ids(["111", "222", "333"]) == ["111", "222", "333"]

    def test_order_preserved(self) -> None:
        ids = ["999", "111", "555"]
        assert normalize_app_ids(ids) == ids

    def test_mixed_urls_and_ids(self) -> None:
        result = normalize_app_ids(
            [
                "123456789",
                "https://apps.apple.com/us/app/foo/id987654321",
            ]
        )
        assert result == ["123456789", "987654321"]

    def test_invalid_entry_raises(self) -> None:
        with pytest.raises(ValueError):
            normalize_app_ids(["123", "bad-input"])

    def test_empty_list(self) -> None:
        assert normalize_app_ids([]) == []


# ---------------------------------------------------------------------------
# normalize_countries
# ---------------------------------------------------------------------------


class TestNormalizeCountries:
    def test_all_expands_to_all_countries(self) -> None:
        result = normalize_countries(["all"])
        assert result == ALL_COUNTRIES

    def test_valid_codes_passthrough(self) -> None:
        assert normalize_countries(["us", "gb"]) == ["us", "gb"]

    def test_order_preserved(self) -> None:
        codes = ["de", "fr", "jp"]
        assert normalize_countries(codes) == codes

    def test_duplicates_deduplicated(self) -> None:
        result = normalize_countries(["us", "gb", "us"])
        assert result.count("us") == 1
        assert "gb" in result

    def test_uppercase_raises(self) -> None:
        with pytest.raises(ValueError, match="US"):
            normalize_countries(["US"])

    def test_too_long_raises(self) -> None:
        with pytest.raises(ValueError):
            normalize_countries(["usa"])

    def test_numeric_raises(self) -> None:
        with pytest.raises(ValueError):
            normalize_countries(["12"])

    def test_empty_code_raises(self) -> None:
        with pytest.raises(ValueError):
            normalize_countries([""])

    def test_empty_list(self) -> None:
        assert normalize_countries([]) == []

    def test_unknown_but_valid_format_accepted(self) -> None:
        # Any 2-lowercase-letter code is structurally valid
        result = normalize_countries(["zz"])
        assert result == ["zz"]


# ---------------------------------------------------------------------------
# detect_store
# ---------------------------------------------------------------------------


class TestDetectStore:
    def test_numeric_is_apple(self) -> None:
        assert detect_store("284882215") == "appstore"

    def test_apple_url(self) -> None:
        assert detect_store("https://apps.apple.com/app/id284882215") == "appstore"

    def test_package_name_is_google(self) -> None:
        assert detect_store("com.whatsapp") == "googleplay"

    def test_google_url(self) -> None:
        url = "https://play.google.com/store/apps/details?id=com.whatsapp"
        assert detect_store(url) == "googleplay"

    def test_ambiguous_raises(self) -> None:
        with pytest.raises(ValueError, match="Cannot detect store"):
            detect_store("ambiguous-input")

    def test_multi_segment_package(self) -> None:
        assert detect_store("com.example.myapp") == "googleplay"

    def test_org_package(self) -> None:
        assert detect_store("org.mozilla.firefox") == "googleplay"


# ---------------------------------------------------------------------------
# normalize_google_app_id
# ---------------------------------------------------------------------------


class TestNormalizeGoogleAppId:
    def test_package_name_passthrough(self) -> None:
        assert normalize_google_app_id("com.whatsapp") == "com.whatsapp"

    def test_url_extraction(self) -> None:
        url = "https://play.google.com/store/apps/details?id=com.whatsapp"
        assert normalize_google_app_id(url) == "com.whatsapp"

    def test_url_with_extra_params(self) -> None:
        url = "https://play.google.com/store/apps/details?id=com.app&hl=en"
        assert normalize_google_app_id(url) == "com.app"

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid Google Play"):
            normalize_google_app_id("not-a-package")
