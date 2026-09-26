import pytest
from backend.profiling import (
    load_csv,
    detect_type,
    count_missing,
    count_unique,
    count_duplicate_rows,
    profile_columns,
    profile_dataset,
    profile_csv
)


# ---------------------------------------------------------
# Tests for load_csv()
# ---------------------------------------------------------

def test_load_csv_valid_file(tmp_path):
    """Verifies that a valid CSV file is loaded into a list of dictionary rows."""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("id,name\n1,Rahul\n2,Amit\n", encoding="utf-8")

    rows = load_csv(str(csv_file))

    assert len(rows) == 2
    assert rows[0] == {"id": "1", "name": "Rahul"}
    assert rows[1] == {"id": "2", "name": "Amit"}


# ---------------------------------------------------------
# Tests for detect_type()
# ---------------------------------------------------------

def test_detect_type_number():
    """Checks detection of positive, negative, zero, and decimal numeric values."""
    assert detect_type("100") == "NUMBER"
    assert detect_type("50.5") == "NUMBER"
    assert detect_type("-30.5") == "NUMBER"
    assert detect_type("0") == "NUMBER"


def test_detect_type_date():
    """Checks detection of YYYY-MM-DD date strings."""
    assert detect_type("2024-01-15") == "DATE"
    assert detect_type("2026-09-26") == "DATE"


def test_detect_type_text():
    """Checks detection of alphabetic text and words with spaces."""
    assert detect_type("Rahul") == "TEXT"
    assert detect_type("John Doe") == "TEXT"


def test_detect_type_alphanumeric():
    """Checks detection of mixed letter-and-number codes."""
    assert detect_type("EMP101") == "ALPHANUMERIC"
    assert detect_type("A123") == "ALPHANUMERIC"


def test_detect_type_empty():
    """Checks detection of empty and whitespace-only strings."""
    assert detect_type("") == "EMPTY"
    assert detect_type("   ") == "EMPTY"


def test_detect_type_other():
    """Checks detection of special characters or email addresses as OTHER."""
    assert detect_type("user@domain.com") == "OTHER"
    assert detect_type("item-100!") == "OTHER"


# ---------------------------------------------------------
# Tests for count_missing()
# ---------------------------------------------------------

def test_count_missing_no_missing():
    """Verifies count_missing returns 0 when no values are missing."""
    values = ["Rahul", "Amit", "Priya"]
    assert count_missing(values) == 0


def test_count_missing_some_missing():
    """Verifies count_missing accurately counts None, empty strings, and whitespace."""
    values = ["Rahul", "", "  ", None, "Priya"]
    assert count_missing(values) == 3


# ---------------------------------------------------------
# Tests for count_unique()
# ---------------------------------------------------------

def test_count_unique_all_unique():
    """Verifies count_unique when all values are distinct."""
    values = ["Rahul", "Amit", "Priya"]
    assert count_unique(values) == 3


def test_count_unique_with_duplicates():
    """Verifies count_unique ignores repeated values (including padded whitespace)."""
    values = ["Rahul", "Rahul", " Rahul ", "Amit"]
    assert count_unique(values) == 2


def test_count_unique_empty_values():
    """Verifies current behavior where empty strings count as unique entries if present."""
    values = ["", "   ", "Rahul"]
    assert count_unique(values) == 2


# ---------------------------------------------------------
# Tests for count_duplicate_rows()
# ---------------------------------------------------------

def test_count_duplicate_rows_with_duplicates():
    """Verifies counting of duplicate rows in a dataset."""
    rows = [
        {"id": "101", "name": "Rahul"},
        {"id": "102", "name": "Amit"},
        {"id": "101", "name": "Rahul"},
        {"id": "101", "name": "Rahul"}
    ]
    assert count_duplicate_rows(rows) == 2


def test_count_duplicate_rows_without_duplicates():
    """Verifies count_duplicate_rows returns 0 when all rows are unique."""
    rows = [
        {"id": "101", "name": "Rahul"},
        {"id": "102", "name": "Amit"}
    ]
    assert count_duplicate_rows(rows) == 0


# ---------------------------------------------------------
# Tests for profile_columns()
# ---------------------------------------------------------

def test_profile_columns():
    """Verifies column type, missing count, unique count, and type_counts per column."""
    rows = [
        {"id": "101", "name": "Rahul", "joining_date": "2024-01-15"},
        {"id": "102", "name": "Amit", "joining_date": "2024-02-20"},
        {"id": "103", "name": "", "joining_date": "invalid-date"}
    ]

    profile = profile_columns(rows)

    assert profile["id"]["type"] == "NUMBER"
    assert profile["id"]["missing"] == 0
    assert profile["id"]["unique"] == 3

    assert profile["name"]["type"] == "TEXT"
    assert profile["name"]["missing"] == 1
    assert profile["name"]["type_counts"]["EMPTY"] == 1

    assert profile["joining_date"]["type_counts"]["DATE"] == 2
    assert profile["joining_date"]["type_counts"]["OTHER"] == 1


# ---------------------------------------------------------
# Tests for profile_dataset()
# ---------------------------------------------------------

def test_profile_dataset_populated():
    """Verifies dataset summary counts for rows, columns, and duplicate rows."""
    rows = [
        {"id": "101", "name": "Rahul"},
        {"id": "102", "name": "Amit"},
        {"id": "101", "name": "Rahul"}
    ]
    result = profile_dataset(rows)

    assert result["rows"] == 3
    assert result["columns"] == 2
    assert result["duplicate_rows"] == 1


def test_profile_dataset_empty():
    """Verifies dataset profiling behavior when rows list is empty."""
    result = profile_dataset([])

    assert result["rows"] == 0
    assert result["columns"] == 0
    assert result["duplicate_rows"] == 0


# ---------------------------------------------------------
# Tests for profile_csv()
# ---------------------------------------------------------

def test_profile_csv(tmp_path):
    """Creates a temporary CSV file and verifies full profile_csv structure."""
    csv_file = tmp_path / "employees.csv"
    csv_content = (
        "employee_id,name,salary\n"
        "101,Rahul,50000\n"
        "102,Amit,45000\n"
    )
    csv_file.write_text(csv_content, encoding="utf-8")

    profile = profile_csv(str(csv_file))

    assert "dataset" in profile
    assert "columns" in profile
    assert profile["dataset"]["rows"] == 2
    assert profile["dataset"]["columns"] == 3
    assert profile["columns"]["employee_id"]["type"] == "NUMBER"
    assert profile["columns"]["name"]["type"] == "TEXT"
    assert profile["columns"]["salary"]["type"] == "NUMBER"
