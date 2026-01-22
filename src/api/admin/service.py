"""
G7: 系统管理API - 服务层
============================
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import logging
import uuid
import secrets
import string

from .models import (
    TenantStatus, UserStatus, UserRole, AuditAction,
    TenantCreate, TenantUpdate, TenantContact, TenantSettings,
    UserCreate, UserUpdate, SystemConfigUpdate,
    TenantListItem, TenantDetail, TenantListResponse, TenantCreateResponse,
    UserListItem, UserDetail, UserListResponse,
    AuditLogItem, AuditLogResponse,
    SystemConfig, SystemConfigListResponse, SystemHealthResponse
)

logger = logging.getLogger(__name__)


class AdminService:
    """系统管理服务"""

    def __init__(self):
        # 内存存储（测试用）
        self._tenants: Dict[str, Dict[str, Any]] = {}
        self._users: Dict[str, Dict[str, Any]] = {}
        self._audit_logs: List[Dict[str, Any]] = []
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._init_sample_data()

    def _init_sample_data(self):
        """初始化示例数据"""
        now = datetime.now(timezone.utc)

        # 示例租户
        self._tenants = {
            "tenant_001": {
                "tenant_id": "tenant_001",
                "name": "某物业管理公司",
                "code": "PROPERTY001",
                "status": TenantStatus.ACTIVE.value,
                "plan": "enterprise",
                "buildings_count": 5,
                "robots_count": 25,
                "users_count": 15,
                "contact": {"name": "张经理", "email": "zhang@prop.com", "phone": "+852-12345678"},
                "settings": {"max_buildings": 10, "max_robots": 50, "max_users": 30},
                "created_at": now - timedelta(days=180),
                "expires_at": now + timedelta(days=180),
                "updated_at": now
            }
        }

        # 示例用户
        role_names = {
            UserRole.PLATFORM_ADMIN: "平台管理员",
            UserRole.TENANT_ADMIN: "租户管理员",
            UserRole.MANAGER: "管理员",
            UserRole.TRAINER: "训练师",
            UserRole.OPERATOR: "操作员"
        }

        self._users = {
            "user_001": {
                "user_id": "user_001",
                "tenant_id": "tenant_001",
                "username": "zhangsan",
                "email": "zhangsan@company.com",
                "name": "张三",
                "role": UserRole.TRAINER.value,
                "role_name": "训练师",
                "status": UserStatus.ACTIVE.value,
                "permissions": ["tasks:read", "tasks:write", "robots:read"],
                "last_login_at": now - timedelta(hours=2),
                "created_at": now - timedelta(days=90),
                "updated_at": now
            },
            "user_002": {
                "user_id": "user_002",
                "tenant_id": "tenant_001",
                "username": "lisi",
                "email": "lisi@company.com",
                "name": "李四",
                "role": UserRole.MANAGER.value,
                "role_name": "管理员",
                "status": UserStatus.ACTIVE.value,
                "permissions": ["tasks:*", "robots:*", "users:read"],
                "last_login_at": now - timedelta(days=1),
                "created_at": now - timedelta(days=60),
                "updated_at": now
            }
        }

        # 示例审计日志
        self._audit_logs = [
            {
                "log_id": "log_001",
                "user_id": "user_001",
                "username": "zhangsan",
                "action": AuditAction.LOGIN.value,
                "resource_type": "session",
                "resource_id": None,
                "details": {"ip": "192.168.1.100"},
                "ip_address": "192.168.1.100",
                "timestamp": now - timedelta(hours=2)
            },
            {
                "log_id": "log_002",
                "user_id": "user_002",
                "username": "lisi",
                "action": AuditAction.UPDATE.value,
                "resource_type": "task",
                "resource_id": "task_001",
                "details": {"changes": {"status": "completed"}},
                "ip_address": "192.168.1.101",
                "timestamp": now - timedelta(hours=1)
            }
        ]

        # 示例配置
        self._configs = {
            "system.name": {
                "key": "system.name",
                "value": "LinkC清洁机器人管理平台",
                "description": "系统名称",
                "updated_at": now,
                "updated_by": "admin"
            },
            "cleaning.default_efficiency": {
                "key": "cleaning.default_efficiency",
                "value": 150.0,
                "description": "默认清洁效率(平方米/小时)",
                "updated_at": now,
                "updated_by": "admin"
            },
            "alert.battery_threshold": {
                "key": "alert.battery_threshold",
                "value": 20,
                "description": "低电量告警阈值(%)",
                "updated_at": now,
                "updated_by": "admin"
            }
        }

    # ========== 租户管理 ==========

    async def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> TenantListResponse:
        """获取租户列表"""
        tenants = list(self._tenants.values())

        if status:
            tenants = [t for t in tenants if t["status"] == status.value]
        if search:
            tenants = [t for t in tenants if search.lower() in t["name"].lower()]

        total = len(tenants)
        start = (page - 1) * page_size
        end = start + page_size
        page_tenants = tenants[start:end]

        items = [
            TenantListItem(
                tenant_id=t["tenant_id"],
                name=t["name"],
                code=t["code"],
                status=TenantStatus(t["status"]),
                plan=t["plan"],
                buildings_count=t.get("buildings_count", 0),
                robots_count=t.get("robots_count", 0),
                users_count=t.get("users_count", 0),
                created_at=t["created_at"],
                expires_at=t.get("expires_at")
            )
            for t in page_tenants
        ]

        return TenantListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )

    async def get_tenant(self, tenant_id: str) -> Optional[TenantDetail]:
        """获取租户详情"""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return None

        return TenantDetail(
            tenant_id=tenant["tenant_id"],
            name=tenant["name"],
            code=tenant["code"],
            status=TenantStatus(tenant["status"]),
            plan=tenant["plan"],
            buildings_count=tenant.get("buildings_count", 0),
            robots_count=tenant.get("robots_count", 0),
            users_count=tenant.get("users_count", 0),
            contact=TenantContact(**tenant["contact"]) if tenant.get("contact") else None,
            settings=TenantSettings(**tenant["settings"]) if tenant.get("settings") else None,
            created_at=tenant["created_at"],
            expires_at=tenant.get("expires_at"),
            updated_at=tenant.get("updated_at")
        )

    async def create_tenant(self, data: TenantCreate) -> TenantCreateResponse:
        """创建租户"""
        tenant_id = f"tenant_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        # 生成临时密码
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))

        tenant = {
            "tenant_id": tenant_id,
            "name": data.name,
            "code": data.code,
            "status": TenantStatus.ACTIVE.value,
            "plan": data.plan,
            "buildings_count": 0,
            "robots_count": 0,
            "users_count": 1,
            "contact": data.contact.model_dump() if data.contact else None,
            "settings": data.settings.model_dump() if data.settings else TenantSettings().model_dump(),
            "created_at": now,
            "expires_at": data.expires_at,
            "updated_at": now
        }

        self._tenants[tenant_id] = tenant
        logger.info(f"Created tenant: {tenant_id}")

        return TenantCreateResponse(
            tenant_id=tenant_id,
            name=data.name,
            status=TenantStatus.ACTIVE,
            admin_account={
                "username": f"admin@{data.code.lower()}",
                "temp_password": temp_password
            }
        )

    async def update_tenant(
        self,
        tenant_id: str,
        data: TenantUpdate
    ) -> Optional[TenantDetail]:
        """更新租户"""
        if tenant_id not in self._tenants:
            return None

        tenant = self._tenants[tenant_id]
        now = datetime.now(timezone.utc)

        if data.name is not None:
            tenant["name"] = data.name
        if data.contact is not None:
            tenant["contact"] = data.contact.model_dump()
        if data.settings is not None:
            tenant["settings"] = data.settings.model_dump()
        if data.status is not None:
            tenant["status"] = data.status.value

        tenant["updated_at"] = now
        logger.info(f"Updated tenant: {tenant_id}")

        return await self.get_tenant(tenant_id)

    async def delete_tenant(self, tenant_id: str) -> bool:
        """删除租户"""
        if tenant_id not in self._tenants:
            return False

        del self._tenants[tenant_id]
        logger.info(f"Deleted tenant: {tenant_id}")
        return True

    # ========== 用户管理 ==========

    async def list_users(
        self,
        tenant_id: Optional[str] = None,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> UserListResponse:
        """获取用户列表"""
        users = list(self._users.values())

        if tenant_id:
            users = [u for u in users if u.get("tenant_id") == tenant_id]
        if role:
            users = [u for u in users if u["role"] == role.value]
        if status:
            users = [u for u in users if u["status"] == status.value]
        if search:
            users = [u for u in users if search.lower() in u["name"].lower() or search.lower() in u["username"].lower()]

        total = len(users)
        start = (page - 1) * page_size
        end = start + page_size
        page_users = users[start:end]

        items = [
            UserListItem(
                user_id=u["user_id"],
                username=u["username"],
                email=u["email"],
                name=u["name"],
                role=UserRole(u["role"]),
                role_name=u["role_name"],
                status=UserStatus(u["status"]),
                last_login_at=u.get("last_login_at"),
                created_at=u["created_at"]
            )
            for u in page_users
        ]

        return UserListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )

    async def get_user(self, user_id: str) -> Optional[UserDetail]:
        """获取用户详情"""
        user = self._users.get(user_id)
        if not user:
            return None

        return UserDetail(
            user_id=user["user_id"],
            username=user["username"],
            email=user["email"],
            name=user["name"],
            role=UserRole(user["role"]),
            role_name=user["role_name"],
            status=UserStatus(user["status"]),
            tenant_id=user.get("tenant_id"),
            permissions=user.get("permissions", []),
            last_login_at=user.get("last_login_at"),
            created_at=user["created_at"],
            updated_at=user.get("updated_at")
        )

    async def create_user(self, tenant_id: str, data: UserCreate) -> UserDetail:
        """创建用户"""
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        role_names = {
            UserRole.PLATFORM_ADMIN: "平台管理员",
            UserRole.TENANT_ADMIN: "租户管理员",
            UserRole.MANAGER: "管理员",
            UserRole.TRAINER: "训练师",
            UserRole.OPERATOR: "操作员"
        }

        user = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "username": data.username,
            "email": data.email,
            "name": data.name,
            "role": data.role.value,
            "role_name": role_names.get(data.role, "未知"),
            "status": UserStatus.ACTIVE.value,
            "permissions": [],
            "last_login_at": None,
            "created_at": now,
            "updated_at": now
        }

        self._users[user_id] = user
        logger.info(f"Created user: {user_id}")

        return await self.get_user(user_id)

    async def update_user(self, user_id: str, data: UserUpdate) -> Optional[UserDetail]:
        """更新用户"""
        if user_id not in self._users:
            return None

        user = self._users[user_id]
        now = datetime.now(timezone.utc)

        if data.name is not None:
            user["name"] = data.name
        if data.email is not None:
            user["email"] = data.email
        if data.role is not None:
            user["role"] = data.role.value
        if data.status is not None:
            user["status"] = data.status.value

        user["updated_at"] = now
        logger.info(f"Updated user: {user_id}")

        return await self.get_user(user_id)

    async def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        if user_id not in self._users:
            return False

        del self._users[user_id]
        logger.info(f"Deleted user: {user_id}")
        return True

    # ========== 审计日志 ==========

    async def get_audit_logs(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> AuditLogResponse:
        """获取审计日志"""
        logs = self._audit_logs.copy()

        if user_id:
            logs = [l for l in logs if l["user_id"] == user_id]
        if action:
            logs = [l for l in logs if l["action"] == action.value]
        if resource_type:
            logs = [l for l in logs if l["resource_type"] == resource_type]
        if start_time:
            logs = [l for l in logs if l["timestamp"] >= start_time]
        if end_time:
            logs = [l for l in logs if l["timestamp"] <= end_time]

        # 按时间倒序
        logs.sort(key=lambda x: x["timestamp"], reverse=True)

        total = len(logs)
        start = (page - 1) * page_size
        end = start + page_size
        page_logs = logs[start:end]

        items = [
            AuditLogItem(
                log_id=l["log_id"],
                user_id=l["user_id"],
                username=l["username"],
                action=AuditAction(l["action"]),
                resource_type=l["resource_type"],
                resource_id=l.get("resource_id"),
                details=l.get("details"),
                ip_address=l.get("ip_address"),
                timestamp=l["timestamp"]
            )
            for l in page_logs
        ]

        return AuditLogResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )

    # ========== 系统配置 ==========

    async def get_configs(self, prefix: Optional[str] = None) -> SystemConfigListResponse:
        """获取系统配置"""
        configs = list(self._configs.values())

        if prefix:
            configs = [c for c in configs if c["key"].startswith(prefix)]

        items = [
            SystemConfig(
                key=c["key"],
                value=c["value"],
                description=c.get("description"),
                updated_at=c.get("updated_at"),
                updated_by=c.get("updated_by")
            )
            for c in configs
        ]

        return SystemConfigListResponse(configs=items)

    async def update_config(self, data: SystemConfigUpdate, user_id: str) -> SystemConfig:
        """更新系统配置"""
        now = datetime.now(timezone.utc)

        self._configs[data.key] = {
            "key": data.key,
            "value": data.value,
            "description": data.description or self._configs.get(data.key, {}).get("description"),
            "updated_at": now,
            "updated_by": user_id
        }

        logger.info(f"Updated config: {data.key}")

        return SystemConfig(**self._configs[data.key])

    # ========== 系统健康 ==========

    async def get_system_health(self) -> SystemHealthResponse:
        """获取系统健康状态"""
        return SystemHealthResponse(
            status="healthy",
            version="1.0.0",
            uptime=86400,
            services={
                "api": "healthy",
                "mcp": "healthy",
                "agents": "healthy"
            },
            database="healthy",
            cache="healthy",
            timestamp=datetime.now(timezone.utc)
        )
