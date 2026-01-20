# G1 认证授权API规格书

## 文档信息

| 属性 | 值 |
|-----|-----|
| 模块ID | G1 |
| 模块名称 | 认证授权API (Auth API) |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 规格书 |
| 前置依赖 | F4-认证授权模块, D2-数据存储 |

---

## 1. 模块概述

### 1.1 职责描述

认证授权API负责：
1. **用户认证**：登录、登出、Token刷新
2. **用户管理**：创建、更新、删除用户
3. **角色管理**：角色定义和权限分配
4. **权限控制**：基于RBAC的API访问控制
5. **租户管理**：多租户隔离

### 1.2 API端点总览

| 端点 | 方法 | 描述 |
|-----|------|------|
| `/auth/login` | POST | 用户登录 |
| `/auth/logout` | POST | 用户登出 |
| `/auth/refresh` | POST | 刷新Token |
| `/auth/me` | GET | 获取当前用户信息 |
| `/users` | GET/POST | 用户列表/创建 |
| `/users/{id}` | GET/PUT/DELETE | 用户详情/更新/删除 |
| `/roles` | GET/POST | 角色列表/创建 |
| `/roles/{id}` | GET/PUT/DELETE | 角色详情/更新/删除 |
| `/permissions` | GET | 权限列表 |

---

## 2. 接口定义

### 2.1 认证接口

#### POST /auth/login

登录获取访问令牌。

**请求体：**
```json
{
  "username": "admin@linkc.com",
  "password": "password123",
  "tenant_id": "tenant-001"  // 可选，多租户场景
}
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user-001",
    "username": "admin@linkc.com",
    "name": "系统管理员",
    "role": "admin",
    "tenant_id": "tenant-001",
    "permissions": ["users:read", "users:write", "robots:read", ...]
  }
}
```

**错误码：**
| 状态码 | 错误码 | 描述 |
|-------|-------|------|
| 401 | INVALID_CREDENTIALS | 用户名或密码错误 |
| 403 | ACCOUNT_DISABLED | 账户已禁用 |
| 403 | TENANT_DISABLED | 租户已禁用 |
| 429 | TOO_MANY_ATTEMPTS | 登录尝试过多，请稍后再试 |

#### POST /auth/logout

登出并使Token失效。

**请求头：**
```
Authorization: Bearer {access_token}
```

**响应：**
```json
{
  "message": "登出成功"
}
```

#### POST /auth/refresh

刷新访问令牌。

**请求体：**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

#### GET /auth/me

获取当前登录用户信息。

**响应：**
```json
{
  "id": "user-001",
  "username": "admin@linkc.com",
  "name": "系统管理员",
  "email": "admin@linkc.com",
  "phone": "+852-12345678",
  "role": {
    "id": "role-admin",
    "name": "管理员",
    "permissions": ["users:*", "robots:*", "tasks:*"]
  },
  "tenant": {
    "id": "tenant-001",
    "name": "香港物业管理公司"
  },
  "created_at": "2026-01-01T00:00:00Z",
  "last_login_at": "2026-01-20T10:30:00Z"
}
```

### 2.2 用户管理接口

#### GET /users

获取用户列表。

**查询参数：**
| 参数 | 类型 | 必填 | 描述 |
|-----|------|-----|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| role_id | string | 否 | 按角色筛选 |
| status | string | 否 | 按状态筛选：active/disabled |
| search | string | 否 | 搜索用户名或姓名 |

**响应：**
```json
{
  "items": [
    {
      "id": "user-001",
      "username": "admin@linkc.com",
      "name": "系统管理员",
      "role_id": "role-admin",
      "role_name": "管理员",
      "status": "active",
      "last_login_at": "2026-01-20T10:30:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

**所需权限：** `users:read`

#### POST /users

创建用户。

**请求体：**
```json
{
  "username": "operator@linkc.com",
  "password": "SecurePass123!",
  "name": "操作员张三",
  "email": "operator@linkc.com",
  "phone": "+852-87654321",
  "role_id": "role-operator"
}
```

**响应：**
```json
{
  "id": "user-002",
  "username": "operator@linkc.com",
  "name": "操作员张三",
  "role_id": "role-operator",
  "status": "active",
  "created_at": "2026-01-20T11:00:00Z"
}
```

**所需权限：** `users:write`

#### GET /users/{id}

获取用户详情。

**响应：**
```json
{
  "id": "user-002",
  "username": "operator@linkc.com",
  "name": "操作员张三",
  "email": "operator@linkc.com",
  "phone": "+852-87654321",
  "role": {
    "id": "role-operator",
    "name": "操作员",
    "permissions": ["robots:read", "tasks:read", "tasks:write"]
  },
  "status": "active",
  "created_at": "2026-01-20T11:00:00Z",
  "updated_at": "2026-01-20T11:00:00Z",
  "last_login_at": null
}
```

#### PUT /users/{id}

更新用户信息。

**请求体：**
```json
{
  "name": "操作员张三（更新）",
  "phone": "+852-11111111",
  "role_id": "role-senior-operator"
}
```

**所需权限：** `users:write`

#### DELETE /users/{id}

删除用户（软删除）。

**所需权限：** `users:delete`

### 2.3 角色管理接口

#### GET /roles

获取角色列表。

**响应：**
```json
{
  "items": [
    {
      "id": "role-admin",
      "name": "管理员",
      "description": "系统管理员，拥有所有权限",
      "user_count": 2,
      "is_system": true
    },
    {
      "id": "role-trainer",
      "name": "训练师",
      "description": "Agent训练和监督",
      "user_count": 5,
      "is_system": true
    },
    {
      "id": "role-operator",
      "name": "运营人员",
      "description": "日常运营管理",
      "user_count": 10,
      "is_system": true
    }
  ]
}
```

#### POST /roles

创建自定义角色。

**请求体：**
```json
{
  "name": "高级操作员",
  "description": "拥有额外权限的操作员",
  "permissions": [
    "robots:read",
    "robots:control",
    "tasks:read",
    "tasks:write",
    "reports:read"
  ]
}
```

**所需权限：** `roles:write`

#### GET /permissions

获取所有可用权限列表。

**响应：**
```json
{
  "permissions": [
    {
      "code": "users:read",
      "name": "查看用户",
      "category": "用户管理"
    },
    {
      "code": "users:write",
      "name": "编辑用户",
      "category": "用户管理"
    },
    {
      "code": "robots:read",
      "name": "查看机器人",
      "category": "机器人管理"
    },
    {
      "code": "robots:control",
      "name": "控制机器人",
      "category": "机器人管理"
    }
    // ...
  ]
}
```

---

## 3. 数据模型

### 3.1 用户模型

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    PENDING = "pending"

class User(BaseModel):
    """用户"""
    id: str
    tenant_id: str
    username: str
    name: str
    email: Optional[EmailStr]
    phone: Optional[str]
    role_id: str
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]

class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=100)
    name: str = Field(min_length=1, max_length=100)
    email: Optional[EmailStr]
    phone: Optional[str]
    role_id: str

class UserUpdate(BaseModel):
    """更新用户请求"""
    name: Optional[str] = Field(min_length=1, max_length=100)
    email: Optional[EmailStr]
    phone: Optional[str]
    role_id: Optional[str]
    status: Optional[UserStatus]
```

### 3.2 角色和权限模型

```python
class Role(BaseModel):
    """角色"""
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    permissions: List[str]
    is_system: bool = False  # 系统内置角色不可删除
    created_at: datetime
    updated_at: datetime

class Permission(BaseModel):
    """权限"""
    code: str  # e.g., "users:read", "robots:control"
    name: str
    description: Optional[str]
    category: str
```

### 3.3 Token模型

```python
class TokenPayload(BaseModel):
    """JWT Token载荷"""
    sub: str  # user_id
    tenant_id: str
    role: str
    permissions: List[str]
    exp: datetime
    iat: datetime
    jti: str  # token唯一标识

class TokenPair(BaseModel):
    """Token对"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
```

---

## 4. 实现要求

### 4.1 技术栈

- FastAPI
- python-jose（JWT）
- passlib（密码哈希）
- Redis（Token黑名单）

### 4.2 核心实现

#### 4.2.1 认证依赖

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> User:
    """获取当前用户"""
    token = credentials.credentials
    
    # 检查Token是否在黑名单
    if await redis.exists(f"token:blacklist:{token}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已失效"
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的Token")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的Token")
    
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    return user

def require_permission(permission: str):
    """权限检查装饰器"""
    async def permission_checker(user: User = Depends(get_current_user)):
        if permission not in user.role.permissions and "*" not in user.role.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {permission}"
            )
        return user
    return permission_checker
```

#### 4.2.2 路由定义

```python
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    user = await authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if user.status == UserStatus.DISABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已禁用"
        )
    
    # 生成Token
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    
    # 更新最后登录时间
    await update_last_login(db, user.id)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_SECONDS,
        user=UserResponse.from_orm(user)
    )

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    redis: Redis = Depends(get_redis)
):
    """用户登出"""
    token = credentials.credentials
    
    # 将Token加入黑名单
    await redis.setex(
        f"token:blacklist:{token}",
        ACCESS_TOKEN_EXPIRE_SECONDS,
        "1"
    )
    
    return {"message": "登出成功"}
```

### 4.3 系统内置角色

| 角色ID | 名称 | 权限 |
|-------|------|------|
| role-admin | 系统管理员 | `*`（所有权限） |
| role-trainer | 训练师 | `robots:*`, `tasks:*`, `agents:*`, `feedback:*` |
| role-operator | 运营人员 | `robots:read`, `tasks:*`, `reports:*`, `alerts:*` |
| role-executive | 管理层 | `reports:*`, `analytics:*`, `decisions:*` |
| role-viewer | 只读用户 | `*:read` |

### 4.4 权限清单

| 权限代码 | 描述 |
|---------|------|
| `users:read` | 查看用户 |
| `users:write` | 创建/编辑用户 |
| `users:delete` | 删除用户 |
| `roles:read` | 查看角色 |
| `roles:write` | 创建/编辑角色 |
| `robots:read` | 查看机器人 |
| `robots:control` | 控制机器人 |
| `tasks:read` | 查看任务 |
| `tasks:write` | 创建/编辑任务 |
| `tasks:delete` | 删除任务 |
| `agents:read` | 查看Agent |
| `agents:control` | 控制Agent |
| `reports:read` | 查看报表 |
| `alerts:read` | 查看告警 |
| `alerts:handle` | 处理告警 |

---

## 5. 测试要求

### 5.1 单元测试用例

```python
@pytest.mark.asyncio
async def test_login_success():
    """测试登录成功"""
    response = await client.post("/auth/login", json={
        "username": "admin@linkc.com",
        "password": "admin123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_login_wrong_password():
    """测试密码错误"""
    response = await client.post("/auth/login", json={
        "username": "admin@linkc.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_permission_required():
    """测试权限检查"""
    # 使用普通用户Token
    headers = {"Authorization": f"Bearer {viewer_token}"}
    response = await client.post("/users", json={...}, headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_token_refresh():
    """测试Token刷新"""
    response = await client.post("/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

---

## 6. 验收标准

### 6.1 功能验收

- [ ] 用户登录返回有效Token
- [ ] 无效密码返回401
- [ ] 禁用账户无法登录
- [ ] Token刷新正常工作
- [ ] 登出后Token失效
- [ ] RBAC权限检查正确

### 6.2 安全要求

- [ ] 密码使用bcrypt加密存储
- [ ] JWT包含必要的过期时间
- [ ] 登录失败次数限制（5次/5分钟）
- [ ] 敏感操作需要重新认证

---

*文档版本：1.0*
*更新日期：2026年1月*
