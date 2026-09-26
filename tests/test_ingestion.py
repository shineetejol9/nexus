"""
Unit tests for backend/ingestion.py module.

Tests loading and execution of backend/ingestion.py script using pandas read_csv mocking.
"""

import sys
import importlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

# Add backend to Python path
sys.path.append(str(Path(__file__).parent.parent / "backend"))


def test_ingestion_script_execution():
    """Verify backend/ingestion.py reads data/raw/transactions.csv and prints data."""
    mock_df = MagicMock(spec=pd.DataFrame)

    with patch("pandas.read_csv", return_value=mock_df) as mock_read_csv, \
         patch("builtins.print") as mock_print:

        # Remove from sys.modules if present to ensure clean import execution
        if "ingestion" in sys.modules:
            del sys.modules["ingestion"]
        if "backend.ingestion" in sys.modules:
            del sys.modules["backend.ingestion"]

        import ingestion

        assert ingestion.file_path == "data/raw/transactions.csv"
        assert ingestion.data == mock_df
        mock_read_csv.assert_called_once_with("data/raw/transactions.csv")
        mock_print.assert_called_once_with(mock_df)


def test_ingestion_module_attributes():
    """Verify backend/ingestion.py exports expected module variables."""
    mock_df = MagicMock(spec=pd.DataFrame)

    with patch("pandas.read_csv", return_value=mock_df):
        if "ingestion" in sys.modules:
            ingestion = importlib.reload(sys.modules["ingestion"])
        else:
            ingestion = importlib.import_module("ingestion")

        assert hasattr(ingestion, "file_path")
        assert hasattr(ingestion, "data")
        assert ingestion.file_path == "data/raw/transactions.csv"
