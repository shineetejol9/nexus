"""
Performance and benchmark tests for NEXUS backend data processing modules:
Cleaning, Profiling, Quality Engine, Transformation, Analytics, and Anomaly Detection.

Measures execution time across dataset sizes: 1,000, 10,000, and 50,000 rows.
"""

import sys
import csv
import time
from pathlib import Path
import pytest

# Add backend to Python path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from cleaning import clean_file
from profiling import profile_csv
from quality import (
    load_csv,
    calculate_completeness,
    calculate_validity,
    calculate_uniqueness,
    calculate_consistency,
    calculate_timeliness,
    calculate_quality_score,
)
from transformation import transform_file
from analytics import analyze_dataset
from anomaly import detect_anomalies


ROW_SIZES = [1000, 10000, 50000]


def create_sample_csv(file_path: Path, num_rows: int):
    """Generate a sample CSV file with specified row count."""
    headers = ["id", "name", "age", "salary", "join_date"]
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for i in range(1, num_rows + 1):
            writer.writerow([
                str(i),
                f"Employee_{i % 200}",
                str(20 + (i % 40)),
                str(40000 + (i % 50000)),
                "2026-01-15",
            ])


def create_in_memory_rows(num_rows: int):
    """Generate in-memory row dictionaries."""
    rows = []
    for i in range(1, num_rows + 1):
        rows.append({
            "id": str(i),
            "name": f"Employee_{i % 200}",
            "age": str(20 + (i % 40)),
            "salary": str(40000 + (i % 50000)),
            "join_date": "2026-01-15",
        })
    return rows


# ==========================================
# 1. CLEANING BENCHMARK
# ==========================================

def test_benchmark_cleaning(tmp_path):
    """Benchmark clean_file across 1k, 10k, and 50k rows."""
    print("\n--- BENCHMARK: Cleaning Module ---")
    for size in ROW_SIZES:
        csv_file = tmp_path / f"clean_{size}.csv"
        create_sample_csv(csv_file, size)

        start_time = time.perf_counter()
        clean_data, bad_data = clean_file(str(csv_file))
        elapsed = time.perf_counter() - start_time

        print(f"\nDataset size: {size}")
        print(f"Cleaning time: {elapsed:.4f} seconds")

        assert isinstance(clean_data, list)
        assert isinstance(bad_data, list)


# ==========================================
# 2. PROFILING BENCHMARK
# ==========================================

def test_benchmark_profiling(tmp_path):
    """Benchmark profile_csv across 1k, 10k, and 50k rows."""
    print("\n--- BENCHMARK: Profiling Module ---")
    for size in ROW_SIZES:
        csv_file = tmp_path / f"profile_{size}.csv"
        create_sample_csv(csv_file, size)

        start_time = time.perf_counter()
        profile = profile_csv(str(csv_file))
        elapsed = time.perf_counter() - start_time

        print(f"\nDataset size: {size}")
        print(f"Profiling time: {elapsed:.4f} seconds")

        assert "dataset" in profile
        assert "columns" in profile


# ==========================================
# 3. QUALITY ENGINE BENCHMARK
# ==========================================

def test_benchmark_quality_engine(tmp_path):
    """Benchmark quality engine calculations across 1k, 10k, and 50k rows."""
    print("\n--- BENCHMARK: Quality Engine ---")
    for size in ROW_SIZES:
        csv_file = tmp_path / f"quality_{size}.csv"
        create_sample_csv(csv_file, size)
        rows = load_csv(str(csv_file))

        start_time = time.perf_counter()
        completeness = calculate_completeness(rows)
        validity = calculate_validity(rows)
        uniqueness = calculate_uniqueness(rows)
        consistency = calculate_consistency(rows)
        timeliness = calculate_timeliness(rows)
        score = calculate_quality_score(
            completeness, validity, uniqueness, consistency, timeliness
        )
        elapsed = time.perf_counter() - start_time

        print(f"\nDataset size: {size}")
        print(f"Quality Engine time: {elapsed:.4f} seconds")

        assert isinstance(score, float)


# ==========================================
# 4. TRANSFORMATION BENCHMARK
# ==========================================

def test_benchmark_transformation(tmp_path):
    """Benchmark transform_file across 1k, 10k, and 50k rows."""
    print("\n--- BENCHMARK: Transformation Module ---")
    for size in ROW_SIZES:
        csv_file = tmp_path / f"transform_{size}.csv"
        create_sample_csv(csv_file, size)

        start_time = time.perf_counter()
        transformed_rows = transform_file(str(csv_file))
        elapsed = time.perf_counter() - start_time

        print(f"\nDataset size: {size}")
        print(f"Transformation time: {elapsed:.4f} seconds")

        assert isinstance(transformed_rows, list)


# ==========================================
# 5. ANALYTICS BENCHMARK
# ==========================================

def test_benchmark_analytics():
    """Benchmark analyze_dataset across 1k, 10k, and 50k rows."""
    print("\n--- BENCHMARK: Analytics Module ---")
    for size in ROW_SIZES:
        rows = create_in_memory_rows(size)

        start_time = time.perf_counter()
        results = analyze_dataset(rows)
        elapsed = time.perf_counter() - start_time

        print(f"\nDataset size: {size}")
        print(f"Analytics time: {elapsed:.4f} seconds")

        assert "numeric" in results
        assert "categorical" in results


# ==========================================
# 6. ANOMALY DETECTION BENCHMARK
# ==========================================

def test_benchmark_anomaly_detection():
    """Benchmark detect_anomalies across 1k, 10k, and 50k rows."""
    print("\n--- BENCHMARK: Anomaly Detection ---")
    for size in ROW_SIZES:
        rows = create_in_memory_rows(size)

        start_time = time.perf_counter()
        anomalies = detect_anomalies(rows)
        elapsed = time.perf_counter() - start_time

        print(f"\nDataset size: {size}")
        print(f"Anomaly Detection time: {elapsed:.4f} seconds")

        assert isinstance(anomalies, list)
