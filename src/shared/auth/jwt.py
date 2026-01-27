"""
F4: 认证授权模块 - JWT处理
============================
Token生成和验证
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
import os

from .models import User, TokenPayload
from .permissions import get_user_permissions

# 配置 - 从环境变量读取
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ecis-robot-dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def create_access_token(user: User) -> str:
    """
    创建访问令牌

    Args:
        user: 用户对象

    Returns:
        JWT access token
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    permissions = get_user_permissions(user.role, user.permissions)

    payload = {
        "sub": str(user.user_id),
        "tenant_id": str(user.tenant_id),
        "role": user.role.value,
        "permissions": permissions,
        "exp": expire,
        "iat": now,
        "type": "access"
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user: User) -> str:
    """
    创建刷新令牌

    Args:
        user: 用户对象

    Returns:
        JWT refresh token
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(user.user_id),
        "tenant_id": str(user.tenant_id),
        "role": user.role.value,
        "permissions": [],  # refresh token不需要权限
        "exp": expire,
        "iat": now,
        "type": "refresh"
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenPayload]:
    """
    解码并验证令牌

    Args:
        token: JWT token字符串

    Returns:
        TokenPayload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # 转换datetime字段
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)

        return TokenPayload(
            sub=payload["sub"],
            tenant_id=payload["tenant_id"],
            role=payload["role"],
            permissions=payload.get("permissions", []),
            exp=exp,
            iat=iat,
            type=payload.get("type", "access")
        )
    except JWTError:
        return None
    except (KeyError, ValueError):
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[TokenPayload]:
    """
    验证令牌

    Args:
        token: JWT token字符串
        token_type: 期望的token类型 ("access" | "refresh")

    Returns:
        TokenPayload if valid, None otherwise
    """
    payload = decode_token(token)
    if not payload:
        return None
    if payload.type != token_type:
        return None
    return payload


def is_token_expired(payload: TokenPayload) -> bool:
    """检查token是否过期"""
    now = datetime.now(timezone.utc)
    return payload.exp < now


def get_token_remaining_time(payload: TokenPayload) -> int:
    """获取token剩余有效时间（秒）"""
    now = datetime.now(timezone.utc)
    remaining = (payload.exp - now).total_seconds()
    return max(0, int(remaining))
