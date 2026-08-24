"""Tests for authentication API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User
from app.core.security import get_password_hash, create_access_token
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.services.auth_service import AuthService


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    user.role = "user"
    user.is_active = True
    user.created_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    user.hashed_password = get_password_hash("TestPassword123")
    return user


class TestRegisterEndpoint:
    """Tests for the /api/v1/auth/register endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, mock_db, mock_user):
        """Test successful user registration."""
        # Patch the AuthService.register_user method
        with patch.object(AuthService, "register_user", new_callable=AsyncMock) as mock_register:
            mock_register.return_value = mock_user

            # Override the database dependency
            app.dependency_overrides[get_db] = lambda: mock_db
            client = TestClient(app)

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "username": "testuser",
                    "email": "test@example.com",
                    "password": "TestPassword123"
                }
            )

            assert response.status_code == 201
            data = response.json()
            assert data["username"] == "testuser"
            assert data["email"] == "test@example.com"

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, mock_db):
        """Test registration with duplicate username."""
        with patch.object(AuthService, "register_user", new_callable=AsyncMock) as mock_register:
            mock_register.side_effect = ValueError("Username 'testuser' already exists")

            app.dependency_overrides[get_db] = lambda: mock_db
            client = TestClient(app)

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "username": "testuser",
                    "email": "test@example.com",
                    "password": "TestPassword123"
                }
            )

            assert response.status_code == 400
            assert "already exists" in response.json()["detail"]

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_register_weak_password(self, mock_db):
        """Test registration with weak password fails validation."""
        app.dependency_overrides[get_db] = lambda: mock_db
        client = TestClient(app)

        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "weak"  # Too short, no uppercase, no digit
            }
        )

        assert response.status_code == 422  # Validation error
        app.dependency_overrides.clear()


class TestLoginEndpoint:
    """Tests for the /api/v1/auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, mock_db, mock_user):
        """Test successful login."""
        with patch.object(AuthService, "authenticate_user", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = mock_user

            app.dependency_overrides[get_db] = lambda: mock_db
            client = TestClient(app)

            response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": "testuser",
                    "password": "TestPassword123"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, mock_db):
        """Test login with invalid credentials."""
        with patch.object(AuthService, "authenticate_user", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = None

            app.dependency_overrides[get_db] = lambda: mock_db
            client = TestClient(app)

            response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": "testuser",
                    "password": "WrongPassword123"
                }
            )

            assert response.status_code == 401
            assert "Incorrect username or password" in response.json()["detail"]

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, mock_db, mock_user):
        """Test login with inactive user account."""
        mock_user.is_active = False

        with patch.object(AuthService, "authenticate_user", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = mock_user

            app.dependency_overrides[get_db] = lambda: mock_db
            client = TestClient(app)

            response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": "testuser",
                    "password": "TestPassword123"
                }
            )

            assert response.status_code == 403
            assert "Inactive user account" in response.json()["detail"]

            app.dependency_overrides.clear()


class TestGetCurrentUserEndpoint:
    """Tests for the /api/v1/auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_user):
        """Test getting current user info."""
        # Override the current user dependency
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        client = TestClient(app)

        response = client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self):
        """Test getting current user without valid token."""
        client = TestClient(app)

        # No authorization header - should fail
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401


class TestChangePasswordEndpoint:
    """Tests for the /api/v1/auth/password endpoint."""

    @pytest.mark.asyncio
    async def test_change_password_success(self, mock_db, mock_user):
        """Test successful password change."""
        with patch.object(AuthService, "change_password", new_callable=AsyncMock) as mock_change:
            mock_change.return_value = True

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.put(
                "/api/v1/auth/password",
                json={
                    "current_password": "TestPassword123",
                    "new_password": "NewPassword456"
                }
            )

            assert response.status_code == 200
            assert "Password changed successfully" in response.json()["message"]

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, mock_db, mock_user):
        """Test password change with wrong current password."""
        with patch.object(AuthService, "change_password", new_callable=AsyncMock) as mock_change:
            mock_change.side_effect = ValueError("Incorrect current password")

            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            client = TestClient(app)

            response = client.put(
                "/api/v1/auth/password",
                json={
                    "current_password": "WrongPassword123",
                    "new_password": "NewPassword456"
                }
            )

            assert response.status_code == 400
            assert "Incorrect current password" in response.json()["detail"]

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_change_password_weak_new_password(self, mock_user):
        """Test password change with weak new password."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        client = TestClient(app)

        response = client.put(
            "/api/v1/auth/password",
            json={
                "current_password": "TestPassword123",
                "new_password": "weak"  # Too short, no uppercase, no digit
            }
        )

        assert response.status_code == 422  # Validation error

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_change_password_unauthorized(self):
        """Test password change without authentication."""
        client = TestClient(app)

        response = client.put(
            "/api/v1/auth/password",
            json={
                "current_password": "TestPassword123",
                "new_password": "NewPassword456"
            }
        )

        assert response.status_code == 401