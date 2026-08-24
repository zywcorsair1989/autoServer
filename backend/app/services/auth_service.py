"""Authentication service for user management operations.

This module provides business logic for user registration,
authentication, and password management.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password


class AuthService:
    """Service class for authentication operations.

    Handles user registration, authentication, and password changes.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the auth service with a database session.

        Args:
            db: AsyncSession for database operations.
        """
        self.db = db

    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user.

        Args:
            user_data: UserCreate schema with registration data.

        Returns:
            Created User object.

        Raises:
            ValueError: If username or email already exists.
        """
        # Check for existing username or email
        existing_user = await self._get_user_by_username_or_email(
            user_data.username,
            user_data.email
        )

        if existing_user:
            if existing_user.username == user_data.username:
                raise ValueError(f"Username '{user_data.username}' already exists")
            else:
                raise ValueError(f"Email '{user_data.email}' already exists")

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            role="user",
            is_active=True
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        return new_user

    async def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Optional[User]:
        """Authenticate a user by username and password.

        Args:
            username: Username to authenticate.
            password: Plain text password to verify.

        Returns:
            User object if authentication successful, None otherwise.
        """
        user = await self._get_user_by_username(username)

        if user is None:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    async def change_password(
        self,
        user: User,
        old_password: str,
        new_password: str
    ) -> bool:
        """Change a user's password.

        Args:
            user: User object to update.
            old_password: Current password for verification.
            new_password: New password to set.

        Returns:
            True if password changed successfully.

        Raises:
            ValueError: If old password is incorrect.
        """
        # Verify old password
        if not verify_password(old_password, user.hashed_password):
            raise ValueError("Incorrect current password")

        # Update password
        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()
        await self.db.refresh(user)

        return True

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID.

        Args:
            user_id: User ID as string (UUID).

        Returns:
            User object if found, None otherwise.
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            return None

        result = await self.db.execute(
            select(User).where(User.id == user_uuid)
        )
        return result.scalar_one_or_none()

    async def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username.

        Args:
            username: Username to search for.

        Returns:
            User object if found, None otherwise.
        """
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def _get_user_by_username_or_email(
        self,
        username: str,
        email: str
    ) -> Optional[User]:
        """Get a user by username or email.

        Args:
            username: Username to search for.
            email: Email to search for.

        Returns:
            User object if found, None otherwise.
        """
        result = await self.db.execute(
            select(User).where(
                or_(User.username == username, User.email == email)
            )
        )
        return result.scalar_one_or_none()