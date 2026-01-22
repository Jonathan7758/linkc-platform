"""
G7: 系统管理API - 数据模型
============================
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================
# 枚举类型
# ============================================================

class TenantStatus(str, Enum):
    """租户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class UserStatus(str, Enum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


class UserRole(str, Enum):
    """用户角色"""
    PLATFORM_ADMIN = "platform_admin"
    TENANT_ADMIN = "tenant_admin"
    MANAGER = "manager"
    TRAINER = "trainer"
    OPERATOR = "operator"


class AuditAction(str, Enum):
    """审计动作"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"


# ============================================================
# 请求模型
# ============================================================

class TenantContact(BaseModel):
    """租户联系人"""
    name: str
    email: str
    phone: Optional[str] = None


class TenantSettings(BaseModel):
    """租户设置"""
    max_buildings: int = 10
    max_robots: int = 50
    max_users: int = 30


class TenantCreate(BaseModel):
    """创建租户请求"""
    name: str
    code: str
    plan: str = "professional"
    contact: TenantContact
    settings: Optional[TenantSettings] = None
    expires_at: Optional[datetime] = None


class TenantUpdate(BaseModel):
    """更新租户请求"""
    name: Optional[str] = None
    contact: Optional[TenantContact] = None
    settings: Optional[TenantSettings] = None
    status: Optional[TenantStatus] = None


class UserCreate(BaseModel):
    """创建用户请求"""
    username: str
    email: str
    name: str
    role: UserRole
    password: Optional[str] = None


class UserUpdate(BaseModel):
    """更新用户请求"""
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class SystemConfigUpdate(BaseModel):
    """系统配置更新"""
    key: str
    value: Any
    description: Optional[str] = None


# ============================================================
# 响应模型
# ============================================================

class TenantListItem(BaseModel):
    """租户列表项"""
    tenant_id: str
    name: str
    code: str
    status: TenantStatus
    plan: str
    buildings_count: int = 0
    robots_count: int = 0
    users_count: int = 0
    created_at: datetime
    expires_at: Optional[datetime] = None


class TenantDetail(TenantListItem):
    """租户详情"""
    contact: Optional[TenantContact] = None
    settings: Optional[TenantSettings] = None
    updated_at: Optional[datetime] = None


class TenantListResponse(BaseModel):
    """租户列表响应"""
    items: List[TenantListItem]
    total: int
    page: int
    page_size: int


class TenantCreateResponse(BaseModel):
    """创建租户响应"""
    tenant_id: str
    name: str
    status: TenantStatus
    admin_account: Optional[Dict[str, str]] = None


class UserListItem(BaseModel):
    """用户列表项"""
    user_id: str
    username: str
    email: str
    name: str
    role: UserRole
    role_name: str
    status: UserStatus
    last_login_at: Optional[datetime] = None
    created_at: datetime


class UserDetail(UserListItem):
    """用户详情"""
    tenant_id: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    updated_at: Optional[datetime] = None


class UserListResponse(BaseModel):
    """用户列表响应"""
    items: List[UserListItem]
    total: int
    page: int
    page_size: int


class AuditLogItem(BaseModel):
    """审计日志项"""
    log_id: str
    user_id: str
    username: str
    action: AuditAction
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    timestamp: datetime


class AuditLogResponse(BaseModel):
    """审计日志响应"""
    items: List[AuditLogItem]
    total: int
    page: int
    page_size: int


class SystemConfig(BaseModel):
    """系统配置"""
    key: str
    value: Any
    description: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


class SystemConfigListResponse(BaseModel):
    """系统配置列表响应"""
    configs: List[SystemConfig]


class SystemHealthResponse(BaseModel):
    """系统健康响应"""
    status: str
    version: str
    uptime: int
    services: Dict[str, str]
    database: str
    cache: str
    timestamp: datetime


# ============================================================
# 通用响应
# ============================================================

class ApiResponse(BaseModel):
    """通用API响应"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None
