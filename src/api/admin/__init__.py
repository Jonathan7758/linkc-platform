"""
G7: 系统管理API
==================
提供租户管理、用户管理、系统配置等管理功能
"""

from .models import (
    # 枚举
    TenantStatus,
    UserStatus,
    UserRole,
    AuditAction,
    # 请求模型
    TenantContact,
    TenantSettings,
    TenantCreate,
    TenantUpdate,
    UserCreate,
    UserUpdate,
    SystemConfigUpdate,
    # 响应模型
    TenantListItem,
    TenantDetail,
    TenantListResponse,
    TenantCreateResponse,
    UserListItem,
    UserDetail,
    UserListResponse,
    AuditLogItem,
    AuditLogResponse,
    SystemConfig,
    SystemConfigListResponse,
    SystemHealthResponse,
    ApiResponse,
)

from .service import AdminService
from .router import router

__all__ = [
    # 枚举
    "TenantStatus",
    "UserStatus",
    "UserRole",
    "AuditAction",
    # 请求模型
    "TenantContact",
    "TenantSettings",
    "TenantCreate",
    "TenantUpdate",
    "UserCreate",
    "UserUpdate",
    "SystemConfigUpdate",
    # 响应模型
    "TenantListItem",
    "TenantDetail",
    "TenantListResponse",
    "TenantCreateResponse",
    "UserListItem",
    "UserDetail",
    "UserListResponse",
    "AuditLogItem",
    "AuditLogResponse",
    "SystemConfig",
    "SystemConfigListResponse",
    "SystemHealthResponse",
    "ApiResponse",
    # 服务
    "AdminService",
    # 路由
    "router",
]
