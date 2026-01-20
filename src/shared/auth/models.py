"""
F4: 认证授权模块 - 数据模型
============================
用户、角色、权限等数据模型定义
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from datetime import datetime


class UserRole(str, Enum):
    """用户角色"""
    SUPER_ADMIN = "super_admin"    # 超级管理员（跨租户）
    TENANT_ADMIN = "tenant_admin"  # 租户管理员
    MANAGER = "manager"            # 运营经理
    TRAINER = "trainer"            # 训练师
    OPERATOR = "operator"          # 操作员
    VIEWER = "viewer"              # 只读用户


class UserStatus(str, Enum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


class User(BaseModel):
    """用户模型"""
    user_id: UUID
    tenant_id: UUID

    # 基本信息
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    display_name: str = Field(..., min_length=1, max_length=100)

    # 认证信息
    hashed_password: str

    # 角色和权限
    role: UserRole = UserRole.VIEWER
    permissions: List[str] = []  # 额外权限

    # 状态
    status: UserStatus = UserStatus.ACTIVE
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0

    # 元信息
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None


class TokenPayload(BaseModel):
    """JWT Token载荷"""
    sub: str                      # user_id
    tenant_id: str
    role: str
    permissions: List[str] = []
    exp: datetime                 # 过期时间
    iat: datetime                 # 签发时间
    type: str = "access"          # access | refresh


class APIKey(BaseModel):
    """API密钥（用于服务间认证）"""
    key_id: UUID
    tenant_id: UUID
    name: str
    key_hash: str                 # 哈希后的密钥
    permissions: List[str]
    is_active: bool = True
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime


# ============================================================
# API请求/响应模型
# ============================================================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str
    tenant_id: Optional[str] = None  # 多租户场景


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒
    user: "UserInfo"


class RefreshRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str


class RefreshResponse(BaseModel):
    """刷新令牌响应"""
    access_token: str
    expires_in: int


class LogoutRequest(BaseModel):
    """登出请求"""
    refresh_token: Optional[str] = None


class UserInfo(BaseModel):
    """用户信息（返回给客户端）"""
    user_id: str
    tenant_id: str
    username: str
    email: str
    display_name: str
    role: str
    permissions: List[str]


class CreateUserRequest(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.VIEWER


class UpdateUserRequest(BaseModel):
    """更新用户请求"""
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    current_password: str
    new_password: str = Field(..., min_length=8)


# Update forward reference
LoginResponse.model_rebuild()
