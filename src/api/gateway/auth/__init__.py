"""
G1: 认证授权API
===============
提供用户认证、授权、用户管理、角色管理功能。
"""

from .models import (
    UserStatus, UserCreate, UserUpdate, UserResponse, UserListResponse,
    RoleCreate, RoleUpdate, RoleResponse, RoleListResponse,
    Permission, PermissionListResponse,
    LoginRequest, LoginResponse, RefreshRequest, RefreshResponse,
    CurrentUser, MessageResponse
)
from .service import AuthService, AuthConfig, InMemoryAuthStorage
from .router import (
    router,
    get_auth_service, set_auth_service,
    get_current_user, get_current_user_optional,
    require_permission
)

__all__ = [
    # Models
    "UserStatus", "UserCreate", "UserUpdate", "UserResponse", "UserListResponse",
    "RoleCreate", "RoleUpdate", "RoleResponse", "RoleListResponse",
    "Permission", "PermissionListResponse",
    "LoginRequest", "LoginResponse", "RefreshRequest", "RefreshResponse",
    "CurrentUser", "MessageResponse",
    # Service
    "AuthService", "AuthConfig", "InMemoryAuthStorage",
    # Router
    "router",
    "get_auth_service", "set_auth_service",
    "get_current_user", "get_current_user_optional",
    "require_permission",
]
