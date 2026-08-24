"""安全模块，提供密码哈希、JWT 令牌管理和认证依赖项。"""

from datetime import datetime, timedelta
from typing import Optional, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import TokenData

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 用于令牌认证的 OAuth2 方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_password_hash(password: str) -> str:
    """使用 bcrypt 对密码进行哈希。

    Args:
        password: 要哈希的明文密码。

    Returns:
        哈希密码字符串。
    """
    # bcrypt 有 72 字节的密码长度限制
    # 截断为 72 个字符以确保不超过字节限制
    # 因为某些字符在 UTF-8 中占用多个字节
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码与其哈希。

    Args:
        plain_password: 要验证的明文密码。
        hashed_password: 用来比较的哈希密码。

    Returns:
        密码匹配则返回 True，否则返回 False。
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT 访问令牌。

    Args:
        data: 要在令牌中编码的有效载荷数据。
        expires_delta: 可选的自定义过期时间。

    Returns:
        编码的 JWT 令牌字符串。
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """解码和验证 JWT 令牌。

    Args:
        token: 要解码的 JWT 令牌字符串。

    Returns:
        令牌有效则返回 TokenData 对象，否则返回 None。
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: Optional[str] = payload.get("sub")
        username: Optional[str] = payload.get("username")
        role: Optional[str] = payload.get("role")

        if user_id is None:
            return None

        return TokenData(
            user_id=user_id,
            username=username,
            role=role
        )
    except JWTError:
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """从 JWT 令牌获取当前认证的用户。

    Args:
        token: 授权头的 JWT 令牌。
        db: 数据库会话依赖项。

    Returns:
        认证成功则返回 User 对象。

    Raises:
        HTTPException: 如果令牌无效或用户未找到。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = decode_token(token)

    if token_data is None or token_data.user_id is None:
        raise credentials_exception

    try:
        # 挥用户 ID
        result = await db.execute(
            select(User).where(User.id == token_data.user_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise credentials_exception

        return user
    except Exception:
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户。

    Args:
        current_user: 当前认证用户依赖项。

    Returns:
        用户活跃则返回 User 对象。

    Raises:
        HTTPException: 如果用户非活跃。
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    return current_user


def require_role(role: str) -> Callable:
    """创建检查用户是否具有所需角色的依赖项。

    Args:
        role: 需要的角色字符串（例如 "admin", "user"）。

    Returns:
        验证角色的依赖项函数。

    Raises:
        HTTPException: 如果用户不具有所需角色。
    """

    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"此操作需要 '{role}' 角色"
            )
        return current_user

    return role_checker