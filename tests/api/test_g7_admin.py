"""
G7: 系统管理API 测试
======================
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.admin import (
    router, AdminService,
    TenantCreate, TenantUpdate, TenantContact, TenantSettings,
    UserCreate, UserUpdate, SystemConfigUpdate,
    TenantStatus, UserStatus, UserRole
)


@pytest.fixture
def app():
    """创建测试应用"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def service():
    """创建服务实例"""
    return AdminService()


class TestAdminService:
    """管理服务测试"""

    @pytest.mark.asyncio
    async def test_list_tenants(self, service):
        """测试获取租户列表"""
        result = await service.list_tenants()
        assert result.total > 0
        assert len(result.items) > 0

    @pytest.mark.asyncio
    async def test_get_tenant(self, service):
        """测试获取租户详情"""
        result = await service.get_tenant("tenant_001")
        assert result is not None
        assert result.tenant_id == "tenant_001"

    @pytest.mark.asyncio
    async def test_get_tenant_not_found(self, service):
        """测试获取不存在的租户"""
        result = await service.get_tenant("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_create_tenant(self, service):
        """测试创建租户"""
        data = TenantCreate(
            name="测试租户",
            code="TEST001",
            plan="professional",
            contact=TenantContact(name="测试", email="test@test.com")
        )
        result = await service.create_tenant(data)
        assert result.tenant_id is not None
        assert result.name == "测试租户"
        assert result.admin_account is not None

    @pytest.mark.asyncio
    async def test_update_tenant(self, service):
        """测试更新租户"""
        data = TenantUpdate(name="更新后的名称")
        result = await service.update_tenant("tenant_001", data)
        assert result is not None
        assert result.name == "更新后的名称"

    @pytest.mark.asyncio
    async def test_delete_tenant(self, service):
        """测试删除租户"""
        # 先创建
        data = TenantCreate(
            name="待删除租户",
            code="DEL001",
            contact=TenantContact(name="测试", email="del@test.com")
        )
        created = await service.create_tenant(data)

        # 删除
        result = await service.delete_tenant(created.tenant_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_list_users(self, service):
        """测试获取用户列表"""
        result = await service.list_users()
        assert result.total > 0

    @pytest.mark.asyncio
    async def test_list_users_by_tenant(self, service):
        """测试按租户筛选用户"""
        result = await service.list_users(tenant_id="tenant_001")
        for user in result.items:
            assert user.user_id is not None

    @pytest.mark.asyncio
    async def test_get_user(self, service):
        """测试获取用户详情"""
        result = await service.get_user("user_001")
        assert result is not None
        assert result.user_id == "user_001"

    @pytest.mark.asyncio
    async def test_create_user(self, service):
        """测试创建用户"""
        data = UserCreate(
            username="testuser",
            email="testuser@test.com",
            name="测试用户",
            role=UserRole.TRAINER
        )
        result = await service.create_user("tenant_001", data)
        assert result.user_id is not None
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_update_user(self, service):
        """测试更新用户"""
        data = UserUpdate(name="更新后的名称")
        result = await service.update_user("user_001", data)
        assert result is not None
        assert result.name == "更新后的名称"

    @pytest.mark.asyncio
    async def test_get_audit_logs(self, service):
        """测试获取审计日志"""
        result = await service.get_audit_logs()
        assert result.total >= 0

    @pytest.mark.asyncio
    async def test_get_configs(self, service):
        """测试获取系统配置"""
        result = await service.get_configs()
        assert len(result.configs) > 0

    @pytest.mark.asyncio
    async def test_update_config(self, service):
        """测试更新系统配置"""
        data = SystemConfigUpdate(
            key="test.config",
            value="test_value",
            description="测试配置"
        )
        result = await service.update_config(data, "user_001")
        assert result.key == "test.config"
        assert result.value == "test_value"

    @pytest.mark.asyncio
    async def test_get_system_health(self, service):
        """测试获取系统健康"""
        result = await service.get_system_health()
        assert result.status == "healthy"


class TestAdminRouter:
    """管理路由测试"""

    def test_list_tenants(self, client):
        """测试租户列表接口"""
        response = client.get("/api/v1/admin/tenants")
        assert response.status_code == 200
        assert "items" in response.json()

    def test_get_tenant(self, client):
        """测试租户详情接口"""
        response = client.get("/api/v1/admin/tenants/tenant_001")
        assert response.status_code == 200
        assert response.json()["tenant_id"] == "tenant_001"

    def test_get_tenant_not_found(self, client):
        """测试获取不存在的租户"""
        response = client.get("/api/v1/admin/tenants/nonexistent")
        assert response.status_code == 404

    def test_create_tenant(self, client):
        """测试创建租户接口"""
        response = client.post("/api/v1/admin/tenants", json={
            "name": "API测试租户",
            "code": "APITEST",
            "contact": {"name": "测试", "email": "api@test.com"}
        })
        assert response.status_code == 201
        assert "tenant_id" in response.json()

    def test_update_tenant(self, client):
        """测试更新租户接口"""
        response = client.put("/api/v1/admin/tenants/tenant_001", json={
            "name": "更新的租户名"
        })
        assert response.status_code == 200

    def test_list_users(self, client):
        """测试用户列表接口"""
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 200
        assert "items" in response.json()

    def test_get_user(self, client):
        """测试用户详情接口"""
        response = client.get("/api/v1/admin/users/user_001")
        assert response.status_code == 200
        assert response.json()["user_id"] == "user_001"

    def test_get_user_not_found(self, client):
        """测试获取不存在的用户"""
        response = client.get("/api/v1/admin/users/nonexistent")
        assert response.status_code == 404

    def test_create_user(self, client):
        """测试创建用户接口"""
        response = client.post("/api/v1/admin/users", json={
            "username": "apiuser",
            "email": "apiuser@test.com",
            "name": "API用户",
            "role": "trainer"
        })
        assert response.status_code == 201
        assert "user_id" in response.json()

    def test_update_user(self, client):
        """测试更新用户接口"""
        response = client.put("/api/v1/admin/users/user_002", json={
            "name": "更新的用户名"
        })
        assert response.status_code == 200

    def test_get_audit_logs(self, client):
        """测试审计日志接口"""
        response = client.get("/api/v1/admin/audit-logs")
        assert response.status_code == 200
        assert "items" in response.json()

    def test_get_configs(self, client):
        """测试配置列表接口"""
        response = client.get("/api/v1/admin/configs")
        assert response.status_code == 200
        assert "configs" in response.json()

    def test_update_config(self, client):
        """测试更新配置接口"""
        response = client.put("/api/v1/admin/configs", json={
            "key": "test.api.config",
            "value": 123,
            "description": "API测试配置"
        })
        assert response.status_code == 200
        assert response.json()["key"] == "test.api.config"

    def test_get_system_health(self, client):
        """测试系统健康接口"""
        response = client.get("/api/v1/admin/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
