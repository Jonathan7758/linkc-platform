"""
Drone Module Tests - 无人机模块测试
"""

import pytest
import asyncio
from src.adapters.drone import (
    MockDroneAdapter,
    DroneStatus,
    DronePosition,
    FlightTask,
    FlightMode,
)
from src.capabilities.drone import (
    DRONE_CAPABILITIES,
    get_drone_capabilities,
    get_drone_capability_ids,
)
from src.agents.drone_agent import DroneAgent


class TestDroneCapabilities:
    """无人机能力测试"""

    def test_drone_capabilities_defined(self):
        """测试无人机能力定义"""
        assert len(DRONE_CAPABILITIES) == 5
        cap_ids = [cap.id for cap in DRONE_CAPABILITIES]
        assert "drone.patrol.aerial" in cap_ids
        assert "drone.inspection.facade" in cap_ids
        assert "drone.inspection.roof" in cap_ids
        assert "drone.delivery.aerial" in cap_ids
        assert "drone.photography.aerial" in cap_ids

    def test_get_drone_capabilities(self):
        """测试获取无人机能力"""
        caps = get_drone_capabilities()
        assert len(caps) == 5

    def test_get_drone_capability_ids(self):
        """测试获取无人机能力ID列表"""
        cap_ids = get_drone_capability_ids()
        assert len(cap_ids) == 5
        assert all(cap_id.startswith("drone.") for cap_id in cap_ids)


class TestMockDroneAdapter:
    """模拟无人机适配器测试"""

    @pytest.fixture
    def adapter(self):
        """创建测试适配器"""
        return MockDroneAdapter("test-drone-001")

    @pytest.mark.asyncio
    async def test_connect(self, adapter):
        """测试连接"""
        result = await adapter.connect()
        assert result is True
        assert adapter.state.status == DroneStatus.IDLE
        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_get_status(self, adapter):
        """测试获取状态"""
        await adapter.connect()
        state = await adapter.get_status()
        assert state.drone_id == "test-drone-001"
        assert state.status == DroneStatus.IDLE
        assert state.battery_percent == 100
        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_arm_disarm(self, adapter):
        """测试解锁/锁定"""
        await adapter.connect()

        result = await adapter.arm()
        assert result is True
        assert adapter.state.is_armed is True

        result = await adapter.disarm()
        assert result is True
        assert adapter.state.is_armed is False

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_takeoff_land(self, adapter):
        """测试起飞/降落"""
        await adapter.connect()
        await adapter.arm()

        result = await adapter.takeoff(10.0)
        assert result is True
        assert adapter.state.status == DroneStatus.HOVERING
        assert adapter.state.position.altitude == pytest.approx(10.0, rel=0.5)

        result = await adapter.land()
        assert result is True
        assert adapter.state.status == DroneStatus.IDLE
        assert adapter.state.position.altitude == 0

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_goto_position(self, adapter):
        """测试飞往指定位置"""
        await adapter.connect()
        await adapter.arm()
        await adapter.takeoff(20.0)

        target = DronePosition(latitude=31.23, longitude=121.48, altitude=25.0)
        result = await adapter.goto_position(target)

        assert result is True
        assert adapter.state.position.latitude == target.latitude
        assert adapter.state.position.longitude == target.longitude

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_camera_operations(self, adapter):
        """测试相机操作"""
        await adapter.connect()

        result = await adapter.start_camera("visible")
        assert result is True
        assert adapter.state.camera_active is True

        image = await adapter.capture_image()
        assert image is not None
        assert "drone_test-drone-001" in image

        result = await adapter.stop_camera()
        assert result is True
        assert adapter.state.camera_active is False

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_execute_flight_task(self, adapter):
        """测试执行飞行任务"""
        await adapter.connect()

        task = FlightTask(
            task_id="task-001",
            task_type="patrol",
            waypoints=[
                DronePosition(31.23, 121.47, 30),
                DronePosition(31.24, 121.48, 30),
            ],
            altitude_m=30.0,
            speed_ms=5.0,
        )

        result = await adapter.execute_flight_task(task)

        assert result.success is True
        assert result.task_id == "task-001"
        assert result.duration_sec > 0
        assert result.images_captured > 0

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_emergency_stop(self, adapter):
        """测试紧急停止"""
        await adapter.connect()
        await adapter.arm()
        await adapter.takeoff(20.0)

        result = await adapter.emergency_stop()

        assert result is True
        assert adapter.state.status == DroneStatus.HOVERING
        assert adapter.state.speed_ms == 0

        await adapter.disconnect()

    def test_is_available(self, adapter):
        """测试可用性检查"""
        adapter._state.status = DroneStatus.IDLE
        adapter._state.battery_percent = 80
        adapter._state.error_code = None

        assert adapter.is_available() is True

        adapter._state.battery_percent = 10
        assert adapter.is_available() is False


class TestDroneAgent:
    """无人机 Agent 测试"""

    @pytest.fixture
    def agent(self):
        """创建测试 Agent"""
        return DroneAgent("agent-001")

    @pytest.mark.asyncio
    async def test_start_stop(self, agent):
        """测试启动/停止"""
        result = await agent.start()
        assert result is True
        assert agent.status == "ready"

        await agent.stop()
        assert agent.status == "offline"

    def test_capabilities(self, agent):
        """测试能力列表"""
        caps = agent.capabilities
        assert len(caps) == 5
        assert "drone.patrol.aerial" in caps

    def test_has_capability(self, agent):
        """测试能力检查"""
        assert agent._has_capability("drone.patrol.aerial") is True
        assert agent._has_capability("drone.*") is True
        assert agent._has_capability("robot.cleaning") is False

    def test_validate_task_parameters(self, agent):
        """测试参数验证"""
        # 有效的巡逻参数
        result = agent._validate_task_parameters({
            "capability": "drone.patrol.aerial",
            "route_id": "route-001",
        })
        assert result.valid is True

        # 缺少 route_id
        result = agent._validate_task_parameters({
            "capability": "drone.patrol.aerial",
        })
        assert result.valid is False

        # 空参数
        result = agent._validate_task_parameters({})
        assert result.valid is False

    def test_estimate_duration(self, agent):
        """测试时长估计"""
        from dataclasses import dataclass

        @dataclass
        class MockTask:
            parameters: dict

        task = MockTask(parameters={"capability": "drone.patrol.aerial"})
        duration = agent._estimate_duration(task)
        assert duration == 45

        task = MockTask(parameters={"capability": "drone.delivery.aerial"})
        duration = agent._estimate_duration(task)
        assert duration == 10

    @pytest.mark.asyncio
    async def test_get_drone_status(self, agent):
        """测试获取无人机状态"""
        await agent.start()

        status = await agent.get_drone_status()

        assert "drone_id" in status
        assert "status" in status
        assert "battery_percent" in status
        assert status["battery_percent"] == 100

        await agent.stop()
