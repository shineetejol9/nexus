"""
Unit tests for backend/auth.py module.

Tests password hashing, verification, JWT token creation/decoding,
login logic with mocked database calls, and role-based permissions.
"""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from jose import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

# Add backend to Python path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    login_user,
    get_current_user,
    require_role,
)

# Test secret key for JWT operations
TEST_SECRET_KEY = "test_secret_key_for_nexus_unit_tests"
TEST_ALGORITHM = "HS256"


@pytest.fixture(autouse=True)
def setup_jwt_env(monkeypatch):
    """Ensure JWT environment variables are set for all auth tests."""
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET_KEY)
    monkeypatch.setenv("JWT_ALGORITHM", TEST_ALGORITHM)
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "60")


def test_hash_password():
    """Verify password hashing returns a non-empty hashed string different from plaintext."""
    plain_password = "MySecurePassword123!"
    hashed = hash_password(plain_password)

    assert hashed is not None
    assert isinstance(hashed, str)
    assert len(hashed) > 0
    assert hashed != plain_password


def test_verify_password():
    """Verify password verification returns True for correct password and False for wrong password."""
    plain_password = "SecretPassword456"
    hashed = hash_password(plain_password)

    assert verify_password(plain_password, hashed) is True
    assert verify_password("WrongPassword789", hashed) is False


def test_create_access_token():
    """Verify JWT token creation and decoding of payload fields."""
    user_id = 42
    username = "test_user"
    role = "Data Engineer"

    token = create_access_token(user_id=user_id, username=username, role=role)
    assert token is not None
    assert isinstance(token, str)

    # Decode and verify payload
    payload = jwt.decode(token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])
    assert payload["user_id"] == user_id
    assert payload["username"] == username
    assert payload["role"] == role
    assert "exp" in payload


@patch("auth.get_connection")
def test_login_user_success(mock_get_connection):
    """Test successful login with mocked database connection."""
    plain_password = "ValidPassword123"
    hashed_pwd = hash_password(plain_password)

    # Setup mocked cursor response: (id, username, password_hash, role)
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (1, "john_doe", hashed_pwd, "Admin")

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    success, token = login_user("john_doe", plain_password)

    assert success is True
    assert isinstance(token, str)

    # Verify query execution
    mock_cursor.execute.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()


@patch("auth.get_connection")
def test_login_user_invalid_username(mock_get_connection):
    """Test login failure when user is not found in database."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    success, message = login_user("non_existent_user", "some_pass")

    assert success is False
    assert message == "Invalid username or password"


@patch("auth.get_connection")
def test_login_user_incorrect_password(mock_get_connection):
    """Test login failure when password does not match."""
    hashed_pwd = hash_password("CorrectPassword")

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (1, "jane_doe", hashed_pwd, "Viewer")

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    success, message = login_user("jane_doe", "WrongPassword")

    assert success is False
    assert message == "Invalid username or password"


def test_get_current_user_valid_token():
    """Test get_current_user decodes valid Bearer token credentials."""
    token = create_access_token(user_id=10, username="valid_user", role="Admin")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    current_user = get_current_user(credentials)
    assert current_user["user_id"] == 10
    assert current_user["username"] == "valid_user"
    assert current_user["role"] == "Admin"


def test_get_current_user_invalid_token():
    """Test get_current_user raises HTTP 401 for an invalid token."""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_jwt_token_str")

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired token"


def test_require_role_allowed():
    """Test require_role allows users with an authorized role."""
    role_checker = require_role("Admin", "Data Engineer")

    user_payload = {"user_id": 1, "username": "admin_user", "role": "Admin"}
    result = role_checker(current_user=user_payload)
    assert result == user_payload


def test_require_role_disallowed():
    """Test require_role raises HTTP 403 when user role is not authorized."""
    role_checker = require_role("Admin")

    user_payload = {"user_id": 2, "username": "viewer_user", "role": "Viewer"}

    with pytest.raises(HTTPException) as exc_info:
        role_checker(current_user=user_payload)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "You do not have permission to access this resource"


def test_require_role_multiple_allowed_roles():
    """Test require_role with multiple allowed roles permits matching user."""
    role_checker = require_role("Admin", "Data Engineer", "Viewer")

    de_user = {"user_id": 3, "username": "de_bob", "role": "Data Engineer"}
    result = role_checker(current_user=de_user)
    assert result == de_user
