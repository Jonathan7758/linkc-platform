"""
G1: 认证授权API - 单元测试
===========================
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.gateway.auth.models import UserStatus
from src.api.gateway.auth.service import AuthService, AuthConfig, InMemoryAuthStorage
from src.api.gateway.auth.router import router, set_auth_service


# ============================================================
# 测试设置
# ============================================================

@pytest.fixture
def auth_service():
    """创建测试用认证服务"""
    storage = InMemoryAuthStorage()
    config = AuthConfig(
        access_token_expire_minutes=60,
        refresh_token_expire_days=7
    )
    return AuthService(storage=storage, config=config)


@pytest.fixture
def app(auth_service):
    """创建测试应用"""
    app = FastAPI()
    app.include_router(router)
    set_auth_service(auth_service)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    """获取管理员Token"""
    response = client.post("/auth/login", json={
        "username": "admin@linkc.com",
        "password": "admin123"
    })
    return response.json()["access_token"]


# ============================================================
# 认证接口测试
# ============================================================

class TestAuthEndpoints:
    """认证接口测试"""

    def test_login_success(self, client):
        """测试登录成功"""
        response = client.post("/auth/login", json={
            "username": "admin@linkc.com",
            "password": "admin123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        assert data["user"]["username"] == "admin@linkc.com"

    def test_login_wrong_password(self, client):
        """测试密码错误"""
        response = client.post("/auth/login", json={
            "username": "admin@linkc.com",
            "password": "wrongpassword"
        })

        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_user_not_found(self, client):
        """测试用户不存在"""
        response = client.post("/auth/login", json={
            "username": "nonexistent@linkc.com",
            "password": "password123"
        })

        assert response.status_code == 401

    def test_logout(self, client, admin_token):
        """测试登出"""
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "登出成功"

        # 登出后Token应失效
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 401

    def test_refresh_token(self, client):
        """测试刷新Token"""
        # 先登录获取Token
        login_response = client.post("/auth/login", json={
            "username": "admin@linkc.com",
            "password": "admin123"
        })
        refresh_token = login_response.json()["refresh_token"]

        # 刷新Token
        response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_get_me(self, client, admin_token):
        """测试获取当前用户"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin@linkc.com"
        assert data["role"]["name"] == "系统管理员"
        assert "*" in data["role"]["permissions"]

    def test_get_me_no_token(self, client):
        """测试无Token访问"""
        response = client.get("/auth/me")
        assert response.status_code == 401


# ============================================================
# 用户管理测试
# ============================================================

class TestUserManagement:
    """用户管理测试"""

    def test_list_users(self, client, admin_token):
        """测试获取用户列表"""
        response = client.get(
            "/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1

    def test_create_user(self, client, admin_token):
        """测试创建用户"""
        response = client.post(
            "/users",
            json={
                "username": "operator@linkc.com",
                "password": "password123",
                "name": "操作员",
                "role_id": "role-operator"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "operator@linkc.com"
        assert data["role_id"] == "role-operator"

    def test_create_user_duplicate(self, client, admin_token):
        """测试创建重复用户"""
        # 先创建一个用户
        client.post(
            "/users",
            json={
                "username": "duplicate@linkc.com",
                "password": "password123",
                "name": "测试用户",
                "role_id": "role-operator"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # 再次创建同名用户
        response = client.post(
            "/users",
            json={
                "username": "duplicate@linkc.com",
                "password": "password123",
                "name": "测试用户2",
                "role_id": "role-operator"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 400
        assert "已存在" in response.json()["detail"]

    def test_get_user(self, client, admin_token):
        """测试获取用户详情"""
        response = client.get(
            "/users/user-admin",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin@linkc.com"

    def test_update_user(self, client, admin_token):
        """测试更新用户"""
        # 先创建用户
        create_response = client.post(
            "/users",
            json={
                "username": "update_test@linkc.com",
                "password": "password123",
                "name": "更新测试",
                "role_id": "role-operator"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        user_id = create_response.json()["id"]

        # 更新用户
        response = client.put(
            f"/users/{user_id}",
            json={"name": "更新后的名称"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        assert response.json()["name"] == "更新后的名称"

    def test_delete_user(self, client, admin_token):
        """测试删除用户"""
        # 先创建用户
        create_response = client.post(
            "/users",
            json={
                "username": "delete_test@linkc.com",
                "password": "password123",
                "name": "删除测试",
                "role_id": "role-operator"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        user_id = create_response.json()["id"]

        # 删除用户
        response = client.delete(
            f"/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

        # 确认已删除
        get_response = client.get(
            f"/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 404


# ============================================================
# 角色管理测试
# ============================================================

class TestRoleManagement:
    """角色管理测试"""

    def test_list_roles(self, client, admin_token):
        """测试获取角色列表"""
        response = client.get(
            "/roles",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 4  # 至少有4个系统角色

    def test_create_role(self, client, admin_token):
        """测试创建角色"""
        response = client.post(
            "/roles",
            json={
                "name": "自定义角色",
                "description": "测试角色",
                "permissions": ["robots:read", "tasks:read"]
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "自定义角色"
        assert data["is_system"] is False

    def test_get_role(self, client, admin_token):
        """测试获取角色详情"""
        response = client.get(
            "/roles/role-admin",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "系统管理员"
        assert "*" in data["permissions"]

    def test_update_system_role_fails(self, client, admin_token):
        """测试更新系统角色失败"""
        response = client.put(
            "/roles/role-admin",
            json={"name": "新名称"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 400
        assert "系统角色" in response.json()["detail"]

    def test_delete_system_role_fails(self, client, admin_token):
        """测试删除系统角色失败"""
        response = client.delete(
            "/roles/role-admin",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 400
        assert "系统角色" in response.json()["detail"]


# ============================================================
# 权限测试
# ============================================================

class TestPermissions:
    """权限测试"""

    def test_list_permissions(self, client, admin_token):
        """测试获取权限列表"""
        response = client.get(
            "/permissions",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "permissions" in data
        assert len(data["permissions"]) > 0

        # 检查权限结构
        perm = data["permissions"][0]
        assert "code" in perm
        assert "name" in perm
        assert "category" in perm

    def test_permission_denied(self, client, admin_token, auth_service):
        """测试权限拒绝"""
        # 创建一个只读用户
        client.post(
            "/users",
            json={
                "username": "viewer@linkc.com",
                "password": "password123",
                "name": "只读用户",
                "role_id": "role-viewer"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # 使用只读用户登录
        login_response = client.post("/auth/login", json={
            "username": "viewer@linkc.com",
            "password": "password123"
        })
        viewer_token = login_response.json()["access_token"]

        # 尝试创建用户（应被拒绝）
        response = client.post(
            "/users",
            json={
                "username": "test@linkc.com",
                "password": "password123",
                "name": "测试",
                "role_id": "role-operator"
            },
            headers={"Authorization": f"Bearer {viewer_token}"}
        )

        assert response.status_code == 403
        assert "缺少权限" in response.json()["detail"]


# ============================================================
# 服务层测试
# ============================================================

class TestAuthService:
    """认证服务测试"""

    @pytest.mark.asyncio
    async def test_check_permission_wildcard(self, auth_service):
        """测试通配符权限"""
        assert auth_service.check_permission(["*"], "users:read") is True
        assert auth_service.check_permission(["*"], "any:permission") is True

    @pytest.mark.asyncio
    async def test_check_permission_category_wildcard(self, auth_service):
        """测试分类通配符权限"""
        assert auth_service.check_permission(["users:*"], "users:read") is True
        assert auth_service.check_permission(["users:*"], "users:write") is True
        assert auth_service.check_permission(["users:*"], "robots:read") is False

    @pytest.mark.asyncio
    async def test_check_permission_action_wildcard(self, auth_service):
        """测试操作通配符权限"""
        assert auth_service.check_permission(["*:read"], "users:read") is True
        assert auth_service.check_permission(["*:read"], "robots:read") is True
        assert auth_service.check_permission(["*:read"], "users:write") is False

    @pytest.mark.asyncio
    async def test_check_permission_exact_match(self, auth_service):
        """测试精确匹配权限"""
        assert auth_service.check_permission(["users:read"], "users:read") is True
        assert auth_service.check_permission(["users:read"], "users:write") is False
