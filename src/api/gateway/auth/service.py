"""
G1: 认证授权API - 业务逻辑
===========================
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
import uuid
import hashlib
import secrets
import logging

from .models import (
    UserStatus, UserCreate, UserUpdate, UserInDB, UserResponse,
    RoleInDB, RoleCreate, RoleUpdate, RoleResponse,
    Permission, TokenPayload, LoginResponse, CurrentUser
)

logger = logging.getLogger(__name__)


# ============================================================
# 配置
# ============================================================

@dataclass
class AuthConfig:
    """认证配置"""
    secret_key: str = "linkc-platform-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    password_salt: str = "linkc-salt"


# ============================================================
# 密码处理
# ============================================================

class PasswordHelper:
    """密码助手"""

    @staticmethod
    def hash_password(password: str, salt: str = "") -> str:
        """哈希密码"""
        salted = f"{password}{salt}"
        return hashlib.sha256(salted.encode()).hexdigest()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str, salt: str = "") -> bool:
        """验证密码"""
        return PasswordHelper.hash_password(plain_password, salt) == hashed_password


# ============================================================
# JWT处理
# ============================================================

class JWTHelper:
    """JWT助手"""

    def __init__(self, config: AuthConfig):
        self.config = config

    def create_access_token(self, user: UserInDB, permissions: List[str]) -> str:
        """创建访问Token"""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.config.access_token_expire_minutes)

        payload = {
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "role": user.role_id,
            "permissions": permissions,
            "exp": expire.timestamp(),
            "iat": now.timestamp(),
            "jti": f"access_{uuid.uuid4().hex[:16]}",
            "type": "access"
        }

        # 简化实现：使用base64编码（生产环境应使用python-jose）
        import json
        import base64
        payload_json = json.dumps(payload)
        token = base64.urlsafe_b64encode(payload_json.encode()).decode()
        return token

    def create_refresh_token(self, user: UserInDB) -> str:
        """创建刷新Token"""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.config.refresh_token_expire_days)

        payload = {
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "exp": expire.timestamp(),
            "iat": now.timestamp(),
            "jti": f"refresh_{uuid.uuid4().hex[:16]}",
            "type": "refresh"
        }

        import json
        import base64
        payload_json = json.dumps(payload)
        token = base64.urlsafe_b64encode(payload_json.encode()).decode()
        return token

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """解码Token"""
        try:
            import json
            import base64
            payload_json = base64.urlsafe_b64decode(token.encode()).decode()
            payload = json.loads(payload_json)

            # 检查过期
            exp = payload.get("exp", 0)
            if datetime.now(timezone.utc).timestamp() > exp:
                return None

            return payload
        except Exception as e:
            logger.warning(f"Token decode error: {e}")
            return None


# ============================================================
# 内存存储（测试用）
# ============================================================

class InMemoryAuthStorage:
    """内存认证存储"""

    def __init__(self):
        self.users: Dict[str, UserInDB] = {}
        self.roles: Dict[str, RoleInDB] = {}
        self.token_blacklist: set = set()
        self._init_default_data()

    def _init_default_data(self):
        """初始化默认数据"""
        now = datetime.now(timezone.utc)

        # 创建默认角色
        self.roles = {
            "role-admin": RoleInDB(
                id="role-admin",
                tenant_id="tenant_001",
                name="系统管理员",
                description="拥有所有权限",
                permissions=["*"],
                is_system=True,
                created_at=now,
                updated_at=now
            ),
            "role-trainer": RoleInDB(
                id="role-trainer",
                tenant_id="tenant_001",
                name="训练师",
                description="Agent训练和监督",
                permissions=["robots:*", "tasks:*", "agents:*", "feedback:*"],
                is_system=True,
                created_at=now,
                updated_at=now
            ),
            "role-operator": RoleInDB(
                id="role-operator",
                tenant_id="tenant_001",
                name="运营人员",
                description="日常运营管理",
                permissions=["robots:read", "tasks:*", "reports:*", "alerts:*"],
                is_system=True,
                created_at=now,
                updated_at=now
            ),
            "role-viewer": RoleInDB(
                id="role-viewer",
                tenant_id="tenant_001",
                name="只读用户",
                description="只有查看权限",
                permissions=["*:read"],
                is_system=True,
                created_at=now,
                updated_at=now
            )
        }

        # 创建默认管理员
        self.users["user-admin"] = UserInDB(
            id="user-admin",
            tenant_id="tenant_001",
            username="admin@linkc.com",
            name="系统管理员",
            email="admin@linkc.com",
            role_id="role-admin",
            status=UserStatus.ACTIVE,
            hashed_password=PasswordHelper.hash_password("admin123"),
            created_at=now,
            updated_at=now
        )


# ============================================================
# 认证服务
# ============================================================

class AuthService:
    """认证服务"""

    def __init__(
        self,
        storage: Optional[InMemoryAuthStorage] = None,
        config: Optional[AuthConfig] = None
    ):
        self.storage = storage or InMemoryAuthStorage()
        self.config = config or AuthConfig()
        self.jwt_helper = JWTHelper(self.config)
        self.password_helper = PasswordHelper()

    async def login(
        self,
        username: str,
        password: str,
        tenant_id: Optional[str] = None
    ) -> Optional[LoginResponse]:
        """用户登录"""
        # 查找用户
        user = None
        for u in self.storage.users.values():
            if u.username == username:
                if tenant_id and u.tenant_id != tenant_id:
                    continue
                user = u
                break

        if not user:
            return None

        # 验证密码
        if not self.password_helper.verify_password(password, user.hashed_password):
            return None

        # 检查状态
        if user.status == UserStatus.DISABLED:
            raise ValueError("账户已禁用")

        # 获取角色权限
        role = self.storage.roles.get(user.role_id)
        permissions = role.permissions if role else []

        # 生成Token
        access_token = self.jwt_helper.create_access_token(user, permissions)
        refresh_token = self.jwt_helper.create_refresh_token(user)

        # 更新最后登录时间
        user.last_login_at = datetime.now(timezone.utc)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=self.config.access_token_expire_minutes * 60,
            user=self._user_to_response(user)
        )

    async def logout(self, token: str) -> bool:
        """用户登出"""
        self.storage.token_blacklist.add(token)
        return True

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """刷新Token"""
        # 检查黑名单
        if refresh_token in self.storage.token_blacklist:
            return None

        # 解码刷新Token
        payload = self.jwt_helper.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None

        # 获取用户
        user_id = payload.get("sub")
        user = self.storage.users.get(user_id)
        if not user:
            return None

        # 获取角色权限
        role = self.storage.roles.get(user.role_id)
        permissions = role.permissions if role else []

        # 生成新Token
        new_access_token = self.jwt_helper.create_access_token(user, permissions)
        new_refresh_token = self.jwt_helper.create_refresh_token(user)

        # 将旧刷新Token加入黑名单
        self.storage.token_blacklist.add(refresh_token)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
            "expires_in": self.config.access_token_expire_minutes * 60
        }

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证Token"""
        if token in self.storage.token_blacklist:
            return None

        return self.jwt_helper.decode_token(token)

    async def get_current_user(self, token: str) -> Optional[CurrentUser]:
        """获取当前用户"""
        payload = await self.validate_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        user = self.storage.users.get(user_id)
        if not user:
            return None

        role = self.storage.roles.get(user.role_id)

        return CurrentUser(
            id=user.id,
            username=user.username,
            name=user.name,
            email=user.email,
            phone=user.phone,
            role=RoleResponse(
                id=role.id if role else "",
                name=role.name if role else "",
                permissions=role.permissions if role else [],
                is_system=role.is_system if role else False
            ),
            tenant_id=user.tenant_id,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )

    # ==================== 用户管理 ====================

    async def list_users(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        role_id: Optional[str] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取用户列表"""
        users = [u for u in self.storage.users.values() if u.tenant_id == tenant_id]

        # 过滤
        if role_id:
            users = [u for u in users if u.role_id == role_id]
        if status:
            users = [u for u in users if u.status == status]
        if search:
            search_lower = search.lower()
            users = [u for u in users if search_lower in u.username.lower() or search_lower in u.name.lower()]

        # 分页
        total = len(users)
        start = (page - 1) * page_size
        users = users[start:start + page_size]

        return {
            "items": [self._user_to_response(u) for u in users],
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def create_user(self, tenant_id: str, data: UserCreate) -> UserResponse:
        """创建用户"""
        # 检查用户名是否已存在
        for u in self.storage.users.values():
            if u.username == data.username and u.tenant_id == tenant_id:
                raise ValueError("用户名已存在")

        now = datetime.now(timezone.utc)
        user_id = f"user_{uuid.uuid4().hex[:8]}"

        user = UserInDB(
            id=user_id,
            tenant_id=tenant_id,
            username=data.username,
            name=data.name,
            email=data.email,
            phone=data.phone,
            role_id=data.role_id,
            status=UserStatus.ACTIVE,
            hashed_password=self.password_helper.hash_password(data.password),
            created_at=now,
            updated_at=now
        )

        self.storage.users[user_id] = user
        return self._user_to_response(user)

    async def get_user(self, user_id: str) -> Optional[UserResponse]:
        """获取用户详情"""
        user = self.storage.users.get(user_id)
        if not user:
            return None
        return self._user_to_response(user)

    async def update_user(self, user_id: str, data: UserUpdate) -> Optional[UserResponse]:
        """更新用户"""
        user = self.storage.users.get(user_id)
        if not user:
            return None

        if data.name is not None:
            user.name = data.name
        if data.email is not None:
            user.email = data.email
        if data.phone is not None:
            user.phone = data.phone
        if data.role_id is not None:
            user.role_id = data.role_id
        if data.status is not None:
            user.status = data.status

        user.updated_at = datetime.now(timezone.utc)
        return self._user_to_response(user)

    async def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        if user_id in self.storage.users:
            del self.storage.users[user_id]
            return True
        return False

    # ==================== 角色管理 ====================

    async def list_roles(self, tenant_id: str) -> List[RoleResponse]:
        """获取角色列表"""
        roles = [r for r in self.storage.roles.values()
                 if r.tenant_id == tenant_id or r.is_system]

        result = []
        for role in roles:
            user_count = sum(1 for u in self.storage.users.values() if u.role_id == role.id)
            result.append(RoleResponse(
                id=role.id,
                name=role.name,
                description=role.description,
                permissions=role.permissions,
                is_system=role.is_system,
                user_count=user_count
            ))
        return result

    async def create_role(self, tenant_id: str, data: RoleCreate) -> RoleResponse:
        """创建角色"""
        now = datetime.now(timezone.utc)
        role_id = f"role_{uuid.uuid4().hex[:8]}"

        role = RoleInDB(
            id=role_id,
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            permissions=data.permissions,
            is_system=False,
            created_at=now,
            updated_at=now
        )

        self.storage.roles[role_id] = role
        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=role.permissions,
            is_system=role.is_system,
            user_count=0
        )

    async def get_role(self, role_id: str) -> Optional[RoleResponse]:
        """获取角色详情"""
        role = self.storage.roles.get(role_id)
        if not role:
            return None

        user_count = sum(1 for u in self.storage.users.values() if u.role_id == role_id)
        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=role.permissions,
            is_system=role.is_system,
            user_count=user_count
        )

    async def update_role(self, role_id: str, data: RoleUpdate) -> Optional[RoleResponse]:
        """更新角色"""
        role = self.storage.roles.get(role_id)
        if not role:
            return None

        if role.is_system:
            raise ValueError("系统角色不可修改")

        if data.name is not None:
            role.name = data.name
        if data.description is not None:
            role.description = data.description
        if data.permissions is not None:
            role.permissions = data.permissions

        role.updated_at = datetime.now(timezone.utc)
        return await self.get_role(role_id)

    async def delete_role(self, role_id: str) -> bool:
        """删除角色"""
        role = self.storage.roles.get(role_id)
        if not role:
            return False

        if role.is_system:
            raise ValueError("系统角色不可删除")

        # 检查是否有用户使用此角色
        user_count = sum(1 for u in self.storage.users.values() if u.role_id == role_id)
        if user_count > 0:
            raise ValueError(f"有{user_count}个用户正在使用此角色，无法删除")

        del self.storage.roles[role_id]
        return True

    # ==================== 权限管理 ====================

    def get_all_permissions(self) -> List[Permission]:
        """获取所有权限"""
        return [
            Permission(code="users:read", name="查看用户", category="用户管理"),
            Permission(code="users:write", name="编辑用户", category="用户管理"),
            Permission(code="users:delete", name="删除用户", category="用户管理"),
            Permission(code="roles:read", name="查看角色", category="用户管理"),
            Permission(code="roles:write", name="编辑角色", category="用户管理"),
            Permission(code="robots:read", name="查看机器人", category="机器人管理"),
            Permission(code="robots:control", name="控制机器人", category="机器人管理"),
            Permission(code="tasks:read", name="查看任务", category="任务管理"),
            Permission(code="tasks:write", name="编辑任务", category="任务管理"),
            Permission(code="tasks:delete", name="删除任务", category="任务管理"),
            Permission(code="spaces:read", name="查看空间", category="空间管理"),
            Permission(code="spaces:write", name="编辑空间", category="空间管理"),
            Permission(code="agents:read", name="查看Agent", category="Agent管理"),
            Permission(code="agents:control", name="控制Agent", category="Agent管理"),
            Permission(code="reports:read", name="查看报表", category="数据分析"),
            Permission(code="alerts:read", name="查看告警", category="告警管理"),
            Permission(code="alerts:handle", name="处理告警", category="告警管理"),
        ]

    def check_permission(self, user_permissions: List[str], required: str) -> bool:
        """检查权限"""
        if "*" in user_permissions:
            return True

        if required in user_permissions:
            return True

        # 检查通配符，如 robots:* 匹配 robots:read
        category = required.split(":")[0]
        if f"{category}:*" in user_permissions:
            return True

        # 检查 *:read 匹配所有 read 权限
        action = required.split(":")[-1]
        if f"*:{action}" in user_permissions:
            return True

        return False

    def _user_to_response(self, user: UserInDB) -> UserResponse:
        """转换用户为响应"""
        role = self.storage.roles.get(user.role_id)
        return UserResponse(
            id=user.id,
            username=user.username,
            name=user.name,
            email=user.email,
            phone=user.phone,
            role_id=user.role_id,
            role_name=role.name if role else None,
            status=user.status,
            tenant_id=user.tenant_id,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
