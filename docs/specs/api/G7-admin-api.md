# 模块开发规格书：G7 系统管理API

## 文档信息
| 项目 | 内容 |
|-----|------|
| 模块ID | G7 |
| 模块名称 | 系统管理API |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | F1数据模型, F4认证授权 |

---

## 1. 模块概述

### 1.1 职责描述
系统管理API提供租户管理、用户管理、角色权限、系统配置、审计日志等系统级管理功能，是平台管理员和租户管理员的管理入口。

### 1.2 在系统中的位置
```
管理后台 / 运营控制台
         │
         ▼
┌─────────────────────────────────────┐
│         G7 系统管理API              │  ← 本模块
│   /api/v1/admin/*                   │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│       数据库 / 缓存 / 配置中心       │
└─────────────────────────────────────┘
```

### 1.3 输入/输出概述
| 方向 | 内容 |
|-----|------|
| 输入 | HTTP请求（管理操作） |
| 输出 | JSON响应（配置数据、管理结果） |
| 依赖 | 数据库、缓存、认证服务 |

---

## 2. API定义

### 2.1 租户管理

#### 获取租户列表
```yaml
GET /api/v1/admin/tenants
描述: 获取租户列表（平台管理员）
权限: platform:admin

查询参数:
  - status: string (optional) - active/inactive/suspended
  - search: string (optional) - 名称搜索
  - page: integer (default: 1)
  - page_size: integer (default: 20)

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "items": [
        {
          "tenant_id": "tenant_001",
          "name": "某物业管理公司",
          "code": "PROPERTY001",
          "status": "active",
          "plan": "enterprise",
          "buildings_count": 5,
          "robots_count": 25,
          "users_count": 15,
          "created_at": "2025-06-01T00:00:00Z",
          "expires_at": "2026-06-01T00:00:00Z"
        }
      ],
      "total": 10,
      "page": 1,
      "page_size": 20
    }
  }
```

#### 创建租户
```yaml
POST /api/v1/admin/tenants
描述: 创建新租户
权限: platform:admin

请求体:
  {
    "name": "新物业公司",
    "code": "NEWPROP001",
    "plan": "professional",
    "contact": {
      "name": "张经理",
      "email": "zhang@newprop.com",
      "phone": "+852-12345678"
    },
    "settings": {
      "max_buildings": 10,
      "max_robots": 50,
      "max_users": 30
    },
    "expires_at": "2027-01-01T00:00:00Z"
  }

响应 201:
  {
    "code": 0,
    "message": "Tenant created successfully",
    "data": {
      "tenant_id": "tenant_002",
      "name": "新物业公司",
      "status": "active",
      "admin_account": {
        "username": "admin@newprop001",
        "temp_password": "TempPass123!"
      }
    }
  }
```

#### 更新租户
```yaml
PUT /api/v1/admin/tenants/{tenant_id}
描述: 更新租户信息
权限: platform:admin | tenant:admin

请求体:
  {
    "name": "更新后的公司名",
    "contact": {
      "name": "李经理",
      "email": "li@newprop.com"
    },
    "settings": {
      "max_robots": 100
    }
  }

响应 200:
  {
    "code": 0,
    "message": "Tenant updated successfully",
    "data": {
      "tenant_id": "tenant_002",
      "name": "更新后的公司名"
    }
  }
```

### 2.2 用户管理

#### 获取用户列表
```yaml
GET /api/v1/admin/users
描述: 获取用户列表
权限: users:read

查询参数:
  - tenant_id: string (required for tenant admin)
  - role: string (optional)
  - status: string (optional) - active/inactive/locked
  - search: string (optional)
  - page: integer (default: 1)
  - page_size: integer (default: 20)

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "items": [
        {
          "user_id": "user_001",
          "username": "zhangsan",
          "email": "zhangsan@company.com",
          "name": "张三",
          "role": "trainer",
          "role_name": "训练师",
          "status": "active",
          "last_login_at": "2026-01-20T08:30:00Z",
          "created_at": "2025-06-15T00:00:00Z"
        }
      ],
      "total": 15,
      "page": 1,
      "page_size": 20
    }
  }
```

#### 创建用户
```yaml
POST /api/v1/admin/users
描述: 创建新用户
权限: users:write

请求体:
  {
    "tenant_id": "tenant_001",
    "username": "lisi",
    "email": "lisi@company.com",
    "name": "李四",
    "role": "operator",
    "phone": "+852-87654321",
    "buildings": ["building_001", "building_002"]
  }

响应 201:
  {
    "code": 0,
    "message": "User created successfully",
    "data": {
      "user_id": "user_002",
      "username": "lisi",
      "temp_password": "TempPass456!"
    }
  }
```

#### 更新用户
```yaml
PUT /api/v1/admin/users/{user_id}
描述: 更新用户信息
权限: users:write

请求体:
  {
    "name": "李四（更新）",
    "role": "trainer",
    "buildings": ["building_001", "building_002", "building_003"]
  }

响应 200:
  {
    "code": 0,
    "message": "User updated successfully"
  }
```

#### 重置密码
```yaml
POST /api/v1/admin/users/{user_id}/reset-password
描述: 重置用户密码
权限: users:write

请求体:
  {
    "send_email": true
  }

响应 200:
  {
    "code": 0,
    "message": "Password reset successfully",
    "data": {
      "temp_password": "NewTempPass789!",
      "email_sent": true
    }
  }
```

#### 禁用/启用用户
```yaml
POST /api/v1/admin/users/{user_id}/status
描述: 更改用户状态
权限: users:write

请求体:
  {
    "status": "inactive",  # active/inactive/locked
    "reason": "离职"
  }

响应 200:
  {
    "code": 0,
    "message": "User status updated"
  }
```

### 2.3 角色权限管理

#### 获取角色列表
```yaml
GET /api/v1/admin/roles
描述: 获取角色列表
权限: roles:read

查询参数:
  - tenant_id: string (optional)

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "roles": [
        {
          "role_id": "role_trainer",
          "name": "训练师",
          "description": "负责AI Agent训练和反馈",
          "is_system": true,
          "permissions": [
            "agents:read", "agents:chat", "agents:feedback",
            "robots:read", "tasks:read", "data:read"
          ],
          "users_count": 5
        },
        {
          "role_id": "role_operator",
          "name": "运营经理",
          "description": "负责日常运营管理",
          "is_system": true,
          "permissions": [
            "agents:read", "agents:write",
            "robots:read", "robots:control",
            "tasks:read", "tasks:write",
            "data:read", "data:export"
          ],
          "users_count": 3
        }
      ]
    }
  }
```

#### 创建自定义角色
```yaml
POST /api/v1/admin/roles
描述: 创建自定义角色
权限: roles:write

请求体:
  {
    "tenant_id": "tenant_001",
    "name": "区域主管",
    "description": "负责特定区域的运营",
    "permissions": [
      "robots:read",
      "tasks:read", "tasks:write",
      "data:read"
    ]
  }

响应 201:
  {
    "code": 0,
    "message": "Role created successfully",
    "data": {
      "role_id": "role_custom_001",
      "name": "区域主管"
    }
  }
```

#### 获取权限列表
```yaml
GET /api/v1/admin/permissions
描述: 获取所有可用权限
权限: roles:read

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "permissions": [
        {
          "category": "agents",
          "items": [
            {"code": "agents:read", "name": "查看Agent", "description": "查看Agent状态和活动"},
            {"code": "agents:chat", "name": "与Agent对话", "description": "使用对话功能"},
            {"code": "agents:feedback", "name": "提交反馈", "description": "对Agent决策提交反馈"},
            {"code": "agents:write", "name": "管理Agent", "description": "控制Agent运行状态"},
            {"code": "agents:admin", "name": "Agent管理员", "description": "Agent高级管理"}
          ]
        },
        {
          "category": "robots",
          "items": [
            {"code": "robots:read", "name": "查看机器人", "description": "查看机器人状态"},
            {"code": "robots:control", "name": "控制机器人", "description": "发送控制指令"},
            {"code": "robots:write", "name": "管理机器人", "description": "添加删除机器人"}
          ]
        }
      ]
    }
  }
```

### 2.4 系统配置

#### 获取系统配置
```yaml
GET /api/v1/admin/settings
描述: 获取系统配置
权限: settings:read

查询参数:
  - tenant_id: string (required)
  - category: string (optional) - general/notification/scheduling/integration

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "general": {
        "timezone": "Asia/Hong_Kong",
        "language": "zh-HK",
        "date_format": "YYYY-MM-DD",
        "working_hours": {"start": "08:00", "end": "22:00"}
      },
      "notification": {
        "email_enabled": true,
        "sms_enabled": false,
        "push_enabled": true,
        "escalation_channels": {
          "critical": ["email", "push", "sms"],
          "warning": ["email", "push"],
          "info": ["push"]
        }
      },
      "scheduling": {
        "default_scheduling_interval": 60,
        "min_battery_for_task": 30,
        "task_timeout_minutes": 120,
        "auto_charge_threshold": 20
      },
      "integration": {
        "gaoxian_enabled": true,
        "ecovacs_enabled": true,
        "webhook_url": "https://webhook.company.com/linkc"
      }
    }
  }
```

#### 更新系统配置
```yaml
PUT /api/v1/admin/settings
描述: 更新系统配置
权限: settings:write

请求体:
  {
    "tenant_id": "tenant_001",
    "category": "scheduling",
    "settings": {
      "default_scheduling_interval": 90,
      "min_battery_for_task": 25
    }
  }

响应 200:
  {
    "code": 0,
    "message": "Settings updated successfully"
  }
```

### 2.5 审计日志

#### 获取审计日志
```yaml
GET /api/v1/admin/audit-logs
描述: 获取审计日志
权限: audit:read

查询参数:
  - tenant_id: string (required)
  - user_id: string (optional)
  - action: string (optional) - login/logout/create/update/delete/control
  - resource_type: string (optional) - user/robot/task/setting
  - start_time: datetime (required)
  - end_time: datetime (required)
  - page: integer (default: 1)
  - page_size: integer (default: 50)

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "items": [
        {
          "log_id": "audit_001",
          "timestamp": "2026-01-20T10:30:00Z",
          "user_id": "user_001",
          "user_name": "张三",
          "action": "control",
          "resource_type": "robot",
          "resource_id": "robot_001",
          "description": "发送暂停指令",
          "details": {
            "command": "pause",
            "reason": "紧急维护"
          },
          "ip_address": "192.168.1.100",
          "user_agent": "Mozilla/5.0..."
        }
      ],
      "total": 256,
      "page": 1,
      "page_size": 50
    }
  }
```

### 2.6 系统健康

#### 获取系统状态
```yaml
GET /api/v1/admin/health
描述: 获取系统健康状态
权限: system:read

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "status": "healthy",
      "timestamp": "2026-01-20T10:30:00Z",
      "components": {
        "api": {"status": "healthy", "latency_ms": 5},
        "database": {"status": "healthy", "latency_ms": 12},
        "redis": {"status": "healthy", "latency_ms": 2},
        "mcp_gaoxian": {"status": "healthy", "latency_ms": 45},
        "mcp_ecovacs": {"status": "healthy", "latency_ms": 52},
        "agent_scheduler": {"status": "healthy", "last_heartbeat": "2026-01-20T10:29:55Z"},
        "agent_conversation": {"status": "healthy", "last_heartbeat": "2026-01-20T10:29:58Z"}
      },
      "metrics": {
        "api_requests_per_minute": 125,
        "active_websockets": 45,
        "active_robots": 23,
        "pending_tasks": 5
      }
    }
  }
```

#### 获取系统指标
```yaml
GET /api/v1/admin/metrics
描述: 获取系统运行指标
权限: system:read

查询参数:
  - period: string (default: 1h) - 1h/6h/24h/7d

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "period": "1h",
      "api": {
        "total_requests": 7500,
        "error_rate": 0.12,
        "avg_latency_ms": 45,
        "p99_latency_ms": 250
      },
      "database": {
        "connections_active": 15,
        "connections_idle": 5,
        "queries_per_second": 85
      },
      "agents": {
        "decisions_count": 156,
        "escalations_count": 3,
        "avg_decision_time_ms": 120
      }
    }
  }
```

---

## 3. 数据模型

### 3.1 请求/响应模型
```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class TenantStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"

class AuditAction(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    CONTROL = "control"

# 租户
class TenantContact(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None

class TenantSettings(BaseModel):
    max_buildings: int = 10
    max_robots: int = 50
    max_users: int = 30

class TenantCreateRequest(BaseModel):
    name: str = Field(max_length=100)
    code: str = Field(max_length=20, pattern="^[A-Z0-9]+$")
    plan: str
    contact: TenantContact
    settings: Optional[TenantSettings] = None
    expires_at: Optional[datetime] = None

class TenantResponse(BaseModel):
    tenant_id: str
    name: str
    code: str
    status: TenantStatus
    plan: str
    buildings_count: int
    robots_count: int
    users_count: int
    created_at: datetime
    expires_at: Optional[datetime]

# 用户
class UserCreateRequest(BaseModel):
    tenant_id: str
    username: str = Field(max_length=50, pattern="^[a-z0-9_]+$")
    email: EmailStr
    name: str = Field(max_length=100)
    role: str
    phone: Optional[str] = None
    buildings: Optional[List[str]] = None

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    buildings: Optional[List[str]] = None

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    name: str
    role: str
    role_name: str
    status: UserStatus
    last_login_at: Optional[datetime]
    created_at: datetime

class UserStatusRequest(BaseModel):
    status: UserStatus
    reason: Optional[str] = None

# 角色权限
class RoleCreateRequest(BaseModel):
    tenant_id: str
    name: str = Field(max_length=50)
    description: Optional[str] = None
    permissions: List[str]

class RoleResponse(BaseModel):
    role_id: str
    name: str
    description: Optional[str]
    is_system: bool
    permissions: List[str]
    users_count: int

# 系统配置
class SettingsUpdateRequest(BaseModel):
    tenant_id: str
    category: str
    settings: Dict

# 审计日志
class AuditLogResponse(BaseModel):
    log_id: str
    timestamp: datetime
    user_id: str
    user_name: str
    action: AuditAction
    resource_type: str
    resource_id: Optional[str]
    description: str
    details: Optional[Dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
```

---

## 4. 实现要求

### 4.1 技术栈
- Python 3.11+
- FastAPI
- Pydantic v2
- SQLAlchemy (ORM)
- Redis (缓存)

### 4.2 核心实现

#### 路由器结构
```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# 租户管理
@router.get("/tenants", response_model=ApiResponse[PaginatedResponse[TenantResponse]])
async def list_tenants(
    status: Optional[TenantStatus] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(require_platform_admin)
):
    """获取租户列表"""
    pass

@router.post("/tenants", response_model=ApiResponse[dict], status_code=201)
async def create_tenant(
    request: TenantCreateRequest,
    current_user: User = Depends(require_platform_admin),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """创建租户"""
    pass

# 用户管理
@router.get("/users", response_model=ApiResponse[PaginatedResponse[UserResponse]])
async def list_users(
    tenant_id: str,
    role: Optional[str] = None,
    status: Optional[UserStatus] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """获取用户列表"""
    pass

@router.post("/users", response_model=ApiResponse[dict], status_code=201)
async def create_user(
    request: UserCreateRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """创建用户"""
    pass

# 审计日志
@router.get("/audit-logs", response_model=ApiResponse[PaginatedResponse[AuditLogResponse]])
async def get_audit_logs(
    tenant_id: str,
    start_time: datetime,
    end_time: datetime,
    user_id: Optional[str] = None,
    action: Optional[AuditAction] = None,
    resource_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """获取审计日志"""
    pass
```

#### 服务层
```python
class TenantService:
    def __init__(self, db: AsyncSession, cache: Redis):
        self.db = db
        self.cache = cache
    
    async def create_tenant(self, request: TenantCreateRequest) -> dict:
        """创建租户"""
        # 检查code唯一性
        existing = await self.db.execute(
            select(Tenant).where(Tenant.code == request.code)
        )
        if existing.scalar():
            raise HTTPException(400, "Tenant code already exists")
        
        # 创建租户
        tenant = Tenant(
            id=f"tenant_{uuid.uuid4().hex[:8]}",
            name=request.name,
            code=request.code,
            plan=request.plan,
            contact=request.contact.dict(),
            settings=request.settings.dict() if request.settings else {},
            status=TenantStatus.ACTIVE,
            expires_at=request.expires_at
        )
        self.db.add(tenant)
        
        # 创建管理员账号
        admin_user, temp_password = await self._create_admin_user(tenant)
        
        await self.db.commit()
        
        return {
            "tenant_id": tenant.id,
            "name": tenant.name,
            "status": tenant.status,
            "admin_account": {
                "username": admin_user.username,
                "temp_password": temp_password
            }
        }
    
    async def _create_admin_user(self, tenant: Tenant) -> tuple[User, str]:
        """创建租户管理员"""
        temp_password = generate_temp_password()
        admin_user = User(
            id=f"user_{uuid.uuid4().hex[:8]}",
            tenant_id=tenant.id,
            username=f"admin@{tenant.code.lower()}",
            email=tenant.contact["email"],
            name=f"{tenant.name}管理员",
            role="tenant_admin",
            password_hash=hash_password(temp_password),
            status=UserStatus.ACTIVE
        )
        self.db.add(admin_user)
        return admin_user, temp_password


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log(
        self,
        user: User,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str],
        description: str,
        details: Optional[dict] = None,
        request: Optional[Request] = None
    ):
        """记录审计日志"""
        log = AuditLog(
            id=f"audit_{uuid.uuid4().hex[:8]}",
            tenant_id=user.tenant_id,
            user_id=user.id,
            user_name=user.name,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            details=details,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            timestamp=datetime.utcnow()
        )
        self.db.add(log)
        await self.db.commit()
```

### 4.3 权限装饰器
```python
from functools import wraps

def require_permission(permission: str):
    """权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User, **kwargs):
            if not has_permission(current_user, permission):
                raise HTTPException(403, "Permission denied")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def require_platform_admin(current_user: User = Depends(get_current_user)) -> User:
    """平台管理员权限检查"""
    if current_user.role != "platform_admin":
        raise HTTPException(403, "Platform admin required")
    return current_user

def require_tenant_admin(current_user: User = Depends(get_current_user)) -> User:
    """租户管理员权限检查"""
    if current_user.role not in ["platform_admin", "tenant_admin"]:
        raise HTTPException(403, "Tenant admin required")
    return current_user
```

---

## 5. 测试要求

### 5.1 单元测试用例
```python
import pytest

@pytest.mark.asyncio
async def test_create_tenant(client, platform_admin_headers):
    """测试创建租户"""
    response = await client.post(
        "/api/v1/admin/tenants",
        json={
            "name": "测试公司",
            "code": "TEST001",
            "plan": "professional",
            "contact": {
                "name": "测试经理",
                "email": "test@test.com"
            }
        },
        headers=platform_admin_headers
    )
    assert response.status_code == 201
    assert "admin_account" in response.json()["data"]

@pytest.mark.asyncio
async def test_create_user(client, tenant_admin_headers):
    """测试创建用户"""
    response = await client.post(
        "/api/v1/admin/users",
        json={
            "tenant_id": "tenant_001",
            "username": "newuser",
            "email": "newuser@test.com",
            "name": "新用户",
            "role": "trainer"
        },
        headers=tenant_admin_headers
    )
    assert response.status_code == 201
    assert "temp_password" in response.json()["data"]

@pytest.mark.asyncio
async def test_permission_denied(client, trainer_headers):
    """测试权限拒绝"""
    response = await client.post(
        "/api/v1/admin/tenants",
        json={"name": "测试", "code": "TEST"},
        headers=trainer_headers
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_audit_log(client, tenant_admin_headers):
    """测试审计日志"""
    response = await client.get(
        "/api/v1/admin/audit-logs",
        params={
            "tenant_id": "tenant_001",
            "start_time": "2026-01-01T00:00:00Z",
            "end_time": "2026-01-31T23:59:59Z"
        },
        headers=tenant_admin_headers
    )
    assert response.status_code == 200
    assert "items" in response.json()["data"]
```

---

## 6. 验收标准

### 6.1 功能验收
- [ ] 租户CRUD正常
- [ ] 用户CRUD正常
- [ ] 角色权限管理正常
- [ ] 系统配置读写正常
- [ ] 审计日志记录完整
- [ ] 系统健康检查正常
- [ ] 权限控制生效

### 6.2 性能要求
- 用户列表查询 < 100ms
- 审计日志查询 < 200ms
- 配置读取 < 50ms

### 6.3 代码质量
- 测试覆盖率 > 80%
- 所有操作记录审计日志
- 敏感操作二次确认
