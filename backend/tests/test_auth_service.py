"""Tests for the authentication service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from app.services.auth_service import AuthService
from app.schemas.user import UserCreate
from app.models.user import User
from app.core.security import get_password_hash, verify_password


class TestRegisterUser:
    """Tests for user registration."""

    @pytest.mark.asyncio
    async def test_register_user_success(self):
        """Test successful user registration."""
        # Create mock database
        mock_db = AsyncMock()

        # Mock the _get_user_by_username_or_email to return None (no existing user)
        with patch.object(
            AuthService,
            '_get_user_by_username_or_email',
            return_value=None
        ):
            # Mock db operations
            mock_db.add = MagicMock()
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            # Create service and register user
            service = AuthService(mock_db)
            user_data = UserCreate(
                username="testuser",
                email="test@example.com",
                password="TestPassword123"
            )

            user = await service.register_user(user_data)

            # Verify db methods were called
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

            # Verify user attributes
            assert user.username == "testuser"
            assert user.email == "test@example.com"
            assert user.role == "user"
            assert user.is_active is True

    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(self):
        """Test registration with duplicate username raises error."""
        # Create mock database
        mock_db = AsyncMock()

        # Create existing user with same username
        existing_user = MagicMock(spec=User)
        existing_user.username = "testuser"
        existing_user.email = "other@example.com"

        # Mock the _get_user_by_username_or_email to return existing user
        with patch.object(
            AuthService,
            '_get_user_by_username_or_email',
            return_value=existing_user
        ):
            service = AuthService(mock_db)
            user_data = UserCreate(
                username="testuser",
                email="test@example.com",
                password="TestPassword123"
            )

            with pytest.raises(ValueError) as exc_info:
                await service.register_user(user_data)

            assert "Username 'testuser' already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self):
        """Test registration with duplicate email raises error."""
        # Create mock database
        mock_db = AsyncMock()

        # Create existing user with same email
        existing_user = MagicMock(spec=User)
        existing_user.username = "otheruser"
        existing_user.email = "test@example.com"

        # Mock the _get_user_by_username_or_email to return existing user
        with patch.object(
            AuthService,
            '_get_user_by_username_or_email',
            return_value=existing_user
        ):
            service = AuthService(mock_db)
            user_data = UserCreate(
                username="newuser",
                email="test@example.com",
                password="TestPassword123"
            )

            with pytest.raises(ValueError) as exc_info:
                await service.register_user(user_data)

            assert "Email 'test@example.com' already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_register_user_password_is_hashed(self):
        """Test that password is properly hashed during registration."""
        # Create mock database
        mock_db = AsyncMock()
        added_user = None

        def capture_add(user):
            nonlocal added_user
            added_user = user

        mock_db.add = capture_add
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock the _get_user_by_username_or_email to return None
        with patch.object(
            AuthService,
            '_get_user_by_username_or_email',
            return_value=None
        ):
            service = AuthService(mock_db)
            user_data = UserCreate(
                username="testuser",
                email="test@example.com",
                password="TestPassword123"
            )

            await service.register_user(user_data)

            # Verify password was hashed (not stored in plain text)
            assert added_user.hashed_password != "TestPassword123"
            assert verify_password("TestPassword123", added_user.hashed_password)


class TestAuthenticateUser:
    """Tests for user authentication."""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Test successful authentication with correct credentials."""
        # Create mock database
        mock_db = AsyncMock()

        # Create user with hashed password
        hashed_password = get_password_hash("TestPassword123")
        mock_user = MagicMock(spec=User)
        mock_user.username = "testuser"
        mock_user.hashed_password = hashed_password

        # Mock _get_user_by_username to return user
        with patch.object(
            AuthService,
            '_get_user_by_username',
            return_value=mock_user
        ):
            service = AuthService(mock_db)
            user = await service.authenticate_user("testuser", "TestPassword123")

            assert user == mock_user

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self):
        """Test authentication fails with wrong password."""
        # Create mock database
        mock_db = AsyncMock()

        # Create user with hashed password
        hashed_password = get_password_hash("CorrectPassword123")
        mock_user = MagicMock(spec=User)
        mock_user.username = "testuser"
        mock_user.hashed_password = hashed_password

        # Mock _get_user_by_username to return user
        with patch.object(
            AuthService,
            '_get_user_by_username',
            return_value=mock_user
        ):
            service = AuthService(mock_db)
            user = await service.authenticate_user("testuser", "WrongPassword123")

            assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_non_existent_user(self):
        """Test authentication fails for non-existent user."""
        # Create mock database
        mock_db = AsyncMock()

        # Mock _get_user_by_username to return None
        with patch.object(
            AuthService,
            '_get_user_by_username',
            return_value=None
        ):
            service = AuthService(mock_db)
            user = await service.authenticate_user("nonexistent", "TestPassword123")

            assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_case_sensitive_username(self):
        """Test that username is case sensitive (database lookup)."""
        # Create mock database
        mock_db = AsyncMock()

        # Create user with lowercase username
        hashed_password = get_password_hash("TestPassword123")
        mock_user = MagicMock(spec=User)
        mock_user.username = "testuser"
        mock_user.hashed_password = hashed_password

        # Track what username was searched
        searched_username = None

        async def mock_get_user(username):
            nonlocal searched_username
            searched_username = username
            if username == "testuser":
                return mock_user
            return None

        # Mock _get_user_by_username
        with patch.object(
            AuthService,
            '_get_user_by_username',
            side_effect=mock_get_user
        ):
            service = AuthService(mock_db)

            # Try with different case - should not find user
            user = await service.authenticate_user("TestUser", "TestPassword123")
            assert user is None
            assert searched_username == "TestUser"


class TestChangePassword:
    """Tests for password change functionality."""

    @pytest.mark.asyncio
    async def test_change_password_success(self):
        """Test successful password change."""
        # Create mock database
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Create user with current password
        old_password = "OldPassword123"
        new_password = "NewPassword456"
        hashed_old = get_password_hash(old_password)

        mock_user = MagicMock(spec=User)
        mock_user.hashed_password = hashed_old

        service = AuthService(mock_db)
        result = await service.change_password(mock_user, old_password, new_password)

        assert result is True
        mock_db.commit.assert_called_once()

        # Verify new password was hashed
        assert verify_password(new_password, mock_user.hashed_password)

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(self):
        """Test password change fails with wrong old password."""
        # Create mock database
        mock_db = AsyncMock()

        # Create user with correct password
        correct_password = "CorrectPassword123"
        hashed_password = get_password_hash(correct_password)

        mock_user = MagicMock(spec=User)
        mock_user.hashed_password = hashed_password

        service = AuthService(mock_db)

        with pytest.raises(ValueError) as exc_info:
            await service.change_password(
                mock_user,
                "WrongOldPassword123",
                "NewPassword456"
            )

        assert "Incorrect current password" in str(exc_info.value)
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_change_password_new_password_is_hashed(self):
        """Test that new password is properly hashed."""
        # Create mock database
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        old_password = "OldPassword123"
        new_password = "NewPassword456"
        hashed_old = get_password_hash(old_password)

        mock_user = MagicMock(spec=User)
        mock_user.hashed_password = hashed_old

        service = AuthService(mock_db)
        await service.change_password(mock_user, old_password, new_password)

        # New password should be hashed, not plain text
        assert mock_user.hashed_password != new_password
        assert verify_password(new_password, mock_user.hashed_password)


class TestGetUserById:
    """Tests for getting user by ID."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_found(self):
        """Test getting an existing user by ID."""
        # Create mock database
        mock_db = AsyncMock()

        user_id = uuid4()
        mock_user = MagicMock(spec=User)
        mock_user.id = user_id

        # Mock database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        user = await service.get_user_by_id(str(user_id))

        assert user == mock_user
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self):
        """Test getting a non-existent user by ID returns None."""
        # Create mock database
        mock_db = AsyncMock()

        user_id = uuid4()

        # Mock database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        user = await service.get_user_by_id(str(user_id))

        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_invalid_uuid(self):
        """Test getting user with invalid UUID returns None."""
        # Create mock database
        mock_db = AsyncMock()

        service = AuthService(mock_db)
        user = await service.get_user_by_id("not-a-uuid")

        assert user is None
        # Database should not be queried for invalid UUID
        mock_db.execute.assert_not_called()


class TestPrivateMethods:
    """Tests for private helper methods."""

    @pytest.mark.asyncio
    async def test_get_user_by_username_found(self):
        """Test _get_user_by_username finds user."""
        # Create mock database
        mock_db = AsyncMock()

        mock_user = MagicMock(spec=User)
        mock_user.username = "testuser"

        # Mock database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        user = await service._get_user_by_username("testuser")

        assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self):
        """Test _get_user_by_username returns None if not found."""
        # Create mock database
        mock_db = AsyncMock()

        # Mock database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        user = await service._get_user_by_username("nonexistent")

        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_username_or_email_by_username(self):
        """Test _get_user_by_username_or_email finds by username."""
        # Create mock database
        mock_db = AsyncMock()

        mock_user = MagicMock(spec=User)
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"

        # Mock database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        user = await service._get_user_by_username_or_email("testuser", "other@example.com")

        assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_user_by_username_or_email_by_email(self):
        """Test _get_user_by_username_or_email finds by email."""
        # Create mock database
        mock_db = AsyncMock()

        mock_user = MagicMock(spec=User)
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"

        # Mock database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        user = await service._get_user_by_username_or_email("otheruser", "test@example.com")

        assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_user_by_username_or_email_not_found(self):
        """Test _get_user_by_username_or_email returns None if not found."""
        # Create mock database
        mock_db = AsyncMock()

        # Mock database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        user = await service._get_user_by_username_or_email("nonexistent", "nonexistent@example.com")

        assert user is None