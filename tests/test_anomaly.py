"""
Unit tests for backend/anomaly.py.

Tests statistical anomaly detection using Interquartile Range (IQR).
"""

import sys
from pathlib import Path

# Add backend to Python path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from anomaly import detect_anomalies


def test_detect_anomalies_no_outliers():
    """Verify that a dataset with consistent values returns no anomalies."""
    rows = [
        {"age": "20"},
        {"age": "21"},
        {"age": "22"},
        {"age": "20"},
        {"age": "21"},
        {"age": "22"},
        {"age": "20"},
        {"age": "21"},
    ]
    anomalies = detect_anomalies(rows)
    assert anomalies == []


def test_detect_anomalies_with_iqr_outlier():
    """Verify that an obvious IQR outlier is detected with the correct dictionary structure."""
    rows = [
        {"val": "10"},
        {"val": "10"},
        {"val": "10"},
        {"val": "11"},
        {"val": "11"},
        {"val": "11"},
        {"val": "12"},
        {"val": "12"},
        {"val": "500"},  # Obvious statistical outlier
    ]

    anomalies = detect_anomalies(rows)
    assert len(anomalies) == 1

    anomaly = anomalies[0]
    assert anomaly["column"] == "val"
    assert anomaly["value"] == 500.0
    assert "lower_bound" in anomaly
    assert "upper_bound" in anomaly
    assert anomaly["row"] == {"val": "500"}


def test_iqr_calculation_values():
    """Verify that lower_bound and upper_bound strictly follow the current IQR implementation."""
    # 8 sorted values: [10, 20, 30, 40, 50, 60, 70, 80]
    # q1_index = 8 // 4 = 2 -> q1 = 30
    # q3_index = (3 * 8) // 4 = 6 -> q3 = 70
    # iqr = 70 - 30 = 40
    # lower_bound = 30 - (1.5 * 40) = -30.0
    # upper_bound = 70 + (1.5 * 40) = 130.0
    rows = [
        {"val": "10"},
        {"val": "20"},
        {"val": "30"},
        {"val": "40"},
        {"val": "50"},
        {"val": "60"},
        {"val": "70"},
        {"val": "80"},
        {"val": "200"},  # 200 > 130.0 (upper bound outlier)
    ]

    anomalies = detect_anomalies(rows)
    assert len(anomalies) == 1
    anomaly = anomalies[0]

    # Check calculated bounds based on current implementation
    # 9 values: [10, 20, 30, 40, 50, 60, 70, 80, 200]
    # q1_index = 9 // 4 = 2 -> q1 = 30
    # q3_index = (3 * 9) // 4 = 6 -> q3 = 70
    # lower_bound = -30.0, upper_bound = 130.0
    assert anomaly["lower_bound"] == -30.0
    assert anomaly["upper_bound"] == 130.0
    assert anomaly["value"] == 200.0


def test_fewer_than_four_numeric_values_skipped():
    """Verify that columns with fewer than 4 numeric values are skipped."""
    rows = [
        {"val": "10"},
        {"val": "20"},
        {"val": "300"},  # Even if 300 looks like an outlier, len(values) = 3 < 4
    ]
    anomalies = detect_anomalies(rows)
    assert anomalies == []


def test_non_numeric_values_ignored():
    """Verify that non-numeric values are safely ignored during float conversion."""
    rows = [
        {"score": "10"},
        {"score": "invalid_text"},
        {"score": "10"},
        {"score": "N/A"},
        {"score": "10"},
        {"score": ""},
        {"score": "10"},
        {"score": "11"},
        {"score": "11"},
        {"score": "999"},  # Outlier among 7 valid numbers
    ]
    anomalies = detect_anomalies(rows)
    assert len(anomalies) == 1
    assert anomalies[0]["column"] == "score"
    assert anomalies[0]["value"] == 999.0


def test_multiple_numeric_columns():
    """Verify that multiple numeric columns in the dataset are evaluated for anomalies."""
    rows = [
        {"age": "20", "salary": "50000"},
        {"age": "21", "salary": "52000"},
        {"age": "20", "salary": "51000"},
        {"age": "22", "salary": "53000"},
        {"age": "21", "salary": "50000"},
        {"age": "20", "salary": "52000"},
        {"age": "21", "salary": "51000"},
        {"age": "200", "salary": "9999999"},  # Outlier in both columns
    ]
    anomalies = detect_anomalies(rows)
    columns_with_anomalies = {a["column"] for a in anomalies}
    assert "age" in columns_with_anomalies
    assert "salary" in columns_with_anomalies


def test_empty_dataset():
    """Verify that an empty dataset returns an empty list."""
    anomalies = detect_anomalies([])
    assert anomalies == []


def test_only_non_numeric_dataset():
    """Verify that a dataset with only categorical/text values returns no anomalies without crashing."""
    rows = [
        {"name": "Alice", "city": "New York"},
        {"name": "Bob", "city": "London"},
        {"name": "Charlie", "city": "Paris"},
        {"name": "David", "city": "Tokyo"},
    ]
    anomalies = detect_anomalies(rows)
    assert anomalies == []
