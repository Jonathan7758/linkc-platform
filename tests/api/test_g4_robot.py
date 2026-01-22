"""
G4: 机器人管理API 测试
======================
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.robot import router, RobotService, RobotCreate, RobotUpdate, RobotControlRequest
from src.api.robot.models import RobotBrand, ControlCommand


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
    return RobotService()


class TestRobotService:
    """机器人服务测试"""

    @pytest.mark.asyncio
    async def test_list_robots(self, service):
        """测试获取机器人列表"""
        result = await service.list_robots("tenant_001")

        assert result.total == 3
        assert len(result.items) == 3
        assert result.page == 1
        assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_list_robots_with_filter(self, service):
        """测试按状态筛选"""
        result = await service.list_robots("tenant_001", status="idle")

        assert result.total == 1
        assert result.items[0].status == "idle"

    @pytest.mark.asyncio
    async def test_list_robots_pagination(self, service):
        """测试分页"""
        result = await service.list_robots("tenant_001", page=1, page_size=2)

        assert len(result.items) == 2
        assert result.total == 3
        assert result.page == 1
        assert result.page_size == 2

    @pytest.mark.asyncio
    async def test_get_robot(self, service):
        """测试获取机器人详情"""
        result = await service.get_robot("robot_001", "tenant_001")

        assert result is not None
        assert result.robot_id == "robot_001"
        assert result.name == "清洁机器人A-01"
        assert result.brand == "gaoxian"
        assert result.statistics is not None

    @pytest.mark.asyncio
    async def test_get_robot_not_found(self, service):
        """测试获取不存在的机器人"""
        result = await service.get_robot("nonexistent", "tenant_001")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_robot_wrong_tenant(self, service):
        """测试获取其他租户的机器人"""
        result = await service.get_robot("robot_001", "wrong_tenant")
        assert result is None

    @pytest.mark.asyncio
    async def test_create_robot(self, service):
        """测试创建机器人"""
        data = RobotCreate(
            tenant_id="tenant_001",
            name="测试机器人",
            brand=RobotBrand.GAOXIAN,
            model="GS-100",
            serial_number="TEST001",
            building_id="building_001"
        )

        result = await service.create_robot(data)

        assert result.name == "测试机器人"
        assert result.brand == "gaoxian"
        assert result.model == "GS-100"
        assert result.status == "offline"

    @pytest.mark.asyncio
    async def test_update_robot(self, service):
        """测试更新机器人"""
        data = RobotUpdate(name="新名称")

        result = await service.update_robot("robot_001", "tenant_001", data)

        assert result is not None
        assert result.name == "新名称"

    @pytest.mark.asyncio
    async def test_update_robot_not_found(self, service):
        """测试更新不存在的机器人"""
        data = RobotUpdate(name="新名称")

        result = await service.update_robot("nonexistent", "tenant_001", data)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_robot(self, service):
        """测试删除机器人"""
        # 先创建一个机器人
        data = RobotCreate(
            tenant_id="tenant_001",
            name="待删除机器人",
            brand=RobotBrand.GAOXIAN,
            model="GS-100",
            serial_number="DEL001",
            building_id="building_001"
        )
        created = await service.create_robot(data)

        # 删除
        result = await service.delete_robot(created.robot_id, "tenant_001")
        assert result is True

        # 确认已删除
        robot = await service.get_robot(created.robot_id, "tenant_001")
        assert robot is None

    @pytest.mark.asyncio
    async def test_delete_robot_not_found(self, service):
        """测试删除不存在的机器人"""
        result = await service.delete_robot("nonexistent", "tenant_001")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_status(self, service):
        """测试获取实时状态"""
        result = await service.get_status("robot_001", "tenant_001")

        assert result is not None
        assert result.robot_id == "robot_001"
        assert result.status == "idle"
        assert result.battery_level == 85
        assert result.position is not None

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, service):
        """测试获取不存在机器人的状态"""
        result = await service.get_status("nonexistent", "tenant_001")
        assert result is None

    @pytest.mark.asyncio
    async def test_send_control_go_charge(self, service):
        """测试发送充电指令"""
        request = RobotControlRequest(command=ControlCommand.GO_CHARGE)

        result = await service.send_control("robot_001", "tenant_001", request)

        assert result is not None
        assert result.success is True
        assert result.robot_id == "robot_001"
        assert result.command == "go_charge"

    @pytest.mark.asyncio
    async def test_send_control_pause(self, service):
        """测试发送暂停指令"""
        request = RobotControlRequest(command=ControlCommand.PAUSE)

        result = await service.send_control("robot_003", "tenant_001", request)

        assert result.success is True
        assert result.command == "pause"

    @pytest.mark.asyncio
    async def test_send_control_not_found(self, service):
        """测试发送指令到不存在的机器人"""
        request = RobotControlRequest(command=ControlCommand.PAUSE)

        result = await service.send_control("nonexistent", "tenant_001", request)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_errors(self, service):
        """测试获取错误信息"""
        result = await service.get_errors("robot_001", "tenant_001")

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_position_history(self, service):
        """测试获取位置历史"""
        now = datetime.now(timezone.utc)
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = now

        result = await service.get_position_history("robot_001", "tenant_001", start, end)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_status_history(self, service):
        """测试获取状态历史"""
        now = datetime.now(timezone.utc)
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = now

        result = await service.get_status_history("robot_001", "tenant_001", start, end)

        assert isinstance(result, list)


class TestRobotRouter:
    """机器人路由测试"""

    def test_list_robots(self, client):
        """测试列表接口"""
        response = client.get("/api/v1/robots")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_robots_with_filter(self, client):
        """测试带筛选的列表接口"""
        response = client.get("/api/v1/robots?status=idle")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 0

    def test_get_robot(self, client):
        """测试详情接口"""
        response = client.get("/api/v1/robots/robot_001")

        assert response.status_code == 200
        data = response.json()
        assert data["robot_id"] == "robot_001"

    def test_get_robot_not_found(self, client):
        """测试详情接口 - 不存在"""
        response = client.get("/api/v1/robots/nonexistent")

        assert response.status_code == 404

    def test_create_robot(self, client):
        """测试创建接口"""
        response = client.post("/api/v1/robots", json={
            "tenant_id": "tenant_001",
            "name": "API测试机器人",
            "brand": "gaoxian",
            "model": "GS-200",
            "serial_number": "API001",
            "building_id": "building_001"
        })

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API测试机器人"

    def test_update_robot(self, client):
        """测试更新接口"""
        response = client.put("/api/v1/robots/robot_001", json={
            "name": "更新后的名称"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的名称"

    def test_update_robot_not_found(self, client):
        """测试更新接口 - 不存在"""
        response = client.put("/api/v1/robots/nonexistent", json={
            "name": "新名称"
        })

        assert response.status_code == 404

    def test_delete_robot(self, client):
        """测试删除接口"""
        # 先创建一个
        create_response = client.post("/api/v1/robots", json={
            "tenant_id": "tenant_001",
            "name": "待删除",
            "brand": "gaoxian",
            "model": "GS-100",
            "serial_number": "DEL002",
            "building_id": "building_001"
        })
        robot_id = create_response.json()["robot_id"]

        # 删除
        response = client.delete(f"/api/v1/robots/{robot_id}")
        assert response.status_code == 204

    def test_delete_robot_not_found(self, client):
        """测试删除接口 - 不存在"""
        response = client.delete("/api/v1/robots/nonexistent")
        assert response.status_code == 404

    def test_get_robot_status(self, client):
        """测试状态接口"""
        response = client.get("/api/v1/robots/robot_001/status")

        assert response.status_code == 200
        data = response.json()
        assert data["robot_id"] == "robot_001"
        assert "status" in data
        assert "battery_level" in data

    def test_get_robot_status_not_found(self, client):
        """测试状态接口 - 不存在"""
        response = client.get("/api/v1/robots/nonexistent/status")
        assert response.status_code == 404

    def test_send_control(self, client):
        """测试控制接口"""
        response = client.post("/api/v1/robots/robot_001/control", json={
            "command": "go_charge"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["command"] == "go_charge"

    def test_send_control_not_found(self, client):
        """测试控制接口 - 不存在"""
        response = client.post("/api/v1/robots/nonexistent/control", json={
            "command": "pause"
        })
        assert response.status_code == 404

    def test_get_errors(self, client):
        """测试错误接口"""
        response = client.get("/api/v1/robots/robot_001/errors")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_errors_not_found(self, client):
        """测试错误接口 - 不存在"""
        response = client.get("/api/v1/robots/nonexistent/errors")
        assert response.status_code == 404
