"""
G1: 认证授权API - 数据模型
===========================
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============================================================
# 枚举类型
# ============================================================

class UserStatus(str, Enum):
    """用户状态"""
    ACTIVE = "active"
    DISABLED = "disabled"
    PENDING = "pending"


# ============================================================
# 用户模型
# ============================================================

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(min_length=3, max_length=100)
    name: str = Field(min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    """创建用户请求"""
    password: str = Field(min_length=8, max_length=100)
    role_id: str = Field(default="role-operator")

    @field_validator('password')
    @classmethod
    def password_complexity(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        return v


class UserUpdate(BaseModel):
    """更新用户请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role_id: Optional[str] = None
    status: Optional[UserStatus] = None


class UserInDB(UserBase):
    """数据库中的用户"""
    id: str
    tenant_id: str
    role_id: str
    status: UserStatus = UserStatus.ACTIVE
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


class UserResponse(BaseModel):
    """用户响应"""
    id: str
    username: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role_id: str
    role_name: Optional[str] = None
    status: UserStatus
    tenant_id: str
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """用户列表响应"""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int


# ============================================================
# 角色模型
# ============================================================

class RoleBase(BaseModel):
    """角色基础模型"""
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)


class RoleCreate(RoleBase):
    """创建角色请求"""
    pass


class RoleUpdate(BaseModel):
    """更新角色请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class RoleInDB(RoleBase):
    """数据库中的角色"""
    id: str
    tenant_id: str
    is_system: bool = False
    created_at: datetime
    updated_at: datetime


class RoleResponse(BaseModel):
    """角色响应"""
    id: str
    name: str
    description: Optional[str] = None
    permissions: List[str]
    is_system: bool
    user_count: int = 0

    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    """角色列表响应"""
    items: List[RoleResponse]


# ============================================================
# 权限模型
# ============================================================

class Permission(BaseModel):
    """权限"""
    code: str
    name: str
    description: Optional[str] = None
    category: str


class PermissionListResponse(BaseModel):
    """权限列表响应"""
    permissions: List[Permission]


# ============================================================
# 认证模型
# ============================================================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str
    tenant_id: Optional[str] = None


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserResponse


class RefreshRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str


class RefreshResponse(BaseModel):
    """刷新Token响应"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """JWT Token载荷"""
    sub: str  # user_id
    tenant_id: str
    role: str
    permissions: List[str]
    exp: datetime
    iat: datetime
    jti: str  # token唯一标识


class CurrentUser(BaseModel):
    """当前用户信息"""
    id: str
    username: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: RoleResponse
    tenant_id: str
    tenant_name: Optional[str] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None


# ============================================================
# 通用响应
# ============================================================

class MessageResponse(BaseModel):
    """消息响应"""
    message: str


class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str
    error_code: Optional[str] = None
