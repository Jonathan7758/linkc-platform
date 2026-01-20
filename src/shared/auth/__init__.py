"""
F4: 认证授权模块
================
提供系统的认证和授权功能

主要功能:
- JWT Token生成和验证
- 密码哈希和验证
- 基于角色的访问控制(RBAC)
- 多租户数据隔离
- FastAPI依赖注入

用法示例:
    from src.shared.auth import (
        create_access_token,
        create_refresh_token,
        decode_token,
        hash_password,
        verify_password,
        get_current_user,
        require_permission,
        Permission,
        UserRole,
    )

    # 登录时生成token
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    # 在API路由中使用
    @router.get("/robots")
    async def list_robots(
        current_user: TokenPayload = Depends(require_permission("robot:read"))
    ):
        pass
"""

# 数据模型
from .models import (
    User,
    UserRole,
    UserStatus,
    TokenPayload,
    APIKey,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    LogoutRequest,
    UserInfo,
    CreateUserRequest,
    UpdateUserRequest,
    ChangePasswordRequest,
)

# 权限
from .permissions import (
    Permission,
    ROLE_PERMISSIONS,
    get_role_permissions,
    get_user_permissions,
    has_permission,
    has_any_permission,
    has_all_permissions,
)

# 密码处理
from .password import (
    hash_password,
    verify_password,
    validate_password,
    validate_password_strength,
)

# JWT处理
from .jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token,
    is_token_expired,
    get_token_remaining_time,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

# FastAPI依赖
from .dependencies import (
    get_current_user,
    get_current_user_optional,
    require_permission,
    require_any_permission,
    require_tenant,
    check_tenant_access,
    RoleRequired,
    require_admin,
    require_super_admin,
    get_api_key_tenant,
)

__all__ = [
    # 模型
    "User",
    "UserRole",
    "UserStatus",
    "TokenPayload",
    "APIKey",
    "LoginRequest",
    "LoginResponse",
    "RefreshRequest",
    "RefreshResponse",
    "LogoutRequest",
    "UserInfo",
    "CreateUserRequest",
    "UpdateUserRequest",
    "ChangePasswordRequest",
    # 权限
    "Permission",
    "ROLE_PERMISSIONS",
    "get_role_permissions",
    "get_user_permissions",
    "has_permission",
    "has_any_permission",
    "has_all_permissions",
    # 密码
    "hash_password",
    "verify_password",
    "validate_password",
    "validate_password_strength",
    # JWT
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token",
    "is_token_expired",
    "get_token_remaining_time",
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "REFRESH_TOKEN_EXPIRE_DAYS",
    # 依赖
    "get_current_user",
    "get_current_user_optional",
    "require_permission",
    "require_any_permission",
    "require_tenant",
    "check_tenant_access",
    "RoleRequired",
    "require_admin",
    "require_super_admin",
    "get_api_key_tenant",
]
