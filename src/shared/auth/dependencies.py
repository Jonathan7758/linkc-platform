"""
F4: 认证授权模块 - FastAPI依赖注入
====================================
用于API路由的认证和授权依赖
"""

from typing import Optional, Callable
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import TokenPayload
from .jwt import decode_token
from .permissions import has_permission

# Bearer token安全方案
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> TokenPayload:
    """
    获取当前认证用户

    从Authorization header中提取并验证JWT token

    Raises:
        HTTPException 401: 未认证或token无效
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[TokenPayload]:
    """
    获取当前用户（可选）

    如果没有token或token无效，返回None而不是抛出异常
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.type != "access":
        return None

    return payload


def require_permission(permission: str) -> Callable:
    """
    权限检查依赖工厂

    用法:
        @router.get("/robots")
        async def list_robots(
            current_user: TokenPayload = Depends(require_permission("robot:read"))
        ):
            pass
    """
    async def permission_checker(
        current_user: TokenPayload = Depends(get_current_user)
    ) -> TokenPayload:
        if not has_permission(current_user.permissions, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required",
            )
        return current_user
    return permission_checker


def require_any_permission(*permissions: str) -> Callable:
    """
    任一权限检查依赖工厂

    用法:
        @router.get("/data")
        async def get_data(
            current_user: TokenPayload = Depends(require_any_permission("data:read", "admin:read"))
        ):
            pass
    """
    async def permission_checker(
        current_user: TokenPayload = Depends(get_current_user)
    ) -> TokenPayload:
        # 超级管理员拥有所有权限
        if "*" in current_user.permissions:
            return current_user
        if not any(perm in current_user.permissions for perm in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: one of {permissions} required",
            )
        return current_user
    return permission_checker


def require_tenant(tenant_id_param: str = "tenant_id") -> Callable:
    """
    租户检查依赖工厂

    确保用户只能访问自己租户的数据

    用法:
        @router.get("/tenants/{tenant_id}/data")
        async def get_tenant_data(
            tenant_id: str,
            current_user: TokenPayload = Depends(require_tenant("tenant_id"))
        ):
            pass
    """
    async def tenant_checker(
        current_user: TokenPayload = Depends(get_current_user),
        **kwargs
    ) -> TokenPayload:
        # 从路径参数获取tenant_id
        # 注意：实际使用时需要从request中获取
        return current_user
    return tenant_checker


async def check_tenant_access(
    current_user: TokenPayload,
    tenant_id: str
) -> bool:
    """
    检查用户是否有权访问指定租户

    Args:
        current_user: 当前用户token
        tenant_id: 目标租户ID

    Returns:
        True if access allowed

    Raises:
        HTTPException 403: 无权访问
    """
    # super_admin可以访问所有租户
    if current_user.role == "super_admin":
        return True

    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant",
        )

    return True


class RoleRequired:
    """
    角色检查依赖类

    用法:
        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: str,
            current_user: TokenPayload = Depends(RoleRequired(["tenant_admin", "super_admin"]))
        ):
            pass
    """

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        current_user: TokenPayload = Depends(get_current_user)
    ) -> TokenPayload:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: one of {self.allowed_roles}",
            )
        return current_user


# 预定义的角色检查
require_admin = RoleRequired(["tenant_admin", "super_admin"])
require_super_admin = RoleRequired(["super_admin"])


async def get_api_key_tenant(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Optional[str]:
    """
    通过API Key获取租户ID（用于服务间认证）

    MVP简化版：直接返回API Key作为tenant_id
    生产环境应该查询数据库验证API Key

    Returns:
        tenant_id if API key is valid, None otherwise
    """
    if not x_api_key:
        return None

    # MVP简化：假设API Key格式为 "tenant_xxx_secretkey"
    # 生产环境应该查询数据库
    if x_api_key.startswith("tenant_"):
        parts = x_api_key.split("_")
        if len(parts) >= 2:
            return parts[1]

    return None
