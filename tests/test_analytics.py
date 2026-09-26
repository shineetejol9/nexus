import pytest
from backend.analytics import (
    calculate_basic_statistics,
    calculate_category_counts,
    analyze_dataset,
    calculate_kpis
)


# ---------------------------------------------------------
# Tests for calculate_basic_statistics()
# ---------------------------------------------------------

def test_calculate_basic_statistics_numeric_columns():
    """Verifies calculation of count, minimum, maximum, and average for numeric columns."""
    rows = [
        {"name": "Rahul", "salary": "50000", "age": "25"},
        {"name": "Amit", "salary": "40000", "age": "35"}
    ]

    stats = calculate_basic_statistics(rows)

    # Check salary column statistics
    assert "salary" in stats
    assert stats["salary"]["count"] == 2
    assert stats["salary"]["minimum"] == 40000.0
    assert stats["salary"]["maximum"] == 50000.0
    assert stats["salary"]["average"] == 45000.0

    # Check age column statistics
    assert "age" in stats
    assert stats["age"]["count"] == 2
    assert stats["age"]["minimum"] == 25.0
    assert stats["age"]["maximum"] == 35.0
    assert stats["age"]["average"] == 30.0


def test_calculate_basic_statistics_ignores_non_numeric():
    """Verifies that non-numeric values (text/empty) are ignored during basic statistics calculation."""
    rows = [
        {"name": "Rahul", "salary": "50000"},
        {"name": "Amit", "salary": "abc"},
        {"name": "Priya", "salary": ""}
    ]

    stats = calculate_basic_statistics(rows)

    assert stats["salary"]["count"] == 1
    assert stats["salary"]["minimum"] == 50000.0
    assert stats["salary"]["maximum"] == 50000.0
    assert stats["salary"]["average"] == 50000.0

    assert "name" not in stats


# ---------------------------------------------------------
# Tests for calculate_category_counts()
# ---------------------------------------------------------

def test_calculate_category_counts_text_columns():
    """Verifies frequency counting for categorical/text columns."""
    rows = [
        {"name": "Rahul", "department": "IT"},
        {"name": "Amit", "department": "HR"},
        {"name": "Priya", "department": "IT"}
    ]

    counts = calculate_category_counts(rows)

    assert "department" in counts
    assert counts["department"]["IT"] == 2
    assert counts["department"]["HR"] == 1

    assert "name" in counts
    assert counts["name"]["Rahul"] == 1
    assert counts["name"]["Amit"] == 1
    assert counts["name"]["Priya"] == 1


def test_calculate_category_counts_ignores_numeric_and_empty():
    """Verifies that numeric values and empty/whitespace strings are ignored in category counts."""
    rows = [
        {"department": "IT", "salary": "50000"},
        {"department": "HR", "salary": "40000"},
        {"department": "", "salary": "60000"},
        {"department": "  ", "salary": "70000"}
    ]

    counts = calculate_category_counts(rows)

    assert counts["department"]["IT"] == 1
    assert counts["department"]["HR"] == 1
    assert "" not in counts["department"]

    assert "salary" not in counts


# ---------------------------------------------------------
# Tests for analyze_dataset()
# ---------------------------------------------------------

def test_analyze_dataset_structure_and_content():
    """Verifies that analyze_dataset returns both 'numeric' and 'categorical' sections with correct metrics."""
    rows = [
        {"name": "Rahul", "department": "IT", "salary": "50000"},
        {"name": "Amit", "department": "HR", "salary": "40000"},
        {"name": "Priya", "department": "IT", "salary": "60000"}
    ]

    analysis = analyze_dataset(rows)

    assert "numeric" in analysis
    assert "categorical" in analysis

    assert "salary" in analysis["numeric"]
    assert analysis["numeric"]["salary"]["count"] == 3
    assert analysis["numeric"]["salary"]["average"] == 50000.0

    assert "department" in analysis["categorical"]
    assert analysis["categorical"]["department"]["IT"] == 2
    assert analysis["categorical"]["department"]["HR"] == 1


# ---------------------------------------------------------
# Tests for calculate_kpis()
# ---------------------------------------------------------

def test_calculate_kpis_counts():
    """Verifies calculate_kpis calculates total_rows, numeric_columns, and categorical_columns correctly."""
    rows = [
        {"id": "101", "name": "Rahul", "department": "IT", "salary": "50000"},
        {"id": "102", "name": "Amit", "department": "HR", "salary": "40000"}
    ]

    kpis = calculate_kpis(rows)

    assert kpis["total_rows"] == 2
    assert kpis["numeric_columns"] == 2
    assert kpis["categorical_columns"] == 2


# ---------------------------------------------------------
# Edge case tests for empty dataset
# ---------------------------------------------------------

def test_empty_dataset_behavior():
    """Verifies that all analytics functions safely return empty dicts for an empty dataset []."""
    assert calculate_basic_statistics([]) == {}
    assert calculate_category_counts([]) == {}
    assert analyze_dataset([]) == {}
    assert calculate_kpis([]) == {}
