"""
Integration and pipeline tests for POST /upload API in backend/upload.py.

Tests file validation, authentication, CSV cleaning, quality scoring,
dataset insertion, pipeline tracking, and error handling.
"""

import sys
import io
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

# Add backend to Python path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from upload import app
from auth import create_access_token

TEST_SECRET_KEY = "test_secret_key_for_nexus_upload_tests"
TEST_ALGORITHM = "HS256"


@pytest.fixture(autouse=True)
def setup_jwt_env(monkeypatch):
    """Ensure JWT environment variables are configured."""
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET_KEY)
    monkeypatch.setenv("JWT_ALGORITHM", TEST_ALGORITHM)


@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Generate Bearer token header for authenticated Admin request."""
    token = create_access_token(user_id=1, username="test_admin", role="Admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers():
    """Generate Bearer token header for Admin user."""
    token = create_access_token(user_id=1, username="admin_user", role="Admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def data_engineer_headers():
    """Generate Bearer token header for Data Engineer user."""
    token = create_access_token(user_id=2, username="de_user", role="Data Engineer")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_headers():
    """Generate Bearer token header for Viewer user."""
    token = create_access_token(user_id=3, username="viewer_user", role="Viewer")
    return {"Authorization": f"Bearer {token}"}


# ==========================================
# 1. AUTHENTICATION & RBAC PERMISSION TESTS
# ==========================================

def test_upload_unauthorized(client):
    """Verify POST /upload without Authorization header returns 401 Unauthorized."""
    files = {"file": ("test.csv", io.BytesIO(b"id,name\n1,Alice"), "text/csv")}
    response = client.post("/upload", files=files)
    assert response.status_code == 401


def test_admin_can_upload_success(client, admin_headers):
    """Verify Admin can upload CSV file successfully (200 OK)."""
    files = {"file": ("admin_test.csv", io.BytesIO(b"id,name,age\n1,Alice,30"), "text/csv")}

    with patch("upload.insert_dataset", return_value=(100, 1, 1)), \
         patch("upload.create_pipeline", return_value=500), \
         patch("upload.insert_quality_report"), \
         patch("upload.update_pipeline"):

        response = client.post("/upload", files=files, headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["message"] == "File uploaded, cleaned and stored successfully"


def test_data_engineer_can_upload_success(client, data_engineer_headers):
    """Verify Data Engineer can upload CSV file successfully (200 OK)."""
    files = {"file": ("de_test.csv", io.BytesIO(b"id,name,age\n1,Bob,25"), "text/csv")}

    with patch("upload.insert_dataset", return_value=(101, 1, 1)), \
         patch("upload.create_pipeline", return_value=501), \
         patch("upload.insert_quality_report"), \
         patch("upload.update_pipeline"):

        response = client.post("/upload", files=files, headers=data_engineer_headers)

    assert response.status_code == 200
    assert response.json()["message"] == "File uploaded, cleaned and stored successfully"


def test_viewer_cannot_upload_forbidden(client, viewer_headers):
    """Verify Viewer cannot upload CSV file and receives 403 Forbidden."""
    files = {"file": ("viewer_test.csv", io.BytesIO(b"id,name,age\n1,Charlie,35"), "text/csv")}
    response = client.post("/upload", files=files, headers=viewer_headers)

    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


def test_upload_authorized(client, auth_headers):
    """Verify POST /upload with valid JWT is accepted and processes file."""
    files = {"file": ("test_auth.csv", io.BytesIO(b"id,name,age\n1,Alice,30\n2,Bob,25"), "text/csv")}

    with patch("upload.insert_dataset", return_value=(100, 2, 1)), \
         patch("upload.create_pipeline", return_value=500), \
         patch("upload.insert_quality_report"), \
         patch("upload.update_pipeline"):

        response = client.post("/upload", files=files, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["message"] == "File uploaded, cleaned and stored successfully"


# ==========================================
# 2. FILE VALIDATION TESTS
# ==========================================

def test_upload_non_csv_file(client, auth_headers):
    """Verify POST /upload with a non-CSV file returns the current error response."""
    files = {"file": ("document.pdf", io.BytesIO(b"PDF content..."), "application/pdf")}
    response = client.post("/upload", files=files, headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"error": "Only CSV files are allowed"}


def test_upload_empty_csv(client, auth_headers):
    """Verify POST /upload with a header-only CSV is processed with 0 clean rows."""
    files = {"file": ("empty.csv", io.BytesIO(b"id,name,age\n"), "text/csv")}

    with patch("upload.insert_dataset", return_value=(101, 0, 1)) as mock_insert, \
         patch("upload.create_pipeline", return_value=501) as mock_create_pipe, \
         patch("upload.insert_quality_report") as mock_insert_qr, \
         patch("upload.update_pipeline") as mock_update_pipe:

        response = client.post("/upload", files=files, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["clean_rows"] == 0
    assert data["bad_rows"] == 0
    assert data["dataset_id"] == 101
    assert data["pipeline_id"] == 501

    mock_insert.assert_called_once_with("empty.csv", [], user_id=1)
    mock_create_pipe.assert_called_once_with(101, user_id=1)
    mock_insert_qr.assert_called_once()
    mock_update_pipe.assert_called_once()


# ==========================================
# 3. PIPELINE BEHAVIOR & RESPONSE STRUCTURE
# ==========================================

def test_upload_valid_csv_pipeline_flow(client, auth_headers):
    """Verify complete upload pipeline steps: clean, analyze, profile, quality score, insert, and update pipeline."""
    csv_content = b"id,name,age\n1,Alice,30\n2,Bob,25\n3,Charlie,35\n"
    files = {"file": ("employees.csv", io.BytesIO(csv_content), "text/csv")}

    with patch("upload.insert_dataset", return_value=(42, 3, 1)) as mock_insert_ds, \
         patch("upload.create_pipeline", return_value=7) as mock_create_pipe, \
         patch("upload.insert_quality_report") as mock_insert_qr, \
         patch("upload.update_pipeline") as mock_update_pipe:

        response = client.post("/upload", files=files, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Verify JSON response structure
    assert data["message"] == "File uploaded, cleaned and stored successfully"
    assert data["filename"] == "employees.csv"
    assert data["download_file"] == "employees_clean.csv"
    assert data["clean_rows"] == 3
    assert data["bad_rows"] == 0
    assert data["dataset_id"] == 42
    assert data["pipeline_id"] == 7
    assert data["database_rows"] == 3
    assert data["version"] == 1
    assert "profile" in data
    assert "analytics" in data
    assert "completeness" in data
    assert "validity" in data
    assert "uniqueness" in data
    assert "consistency" in data
    assert "timeliness" in data
    assert "quality_score" in data

    # Verify database utility calls with authenticated user_id
    mock_insert_ds.assert_called_once()
    assert mock_insert_ds.call_args[1].get("user_id") == 1
    mock_create_pipe.assert_called_once_with(42, user_id=1)
    mock_insert_qr.assert_called_once()
    mock_update_pipe.assert_called_once_with(7, "SUCCESS", 3, 3, 0)


def test_upload_csv_handling_bad_rows(client, auth_headers):
    """Verify that rejected/duplicate rows are identified and reported in bad_rows."""
    # Rows 1 and 2 are exact duplicates
    csv_content = b"id,name,age\n1,Alice,30\n1,Alice,30\n2,Bob,25\n"
    files = {"file": ("duplicates.csv", io.BytesIO(csv_content), "text/csv")}

    with patch("upload.insert_dataset", return_value=(43, 2, 1)), \
         patch("upload.create_pipeline", return_value=8), \
         patch("upload.insert_quality_report"), \
         patch("upload.update_pipeline") as mock_update_pipe:

        response = client.post("/upload", files=files, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["clean_rows"] == 2
    assert data["bad_rows"] == 1
    mock_update_pipe.assert_called_once_with(8, "SUCCESS", 3, 2, 1)


# ==========================================
# 4. ERROR HANDLING TESTS
# ==========================================

def test_upload_database_failure_handling(auth_headers):
    """Verify that a database failure during insert_dataset returns HTTP 500 server error response."""
    # Pass raise_server_exceptions=False to test actual HTTP 500 response handling
    custom_client = TestClient(app, raise_server_exceptions=False)
    csv_content = b"id,name,age\n1,Alice,30\n"
    files = {"file": ("failure_test.csv", io.BytesIO(csv_content), "text/csv")}

    with patch("upload.insert_dataset", side_effect=Exception("Database connection error")):
        response = custom_client.post("/upload", files=files, headers=auth_headers)

    # Unhandled database exception results in HTTP 500 status code
    assert response.status_code == 500


def test_upload_ownership_tracking(client, auth_headers):
    """Verify that uploading a CSV associates dataset, pipeline, and user activity with authenticated user_id."""
    files = {"file": ("user_inventory.csv", io.BytesIO(b"id,item,qty\n1,Widget,10\n"), "text/csv")}

    with patch("upload.insert_dataset", return_value=(200, 1, 1)) as mock_insert, \
         patch("upload.create_pipeline", return_value=600) as mock_create_pipe, \
         patch("upload.insert_quality_report"), \
         patch("upload.update_pipeline"), \
         patch("upload.log_user_activity") as mock_log_act:

        response = client.post("/upload", files=files, headers=auth_headers)

    assert response.status_code == 200
    mock_insert.assert_called_once_with("user_inventory.csv", [{"id": "1", "item": "Widget", "qty": "10"}], user_id=1)
    mock_create_pipe.assert_called_once_with(200, user_id=1)
    mock_log_act.assert_called_once_with(1, "DATASET_UPLOAD", "Uploaded dataset user_inventory.csv (v1)")

