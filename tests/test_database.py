"""
Unit tests for backend/database.py module.

Tests database utility functions using unittest.mock to ensure
no actual connection to PostgreSQL is made.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add backend to Python path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from database import (
    get_connection,
    insert_dataset,
    insert_quality_report,
    get_dataset,
    get_dataset_rows,
    get_datasets,
    get_quality_report,
    create_pipeline,
    update_pipeline,
    get_pipelines,
    get_pipeline,
    get_all_users,
    get_user_by_id,
    update_user_role,
    update_user_status,
    get_user_datasets,
    get_user_pipelines,
    get_user_activity,
    log_user_activity,
)


@patch("database.psycopg2.connect")
def test_get_connection(mock_connect, monkeypatch):
    """Verify get_connection passes environment variables to psycopg2.connect."""
    monkeypatch.setenv("DATABASE_HOST", "localhost")
    monkeypatch.setenv("DATABASE_NAME", "nexus_db")
    monkeypatch.setenv("DATABASE_USER", "postgres")
    monkeypatch.setenv("DATABASE_PASSWORD", "secret")
    monkeypatch.setenv("DATABASE_PORT", "5432")

    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    conn = get_connection()

    assert conn == mock_conn
    mock_connect.assert_called_once_with(
        host="localhost",
        database="nexus_db",
        user="postgres",
        password="secret",
        port="5432"
    )


@patch("database.get_connection")
def test_insert_dataset(mock_get_connection):
    """Verify insert_dataset handles versioning, dataset creation, and row insertion."""
    mock_cursor = MagicMock()
    # 1st fetchone: MAX(version) = 0
    # 2nd fetchone: RETURNING id = 42
    mock_cursor.fetchone.side_effect = [(0,), (42,)]

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    clean_data = [
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": "Bob"},
    ]

    dataset_id, row_count, new_version = insert_dataset("employees.csv", clean_data)

    assert dataset_id == 42
    assert row_count == 2
    assert new_version == 1

    mock_conn.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()


@patch("database.get_connection")
def test_insert_dataset_with_user_id(mock_get_connection):
    """Verify insert_dataset includes user_id in SQL INSERT statement when provided."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.side_effect = [(0,), (105,)]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    clean_data = [{"id": "1", "name": "Alice"}]
    dataset_id, row_count, new_version = insert_dataset("inventory.csv", clean_data, user_id=5)

    assert dataset_id == 105
    # Verify user_id=5 was passed to SQL query
    insert_call_args = mock_cursor.execute.call_args_list[1][0]
    assert "user_id" in insert_call_args[0]
    assert insert_call_args[1] == ("inventory.csv", 1, 5)


@patch("database.get_connection")
def test_insert_quality_report(mock_get_connection):
    """Verify quality report insertion executes expected INSERT query and parameters."""
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    insert_quality_report(
        dataset_id=42,
        completeness=100.0,
        validity=95.0,
        uniqueness=100.0,
        consistency=90.0,
        timeliness=100.0,
        quality_score=97.0
    )

    mock_cursor.execute.assert_called_once()
    args = mock_cursor.execute.call_args[0][1]
    assert args == (42, 100.0, 95.0, 100.0, 90.0, 100.0, 97.0)

    mock_conn.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()


@patch("database.get_connection")
def test_get_dataset_found(mock_get_connection):
    """Verify get_dataset converts metadata and rows into expected dictionary structure."""
    mock_cursor = MagicMock()
    # fetchone for dataset info: (id, file_name, version, uploaded_at)
    mock_cursor.fetchone.return_value = (42, "data.csv", 1, "2026-09-26 00:00:00")
    # fetchall for dataset rows
    mock_cursor.fetchall.return_value = [
        ({"col1": "val1"},),
        ({"col1": "val2"},),
    ]

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    result = get_dataset(42)

    assert result == {
        "id": 42,
        "file_name": "data.csv",
        "version": 1,
        "uploaded_at": "2026-09-26 00:00:00",
        "rows": [{"col1": "val1"}, {"col1": "val2"}]
    }


@patch("database.get_connection")
def test_get_dataset_not_found(mock_get_connection):
    """Verify get_dataset returns None for missing dataset_id."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    result = get_dataset(999)
    assert result is None


@patch("database.get_connection")
def test_get_dataset_rows(mock_get_connection):
    """Verify get_dataset_rows extracts row_data list."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ({"a": 10},),
        ({"a": 20},),
    ]

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    rows = get_dataset_rows(42)
    assert rows == [{"a": 10}, {"a": 20}]


@patch("database.get_connection")
def test_get_datasets(mock_get_connection):
    """Verify get_datasets returns list of dataset metadata objects."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (42, "file1.csv", 2, "2026-09-26 01:00:00"),
        (41, "file2.csv", 1, "2026-09-25 12:00:00"),
    ]

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    datasets = get_datasets()

    assert len(datasets) == 2
    assert datasets[0] == {
        "id": 42,
        "file_name": "file1.csv",
        "version": 2,
        "uploaded_at": "2026-09-26 01:00:00"
    }
    assert datasets[1]["id"] == 41


@patch("database.get_connection")
def test_get_quality_report_found(mock_get_connection):
    """Verify get_quality_report converts report tuple to dictionary."""
    mock_cursor = MagicMock()
    # (completeness, validity, uniqueness, consistency, timeliness, quality_score, created_at)
    mock_cursor.fetchone.return_value = (100.0, 90.0, 100.0, 95.0, 100.0, 97.0, "2026-09-26 01:00:00")

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    report = get_quality_report(42)

    assert report == {
        "dataset_id": 42,
        "completeness": 100.0,
        "validity": 90.0,
        "uniqueness": 100.0,
        "consistency": 95.0,
        "timeliness": 100.0,
        "quality_score": 97.0,
        "created_at": "2026-09-26 01:00:00"
    }


@patch("database.get_connection")
def test_get_quality_report_not_found(mock_get_connection):
    """Verify get_quality_report returns None when no report exists."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    report = get_quality_report(999)
    assert report is None


@patch("database.get_connection")
def test_create_pipeline(mock_get_connection):
    """Verify create_pipeline inserts new pipeline with status RUNNING and returns pipeline_id."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (7,)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    pipeline_id = create_pipeline(dataset_id=42)

    assert pipeline_id == 7
    mock_cursor.execute.assert_called_once()
    assert mock_cursor.execute.call_args[0][1] == (42, "RUNNING")
    mock_conn.commit.assert_called_once()


@patch("database.get_connection")
def test_create_pipeline_with_user_id(mock_get_connection):
    """Verify create_pipeline includes user_id in SQL INSERT statement when provided."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (15,)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    pipeline_id = create_pipeline(dataset_id=42, user_id=5)

    assert pipeline_id == 15
    mock_cursor.execute.assert_called_once()
    assert "user_id" in mock_cursor.execute.call_args[0][0]
    assert mock_cursor.execute.call_args[0][1] == (42, "RUNNING", 5)
    mock_conn.commit.assert_called_once()


@patch("database.get_connection")
def test_update_pipeline(mock_get_connection):
    """Verify update_pipeline executes UPDATE query with updated status and row metrics."""
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    update_pipeline(
        pipeline_id=7,
        status="COMPLETED",
        total_rows=100,
        clean_rows=95,
        bad_rows=5
    )

    mock_cursor.execute.assert_called_once()
    args = mock_cursor.execute.call_args[0][1]
    assert args == ("COMPLETED", 100, 95, 5, 7)
    mock_conn.commit.assert_called_once()


@patch("database.get_connection")
def test_get_pipelines(mock_get_connection):
    """Verify get_pipelines returns list of all pipeline records formatted as dicts."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (7, 42, "COMPLETED", "2026-09-26 01:00:00", "2026-09-26 01:01:00", 100, 95, 5),
        (6, 41, "FAILED", "2026-09-25 10:00:00", "2026-09-25 10:00:05", 50, 0, 50),
    ]

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    pipelines = get_pipelines()

    assert len(pipelines) == 2
    assert pipelines[0] == {
        "id": 7,
        "dataset_id": 42,
        "status": "COMPLETED",
        "started_at": "2026-09-26 01:00:00",
        "completed_at": "2026-09-26 01:01:00",
        "total_rows": 100,
        "clean_rows": 95,
        "bad_rows": 5
    }
    assert pipelines[1]["id"] == 6


@patch("database.get_connection")
def test_get_pipeline_found(mock_get_connection):
    """Verify get_pipeline returns correct dictionary for valid pipeline_id."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (
        7, 42, "COMPLETED", "2026-09-26 01:00:00", "2026-09-26 01:01:00", 100, 95, 5
    )

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    pipeline = get_pipeline(7)

    assert pipeline == {
        "id": 7,
        "dataset_id": 42,
        "status": "COMPLETED",
        "started_at": "2026-09-26 01:00:00",
        "completed_at": "2026-09-26 01:01:00",
        "total_rows": 100,
        "clean_rows": 95,
        "bad_rows": 5
    }


@patch("database.get_connection")
def test_get_pipeline_not_found(mock_get_connection):
    """Verify get_pipeline returns None when pipeline_id is missing."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    pipeline = get_pipeline(999)
    assert pipeline is None


@patch("database.get_connection")
def test_get_all_users(mock_get_connection):
    """Verify get_all_users fetches and formats only safe user fields including status without password_hash."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (1, "admin", "admin@nexus.com", "Admin", "2026-09-24 02:02:19", "active"),
        (2, "viewer", "viewer@nexus.com", "Viewer", "2026-09-24 03:56:01", "inactive"),
    ]

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    users = get_all_users()

    assert len(users) == 2
    assert users[0] == {
        "id": 1,
        "username": "admin",
        "email": "admin@nexus.com",
        "role": "Admin",
        "status": "active",
        "created_at": "2026-09-24 02:02:19"
    }
    assert "password_hash" not in users[0]
    assert "password" not in users[0]
    assert users[1]["role"] == "Viewer"
    assert users[1]["status"] == "inactive"
    mock_cursor.execute.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()


@patch("database.get_connection")
def test_get_user_by_id_found(mock_get_connection):
    """Verify get_user_by_id returns formatted user dictionary when user exists."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (1, "admin", "admin@nexus.com", "Admin", "active", "2026-09-24 02:02:19")
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    user = get_user_by_id(1)
    assert user == {
        "id": 1,
        "username": "admin",
        "email": "admin@nexus.com",
        "role": "Admin",
        "status": "active",
        "created_at": "2026-09-24 02:02:19"
    }


@patch("database.get_connection")
def test_get_user_by_id_not_found(mock_get_connection):
    """Verify get_user_by_id returns None when user does not exist."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    user = get_user_by_id(9999)
    assert user is None


@patch("database.get_connection")
def test_update_user_role(mock_get_connection):
    """Verify update_user_role executes UPDATE query and returns updated user."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (2, "viewer", "viewer@nexus.com", "Data Engineer", "active", "2026-09-24 03:56:01")
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    updated = update_user_role(2, "Data Engineer")
    assert updated["role"] == "Data Engineer"
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


@patch("database.get_connection")
def test_update_user_status(mock_get_connection):
    """Verify update_user_status executes UPDATE query and returns updated user."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (2, "viewer", "viewer@nexus.com", "Viewer", "inactive", "2026-09-24 03:56:01")
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    updated = update_user_status(2, "inactive")
    assert updated["status"] == "inactive"
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


@patch("database.get_connection")
def test_get_user_datasets(mock_get_connection):
    """Verify get_user_datasets extracts datasets associated with user_id."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (10, "sales.csv", 1, "2026-09-26 12:00:00")
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    datasets = get_user_datasets(1)
    assert len(datasets) == 1
    assert datasets[0]["id"] == 10
    assert datasets[0]["file_name"] == "sales.csv"


@patch("database.get_connection")
def test_get_user_pipelines(mock_get_connection):
    """Verify get_user_pipelines extracts pipelines associated with user_id."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (5, 10, "SUCCESS", "2026-09-26 12:00:00", "2026-09-26 12:01:00", 100, 95, 5)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    pipelines = get_user_pipelines(1)
    assert len(pipelines) == 1
    assert pipelines[0]["id"] == 5
    assert pipelines[0]["clean_rows"] == 95


@patch("database.get_connection")
def test_get_user_activity(mock_get_connection):
    """Verify get_user_activity extracts user activity entries."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (1, "ROLE_CHANGE", "Role changed to Admin", "2026-09-26 12:00:00")
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    activity = get_user_activity(1)
    assert len(activity) == 1
    assert activity[0]["activity_type"] == "ROLE_CHANGE"


@patch("database.get_connection")
def test_log_user_activity(mock_get_connection):
    """Verify log_user_activity inserts an activity row into user_activity."""
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    log_user_activity(1, "LOGIN", "User logged in")
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


