"""
API integration tests for NEXUS FastAPI application (backend/upload.py).

Tests authentication, dataset management, quality reports, anomaly detection,
KPI calculation, and pipeline endpoints using FastAPI TestClient and mocking.
"""

import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

# Add backend to Python path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from upload import app
from auth import create_access_token

TEST_SECRET_KEY = "test_secret_key_for_nexus_api_tests"
TEST_ALGORITHM = "HS256"


@pytest.fixture(autouse=True)
def setup_jwt_env(monkeypatch):
    """Ensure JWT environment variables are set for API tests."""
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET_KEY)
    monkeypatch.setenv("JWT_ALGORITHM", TEST_ALGORITHM)


@pytest.fixture
def client():
    """Create a FastAPI TestClient instance."""
    return TestClient(app)


@pytest.fixture
def admin_headers():
    """Generate Authorization header for an Admin user."""
    token = create_access_token(user_id=1, username="admin_user", role="Admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_headers():
    """Generate Authorization header for a Viewer user."""
    token = create_access_token(user_id=2, username="viewer_user", role="Viewer")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def data_engineer_headers():
    """Generate Authorization header for a Data Engineer user."""
    token = create_access_token(user_id=3, username="engineer_user", role="Data Engineer")
    return {"Authorization": f"Bearer {token}"}


# ==========================================
# AUTHENTICATION ENDPOINTS
# ==========================================

@patch("upload.login_user")
def test_login_success(mock_login_user, client):
    """Test POST /api/v1/auth/login with valid credentials."""
    mock_login_user.return_value = (True, "mocked_jwt_access_token")

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "valid_user", "password": "valid_password"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Login successful"
    assert data["access_token"] == "mocked_jwt_access_token"
    assert data["token_type"] == "bearer"


@patch("upload.login_user")
def test_login_failure(mock_login_user, client):
    """Test POST /api/v1/auth/login with invalid credentials."""
    mock_login_user.return_value = (False, "Invalid username or password")

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "wrong_user", "password": "wrong_password"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Invalid username or password"


def test_get_me_unauthorized(client):
    """Test GET /api/v1/auth/me without Authorization header returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_authorized(client, viewer_headers):
    """Test GET /api/v1/auth/me with valid Bearer token returns user info."""
    response = client.get("/api/v1/auth/me", headers=viewer_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["username"] == "viewer_user"
    assert data["user"]["role"] == "Viewer"


def test_admin_test_allowed_for_admin(client, admin_headers):
    """Test GET /api/v1/auth/admin-test with Admin token returns 200."""
    response = client.get("/api/v1/auth/admin-test", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Admin access granted"


def test_admin_test_forbidden_for_viewer(client, viewer_headers):
    """Test GET /api/v1/auth/admin-test with Viewer token returns 403 Forbidden."""
    response = client.get("/api/v1/auth/admin-test", headers=viewer_headers)
    assert response.status_code == 403


# ==========================================
# DATASETS ENDPOINTS
# ==========================================

def test_list_datasets_unauthorized(client):
    """Test GET /api/v1/datasets without JWT returns 401."""
    response = client.get("/api/v1/datasets")
    assert response.status_code == 401


@patch("upload.get_datasets")
def test_list_datasets_authorized(mock_get_datasets, client, viewer_headers):
    """Test GET /api/v1/datasets with valid JWT returns list of datasets."""
    mock_datasets = [
        {"id": 1, "file_name": "employees.csv", "version": 1, "uploaded_at": "2026-09-26T00:00:00"},
        {"id": 2, "file_name": "students.csv", "version": 2, "uploaded_at": "2026-09-26T01:00:00"},
    ]
    mock_get_datasets.return_value = mock_datasets

    response = client.get("/api/v1/datasets", headers=viewer_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert data["datasets"] == mock_datasets


@patch("upload.get_dataset")
def test_get_dataset_details_existing(mock_get_dataset, client, viewer_headers):
    """Test GET /api/v1/datasets/{id} for an existing dataset."""
    mock_dataset = {
        "id": 1,
        "file_name": "employees.csv",
        "version": 1,
        "uploaded_at": "2026-09-26T00:00:00",
        "rows": [{"id": 1, "name": "Alice"}]
    }
    mock_get_dataset.return_value = mock_dataset

    response = client.get("/api/v1/datasets/1", headers=viewer_headers)

    assert response.status_code == 200
    assert response.json() == mock_dataset


@patch("upload.get_dataset")
def test_get_dataset_details_nonexistent(mock_get_dataset, client, viewer_headers):
    """Test GET /api/v1/datasets/{id} for a nonexistent dataset."""
    mock_get_dataset.return_value = None

    response = client.get("/api/v1/datasets/999", headers=viewer_headers)

    assert response.status_code == 200
    data = response.json()
    assert data == {"error": "Dataset not found"}


@patch("upload.get_dataset_rows")
@patch("upload.analyze_dataset")
def test_get_analytics_authorized(mock_analyze, mock_get_rows, client, data_engineer_headers):
    """Test GET /analytics/{dataset_id} for Data Engineer returns analytics."""
    mock_get_rows.return_value = [{"col1": 10, "col2": 20}]
    mock_analyze.return_value = {"summary": "ok"}

    response = client.get("/analytics/1", headers=data_engineer_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == 1
    assert data["rows"] == 1
    assert data["analytics"] == {"summary": "ok"}


def test_get_analytics_unauthorized(client):
    """Test GET /analytics/{dataset_id} without JWT returns 401 Unauthorized."""
    response = client.get("/analytics/1")
    assert response.status_code == 401


# ==========================================
# QUALITY ENDPOINTS
# ==========================================

@patch("upload.get_quality_report")
def test_get_quality_report_existing(mock_get_quality_report, client, viewer_headers):
    """Test GET /api/v1/quality/{dataset_id} for an existing quality report."""
    mock_report = {
        "dataset_id": 1,
        "completeness": 100.0,
        "validity": 95.0,
        "uniqueness": 100.0,
        "consistency": 90.0,
        "timeliness": 100.0,
        "quality_score": 97.0,
        "created_at": "2026-09-26T00:00:00"
    }
    mock_get_quality_report.return_value = mock_report

    response = client.get("/api/v1/quality/1", headers=viewer_headers)

    assert response.status_code == 200
    assert response.json() == mock_report


@patch("upload.get_quality_report")
def test_get_quality_report_nonexistent(mock_get_quality_report, client, viewer_headers):
    """Test GET /api/v1/quality/{dataset_id} for a missing quality report."""
    mock_get_quality_report.return_value = None

    response = client.get("/api/v1/quality/999", headers=viewer_headers)

    assert response.status_code == 200
    assert response.json() == {"error": "Quality report not found"}


# ==========================================
# ANOMALIES ENDPOINTS
# ==========================================

@patch("upload.get_dataset_rows")
@patch("upload.detect_anomalies")
def test_get_anomalies_existing(mock_detect_anomalies, mock_get_dataset_rows, client, viewer_headers):
    """Test GET /api/v1/anomalies with valid dataset_id."""
    mock_rows = [{"val": "10"}, {"val": "1000"}]
    mock_get_dataset_rows.return_value = mock_rows

    mock_anomalies = [
        {"column": "val", "value": 1000.0, "lower_bound": 0.0, "upper_bound": 50.0, "row": {"val": "1000"}}
    ]
    mock_detect_anomalies.return_value = mock_anomalies

    response = client.get("/api/v1/anomalies?dataset_id=1", headers=viewer_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == 1
    assert data["anomaly_count"] == 1
    assert data["anomalies"] == mock_anomalies


@patch("upload.get_dataset_rows")
def test_get_anomalies_nonexistent(mock_get_dataset_rows, client, viewer_headers):
    """Test GET /api/v1/anomalies for a nonexistent dataset."""
    mock_get_dataset_rows.return_value = []

    response = client.get("/api/v1/anomalies?dataset_id=999", headers=viewer_headers)

    assert response.status_code == 200
    assert response.json() == {"error": "Dataset not found"}


# ==========================================
# KPIS ENDPOINTS
# ==========================================

@patch("upload.get_dataset_rows")
@patch("upload.calculate_kpis")
def test_get_kpis_existing(mock_calculate_kpis, mock_get_dataset_rows, client, viewer_headers):
    """Test GET /api/v1/kpis with valid dataset_id."""
    mock_rows = [{"age": "30", "name": "Alice"}]
    mock_get_dataset_rows.return_value = mock_rows

    mock_kpis = {
        "total_rows": 1,
        "numeric_columns": 1,
        "categorical_columns": 1
    }
    mock_calculate_kpis.return_value = mock_kpis

    response = client.get("/api/v1/kpis?dataset_id=1", headers=viewer_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == 1
    assert data["kpis"] == mock_kpis


@patch("upload.get_dataset_rows")
def test_get_kpis_nonexistent(mock_get_dataset_rows, client, viewer_headers):
    """Test GET /api/v1/kpis for a nonexistent dataset."""
    mock_get_dataset_rows.return_value = []

    response = client.get("/api/v1/kpis?dataset_id=999", headers=viewer_headers)

    assert response.status_code == 200
    assert response.json() == {"error": "Dataset not found"}


# ==========================================
# PIPELINES ENDPOINTS
# ==========================================

@patch("upload.get_pipelines")
def test_list_pipelines_authorized(mock_get_pipelines, client, viewer_headers):
    """Test GET /api/v1/pipelines with valid JWT."""
    mock_pipelines = [
        {"id": 1, "dataset_id": 1, "status": "COMPLETED", "total_rows": 100, "clean_rows": 95, "bad_rows": 5}
    ]
    mock_get_pipelines.return_value = mock_pipelines

    response = client.get("/api/v1/pipelines", headers=viewer_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["pipelines"] == mock_pipelines


@patch("upload.get_pipeline")
def test_get_pipeline_details_existing(mock_get_pipeline, client, viewer_headers):
    """Test GET /api/v1/pipelines/{id} for an existing pipeline."""
    mock_pipeline = {
        "id": 1, "dataset_id": 1, "status": "COMPLETED", "total_rows": 100, "clean_rows": 95, "bad_rows": 5
    }
    mock_get_pipeline.return_value = mock_pipeline

    response = client.get("/api/v1/pipelines/1", headers=viewer_headers)

    assert response.status_code == 200
    assert response.json() == mock_pipeline


@patch("upload.get_pipeline")
def test_get_pipeline_details_nonexistent(mock_get_pipeline, client, viewer_headers):
    """Test GET /api/v1/pipelines/{id} for a nonexistent pipeline."""
    mock_get_pipeline.return_value = None

    response = client.get("/api/v1/pipelines/999", headers=viewer_headers)

    assert response.status_code == 200
    assert response.json() == {"error": "Pipeline not found"}


# ==========================================
# USER MANAGEMENT (ADMIN ONLY) ENDPOINTS
# ==========================================

@patch("upload.get_all_users")
def test_admin_can_get_users(mock_get_all_users, client, admin_headers):
    """Test: Admin can GET /api/v1/users -> 200."""
    mock_users = [
        {"id": 1, "username": "admin", "email": "admin@nexus.com", "role": "Admin", "status": "active", "created_at": "2026-09-24T02:02:19"},
        {"id": 2, "username": "viewer", "email": "viewer@nexus.com", "role": "Viewer", "status": "active", "created_at": "2026-09-24T03:56:01"},
    ]
    mock_get_all_users.return_value = mock_users

    response = client.get("/api/v1/users", headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == mock_users


def test_viewer_get_users_forbidden(client, viewer_headers):
    """Test: Viewer gets 403 when requesting /api/v1/users."""
    response = client.get("/api/v1/users", headers=viewer_headers)
    assert response.status_code == 403


def test_data_engineer_get_users_forbidden(client, data_engineer_headers):
    """Test: Data Engineer gets 403 when requesting /api/v1/users."""
    response = client.get("/api/v1/users", headers=data_engineer_headers)
    assert response.status_code == 403


def test_no_jwt_get_users_unauthorized(client):
    """Test: No JWT -> 401 when requesting /api/v1/users."""
    response = client.get("/api/v1/users")
    assert response.status_code == 401


@patch("upload.get_user_by_id")
@patch("upload.get_user_datasets")
@patch("upload.get_user_pipelines")
@patch("upload.get_user_activity")
def test_admin_can_view_user_details(mock_activity, mock_pipelines, mock_datasets, mock_get_user, client, admin_headers):
    """Test: Admin can view user details with datasets, pipelines, and activity."""
    mock_get_user.return_value = {
        "id": 2, "username": "viewer", "email": "viewer@nexus.com", "role": "Viewer", "status": "active", "created_at": "2026-09-24T03:56:01"
    }
    mock_datasets.return_value = [{"id": 1, "file_name": "data.csv", "version": 1, "uploaded_at": "2026-09-26T12:00:00"}]
    mock_pipelines.return_value = [{"id": 1, "dataset_id": 1, "status": "SUCCESS", "started_at": "2026-09-26T12:00:00", "completed_at": "2026-09-26T12:01:00", "total_rows": 10, "clean_rows": 10, "bad_rows": 0}]
    mock_activity.return_value = [{"id": 1, "activity_type": "DATASET_UPLOAD", "description": "Uploaded dataset data.csv", "created_at": "2026-09-26T12:00:00"}]

    response = client.get("/api/v1/users/2", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["username"] == "viewer"
    assert len(data["datasets"]) == 1
    assert len(data["pipelines"]) == 1
    assert len(data["recent_activity"]) == 1
    assert "ownership_note" in data


def test_viewer_cannot_view_user_details(client, viewer_headers):
    """Test: Viewer gets 403 when requesting /api/v1/users/{id}."""
    response = client.get("/api/v1/users/2", headers=viewer_headers)
    assert response.status_code == 403


def test_data_engineer_cannot_view_user_details(client, data_engineer_headers):
    """Test: Data Engineer gets 403 when requesting /api/v1/users/{id}."""
    response = client.get("/api/v1/users/2", headers=data_engineer_headers)
    assert response.status_code == 403


@patch("upload.get_user_by_id")
def test_view_user_details_not_found(mock_get_user, client, admin_headers):
    """Test: Returns 404 when user is not found."""
    mock_get_user.return_value = None
    response = client.get("/api/v1/users/9999", headers=admin_headers)
    assert response.status_code == 404


@patch("upload.get_user_by_id")
@patch("upload.update_user_role")
@patch("upload.log_user_activity")
def test_admin_can_change_another_user_role(mock_log, mock_update_role, mock_get_user, client, admin_headers):
    """Test: Admin can change another user's role."""
    mock_get_user.return_value = {
        "id": 2, "username": "viewer", "email": "viewer@nexus.com", "role": "Viewer", "status": "active", "created_at": "2026-09-24T03:56:01"
    }
    mock_update_role.return_value = {
        "id": 2, "username": "viewer", "email": "viewer@nexus.com", "role": "Data Engineer", "status": "active", "created_at": "2026-09-24T03:56:01"
    }

    response = client.put("/api/v1/users/2/role", json={"role": "Data Engineer"}, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["role"] == "Data Engineer"


def test_non_admin_cannot_change_role(client, viewer_headers, data_engineer_headers):
    """Test: Neither Viewer nor Data Engineer can change roles -> 403."""
    res_viewer = client.put("/api/v1/users/2/role", json={"role": "Admin"}, headers=viewer_headers)
    assert res_viewer.status_code == 403

    res_de = client.put("/api/v1/users/2/role", json={"role": "Admin"}, headers=data_engineer_headers)
    assert res_de.status_code == 403


def test_admin_cannot_change_own_role(client, admin_headers):
    """Test: Users cannot change their own role -> 400 Bad Request."""
    # admin_headers has user_id = 1
    response = client.put("/api/v1/users/1/role", json={"role": "Viewer"}, headers=admin_headers)
    assert response.status_code == 400
    assert "own role" in response.json()["detail"].lower()


def test_change_role_invalid_role(client, admin_headers):
    """Test: Changing to an invalid role returns 400 Bad Request."""
    response = client.put("/api/v1/users/2/role", json={"role": "SuperUser"}, headers=admin_headers)
    assert response.status_code == 400
    assert "Invalid role" in response.json()["detail"]


@patch("upload.get_user_by_id")
@patch("upload.update_user_status")
@patch("upload.log_user_activity")
def test_admin_can_deactivate_user(mock_log, mock_update_status, mock_get_user, client, admin_headers):
    """Test: Admin can deactivate a user."""
    mock_get_user.return_value = {
        "id": 2, "username": "viewer", "email": "viewer@nexus.com", "role": "Viewer", "status": "active", "created_at": "2026-09-24T03:56:01"
    }
    mock_update_status.return_value = {
        "id": 2, "username": "viewer", "email": "viewer@nexus.com", "role": "Viewer", "status": "inactive", "created_at": "2026-09-24T03:56:01"
    }

    response = client.put("/api/v1/users/2/status", json={"status": "inactive"}, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["status"] == "inactive"


def test_non_admin_cannot_deactivate_user(client, viewer_headers, data_engineer_headers):
    """Test: Non-admin users cannot deactivate users -> 403."""
    res_viewer = client.put("/api/v1/users/2/status", json={"status": "inactive"}, headers=viewer_headers)
    assert res_viewer.status_code == 403

    res_de = client.put("/api/v1/users/2/status", json={"status": "inactive"}, headers=data_engineer_headers)
    assert res_de.status_code == 403


@patch("upload.get_user_by_id")
@patch("upload.update_user_status")
@patch("upload.log_user_activity")
def test_admin_deactivate_own_account_requires_confirmation(mock_log, mock_update_status, mock_get_user, client, admin_headers):
    """Test: Admin cannot accidentally deactivate own account without confirm_self=True."""
    mock_get_user.return_value = {
        "id": 1, "username": "admin_user", "email": "admin@nexus.com", "role": "Admin", "status": "active", "created_at": "2026-09-24T02:02:19"
    }
    mock_update_status.return_value = {
        "id": 1, "username": "admin_user", "email": "admin@nexus.com", "role": "Admin", "status": "inactive", "created_at": "2026-09-24T02:02:19"
    }

    # Attempt without confirmation -> 400
    res_unconfirmed = client.put("/api/v1/users/1/status", json={"status": "inactive", "confirm_self": False}, headers=admin_headers)
    assert res_unconfirmed.status_code == 400
    assert "Confirmation required" in res_unconfirmed.json()["detail"]

    # Attempt with confirmation -> 200
    res_confirmed = client.put("/api/v1/users/1/status", json={"status": "inactive", "confirm_self": True}, headers=admin_headers)
    assert res_confirmed.status_code == 200
    assert res_confirmed.json()["success"] is True


@patch("upload.get_user_by_id")
@patch("upload.update_user_status")
@patch("upload.log_user_activity")
def test_admin_can_reactivate_user(mock_log, mock_update_status, mock_get_user, client, admin_headers):
    """Test: Admin can reactivate an inactive user."""
    mock_get_user.return_value = {
        "id": 2, "username": "viewer", "email": "viewer@nexus.com", "role": "Viewer", "status": "inactive", "created_at": "2026-09-24T03:56:01"
    }
    mock_update_status.return_value = {
        "id": 2, "username": "viewer", "email": "viewer@nexus.com", "role": "Viewer", "status": "active", "created_at": "2026-09-24T03:56:01"
    }

    response = client.put("/api/v1/users/2/status", json={"status": "active"}, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["status"] == "active"


@patch("upload.login_user")
def test_inactive_user_cannot_authenticate(mock_login_user, client):
    """Test: Inactive user cannot authenticate via login."""
    mock_login_user.return_value = (False, "Account is deactivated. Please contact an administrator.")

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "inactive_user", "password": "valid_password"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "deactivated" in data["message"].lower() or "inactive" in data["message"].lower()


@patch("backend.auth.check_user_active")
def test_inactive_user_cannot_access_protected_apis(mock_check_active, client, viewer_headers):
    """Test: Inactive user token gets 403 Forbidden on protected APIs."""
    mock_check_active.return_value = False

    response = client.get("/api/v1/auth/me", headers=viewer_headers)
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower() or "deactivated" in response.json()["detail"].lower()


@patch("upload.get_all_users")
@patch("upload.get_user_by_id")
@patch("upload.get_user_datasets")
@patch("upload.get_user_pipelines")
@patch("upload.get_user_activity")
def test_sensitive_fields_never_returned(mock_activity, mock_pipelines, mock_datasets, mock_get_user, mock_get_all_users, client, admin_headers):
    """Test: Responses for list users and user details never expose password_hash or password."""
    mock_get_all_users.return_value = [
        {"id": 1, "username": "admin", "email": "admin@nexus.com", "role": "Admin", "status": "active", "created_at": "2026-09-24T02:02:19"}
    ]
    mock_get_user.return_value = {
        "id": 1, "username": "admin", "email": "admin@nexus.com", "role": "Admin", "status": "active", "created_at": "2026-09-24T02:02:19"
    }
    mock_datasets.return_value = []
    mock_pipelines.return_value = []
    mock_activity.return_value = []

    res_list = client.get("/api/v1/users", headers=admin_headers)
    assert res_list.status_code == 200
    assert "password_hash" not in res_list.text
    assert "password" not in res_list.text

    res_detail = client.get("/api/v1/users/1", headers=admin_headers)
    assert res_detail.status_code == 200
    assert "password_hash" not in res_detail.text
    assert "password" not in res_detail.text


# ==========================================
# DATA ENGINEER DATA CORRECTION & VERSIONING
# ==========================================

@patch("upload.get_dataset")
@patch("upload.get_dataset_rows")
@patch("upload.load_rejected_rows_for_dataset")
@patch("upload.clean_file")
@patch("upload.insert_dataset")
@patch("upload.create_pipeline")
@patch("upload.update_pipeline")
@patch("upload.insert_quality_report")
@patch("upload.insert_data_correction")
@patch("upload.log_user_activity")
def test_admin_can_edit_data(
    mock_log, mock_insert_audit, mock_insert_qr, mock_update_pipe, mock_create_pipe,
    mock_insert_ds, mock_clean_file, mock_rejected, mock_rows, mock_get_ds, client, admin_headers
):
    """Test 1: Admin can submit data correction successfully -> 200 OK."""
    mock_get_ds.return_value = {"id": 1, "file_name": "employee.csv", "version": 1}
    mock_rows.return_value = [{"employee_id": "104", "name": "Rohan", "salary": "abc"}]
    mock_rejected.return_value = []
    mock_clean_file.return_value = ([{"employee_id": "104", "name": "Rohan", "salary": "55000"}], [])
    mock_insert_ds.return_value = (2, 1, 2)
    mock_create_pipe.return_value = 10
    mock_insert_audit.return_value = 1

    payload = {"row_index": 0, "column_name": "salary", "new_value": "55000", "source": "clean"}
    response = client.post("/api/v1/datasets/1/correct", json=payload, headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["previous_version"] == 1
    assert data["new_version"] == 2
    assert data["dataset_id"] == 2


@patch("upload.get_dataset")
@patch("upload.get_dataset_rows")
@patch("upload.load_rejected_rows_for_dataset")
@patch("upload.clean_file")
@patch("upload.insert_dataset")
@patch("upload.create_pipeline")
@patch("upload.update_pipeline")
@patch("upload.insert_quality_report")
@patch("upload.insert_data_correction")
@patch("upload.log_user_activity")
def test_data_engineer_can_edit_data(
    mock_log, mock_insert_audit, mock_insert_qr, mock_update_pipe, mock_create_pipe,
    mock_insert_ds, mock_clean_file, mock_rejected, mock_rows, mock_get_ds, client, data_engineer_headers
):
    """Test 2: Data Engineer can submit data correction successfully -> 200 OK."""
    mock_get_ds.return_value = {"id": 1, "file_name": "sales.csv", "version": 1}
    mock_rows.return_value = [{"id": "1", "val": "10"}]
    mock_rejected.return_value = []
    mock_clean_file.return_value = ([{"id": "1", "val": "20"}], [])
    mock_insert_ds.return_value = (5, 1, 2)
    mock_create_pipe.return_value = 20
    mock_insert_audit.return_value = 2

    payload = {"row_index": 0, "column_name": "val", "new_value": "20", "source": "clean"}
    response = client.post("/api/v1/datasets/1/correct", json=payload, headers=data_engineer_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["new_version"] == 2


def test_viewer_cannot_edit_data_forbidden(client, viewer_headers):
    """Test 3: Viewer gets 403 Forbidden when calling correction API."""
    payload = {"row_index": 0, "column_name": "salary", "new_value": "55000", "source": "clean"}
    response = client.post("/api/v1/datasets/1/correct", json=payload, headers=viewer_headers)

    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


def test_unauthenticated_user_cannot_edit_data_unauthorized(client):
    """Test 4: Unauthenticated request to correction API receives 401 Unauthorized."""
    payload = {"row_index": 0, "column_name": "salary", "new_value": "55000", "source": "clean"}
    response = client.post("/api/v1/datasets/1/correct", json=payload)

    assert response.status_code == 401


@patch("upload.get_dataset")
@patch("upload.get_dataset_rows")
@patch("upload.load_rejected_rows_for_dataset")
@patch("upload.clean_file")
@patch("upload.insert_dataset")
@patch("upload.create_pipeline")
@patch("upload.update_pipeline")
@patch("upload.insert_quality_report")
@patch("upload.insert_data_correction")
def test_original_dataset_unchanged_and_new_version_created(
    mock_insert_audit, mock_insert_qr, mock_update_pipe, mock_create_pipe,
    mock_insert_ds, mock_clean_file, mock_rejected, mock_rows, mock_get_ds, client, data_engineer_headers
):
    """Test 5 & 6: Original dataset (v1) remains untouched and correction creates version 2."""
    orig_dataset = {"id": 1, "file_name": "employee.csv", "version": 1}
    mock_get_ds.return_value = orig_dataset
    mock_rows.return_value = [{"employee_id": "104", "name": "Rohan", "salary": "abc"}]
    mock_rejected.return_value = []
    mock_clean_file.return_value = ([{"employee_id": "104", "name": "Rohan", "salary": "55000"}], [])
    mock_insert_ds.return_value = (102, 1, 2)
    mock_create_pipe.return_value = 50

    payload = {"row_index": 0, "column_name": "salary", "new_value": "55000", "source": "clean"}
    response = client.post("/api/v1/datasets/1/correct", json=payload, headers=data_engineer_headers)

    assert response.status_code == 200
    # Original metadata is unchanged
    assert orig_dataset["version"] == 1
    # New version 2 created
    mock_insert_ds.assert_called_once()
    assert mock_insert_ds.call_args[0][0] == "employee.csv"


@patch("upload.get_dataset")
@patch("upload.get_dataset_rows")
@patch("upload.load_rejected_rows_for_dataset")
@patch("upload.clean_file")
@patch("upload.insert_dataset")
@patch("upload.create_pipeline")
@patch("upload.update_pipeline")
@patch("upload.insert_quality_report")
@patch("upload.insert_data_correction")
def test_validation_quality_and_pipeline_recorded(
    mock_insert_audit, mock_insert_qr, mock_update_pipe, mock_create_pipe,
    mock_insert_ds, mock_clean_file, mock_rejected, mock_rows, mock_get_ds, client, data_engineer_headers
):
    """Test 7, 8, 9: Validation runs, quality report is updated, and pipeline execution is recorded."""
    mock_get_ds.return_value = {"id": 1, "file_name": "data.csv", "version": 1}
    mock_rows.return_value = [{"id": "1", "age": "invalid"}]
    mock_rejected.return_value = []
    mock_clean_file.return_value = ([{"id": "1", "age": "30"}], [])
    mock_insert_ds.return_value = (3, 1, 2)
    mock_create_pipe.return_value = 15

    payload = {"row_index": 0, "column_name": "age", "new_value": "30", "source": "clean"}
    response = client.post("/api/v1/datasets/1/correct", json=payload, headers=data_engineer_headers)

    assert response.status_code == 200
    mock_clean_file.assert_called_once()
    mock_insert_qr.assert_called_once()
    mock_create_pipe.assert_called_once_with(3, user_id=3)
    mock_update_pipe.assert_called_once_with(15, "SUCCESS", 1, 1, 0)


@patch("upload.get_dataset")
@patch("upload.get_dataset_rows")
@patch("upload.load_rejected_rows_for_dataset")
@patch("upload.clean_file")
@patch("upload.insert_dataset")
@patch("upload.create_pipeline")
@patch("upload.update_pipeline")
@patch("upload.insert_quality_report")
@patch("upload.insert_data_correction")
@patch("upload.log_user_activity")
def test_audit_trail_records_user_and_correction_details(
    mock_log, mock_insert_audit, mock_insert_qr, mock_update_pipe, mock_create_pipe,
    mock_insert_ds, mock_clean_file, mock_rejected, mock_rows, mock_get_ds, client, data_engineer_headers
):
    """Test 10: Audit entry identifies dataset ID, versions, user ID, username, row, column, old & new values."""
    mock_get_ds.return_value = {"id": 1, "file_name": "employee.csv", "version": 1}
    mock_rows.return_value = [{"employee_id": "104", "name": "Rohan", "salary": "abc"}]
    mock_rejected.return_value = []
    mock_clean_file.return_value = ([{"employee_id": "104", "name": "Rohan", "salary": "55000"}], [])
    mock_insert_ds.return_value = (4, 1, 2)

    payload = {"row_index": 0, "column_name": "salary", "new_value": "55000", "source": "clean"}
    response = client.post("/api/v1/datasets/1/correct", json=payload, headers=data_engineer_headers)

    assert response.status_code == 200
    mock_insert_audit.assert_called_once_with(
        4, 1, 2, 3, "engineer_user", 0, "salary", "abc", "55000"
    )


# ==========================================
# PRIVILEGED ROLE LOCKING & SECURITY POLICY
# ==========================================

@patch("upload.register_user")
def test_public_registration_defaults_to_viewer(mock_register_user, client):
    """Test: Public registration creates user with role='Viewer'."""
    mock_register_user.return_value = (True, 99)

    response = client.post(
        "/api/v1/auth/register",
        json={"username": "new_user", "email": "new@nexus.com", "password": "Password123!"}
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    mock_register_user.assert_called_once_with("new_user", "new@nexus.com", "Password123!", role="Viewer")


@patch("upload.register_user")
def test_public_registration_ignores_client_admin_role(mock_register_user, client):
    """Test: Public registration passing role='Admin' is forced to role='Viewer'."""
    mock_register_user.return_value = (True, 100)

    response = client.post(
        "/api/v1/auth/register",
        json={"username": "hacker_admin", "email": "hacker@nexus.com", "password": "Password123!", "role": "Admin"}
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    # Verify backend enforced role='Viewer'
    mock_register_user.assert_called_once_with("hacker_admin", "hacker@nexus.com", "Password123!", role="Viewer")


@patch("upload.register_user")
def test_public_registration_ignores_client_data_engineer_role(mock_register_user, client):
    """Test: Public registration passing role='Data Engineer' is forced to role='Viewer'."""
    mock_register_user.return_value = (True, 101)

    response = client.post(
        "/api/v1/auth/register",
        json={"username": "hacker_de", "email": "hacker_de@nexus.com", "password": "Password123!", "role": "Data Engineer"}
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    # Verify backend enforced role='Viewer'
    mock_register_user.assert_called_once_with("hacker_de", "hacker_de@nexus.com", "Password123!", role="Viewer")


def test_role_management_data_engineer_forbidden(client, data_engineer_headers):
    """Test: Data Engineer attempting to change user role returns 403 Forbidden."""
    response = client.put("/api/v1/users/2/role", json={"role": "Admin"}, headers=data_engineer_headers)
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


def test_role_management_viewer_forbidden(client, viewer_headers):
    """Test: Viewer attempting to change user role returns 403 Forbidden."""
    response = client.put("/api/v1/users/2/role", json={"role": "Data Engineer"}, headers=viewer_headers)
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


def test_role_management_unauthenticated_unauthorized(client):
    """Test: Unauthenticated request to change user role returns 401 Unauthorized."""
    response = client.put("/api/v1/users/2/role", json={"role": "Data Engineer"})
    assert response.status_code == 401


@patch("upload.get_all_users")
def test_verify_designated_privileged_accounts_policy(mock_get_all_users, client, admin_headers):
    """Test: Verify only designated accounts hold Admin or Data Engineer roles."""
    mock_users = [
        {"id": 1, "username": "admin", "email": "admin@nexus.com", "role": "Admin", "status": "active"},
        {"id": 2, "username": "viewer", "email": "viewer@nexus.com", "role": "Viewer", "status": "active"},
        {"id": 3, "username": "engineer", "email": "engineer@nexus.com", "role": "Data Engineer", "status": "active"},
        {"id": 8, "username": "shine", "email": "abc@gmail.com", "role": "Data Engineer", "status": "active"},
    ]
    mock_get_all_users.return_value = mock_users

    response = client.get("/api/v1/users", headers=admin_headers)
    assert response.status_code == 200

    users_list = response.json()
    admin_count = len([u for u in users_list if u["role"] == "Admin"])
    de_count = len([u for u in users_list if u["role"] == "Data Engineer"])

    assert admin_count == 1
    assert de_count == 2




