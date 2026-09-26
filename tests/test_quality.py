import pytest
from backend.quality import (
    load_csv,
    detect_type,
    is_valid_value,
    calculate_completeness,
    calculate_validity,
    calculate_uniqueness,
    calculate_consistency,
    calculate_timeliness,
    calculate_quality_score
)


# ---------------------------------------------------------
# Tests for load_csv()
# ---------------------------------------------------------

def test_load_csv(tmp_path):
    """Verifies that load_csv reads a valid CSV into dictionary rows."""
    csv_file = tmp_path / "students.csv"
    csv_file.write_text("id,name,score\n1,Rahul,90\n2,Amit,85\n", encoding="utf-8")

    rows = load_csv(str(csv_file))

    assert len(rows) == 2
    assert rows[0] == {"id": "1", "name": "Rahul", "score": "90"}
    assert rows[1] == {"id": "2", "name": "Amit", "score": "85"}


# ---------------------------------------------------------
# Tests for detect_type()
# ---------------------------------------------------------

def test_detect_type_number():
    """Checks detection of numeric values."""
    assert detect_type("100") == "NUMBER"
    assert detect_type("45.5") == "NUMBER"
    assert detect_type("-10") == "NUMBER"


def test_detect_type_date():
    """Checks detection of YYYY-MM-DD date strings."""
    assert detect_type("2024-01-15") == "DATE"


def test_detect_type_text():
    """Checks detection of alphabetic words."""
    assert detect_type("Rahul") == "TEXT"
    assert detect_type("John Doe") == "TEXT"


def test_detect_type_alphanumeric_and_other():
    """Checks detection of alphanumeric codes and empty/other strings."""
    assert detect_type("EMP101") == "ALPHANUMERIC"
    assert detect_type("") == "EMPTY"
    assert detect_type("   ") == "EMPTY"
    assert detect_type("user@email.com") == "OTHER"


# ---------------------------------------------------------
# Tests for is_valid_value()
# ---------------------------------------------------------

def test_is_valid_value_positive_number():
    """Checks positive numbers return True."""
    assert is_valid_value("50000") is True
    assert is_valid_value("45.5") is True


def test_is_valid_value_zero_and_negative_number():
    """Checks zero and negative numbers return False under current implementation (number > 0)."""
    assert is_valid_value("0") is False
    assert is_valid_value("-30000") is False


def test_is_valid_value_invalid_strings():
    """Checks that non-alphanumeric, non-numeric, non-date strings with symbols return False."""
    assert is_valid_value("!@#$%") is False
    assert is_valid_value("invalid-date") is False


def test_is_valid_value_date():
    """Checks YYYY-MM-DD dates return True, invalid date formats return False."""
    assert is_valid_value("2024-01-15") is True
    assert is_valid_value("10-10-2024") is False
    assert is_valid_value("invalid-date") is False


def test_is_valid_value_text():
    """Checks alphabetic text returns True, invalid text returns False."""
    assert is_valid_value("Rahul") is True
    assert is_valid_value("John Doe") is True
    assert is_valid_value("!@#$%") is False


def test_is_valid_value_empty():
    """Checks empty and whitespace strings return False."""
    assert is_valid_value("") is False
    assert is_valid_value("   ") is False


# ---------------------------------------------------------
# Tests for calculate_completeness()
# ---------------------------------------------------------

def test_calculate_completeness_full():
    """Verifies 100% completeness when all values are populated."""
    rows = [
        {"id": "1", "name": "Rahul", "score": "90"},
        {"id": "2", "name": "Amit", "score": "85"}
    ]
    assert calculate_completeness(rows) == 100.0


def test_calculate_completeness_partial():
    """Verifies completeness percentage with missing values (5 filled out of 6 cells = 83.33%)."""
    rows = [
        {"id": "1", "name": "Rahul", "score": "90"},
        {"id": "2", "name": "", "score": "85"}
    ]
    assert pytest.approx(calculate_completeness(rows), 0.01) == 83.33


# ---------------------------------------------------------
# Tests for calculate_validity()
# ---------------------------------------------------------

def test_calculate_validity_all_valid():
    """Verifies 100% validity when all values pass is_valid_value()."""
    rows = [
        {"id": "101", "name": "Rahul", "joining_date": "2024-01-15"},
        {"id": "102", "name": "Amit", "joining_date": "2024-02-20"}
    ]
    assert calculate_validity(rows) == 100.0


def test_calculate_validity_with_invalid_values():
    """Verifies validity score when some cells contain invalid values."""
    rows = [
        {"id": "101", "name": "Rahul", "joining_date": "2024-01-15"},
        {"id": "102", "name": "Amit", "joining_date": "wrong-date"}
    ]
    assert pytest.approx(calculate_validity(rows), 0.01) == 83.33


# ---------------------------------------------------------
# Tests for calculate_uniqueness()
# ---------------------------------------------------------

def test_calculate_uniqueness_unique_rows():
    """Verifies 100% uniqueness when all rows are unique."""
    rows = [
        {"id": "1", "name": "Rahul"},
        {"id": "2", "name": "Amit"}
    ]
    assert calculate_uniqueness(rows) == 100.0


def test_calculate_uniqueness_with_duplicates():
    """Verifies uniqueness score when duplicate rows exist."""
    rows = [
        {"id": "1", "name": "Rahul"},
        {"id": "2", "name": "Amit"},
        {"id": "1", "name": "Rahul"},
        {"id": "1", "name": "Rahul"}
    ]
    assert calculate_uniqueness(rows) == 50.0


# ---------------------------------------------------------
# Tests for calculate_consistency()
# ---------------------------------------------------------

def test_calculate_consistency_consistent_data():
    """Verifies 100% consistency when column data types remain consistent across rows."""
    rows = [
        {"id": "101", "name": "Rahul"},
        {"id": "102", "name": "Amit"}
    ]
    assert calculate_consistency(rows) == 100.0


def test_calculate_consistency_inconsistent_data():
    """Verifies consistency calculation when column types vary across rows."""
    rows = [
        {"score": "90"},
        {"score": "Rahul"}
    ]
    assert calculate_consistency(rows) == 50.0


# ---------------------------------------------------------
# Tests for calculate_timeliness()
# ---------------------------------------------------------

def test_calculate_timeliness_valid_and_invalid_dates():
    """Verifies timeliness score based on YYYY-MM-DD date validity in date columns."""
    rows = [
        {"joining_date": "2024-01-15"},
        {"joining_date": "wrong-date"}
    ]
    assert calculate_timeliness(rows) == 50.0


def test_calculate_timeliness_no_date_columns():
    """Verifies current implementation behavior returning 100% when no date column exists."""
    rows = [
        {"id": "101", "name": "Rahul"}
    ]
    assert calculate_timeliness(rows) == 100.0


# ---------------------------------------------------------
# Tests for calculate_quality_score()
# ---------------------------------------------------------

def test_calculate_quality_score():
    """Verifies quality score calculation as the average of 5 quality dimensions."""
    score = calculate_quality_score(100.0, 80.0, 60.0, 80.0, 80.0)
    assert score == 80.0


# ---------------------------------------------------------
# Edge case tests for empty datasets
# ---------------------------------------------------------

def test_empty_dataset_edge_cases():
    """Verifies that all quality metrics return 0 for an empty dataset."""
    assert calculate_completeness([]) == 0
    assert calculate_validity([]) == 0
    assert calculate_uniqueness([]) == 0
    assert calculate_consistency([]) == 0
    assert calculate_timeliness([]) == 0
