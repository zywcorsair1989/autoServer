"""Tests for the security module."""

import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException
from jose import jwt

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_token,
    get_current_user,
    get_current_active_user,
    require_role,
    pwd_context,
)
from app.core.config import settings
from app.schemas.user import TokenData
from app.models.user import User


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_get_password_hash_returns_string(self):
        """Test that get_password_hash returns a string."""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) > 0

    def test_get_password_hash_creates_different_hashes(self):
        """Test that different passwords create different hashes."""
        hash1 = get_password_hash("Password1")
        hash2 = get_password_hash("Password2")

        assert hash1 != hash2

    def test_get_password_hash_creates_different_hashes_for_same_password(self):
        """Test that same password creates different hashes (due to salt)."""
        password = "TestPassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert verify_password("WrongPassword", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case sensitive."""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert verify_password(password.lower(), hashed) is False
        assert verify_password(password.upper(), hashed) is False


class TestJWTToken:
    """Tests for JWT token functions."""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a string."""
        data = {"sub": str(uuid4()), "username": "testuser"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiry(self):
        """Test token creation with custom expiration time."""
        data = {"sub": str(uuid4())}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)

        # Decode and check expiration
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert "exp" in payload

    def test_create_access_token_contains_data(self):
        """Test that token contains the provided data."""
        user_id = str(uuid4())
        username = "testuser"
        role = "admin"
        data = {"sub": user_id, "username": username, "role": role}
        token = create_access_token(data)

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        assert payload["sub"] == user_id
        assert payload["username"] == username
        assert payload["role"] == role

    def test_decode_token_valid(self):
        """Test decoding a valid token."""
        user_id = str(uuid4())
        username = "testuser"
        role = "user"
        data = {"sub": user_id, "username": username, "role": role}
        token = create_access_token(data)

        token_data = decode_token(token)

        assert token_data is not None
        assert str(token_data.user_id) == user_id
        assert token_data.username == username
        assert token_data.role == role

    def test_decode_token_invalid(self):
        """Test decoding an invalid token returns None."""
        invalid_token = "invalid.token.string"
        token_data = decode_token(invalid_token)

        assert token_data is None

    def test_decode_token_missing_sub(self):
        """Test decoding token without 'sub' field returns None."""
        data = {"username": "testuser"}  # No 'sub' field
        token = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        token_data = decode_token(token)

        assert token_data is None

    def test_decode_token_expired(self):
        """Test decoding an expired token returns None."""
        # Create an already expired token
        data = {"sub": str(uuid4()), "exp": 0}  # Expired at epoch 0
        token = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        token_data = decode_token(token)

        assert token_data is None

    def test_decode_token_wrong_secret(self):
        """Test decoding token with wrong secret returns None."""
        data = {"sub": str(uuid4())}
        token = jwt.encode(data, "wrong-secret", algorithm=settings.ALGORITHM)

        token_data = decode_token(token)

        assert token_data is None


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Test getting user with valid token."""
        user_id = uuid4()
        username = "testuser"

        # Create a mock user
        mock_user = MagicMock(spec=User)
        mock_user.id = user_id
        mock_user.username = username
        mock_user.is_active = True
        mock_user.role = "user"

        # Create token
        token = create_access_token({
            "sub": str(user_id),
            "username": username,
            "role": "user"
        })

        # Mock database session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        # Get current user
        user = await get_current_user(token=token, db=mock_db)

        assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test getting user with invalid token raises exception."""
        mock_db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="invalid.token", db=mock_db)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self):
        """Test getting non-existent user raises exception."""
        user_id = str(uuid4())
        token = create_access_token({"sub": user_id})

        # Mock database session returning None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=mock_db)

        assert exc_info.value.status_code == 401


class TestGetCurrentActiveUser:
    """Tests for get_current_active_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_active_user_active(self):
        """Test getting active user succeeds."""
        mock_user = MagicMock(spec=User)
        mock_user.is_active = True

        user = await get_current_active_user(current_user=mock_user)

        assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self):
        """Test getting inactive user raises exception."""
        mock_user = MagicMock(spec=User)
        mock_user.is_active = False

        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(current_user=mock_user)

        assert exc_info.value.status_code == 403
        assert "Inactive user" in exc_info.value.detail


class TestRequireRole:
    """Tests for require_role dependency."""

    @pytest.mark.asyncio
    async def test_require_role_correct_role(self):
        """Test user with correct role passes check."""
        mock_user = MagicMock(spec=User)
        mock_user.role = "admin"
        mock_user.is_active = True

        role_checker = require_role("admin")
        user = await role_checker(current_user=mock_user)

        assert user == mock_user

    @pytest.mark.asyncio
    async def test_require_role_incorrect_role(self):
        """Test user with incorrect role raises exception."""
        mock_user = MagicMock(spec=User)
        mock_user.role = "user"
        mock_user.is_active = True

        role_checker = require_role("admin")

        with pytest.raises(HTTPException) as exc_info:
            await role_checker(current_user=mock_user)

        assert exc_info.value.status_code == 403
        assert "admin" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_role_different_roles(self):
        """Test role checking for different roles."""
        # User role checker
        user_checker = require_role("user")

        mock_user = MagicMock(spec=User)
        mock_user.role = "user"
        mock_user.is_active = True

        user = await user_checker(current_user=mock_user)
        assert user == mock_user

        # Admin role checker - should fail
        admin_checker = require_role("admin")

        with pytest.raises(HTTPException):
            await admin_checker(current_user=mock_user)


class TestTokenData:
    """Tests for TokenData schema."""

    def test_token_data_creation(self):
        """Test TokenData object creation."""
        user_id = str(uuid4())
        token_data = TokenData(
            user_id=user_id,
            username="testuser",
            role="admin"
        )

        assert str(token_data.user_id) == user_id
        assert token_data.username == "testuser"
        assert token_data.role == "admin"

    def test_token_data_optional_fields(self):
        """Test TokenData with optional fields."""
        token_data = TokenData()

        assert token_data.user_id is None
        assert token_data.username is None
        assert token_data.role is None