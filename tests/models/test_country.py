"""Tests for Country enum and region groups."""

from app_reviews.models.country import Country


def test_country_is_str_enum():
    assert isinstance(Country.US, str)
    assert Country.US == "us"
    assert Country.GB == "gb"
    assert Country.DE == "de"
    assert Country.JP == "jp"


def test_country_value_is_lowercase_code():
    for member in Country:
        assert member.value == member.value.lower()
        assert len(member.value) == 2


def test_all_group_contains_every_member():
    assert Country.ALL == frozenset(Country)


def test_europe_group():
    assert Country.DE in Country.EUROPE
    assert Country.FR in Country.EUROPE
    assert Country.GB in Country.EUROPE
    assert Country.US not in Country.EUROPE


def test_americas_group():
    assert Country.US in Country.AMERICAS
    assert Country.CA in Country.AMERICAS
    assert Country.BR in Country.AMERICAS
    assert Country.DE not in Country.AMERICAS


def test_asia_pacific_group():
    assert Country.JP in Country.ASIA_PACIFIC
    assert Country.KR in Country.ASIA_PACIFIC
    assert Country.AU in Country.ASIA_PACIFIC
    assert Country.US not in Country.ASIA_PACIFIC


def test_middle_east_group():
    assert Country.SA in Country.MIDDLE_EAST
    assert Country.AE in Country.MIDDLE_EAST
    assert Country.QA in Country.MIDDLE_EAST
    assert Country.US not in Country.MIDDLE_EAST


def test_english_speaking_group():
    assert Country.US in Country.ENGLISH_SPEAKING
    assert Country.GB in Country.ENGLISH_SPEAKING
    assert Country.AU in Country.ENGLISH_SPEAKING
    assert Country.CA in Country.ENGLISH_SPEAKING
    assert Country.DE not in Country.ENGLISH_SPEAKING


def test_string_accepted_where_country_expected():
    countries = [Country.US, Country.GB]
    assert "us" in countries
    assert "gb" in countries
