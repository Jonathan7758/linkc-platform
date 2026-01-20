# 模块开发规格书：F4 认证授权模块

## 文档信息

| 项目 | 内容 |
|-----|------|
| 模块ID | F4 |
| 模块名称 | 认证授权模块 |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | F1数据模型、F3配置管理 |

---

## 1. 模块概述

### 1.1 职责描述

认证授权模块负责系统的安全访问控制，包括：
- **用户认证**：验证用户身份（JWT Token）
- **权限管理**：基于角色的访问控制（RBAC）
- **多租户隔离**：确保租户数据隔离
- **API密钥管理**：支持服务间认证

### 1.2 在系统中的位置

```
┌─────────────────────────────────────────────────────────────┐
│                         前端层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 训练工作台   │  │ 运营控制台   │  │ 战略驾驶舱   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                      API网关层                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              【F4 认证授权中间件】                      │  │
│  │         JWT验证 → 权限检查 → 租户隔离                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ▼                                  │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐          │
│  │空间 │ │任务 │ │机器人│ │监控 │ │Agent│ │报表 │          │
│  │API │ │API │ │API  │ │API │ │API │ │API │          │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 技术选型

| 技术 | 用途 | 说明 |
|-----|------|------|
| python-jose | JWT处理 | Token生成和验证 |
| passlib | 密码哈希 | bcrypt算法 |
| pydantic | 数据验证 | 用户模型验证 |

---

## 2. 数据模型

### 2.1 用户模型

```python
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
```

### 2.2 权限定义

```python
class Permission(str, Enum):
    """系统权限"""
    # 空间管理
    SPACE_READ = "space:read"
    SPACE_WRITE = "space:write"
    SPACE_DELETE = "space:delete"

    # 任务管理
    TASK_READ = "task:read"
    TASK_WRITE = "task:write"
    TASK_DELETE = "task:delete"
    TASK_ASSIGN = "task:assign"

    # 机器人管理
    ROBOT_READ = "robot:read"
    ROBOT_CONTROL = "robot:control"
    ROBOT_CONFIG = "robot:config"

    # Agent管理
    AGENT_READ = "agent:read"
    AGENT_CONTROL = "agent:control"
    AGENT_CONFIG = "agent:config"

    # 用户管理
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"

    # 报表
    REPORT_READ = "report:read"
    REPORT_EXPORT = "report:export"

    # 系统管理
    SYSTEM_CONFIG = "system:config"
    AUDIT_READ = "audit:read"


# 角色-权限映射
ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: ["*"],  # 所有权限

    UserRole.TENANT_ADMIN: [
        Permission.SPACE_READ, Permission.SPACE_WRITE, Permission.SPACE_DELETE,
        Permission.TASK_READ, Permission.TASK_WRITE, Permission.TASK_DELETE, Permission.TASK_ASSIGN,
        Permission.ROBOT_READ, Permission.ROBOT_CONTROL, Permission.ROBOT_CONFIG,
        Permission.AGENT_READ, Permission.AGENT_CONTROL, Permission.AGENT_CONFIG,
        Permission.USER_READ, Permission.USER_WRITE, Permission.USER_DELETE,
        Permission.REPORT_READ, Permission.REPORT_EXPORT,
        Permission.AUDIT_READ,
    ],

    UserRole.MANAGER: [
        Permission.SPACE_READ, Permission.SPACE_WRITE,
        Permission.TASK_READ, Permission.TASK_WRITE, Permission.TASK_ASSIGN,
        Permission.ROBOT_READ, Permission.ROBOT_CONTROL,
        Permission.AGENT_READ, Permission.AGENT_CONTROL,
        Permission.USER_READ,
        Permission.REPORT_READ, Permission.REPORT_EXPORT,
    ],

    UserRole.TRAINER: [
        Permission.SPACE_READ,
        Permission.TASK_READ, Permission.TASK_WRITE,
        Permission.ROBOT_READ, Permission.ROBOT_CONTROL,
        Permission.AGENT_READ, Permission.AGENT_CONTROL, Permission.AGENT_CONFIG,
        Permission.REPORT_READ,
    ],

    UserRole.OPERATOR: [
        Permission.SPACE_READ,
        Permission.TASK_READ, Permission.TASK_WRITE,
        Permission.ROBOT_READ, Permission.ROBOT_CONTROL,
        Permission.AGENT_READ,
    ],

    UserRole.VIEWER: [
        Permission.SPACE_READ,
        Permission.TASK_READ,
        Permission.ROBOT_READ,
        Permission.AGENT_READ,
        Permission.REPORT_READ,
    ],
}
```

---

## 3. 接口定义

### 3.1 认证接口

```python
# POST /api/v1/auth/login
class LoginRequest(BaseModel):
    username: str
    password: str
    tenant_id: Optional[str] = None  # 多租户场景


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒
    user: UserInfo


# POST /api/v1/auth/refresh
class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    expires_in: int


# POST /api/v1/auth/logout
class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None  # 可选，用于使refresh token失效


# GET /api/v1/auth/me
class UserInfo(BaseModel):
    user_id: str
    tenant_id: str
    username: str
    email: str
    display_name: str
    role: str
    permissions: List[str]
```

### 3.2 用户管理接口

```python
# GET /api/v1/users
# POST /api/v1/users
# GET /api/v1/users/{user_id}
# PUT /api/v1/users/{user_id}
# DELETE /api/v1/users/{user_id}

class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    display_name: str
    role: UserRole = UserRole.VIEWER


class UpdateUserRequest(BaseModel):
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
```

---

## 4. 实现要求

### 4.1 核心功能

#### 4.1.1 密码处理

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)
```

#### 4.1.2 JWT Token处理

```python
from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Optional

# 配置
SECRET_KEY = "your-secret-key"  # 从环境变量读取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user: User) -> str:
    """创建访问令牌"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = TokenPayload(
        sub=str(user.user_id),
        tenant_id=str(user.tenant_id),
        role=user.role.value,
        permissions=get_user_permissions(user),
        exp=expire,
        iat=datetime.utcnow(),
        type="access"
    )
    return jwt.encode(payload.model_dump(), SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user: User) -> str:
    """创建刷新令牌"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = TokenPayload(
        sub=str(user.user_id),
        tenant_id=str(user.tenant_id),
        role=user.role.value,
        permissions=[],
        exp=expire,
        iat=datetime.utcnow(),
        type="refresh"
    )
    return jwt.encode(payload.model_dump(), SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenPayload]:
    """解码令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        return None
```

#### 4.1.3 FastAPI依赖注入

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenPayload:
    """获取当前用户"""
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
        )

    return payload


def require_permission(permission: str):
    """权限检查装饰器"""
    async def permission_checker(
        current_user: TokenPayload = Depends(get_current_user)
    ) -> TokenPayload:
        if "*" in current_user.permissions:
            return current_user
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required",
            )
        return current_user
    return permission_checker


def require_tenant(tenant_id: str):
    """租户检查"""
    async def tenant_checker(
        current_user: TokenPayload = Depends(get_current_user)
    ) -> TokenPayload:
        # super_admin可以访问所有租户
        if current_user.role == "super_admin":
            return current_user
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant",
            )
        return current_user
    return tenant_checker
```

### 4.2 使用示例

```python
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/robots")
async def list_robots(
    tenant_id: str,
    current_user: TokenPayload = Depends(require_permission(Permission.ROBOT_READ))
):
    """需要 robot:read 权限"""
    # 自动进行租户隔离
    if current_user.role != "super_admin" and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return await robot_service.list_robots(tenant_id)


@router.post("/robots/{robot_id}/start")
async def start_robot(
    robot_id: str,
    current_user: TokenPayload = Depends(require_permission(Permission.ROBOT_CONTROL))
):
    """需要 robot:control 权限"""
    return await robot_service.start(robot_id)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: TokenPayload = Depends(require_permission(Permission.USER_DELETE))
):
    """需要 user:delete 权限"""
    return await user_service.delete(user_id)
```

---

## 5. 安全要求

### 5.1 密码策略

```python
import re

def validate_password(password: str) -> tuple[bool, str]:
    """验证密码强度"""
    if len(password) < 8:
        return False, "密码长度至少8位"
    if not re.search(r"[A-Z]", password):
        return False, "密码必须包含大写字母"
    if not re.search(r"[a-z]", password):
        return False, "密码必须包含小写字母"
    if not re.search(r"\d", password):
        return False, "密码必须包含数字"
    return True, ""
```

### 5.2 登录安全

```python
# 登录失败锁定
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)

async def check_login_attempts(user: User) -> bool:
    """检查是否被锁定"""
    if user.status == UserStatus.LOCKED:
        return False
    if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
        # 自动锁定
        await user_repo.update(user.user_id, {"status": UserStatus.LOCKED})
        return False
    return True


async def record_failed_login(user: User):
    """记录失败登录"""
    await user_repo.update(user.user_id, {
        "failed_login_attempts": user.failed_login_attempts + 1
    })


async def reset_login_attempts(user: User):
    """重置登录尝试"""
    await user_repo.update(user.user_id, {
        "failed_login_attempts": 0,
        "last_login": datetime.utcnow()
    })
```

### 5.3 Token安全

```python
# Token黑名单（用于登出和强制失效）
# MVP阶段使用Redis存储

async def blacklist_token(token: str, expires_at: datetime):
    """将token加入黑名单"""
    ttl = int((expires_at - datetime.utcnow()).total_seconds())
    if ttl > 0:
        await redis.setex(f"token_blacklist:{token}", ttl, "1")


async def is_token_blacklisted(token: str) -> bool:
    """检查token是否在黑名单"""
    return await redis.exists(f"token_blacklist:{token}")
```

---

## 6. 文件结构

```
src/shared/
├── auth/
│   ├── __init__.py
│   ├── models.py          # 用户、权限等数据模型
│   ├── jwt.py             # JWT处理
│   ├── password.py        # 密码处理
│   ├── dependencies.py    # FastAPI依赖注入
│   ├── permissions.py     # 权限定义和检查
│   └── middleware.py      # 认证中间件

backend/app/api/v1/routers/
├── auth.py                # 认证API路由
└── users.py               # 用户管理API路由
```

---

## 7. MVP简化方案

对于MVP阶段，可以采用简化方案：

### 7.1 简化认证（可选）

```python
# 如果暂不需要完整用户系统，可以使用API Key认证

async def get_tenant_from_api_key(
    x_api_key: str = Header(...)
) -> str:
    """通过API Key获取租户ID"""
    api_key = await api_key_repo.get_by_key(x_api_key)
    if not api_key or not api_key.is_active:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key.tenant_id
```

### 7.2 MVP阶段实现优先级

| 功能 | 优先级 | 说明 |
|-----|--------|------|
| JWT Token生成/验证 | P0 | 核心认证 |
| 密码哈希 | P0 | 安全基础 |
| 基本权限检查 | P0 | 权限控制 |
| 多租户隔离 | P0 | 数据安全 |
| 用户CRUD | P1 | 用户管理 |
| Token刷新 | P1 | 用户体验 |
| 登录锁定 | P2 | 安全增强 |
| Token黑名单 | P2 | 安全增强 |
| 审计日志 | P2 | 合规要求 |

---

## 8. 测试要求

### 8.1 单元测试

```python
# tests/test_auth.py

import pytest
from src.shared.auth import hash_password, verify_password, create_access_token, decode_token


class TestPassword:
    def test_hash_and_verify(self):
        password = "MySecurePass123"
        hashed = hash_password(password)
        assert verify_password(password, hashed)
        assert not verify_password("wrong", hashed)


class TestJWT:
    def test_create_and_decode_token(self):
        user = create_test_user()
        token = create_access_token(user)
        payload = decode_token(token)
        assert payload is not None
        assert payload.sub == str(user.user_id)
        assert payload.tenant_id == str(user.tenant_id)

    def test_expired_token(self):
        # 创建过期token
        pass

    def test_invalid_token(self):
        payload = decode_token("invalid.token.here")
        assert payload is None


class TestPermissions:
    def test_role_permissions(self):
        # 测试角色权限映射
        pass

    def test_permission_check(self):
        # 测试权限检查
        pass
```

---

## 9. 验收标准

### 9.1 功能验收

- [ ] JWT Token生成和验证
- [ ] 密码哈希和验证
- [ ] 用户登录/登出
- [ ] Token刷新
- [ ] 权限检查装饰器
- [ ] 多租户数据隔离
- [ ] FastAPI依赖注入

### 9.2 安全验收

- [ ] 密码不明文存储
- [ ] Token有过期时间
- [ ] 敏感操作有权限控制
- [ ] 租户间数据隔离

---

**预计开发时间**: 4-6小时（MVP版本）

**开发优先级**: P1（API安全依赖此模块）

**前置依赖**: F3配置管理（读取SECRET_KEY等配置）
