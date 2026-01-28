"""
Mobile Robot Integration Tests - 移动机器人集成测试
"""

import pytest
import asyncio
from src.integration.mobile_robot import (
    MobileRobotIntegration,
    MobileRobotConfig,
    get_mobile_robot_integration,
    init_mobile_robot_integration,
)
from src.capabilities.registry import CapabilityRegistry
from src.capabilities.drone import get_drone_capability_ids
from src.capabilities.robot_dog import get_robot_dog_capability_ids


class TestMobileRobotIntegration:
    """移动机器人集成测试"""

    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return MobileRobotConfig(
            drone_count=2,
            robot_dog_count=2,
            auto_register=True,
            enable_federation=False,  # 测试时禁用 Federation
        )

    @pytest.fixture
    def registry(self):
        """创建能力注册表"""
        return CapabilityRegistry()

    @pytest.fixture
    def integration(self, config, registry):
        """创建集成实例"""
        return MobileRobotIntegration(
            config=config,
            capability_registry=registry,
        )

    @pytest.mark.asyncio
    async def test_initialize(self, integration):
        """测试初始化"""
        result = await integration.initialize()

        assert result is True
        assert len(integration.drone_agents) == 2
        assert len(integration.robot_dog_agents) == 2

        await integration.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown(self, integration):
        """测试关闭"""
        await integration.initialize()
        await integration.shutdown()

        assert len(integration.drone_agents) == 0
        assert len(integration.robot_dog_agents) == 0

    @pytest.mark.asyncio
    async def test_get_agent(self, integration):
        """测试获取 Agent"""
        await integration.initialize()

        drone = integration.get_agent("drone-001")
        assert drone is not None
        assert drone.agent_id == "drone-001"

        robot_dog = integration.get_agent("robotdog-001")
        assert robot_dog is not None
        assert robot_dog.agent_id == "robotdog-001"

        nonexistent = integration.get_agent("nonexistent")
        assert nonexistent is None

        await integration.shutdown()

    @pytest.mark.asyncio
    async def test_get_agents_by_capability(self, integration):
        """测试按能力获取 Agent"""
        await integration.initialize()

        # 获取无人机巡逻能力
        patrol_drones = integration.get_agents_by_capability("drone.patrol.aerial")
        assert len(patrol_drones) == 2

        # 获取机器狗护送能力
        escort_dogs = integration.get_agents_by_capability("robotdog.escort.security")
        assert len(escort_dogs) == 2

        # 通配符匹配
        all_drones = integration.get_agents_by_capability("drone.*")
        assert len(all_drones) == 2

        await integration.shutdown()

    @pytest.mark.asyncio
    async def test_get_available_agents(self, integration):
        """测试获取可用 Agent"""
        await integration.initialize()

        # 获取所有可用 Agent
        all_available = integration.get_available_agents()
        assert len(all_available) == 4

        # 只获取无人机
        drones = integration.get_available_agents(agent_type="drone")
        assert len(drones) == 2

        # 只获取机器狗
        robot_dogs = integration.get_available_agents(agent_type="robot_dog")
        assert len(robot_dogs) == 2

        await integration.shutdown()

    @pytest.mark.asyncio
    async def test_dispatch_task_drone(self, integration):
        """测试分派无人机任务"""
        await integration.initialize()

        task_id = await integration.dispatch_task(
            capability_id="drone.patrol.aerial",
            parameters={
                "route_id": "route-001",
                "altitude_m": 50,
            },
            priority=2
        )

        assert task_id is not None
        assert task_id.startswith("task-")

        # 等待任务开始
        await asyncio.sleep(0.5)

        await integration.shutdown()

    @pytest.mark.asyncio
    async def test_dispatch_task_robot_dog(self, integration):
        """测试分派机器狗任务"""
        await integration.initialize()

        task_id = await integration.dispatch_task(
            capability_id="robotdog.patrol.rough",
            parameters={
                "route_id": "route-001",
                "terrain_type": "mixed",
            },
            priority=2
        )

        assert task_id is not None
        assert task_id.startswith("task-")

        await asyncio.sleep(0.5)

        await integration.shutdown()

    @pytest.mark.asyncio
    async def test_dispatch_task_no_available_agent(self, integration):
        """测试无可用 Agent 时的任务分派"""
        await integration.initialize()

        # 使用一个不存在的能力
        task_id = await integration.dispatch_task(
            capability_id="nonexistent.capability",
            parameters={},
        )

        assert task_id is None

        await integration.shutdown()

    @pytest.mark.asyncio
    async def test_get_status(self, integration):
        """测试获取状态"""
        await integration.initialize()

        status = integration.get_status()

        assert status["initialized"] is True
        assert status["drone_count"] == 2
        assert status["robot_dog_count"] == 2
        assert "drone-001" in status["drones"]
        assert "robotdog-001" in status["robot_dogs"]

        await integration.shutdown()

    @pytest.mark.asyncio
    async def test_capability_registration(self, integration, registry):
        """测试能力注册"""
        await integration.initialize()

        # 检查无人机能力
        drone_caps = registry.list_all_capabilities()
        drone_cap_ids = [c.id for c in drone_caps]
        for cap_id in get_drone_capability_ids():
            assert cap_id in drone_cap_ids

        # 检查机器狗能力
        for cap_id in get_robot_dog_capability_ids():
            assert cap_id in drone_cap_ids  # 所有能力都在同一个列表

        await integration.shutdown()

    @pytest.mark.asyncio
    async def test_agent_registration_to_registry(self, integration, registry):
        """测试 Agent 注册到能力注册表"""
        await integration.initialize()

        # 检查无人机 Agent 注册
        drone_info = registry.get_agent_capabilities("drone-001")
        assert drone_info is not None
        assert drone_info.agent_type == "drone"
        assert "drone.patrol.aerial" in drone_info.capabilities

        # 检查机器狗 Agent 注册
        dog_info = registry.get_agent_capabilities("robotdog-001")
        assert dog_info is not None
        assert dog_info.agent_type == "robot_dog"
        assert "robotdog.patrol.rough" in dog_info.capabilities

        await integration.shutdown()

    @pytest.mark.asyncio
    async def test_find_agents_by_capability_through_registry(self, integration, registry):
        """测试通过注册表查找 Agent"""
        await integration.initialize()

        # 查找具有无人机巡逻能力的 Agent
        agents = registry.find_agents_by_capability("drone.patrol.aerial")
        assert len(agents) == 2

        # 查找具有机器狗检查能力的 Agent
        agents = registry.find_agents_by_capability("robotdog.inspection.underground")
        assert len(agents) == 2

        # 通配符查找
        agents = registry.find_agents_by_capability("drone.*")
        assert len(agents) == 2

        await integration.shutdown()


class TestMobileRobotIntegrationSingleAgent:
    """单 Agent 集成测试"""

    @pytest.fixture
    def config(self):
        return MobileRobotConfig(
            drone_count=1,
            robot_dog_count=1,
            enable_federation=False,
        )

    @pytest.fixture
    def integration(self, config):
        return MobileRobotIntegration(config=config)

    @pytest.mark.asyncio
    async def test_single_drone_patrol(self, integration):
        """测试单无人机巡逻任务"""
        await integration.initialize()

        drone = integration.get_agent("drone-001")
        assert drone is not None

        # 获取无人机状态
        status = await drone.get_drone_status()
        assert status["status"] == "idle"
        assert status["battery_percent"] == 100

        await integration.shutdown()

    @pytest.mark.asyncio
    async def test_single_robot_dog_escort(self, integration):
        """测试单机器狗护送任务"""
        await integration.initialize()

        robot_dog = integration.get_agent("robotdog-001")
        assert robot_dog is not None

        # 获取机器狗状态
        status = await robot_dog.get_robot_dog_status()
        assert status["status"] == "idle"
        assert status["battery_percent"] == 100

        await integration.shutdown()

    @pytest.mark.asyncio
    async def test_concurrent_tasks(self, integration):
        """测试并发任务"""
        await integration.initialize()

        # 同时分派两个任务
        task1 = asyncio.create_task(integration.dispatch_task(
            capability_id="drone.patrol.aerial",
            parameters={"route_id": "route-001"},
        ))
        task2 = asyncio.create_task(integration.dispatch_task(
            capability_id="robotdog.patrol.rough",
            parameters={"route_id": "route-002"},
        ))

        results = await asyncio.gather(task1, task2)

        assert results[0] is not None
        assert results[1] is not None

        await asyncio.sleep(0.5)
        await integration.shutdown()


class TestGlobalIntegrationInstance:
    """全局实例测试"""

    @pytest.mark.asyncio
    async def test_init_global_instance(self):
        """测试初始化全局实例"""
        config = MobileRobotConfig(
            drone_count=1,
            robot_dog_count=1,
            enable_federation=False,
        )

        integration = await init_mobile_robot_integration(config=config)

        assert integration is not None
        assert len(integration.drone_agents) == 1
        assert len(integration.robot_dog_agents) == 1

        # 获取全局实例
        global_instance = get_mobile_robot_integration()
        assert global_instance is integration

        await integration.shutdown()
