"""
Robot Dog Module Tests - 机器狗模块测试
"""

import pytest
import asyncio
from src.adapters.robot_dog import (
    MockRobotDogAdapter,
    RobotDogStatus,
    RobotDogPosition,
    GroundTask,
    MovementMode,
    GaitType,
)
from src.capabilities.robot_dog import (
    ROBOT_DOG_CAPABILITIES,
    get_robot_dog_capabilities,
    get_robot_dog_capability_ids,
)
from src.agents.robot_dog_agent import RobotDogAgent


class TestRobotDogCapabilities:
    """机器狗能力测试"""

    def test_robot_dog_capabilities_defined(self):
        """测试机器狗能力定义"""
        assert len(ROBOT_DOG_CAPABILITIES) == 4
        cap_ids = [cap.id for cap in ROBOT_DOG_CAPABILITIES]
        assert "robotdog.patrol.rough" in cap_ids
        assert "robotdog.inspection.underground" in cap_ids
        assert "robotdog.escort.security" in cap_ids
        assert "robotdog.care.companion" in cap_ids

    def test_get_robot_dog_capabilities(self):
        """测试获取机器狗能力"""
        caps = get_robot_dog_capabilities()
        assert len(caps) == 4

    def test_get_robot_dog_capability_ids(self):
        """测试获取机器狗能力ID列表"""
        cap_ids = get_robot_dog_capability_ids()
        assert len(cap_ids) == 4
        assert all(cap_id.startswith("robotdog.") for cap_id in cap_ids)


class TestMockRobotDogAdapter:
    """模拟机器狗适配器测试"""

    @pytest.fixture
    def adapter(self):
        """创建测试适配器"""
        return MockRobotDogAdapter("test-robotdog-001")

    @pytest.mark.asyncio
    async def test_connect(self, adapter):
        """测试连接"""
        result = await adapter.connect()
        assert result is True
        assert adapter.state.status == RobotDogStatus.IDLE
        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_get_status(self, adapter):
        """测试获取状态"""
        await adapter.connect()
        state = await adapter.get_status()
        assert state.robot_id == "test-robotdog-001"
        assert state.status == RobotDogStatus.IDLE
        assert state.battery_percent == 100
        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_stand_up_sit_down(self, adapter):
        """测试站立/坐下"""
        await adapter.connect()

        result = await adapter.stand_up()
        assert result is True
        assert adapter.state.status == RobotDogStatus.STANDING

        result = await adapter.sit_down()
        assert result is True
        assert adapter.state.status == RobotDogStatus.RESTING

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_lie_down(self, adapter):
        """测试卧下"""
        await adapter.connect()
        await adapter.stand_up()

        result = await adapter.lie_down()
        assert result is True
        assert adapter.state.status == RobotDogStatus.IDLE

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_set_movement_mode(self, adapter):
        """测试设置运动模式"""
        await adapter.connect()

        result = await adapter.set_movement_mode(MovementMode.TROT)
        assert result is True
        assert adapter.state.movement_mode == MovementMode.TROT

        result = await adapter.set_movement_mode(MovementMode.RUN)
        assert result is True
        assert adapter.state.movement_mode == MovementMode.RUN

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_set_gait(self, adapter):
        """测试设置步态"""
        await adapter.connect()

        result = await adapter.set_gait(GaitType.STAIR)
        assert result is True
        assert adapter.state.gait_type == GaitType.STAIR

        result = await adapter.set_gait(GaitType.SLOPE)
        assert result is True
        assert adapter.state.gait_type == GaitType.SLOPE

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_goto_position(self, adapter):
        """测试移动到指定位置"""
        await adapter.connect()

        target = RobotDogPosition(x=10.0, y=5.0, z=0)
        result = await adapter.goto_position(target)

        assert result is True
        assert adapter.state.position.x == target.x
        assert adapter.state.position.y == target.y

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
        assert "robotdog_test-robotdog-001" in image

        result = await adapter.stop_camera()
        assert result is True
        assert adapter.state.camera_active is False

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_lidar_operations(self, adapter):
        """测试激光雷达操作"""
        await adapter.connect()

        result = await adapter.start_lidar()
        assert result is True
        assert adapter.state.lidar_active is True

        result = await adapter.stop_lidar()
        assert result is True
        assert adapter.state.lidar_active is False

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_gas_readings(self, adapter):
        """测试气体传感器读数"""
        await adapter.connect()

        readings = await adapter.get_gas_readings()

        assert "co" in readings
        assert "co2" in readings
        assert "o2" in readings
        assert readings["o2"] > 0

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_execute_ground_task(self, adapter):
        """测试执行地面任务"""
        await adapter.connect()

        task = GroundTask(
            task_id="task-001",
            task_type="patrol",
            waypoints=[
                RobotDogPosition(0, 0, 0),
                RobotDogPosition(10, 5, 0),
                RobotDogPosition(20, 0, 0),
            ],
            parameters={"terrain_type": "mixed"},
            speed_mode="normal",
        )

        result = await adapter.execute_ground_task(task)

        assert result.success is True
        assert result.task_id == "task-001"
        assert result.duration_sec > 0
        assert result.images_captured > 0

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_execute_inspection_task(self, adapter):
        """测试执行检查任务"""
        await adapter.connect()

        task = GroundTask(
            task_id="task-002",
            task_type="inspect",
            waypoints=[
                RobotDogPosition(0, 0, -1),
                RobotDogPosition(5, 0, -1),
            ],
            parameters={"gas_detection": True},
            speed_mode="slow",
        )

        result = await adapter.execute_ground_task(task)

        assert result.success is True
        assert result.gas_readings is not None

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_play_sound(self, adapter):
        """测试播放声音"""
        await adapter.connect()

        result = await adapter.play_sound("alert")
        assert result is True

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_emergency_stop(self, adapter):
        """测试紧急停止"""
        await adapter.connect()
        await adapter.stand_up()

        result = await adapter.emergency_stop()

        assert result is True
        assert adapter.state.status == RobotDogStatus.STANDING
        assert adapter.state.speed_ms == 0

        await adapter.disconnect()

    def test_is_available(self, adapter):
        """测试可用性检查"""
        adapter._state.status = RobotDogStatus.IDLE
        adapter._state.battery_percent = 80
        adapter._state.error_code = None

        assert adapter.is_available() is True

        adapter._state.battery_percent = 10
        assert adapter.is_available() is False


class TestRobotDogAgent:
    """机器狗 Agent 测试"""

    @pytest.fixture
    def agent(self):
        """创建测试 Agent"""
        return RobotDogAgent("agent-001")

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
        assert len(caps) == 4
        assert "robotdog.patrol.rough" in caps

    def test_has_capability(self, agent):
        """测试能力检查"""
        assert agent._has_capability("robotdog.patrol.rough") is True
        assert agent._has_capability("robotdog.*") is True
        assert agent._has_capability("drone.patrol") is False

    def test_validate_task_parameters(self, agent):
        """测试参数验证"""
        # 有效的巡逻参数
        result = agent._validate_task_parameters({
            "capability": "robotdog.patrol.rough",
            "route_id": "route-001",
        })
        assert result.valid is True

        # 缺少 route_id
        result = agent._validate_task_parameters({
            "capability": "robotdog.patrol.rough",
        })
        assert result.valid is False

        # 护送任务参数
        result = agent._validate_task_parameters({
            "capability": "robotdog.escort.security",
            "person_id": "person-001",
            "start_location": "lobby",
            "end_location": "office",
        })
        assert result.valid is True

        # 空参数
        result = agent._validate_task_parameters({})
        assert result.valid is False

    def test_estimate_duration(self, agent):
        """测试时长估计"""
        from dataclasses import dataclass

        @dataclass
        class MockTask:
            parameters: dict

        task = MockTask(parameters={"capability": "robotdog.patrol.rough"})
        duration = agent._estimate_duration(task)
        assert duration == 45

        task = MockTask(parameters={"capability": "robotdog.escort.security"})
        duration = agent._estimate_duration(task)
        assert duration == 20

        task = MockTask(parameters={"capability": "robotdog.care.companion", "duration_min": 60})
        duration = agent._estimate_duration(task)
        assert duration == 60

    @pytest.mark.asyncio
    async def test_get_robot_dog_status(self, agent):
        """测试获取机器狗状态"""
        await agent.start()

        status = await agent.get_robot_dog_status()

        assert "robot_id" in status
        assert "status" in status
        assert "battery_percent" in status
        assert status["battery_percent"] == 100

        await agent.stop()

    @pytest.mark.asyncio
    async def test_get_gas_readings(self, agent):
        """测试获取气体传感器读数"""
        await agent.start()

        readings = await agent.get_gas_readings()

        assert "co" in readings
        assert "o2" in readings

        await agent.stop()

    @pytest.mark.asyncio
    async def test_stand_sit_lie(self, agent):
        """测试站立/坐下/卧下"""
        await agent.start()

        result = await agent.stand_up()
        assert result is True

        result = await agent.sit_down()
        assert result is True

        result = await agent.lie_down()
        assert result is True

        await agent.stop()
