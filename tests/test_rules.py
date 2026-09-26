"""
Unit tests for backend/rules.py module.

Tests individual rule check functions and composite business rules validation.
"""

import sys
from pathlib import Path
import pytest

# Add backend to Python path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from rules import (
    check_required,
    check_range,
    check_min,
    check_max,
    check_positive,
    check_non_negative,
    check_integer,
    check_decimal,
    check_allowed_values,
    check_min_length,
    check_max_length,
    check_regex,
    check_date_format,
    check_email,
    validate_business_rules,
)


# ==========================================
# 1. INDIVIDUAL RULE CHECKER TESTS
# ==========================================

def test_check_required():
    """Verify check_required validates non-empty, non-None strings."""
    assert check_required("valid text") is True
    assert check_required("  text  ") is True
    assert check_required("") is False
    assert check_required("   ") is False
    assert check_required(None) is False


def test_check_range():
    """Verify check_range checks numeric bounds and handles invalid inputs."""
    assert check_range("15", minimum=10, maximum=20) is True
    assert check_range("10", minimum=10, maximum=20) is True
    assert check_range("20", minimum=10, maximum=20) is True
    assert check_range("5", minimum=10, maximum=20) is False
    assert check_range("25", minimum=10, maximum=20) is False
    assert check_range("15", minimum=10, maximum=None) is True
    assert check_range("5", minimum=10, maximum=None) is False
    assert check_range("15", minimum=None, maximum=20) is True
    assert check_range("25", minimum=None, maximum=20) is False
    assert check_range("not_a_number", minimum=10, maximum=20) is False


def test_check_min():
    """Verify check_min enforces minimum threshold."""
    assert check_min("10", 10) is True
    assert check_min("15.5", 10) is True
    assert check_min("9.99", 10) is False
    assert check_min("invalid", 10) is False


def test_check_max():
    """Verify check_max enforces maximum threshold."""
    assert check_max("20", 20) is True
    assert check_max("15.5", 20) is True
    assert check_max("20.01", 20) is False
    assert check_max("invalid", 20) is False


def test_check_positive():
    """Verify check_positive allows only numbers strictly greater than 0."""
    assert check_positive("0.001") is True
    assert check_positive("100") is True
    assert check_positive("0") is False
    assert check_positive("-10") is False
    assert check_positive("abc") is False


def test_check_non_negative():
    """Verify check_non_negative allows 0 and positive numbers."""
    assert check_non_negative("0") is True
    assert check_non_negative("10.5") is True
    assert check_non_negative("-0.01") is False
    assert check_non_negative("invalid") is False


def test_check_integer():
    """Verify check_integer validates whole numbers."""
    assert check_integer("100") is True
    assert check_integer("-50") is True
    assert check_integer("0") is True
    assert check_integer("10.5") is False
    assert check_integer("abc") is False


def test_check_decimal():
    """Verify check_decimal validates floating-point numbers."""
    assert check_decimal("10.5") is True
    assert check_decimal("100") is True
    assert check_decimal("-3.14") is True
    assert check_decimal("invalid") is False


def test_check_allowed_values():
    """Verify check_allowed_values checks inclusion in set/list."""
    allowed = ["Active", "Pending", "Inactive"]
    assert check_allowed_values("Active", allowed) is True
    assert check_allowed_values("Deleted", allowed) is False


def test_check_min_length():
    """Verify check_min_length validates string length lower bound."""
    assert check_min_length("hello", 3) is True
    assert check_min_length("abc", 3) is True
    assert check_min_length("hi", 3) is False


def test_check_max_length():
    """Verify check_max_length validates string length upper bound."""
    assert check_max_length("hello", 5) is True
    assert check_max_length("hi", 5) is True
    assert check_max_length("hello world", 5) is False


def test_check_regex():
    """Verify check_regex performs full pattern matching."""
    pattern = r"^[A-Z]{3}-\d{3}$"
    assert check_regex("ABC-123", pattern) is True
    assert check_regex("abc-123", pattern) is False
    assert check_regex("ABC-1234", pattern) is False


def test_check_date_format():
    """Verify check_date_format parses date string against specific format."""
    assert check_date_format("2026-09-26", "%Y-%m-%d") is True
    assert check_date_format("26/09/2026", "%Y-%m-%d") is False
    assert check_date_format("not-a-date", "%Y-%m-%d") is False


def test_check_email():
    """Verify check_email validates basic email address structure."""
    assert check_email("user@example.com") is True
    assert check_email("john.doe@sub.domain.org") is True
    assert check_email("invalid-email") is False
    assert check_email("user@domain") is False
    assert check_email("user @domain.com") is False
    assert check_email("") is False


# ==========================================
# 2. BUSINESS RULES VALIDATION TESTS
# ==========================================

def test_validate_business_rules_all_valid():
    """Verify validate_business_rules returns True when all rules pass."""
    row = {
        "username": "john_doe",
        "age": "25",
        "status": "Active",
        "email": "john@example.com",
        "created": "2026-01-01",
    }
    rules = {
        "username": {"required": True, "min_length": 3, "max_length": 20, "regex": r"^[a-z_]+$"},
        "age": {"integer": True, "positive": True, "range": {"min": 18, "max": 100}},
        "status": {"allowed_values": ["Active", "Pending"]},
        "email": {"email": True},
        "created": {"date_format": "%Y-%m-%d"},
    }

    assert validate_business_rules(row, rules) is True


def test_validate_business_rules_column_missing_in_row():
    """Verify validate_business_rules skips evaluation if column is not present in row."""
    row = {"username": "john_doe"}
    rules = {
        "missing_col": {"required": True, "min": 100}
    }
    # Column missing_col is skipped, returns True
    assert validate_business_rules(row, rules) is True


def test_validate_business_rules_unknown_rule_name():
    """Verify validate_business_rules ignores unrecognized rule names."""
    row = {"age": "25"}
    rules = {"age": {"unknown_rule": "some_value"}}
    assert validate_business_rules(row, rules) is True


def test_validate_business_rules_failing_required():
    """Verify failure on required rule."""
    row = {"name": ""}
    rules = {"name": {"required": True}}
    assert validate_business_rules(row, rules) is False


def test_validate_business_rules_failing_range():
    """Verify failure on range rule."""
    row = {"score": "150"}
    rules = {"score": {"range": {"min": 0, "max": 100}}}
    assert validate_business_rules(row, rules) is False


def test_validate_business_rules_failing_min():
    """Verify failure on min rule."""
    row = {"age": "15"}
    rules = {"age": {"min": 18}}
    assert validate_business_rules(row, rules) is False


def test_validate_business_rules_failing_max():
    """Verify failure on max rule."""
    row = {"count": "50"}
    rules = {"count": {"max": 10}}
    assert validate_business_rules(row, rules) is False


def test_validate_business_rules_failing_positive():
    """Verify failure on positive rule."""
    row = {"price": "-10.5"}
    rules = {"price": {"positive": True}}
    assert validate_business_rules(row, rules) is False


def test_validate_business_rules_failing_non_negative():
    """Verify failure on non_negative rule."""
    row = {"balance": "-1"}
    rules = {"balance": {"non_negative": True}}
    assert validate_business_rules(row, rules) is False


def test_validate_business_rules_failing_integer():
    """Verify failure on integer rule."""
    row = {"qty": "12.34"}
    rules = {"qty": {"integer": True}}
    assert validate_business_rules(row, rules) is False


def test_validate_business_rules_failing_decimal():
    """Verify failure on decimal rule."""
    row = {"rate": "abc"}
    rules = {"rate": {"decimal": True}}
    assert validate_business_rules(row, rules) is False


def test_validate_business_rules_failing_allowed_values():
    """Verify failure on allowed_values rule."""
    row = {"role": "Guest"}
    rules = {"role": {"allowed_values": ["Admin", "Viewer"]}}
    assert validate_business_rules(row, rules) is False


def test_validate_business_rules_failing_min_length():
    """Verify failure on min_length rule."""
    row = {"code": "AB"}
    rules = {"code": {"min_length": 3}}
    assert validate_business_rules(row, rules) is False


def test_validate_business_rules_failing_max_length():
    """Verify failure on max_length rule."""
    row = {"code": "ABCDEF"}
    rules = {"code": {"max_length": 5}}
    assert validate_business_rules(row, rules) is False


def test_validate_business_rules_failing_regex():
    """Verify failure on regex rule."""
    row = {"id": "123"}
    rules = {"id": {"regex": r"^[A-Z]+$"}}
    assert validate_business_rules(row, rules) is False


def test_validate_business_rules_failing_date_format():
    """Verify failure on date_format rule."""
    row = {"dob": "2026/09/26"}
    rules = {"dob": {"date_format": "%Y-%m-%d"}}
    assert validate_business_rules(row, rules) is False


def test_validate_business_rules_failing_email():
    """Verify failure on email rule."""
    row = {"contact": "not_an_email"}
    rules = {"contact": {"email": True}}
    assert validate_business_rules(row, rules) is False


def test_validate_business_rules_rule_value_disabled():
    """Verify that setting boolean rule_value to False skips validation."""
    row = {"name": "", "price": "-10", "email": "bad_email"}
    rules = {
        "name": {"required": False},
        "price": {"positive": False, "non_negative": False, "integer": False, "decimal": False},
        "email": {"email": False},
    }
    assert validate_business_rules(row, rules) is True
