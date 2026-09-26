import csv
import pytest
from backend.transformation import (
    clean_text,
    transform_row,
    transform_file,
    save_transformed_data
)


# ---------------------------------------------------------
# Tests for clean_text()
# ---------------------------------------------------------

def test_clean_text_normal():
    """Checks clean_text with standard string."""
    assert clean_text("Rahul") == "Rahul"


def test_clean_text_leading_trailing_spaces():
    """Checks stripping of leading and trailing spaces."""
    assert clean_text("  Rahul  ") == "Rahul"


def test_clean_text_multiple_internal_spaces():
    """Checks normalization of multiple spaces between words into a single space."""
    assert clean_text("Rahul    Kumar") == "Rahul Kumar"
    assert clean_text("  Rahul   \t  Kumar  ") == "Rahul Kumar"


def test_clean_text_empty_string():
    """Checks clean_text with an empty string."""
    assert clean_text("") == ""
    assert clean_text("   ") == ""


def test_clean_text_none():
    """Checks clean_text returns empty string when None is passed."""
    assert clean_text(None) == ""


# ---------------------------------------------------------
# Tests for transform_row()
# ---------------------------------------------------------

def test_transform_row_column_and_value_formatting():
    """
    Verifies that transform_row:
    - Strips column names and converts to lowercase
    - Replaces spaces in column names with underscores
    - Cleans values using clean_text()
    """
    raw_row = {
        " Employee ID ": " 101 ",
        " Full Name ": "  Rahul   Kumar  ",
        "Joining Date": " 2024-01-15 "
    }

    transformed = transform_row(raw_row)

    assert "employee_id" in transformed
    assert "full_name" in transformed
    assert "joining_date" in transformed

    assert transformed["employee_id"] == "101"
    assert transformed["full_name"] == "Rahul Kumar"
    assert transformed["joining_date"] == "2024-01-15"


# ---------------------------------------------------------
# Tests for transform_file()
# ---------------------------------------------------------

def test_transform_file(tmp_path):
    """Creates a temporary CSV file, transforms it, and verifies returned columns and values."""
    csv_file = tmp_path / "raw_employees.csv"
    csv_content = (
        " Employee ID , Full Name , Salary \n"
        " 101 ,  Rahul   Kumar  ,  50000 \n"
        " 102 ,  Amit   Sharma  ,  45000 \n"
    )
    csv_file.write_text(csv_content, encoding="utf-8")

    transformed_data = transform_file(str(csv_file))

    assert len(transformed_data) == 2
    assert transformed_data[0] == {
        "employee_id": "101",
        "full_name": "Rahul Kumar",
        "salary": "50000"
    }
    assert transformed_data[1] == {
        "employee_id": "102",
        "full_name": "Amit Sharma",
        "salary": "45000"
    }


# ---------------------------------------------------------
# Tests for save_transformed_data()
# ---------------------------------------------------------

def test_save_transformed_data(tmp_path):
    """Verifies that transformed data is written to a CSV file correctly."""
    data = [
        {"employee_id": "101", "full_name": "Rahul Kumar", "salary": "50000"},
        {"employee_id": "102", "full_name": "Amit Sharma", "salary": "45000"}
    ]
    output_file = tmp_path / "transformed_output.csv"

    save_transformed_data(data, str(output_file))

    assert output_file.exists()

    with open(output_file, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    assert len(reader) == 2
    assert reader[0] == {"employee_id": "101", "full_name": "Rahul Kumar", "salary": "50000"}
    assert reader[1] == {"employee_id": "102", "full_name": "Amit Sharma", "salary": "45000"}


# ---------------------------------------------------------
# Edge case tests for empty dataset
# ---------------------------------------------------------

def test_save_transformed_data_empty(tmp_path):
    """Verifies that save_transformed_data returns safely without creating file when data is empty."""
    output_file = tmp_path / "empty_output.csv"
    save_transformed_data([], str(output_file))

    assert not output_file.exists()


def test_transform_file_empty(tmp_path):
    """Verifies transform_file returns empty list when CSV has only header or no rows."""
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text(" Employee ID , Full Name \n", encoding="utf-8")

    result = transform_file(str(csv_file))
    assert result == []
