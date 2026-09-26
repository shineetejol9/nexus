import pytest
from backend.cleaning import detect_column_type, is_valid, clean_file


# ---------------------------------------------------------
# Tests for detect_column_type()
# ---------------------------------------------------------

def test_detect_column_type_number():
    """Checks that a list of numeric strings is detected as NUMBER."""
    values = ["100", "50.5", "0.25", "3000"]
    assert detect_column_type(values) == "NUMBER"


def test_detect_column_type_date():
    """Checks that a list of YYYY-MM-DD date strings is detected as DATE."""
    values = ["2024-01-15", "2024-02-20", "2024-03-10"]
    assert detect_column_type(values) == "DATE"


def test_detect_column_type_text():
    """Checks that a list of alphabetic names is detected as TEXT."""
    values = ["Rahul", "Amit", "Priya", "Rohan"]
    assert detect_column_type(values) == "TEXT"


def test_detect_column_type_alphanumeric():
    """Checks that a list of alphanumeric codes is detected as ALPHANUMERIC."""
    values = ["EMP101", "EMP102", "EMP103"]
    assert detect_column_type(values) == "ALPHANUMERIC"


def test_detect_column_type_with_empty_values():
    """Checks type detection ignores empty or whitespace-only strings."""
    values = ["", "  ", "2024-05-18", "2024-06-20"]
    assert detect_column_type(values) == "DATE"


# ---------------------------------------------------------
# Tests for is_valid()
# ---------------------------------------------------------

def test_is_valid_empty_value():
    """Checks that empty or whitespace-only strings return False for any data type."""
    assert is_valid("", "NUMBER") is False
    assert is_valid("   ", "DATE") is False
    assert is_valid("", "TEXT") is False
    assert is_valid("", "ALPHANUMERIC") is False


def test_is_valid_number_valid_and_invalid():
    """Checks positive numbers return True and non-numeric strings return False."""
    # Valid positive numbers
    assert is_valid("50000", "NUMBER") is True
    assert is_valid("45.5", "NUMBER") is True

    # Invalid numeric strings
    assert is_valid("abc", "NUMBER") is False
    assert is_valid("12a34", "NUMBER") is False


def test_is_valid_number_negative_and_zero():
    """Checks negative numbers and zero return False under current implementation (float(value) > 0)."""
    assert is_valid("-30000", "NUMBER") is False
    assert is_valid("0", "NUMBER") is False
    assert is_valid("-5.5", "NUMBER") is False


def test_is_valid_date_valid_and_invalid():
    """Checks YYYY-MM-DD dates return True, while invalid formats return False."""
    # Valid dates
    assert is_valid("2024-01-15", "DATE") is True
    assert is_valid("2024-12-31", "DATE") is True

    # Invalid date formats
    assert is_valid("10-10-2024", "DATE") is False
    assert is_valid("wrong-date", "DATE") is False
    assert is_valid("2024/01/15", "DATE") is False


def test_is_valid_text():
    """Checks text validation for alphabetic words."""
    assert is_valid("Rahul", "TEXT") is True
    assert is_valid("John Doe", "TEXT") is True
    assert is_valid("12345", "TEXT") is False
    assert is_valid("EMP109", "TEXT") is False


def test_is_valid_alphanumeric():
    """Checks alphanumeric validation for letters and numbers."""
    assert is_valid("EMP109", "ALPHANUMERIC") is True
    assert is_valid("101", "ALPHANUMERIC") is True
    assert is_valid("EMP-109", "ALPHANUMERIC") is False


# ---------------------------------------------------------
# Tests for clean_file()
# ---------------------------------------------------------

def test_clean_file_valid_invalid_and_duplicates(tmp_path):
    """
    Creates a temporary CSV file with valid, invalid, and duplicate rows,
    then verifies clean_file separates them correctly into clean_data and bad_data.
    """
    csv_file = tmp_path / "sample_employees.csv"
    csv_content = (
        "employee_id,name,department,salary,joining_date\n"
        "101,Rahul,IT,50000,2024-01-15\n"       # Valid row
        "102,Amit,HR,45000,2024-02-20\n"        # Valid row
        "101,Rahul,IT,50000,2024-01-15\n"       # Duplicate row -> bad_data
        "103,Rohan,IT,abc,2024-04-12\n"         # Invalid salary ("abc") -> bad_data
        "104,Neha,HR,-30000,2024-05-18\n"       # Negative salary (-30000) -> bad_data
        "105,Sumit,IT,65000,wrong-date\n"       # Invalid date -> bad_data
    )
    csv_file.write_text(csv_content, encoding="utf-8")

    clean_data, bad_data = clean_file(str(csv_file))

    # Verify clean rows
    assert len(clean_data) == 2
    assert clean_data[0]["name"] == "Rahul"
    assert clean_data[1]["name"] == "Amit"

    # Verify bad rows (1 duplicate + 3 invalid rows = 4 bad rows)
    assert len(bad_data) == 4
    bad_names = [row["name"] for row in bad_data]
    assert "Rahul" in bad_names     # Duplicate row
    assert "Rohan" in bad_names     # Invalid salary "abc"
    assert "Neha" in bad_names      # Negative salary -30000
    assert "Sumit" in bad_names     # Invalid date "wrong-date"
