"""用户管理操作的认证服务。

这个模块提供用户注册、认证和密码管理的业务逻辑。
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
    """认证操作的服务类。

    处理用户注册、认证和密码更改。
    """

    def __init__(self, db: AsyncSession):
        """使用数据库会话初始化认证服务。

        Args:
            db: 用于数据库操作的 AsyncSession。
        """
        self.db = db

    async def register_user(self, user_data: UserCreate) -> User:
        """注册新用户。

        Args:
            user_data: 带注册数据的 UserCreate schema。

        Returns:
            创建的 User 对象。

        Raises:
            ValueError: 如果用户名或邮箱已存在。
        """
        # 检查用户名或邮箱是否存在
        existing_user = await self._get_user_by_username_or_email(
            user_data.username,
            user_data.email
        )

        if existing_user:
            if existing_user.username == user_data.username:
                raise ValueError(f"用户名 '{user_data.username}' 已存在")
            else:
                raise ValueError(f"邮箱 '{user_data.email}' 已存在")

        # 创建新用户
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
        """通过用户名和密码认证用户。

        Args:
            username: 要认证的用户名。
            password: 要验证的明文密码。

        Returns:
            认证成功则返回 User 对象，否则返回 None。
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
        """更改用户密码。

        Args:
            user: 要更新的 User 对象。
            old_password: 用于验证的当前密码。
            new_password: 要设置的新密码。

        Returns:
            密码更改成功则返回 True。

        Raises:
            ValueError: 如果旧密码不正确。
        """
        # 验证旧密码
        if not verify_password(old_password, user.hashed_password):
            raise ValueError("旧密码不正确")

        # 更新密码
        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()
        await self.db.refresh(user)

        return True

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """通过 ID 获取用户。

        Args:
            user_id: 作为字符串 (UUID) 的用户 ID。

        Returns:
            找到则返回 User 对象，否则返回 None。
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
        """通过用户名获取用户。

        Args:
            username: 要搜索的用户名。

        Returns:
            找到则返回 User 对象，否则返回 None。
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
        """通过用户名或邮箱获取用户。

        Args:
            username: 要搜索的用户名。
            email: 要搜索的邮箱。

        Returns:
            找到则返回 User 对象，否则返回 None。
        """
        result = await self.db.execute(
            select(User).where(
                or_(User.username == username, User.email == email)
            )
        )
        return result.scalar_one_or_none()