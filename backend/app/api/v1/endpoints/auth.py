"""Authentication API endpoints.

This module provides REST API endpoints for user authentication,
including registration, login, user info, and password management.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, get_current_active_user
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserResponse,
    Token,
    PasswordChange,
)
from app.services.auth_service import AuthService
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with username, email, and password."
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Register a new user.

    Args:
        user_data: User registration data.
        db: Database session.

    Returns:
        Created user object.

    Raises:
        HTTPException: If username or email already exists.
    """
    service = AuthService(db)

    try:
        user = await service.register_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=Token,
    summary="User login",
    description="Authenticate user and return JWT access token."
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Authenticate user and return JWT token.

    Args:
        form_data: OAuth2 password request form with username and password.
        db: Database session.

    Returns:
        Token object with access_token and token_type.

    Raises:
        HTTPException: If authentication fails.
    """
    service = AuthService(db)

    user = await service.authenticate_user(
        form_data.username,
        form_data.password
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账号已被禁用"
        )

    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's information."
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current authenticated user info.

    Args:
        current_user: Current authenticated user.

    Returns:
        Current user object.
    """
    return current_user


@router.put(
    "/password",
    summary="Change password",
    description="Change the current user's password."
)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Change user password.

    Args:
        password_data: Password change data with current and new password.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Success message.

    Raises:
        HTTPException: If current password is incorrect.
    """
    service = AuthService(db)

    try:
        await service.change_password(
            current_user,
            password_data.current_password,
            password_data.new_password
        )
        return {"message": "密码修改成功"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )