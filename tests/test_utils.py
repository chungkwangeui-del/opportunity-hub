"""Tests for scraper utility functions."""
import pytest

from scraper import _jsearch_comp, FIELD_ALIASES


def infer_field_from_keyword(keyword: str) -> str:
    """Replicate infer_field logic for testing."""
    kw = keyword.lower()
    for alias, field in FIELD_ALIASES.items():
        if alias in kw:
            return field
    return "General STEM"


class TestJsearchComp:
    def test_both_none_none(self):
        assert _jsearch_comp(None, None) is None

    def test_both_zero_none(self):
        assert _jsearch_comp(0, 0) is None

    def test_min_max(self):
        assert _jsearch_comp(50000, 80000) == "$50,000-$80,000"
        assert _jsearch_comp(100000, 150000) == "$100,000-$150,000"

    def test_min_only(self):
        assert _jsearch_comp(60000, None) == "$60,000"

    def test_invalid_returns_none(self):
        assert _jsearch_comp("invalid", 50000) is None


class TestInferField:
    def test_computer_science(self):
        assert infer_field_from_keyword("cs research") == "Computer Science"
        assert infer_field_from_keyword("computing internship") == "Computer Science"
        assert infer_field_from_keyword("software engineering") == "Computer Science"

    def test_biology(self):
        assert infer_field_from_keyword("biology lab") == "Biology"
        assert infer_field_from_keyword("bio research") == "Biology"

    def test_data_science(self):
        assert infer_field_from_keyword("machine learning internship") == "Data Science"
        assert infer_field_from_keyword("ai research") == "Data Science"

    def test_unknown_returns_general_stem(self):
        assert infer_field_from_keyword("unknown field xyz") == "General STEM"
