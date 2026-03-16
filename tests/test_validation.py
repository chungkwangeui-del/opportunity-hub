"""Tests for scraper validation and normalization."""
import pytest
from datetime import date

from scraper import (
    normalize_country,
    normalize_field,
    normalize_type,
    parse_deadline,
    is_valid_url,
    validate_opportunity,
)


class TestNormalizeCountry:
    def test_none_returns_usa(self):
        assert normalize_country(None) == "USA"

    def test_empty_returns_usa(self):
        assert normalize_country("") == "USA"

    def test_aliases(self):
        assert normalize_country("united states") == "USA"
        assert normalize_country("us") == "USA"
        assert normalize_country("usa") == "USA"
        assert normalize_country("south korea") == "South Korea"
        assert normalize_country("korea") == "South Korea"

    def test_already_valid(self):
        assert normalize_country("USA") == "USA"
        assert normalize_country("South Korea") == "South Korea"

    def test_unknown_passthrough(self):
        assert normalize_country("Canada") == "Canada"


class TestNormalizeField:
    def test_none_returns_general_stem(self):
        assert normalize_field(None) == "General STEM"

    def test_aliases(self):
        assert normalize_field("cs") == "Computer Science"
        assert normalize_field("bio") == "Biology"
        assert normalize_field("chem") == "Chemistry"
        assert normalize_field("ml") == "Data Science"

    def test_already_valid(self):
        assert normalize_field("Computer Science") == "Computer Science"
        assert normalize_field("Biology") == "Biology"


class TestNormalizeType:
    def test_none_returns_internship(self):
        assert normalize_type(None) == "Internship"

    def test_aliases(self):
        assert normalize_type("reu") == "Research"
        assert normalize_type("intern") == "Internship"
        assert normalize_type("co-op") == "Co-op"


class TestParseDeadline:
    def test_none_empty_unknown_rolling_return_none(self):
        assert parse_deadline(None) is None
        assert parse_deadline("") is None
        assert parse_deadline("Unknown") is None
        assert parse_deadline("Rolling") is None

    def test_valid_date(self):
        assert parse_deadline("2026-03-15") == date(2026, 3, 15)
        assert parse_deadline("2026-12-31") == date(2026, 12, 31)

    def test_long_string_truncated(self):
        assert parse_deadline("2026-01-01T00:00:00Z") == date(2026, 1, 1)

    def test_invalid_returns_none(self):
        assert parse_deadline("not-a-date") is None
        assert parse_deadline("2026-13-01") is None


class TestIsValidUrl:
    def test_none_empty_false(self):
        assert is_valid_url(None) is False
        assert is_valid_url("") is False

    def test_valid_http_https(self):
        assert is_valid_url("https://example.com") is True
        assert is_valid_url("http://example.com/path") is True

    def test_invalid_scheme(self):
        assert is_valid_url("ftp://example.com") is False
        assert is_valid_url("javascript:alert(1)") is False

    def test_no_netloc(self):
        assert is_valid_url("http://") is False


class TestValidateOpportunity:
    def test_valid_minimal(self):
        opp = {
            "organization": "Test Org",
            "title": "Test Title",
            "url": "https://example.com",
            "country": "USA",
        }
        result = validate_opportunity(opp)
        assert result is not None
        assert result["organization"] == "Test Org"
        assert result["title"] == "Test Title"
        assert result["url"] == "https://example.com"
        assert result["country"] == "USA"
        assert result["field"] == "General STEM"
        assert result["opportunity_type"] == "Internship"

    def test_invalid_url_returns_none(self):
        opp = {
            "organization": "Test",
            "title": "Test",
            "url": "not-a-url",
            "country": "USA",
        }
        assert validate_opportunity(opp) is None

    def test_invalid_country_returns_none(self):
        opp = {
            "organization": "Test",
            "title": "Test",
            "url": "https://example.com",
            "country": "Canada",
        }
        assert validate_opportunity(opp) is None

    def test_normalizes_aliases(self):
        opp = {
            "organization": "Test",
            "title": "Test",
            "url": "https://example.com",
            "country": "us",
            "field": "cs",
            "opportunity_type": "intern",
        }
        result = validate_opportunity(opp)
        assert result is not None
        assert result["country"] == "USA"
        assert result["field"] == "Computer Science"
        assert result["opportunity_type"] == "Internship"
