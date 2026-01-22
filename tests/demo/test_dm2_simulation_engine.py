"""
DM2: 实时模拟引擎单元测试

测试范围:
- 模拟引擎启动/停止
- 机器人移动模拟
- 电量消耗模拟
- 任务进度模拟
- 状态控制
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.demo.simulation_engine import (
    SimulationEngine,
    SimulationConfig,
    RobotSimState,
    Position,
    RobotMovementPattern
)


class TestPosition:
    """测试位置类"""

    def test_position_init(self):
        """测试位置初始化"""
        pos = Position(x=100, y=200, floor_id="floor_001")
        assert pos.x == 100
        assert pos.y == 200
        assert pos.floor_id == "floor_001"

    def test_position_to_dict(self):
        """测试位置转字典"""
        pos = Position(x=100, y=200, floor_id="floor_001")
        d = pos.to_dict()
        assert d["x"] == 100
        assert d["y"] == 200
        assert d["floor_id"] == "floor_001"

    def test_distance_to(self):
        """测试距离计算"""
        pos1 = Position(x=0, y=0)
        pos2 = Position(x=3, y=4)
        assert pos1.distance_to(pos2) == 5.0

        pos3 = Position(x=10, y=10)
        assert pos1.distance_to(pos3) == pytest.approx(14.142, rel=0.01)


class TestRobotSimState:
    """测试机器人模拟状态"""

    def test_state_init(self):
        """测试状态初始化"""
        pos = Position(x=100, y=100)
        state = RobotSimState(
            robot_id="robot_001",
            name="Test Robot",
            position=pos,
            status="idle",
            battery=80.0
        )

        assert state.robot_id == "robot_001"
        assert state.name == "Test Robot"
        assert state.battery == 80.0
        assert state.status == "idle"
        assert state.task_progress == 0.0

    def test_state_to_dict(self):
        """测试状态转字典"""
        pos = Position(x=100, y=100)
        state = RobotSimState(
            robot_id="robot_001",
            name="Test Robot",
            position=pos,
            status="working",
            battery=75.5,
            task_progress=45.3
        )

        d = state.to_dict()
        assert d["robot_id"] == "robot_001"
        assert d["name"] == "Test Robot"
        assert d["status"] == "working"
        assert d["battery"] == 75.5
        assert d["task_progress"] == 45.3
        assert d["position"]["x"] == 100


class TestSimulationConfig:
    """测试模拟配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = SimulationConfig()

        assert config.tick_interval == 1.0
        assert config.speed_multiplier == 1.0
        assert config.battery_drain_rate == 0.02
        assert config.battery_charge_rate == 0.5
        assert config.task_progress_rate == 0.5

    def test_custom_config(self):
        """测试自定义配置"""
        config = SimulationConfig(
            tick_interval=0.5,
            speed_multiplier=2.0,
            battery_drain_rate=0.05
        )

        assert config.tick_interval == 0.5
        assert config.speed_multiplier == 2.0
        assert config.battery_drain_rate == 0.05


class TestSimulationEngine:
    """测试模拟引擎"""

    @pytest_asyncio.fixture
    async def engine(self):
        """创建测试用引擎实例"""
        # 重置单例
        SimulationEngine._instance = None
        eng = SimulationEngine()

        # 添加测试机器人
        eng._robots = {
            "robot_001": RobotSimState(
                robot_id="robot_001",
                name="Test Robot 1",
                position=Position(x=100, y=100, floor_id="floor_001"),
                status="idle",
                battery=80.0
            ),
            "robot_002": RobotSimState(
                robot_id="robot_002",
                name="Test Robot 2",
                position=Position(x=150, y=150, floor_id="floor_001"),
                status="working",
                battery=60.0,
                task_id="task_001",
                task_progress=30.0,
                movement_pattern=RobotMovementPattern.CLEANING,
                target_position=Position(x=200, y=200)
            ),
            "robot_003": RobotSimState(
                robot_id="robot_003",
                name="Test Robot 3",
                position=Position(x=10, y=10, floor_id="floor_002"),
                status="charging",
                battery=25.0
            )
        }

        yield eng

        # 清理
        if eng.is_running:
            await eng.stop()
        SimulationEngine._instance = None

    @pytest.mark.asyncio
    async def test_start_stop(self, engine):
        """测试启动和停止"""
        # 启动
        result = await engine.start()
        assert result["success"] is True
        assert engine.is_running is True

        # 再次启动应该失败
        result = await engine.start()
        assert result["success"] is False

        # 停止
        result = await engine.stop()
        assert result["success"] is True
        assert engine.is_running is False

        # 再次停止应该失败
        result = await engine.stop()
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_pause_resume(self, engine):
        """测试暂停和恢复"""
        # 未运行时暂停应该失败
        result = engine.pause()
        assert result["success"] is False

        # 启动后暂停
        await engine.start()
        result = engine.pause()
        assert result["success"] is True
        assert engine.is_paused is True

        # 恢复
        result = engine.resume()
        assert result["success"] is True
        assert engine.is_paused is False

        await engine.stop()

    @pytest.mark.asyncio
    async def test_set_speed(self, engine):
        """测试设置速度"""
        # 正常速度
        result = engine.set_speed(2.0)
        assert result["success"] is True
        assert engine.config.speed_multiplier == 2.0

        # 超出范围
        result = engine.set_speed(15.0)
        assert result["success"] is False

        result = engine.set_speed(0.05)
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_get_robot_state(self, engine):
        """测试获取机器人状态"""
        state = engine.get_robot_state("robot_001")
        assert state is not None
        assert state["robot_id"] == "robot_001"
        assert state["battery"] == 80.0

        # 不存在的机器人
        state = engine.get_robot_state("robot_999")
        assert state is None

    @pytest.mark.asyncio
    async def test_get_all_states(self, engine):
        """测试获取所有状态"""
        states = engine.get_all_states()
        assert len(states) == 3

    @pytest.mark.asyncio
    async def test_assign_task(self, engine):
        """测试分配任务"""
        # 给空闲机器人分配任务
        result = engine.assign_task("robot_001", "task_new_001")
        assert result["success"] is True

        state = engine.get_robot_state("robot_001")
        assert state["status"] == "working"
        assert state["task_id"] == "task_new_001"

        # 给工作中机器人分配任务应该失败
        result = engine.assign_task("robot_002", "task_new_002")
        assert result["success"] is False

        # 不存在的机器人
        result = engine.assign_task("robot_999", "task_999")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_assign_task_with_target(self, engine):
        """测试分配任务带目标位置"""
        result = engine.assign_task(
            "robot_001",
            "task_target_001",
            target={"x": 250, "y": 180}
        )
        assert result["success"] is True

        state = engine._robots["robot_001"]
        assert state.target_position is not None
        assert state.target_position.x == 250
        assert state.target_position.y == 180

    @pytest.mark.asyncio
    async def test_recall_robot(self, engine):
        """测试召回机器人"""
        result = engine.recall_robot("robot_002")
        assert result["success"] is True

        state = engine.get_robot_state("robot_002")
        assert state["status"] == "returning"

        # 不存在的机器人
        result = engine.recall_robot("robot_999")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_set_robot_status(self, engine):
        """测试设置机器人状态"""
        result = engine.set_robot_status("robot_001", "maintenance")
        assert result["success"] is True
        assert result["old_status"] == "idle"
        assert result["new_status"] == "maintenance"

        state = engine.get_robot_state("robot_001")
        assert state["status"] == "maintenance"

        # 无效状态
        result = engine.set_robot_status("robot_001", "invalid_status")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_get_status(self, engine):
        """测试获取引擎状态"""
        status = engine.get_status()

        assert "running" in status
        assert "paused" in status
        assert "speed" in status
        assert "robots_count" in status
        assert "robots_by_status" in status

        assert status["robots_count"] == 3

    @pytest.mark.asyncio
    async def test_move_towards_target(self, engine):
        """测试机器人移动"""
        state = engine._robots["robot_002"]
        initial_x = state.position.x
        initial_y = state.position.y

        # 移动一次
        moved = engine._move_towards_target(state)
        assert moved is True

        # 位置应该改变
        assert state.position.x != initial_x or state.position.y != initial_y

        # 应该向目标移动
        initial_distance = Position(initial_x, initial_y).distance_to(state.target_position)
        new_distance = state.position.distance_to(state.target_position)
        assert new_distance < initial_distance

    @pytest.mark.asyncio
    async def test_update_working_robot(self, engine):
        """测试更新工作中机器人"""
        state = engine._robots["robot_002"]
        initial_battery = state.battery
        initial_progress = state.task_progress

        changed = engine._update_working_robot(state)
        assert changed is True

        # 电量应该减少
        assert state.battery < initial_battery

        # 进度应该增加
        assert state.task_progress > initial_progress

    @pytest.mark.asyncio
    async def test_update_charging_robot(self, engine):
        """测试更新充电中机器人"""
        state = engine._robots["robot_003"]
        initial_battery = state.battery

        changed = engine._update_charging_robot(state)
        assert changed is True

        # 电量应该增加
        assert state.battery > initial_battery

    @pytest.mark.asyncio
    async def test_charging_complete(self, engine):
        """测试充电完成"""
        state = engine._robots["robot_003"]
        state.battery = 99.8

        # 更新后应该充满并变为空闲
        engine._update_charging_robot(state)

        assert state.battery == 100
        assert state.status == "idle"

    @pytest.mark.asyncio
    async def test_low_battery_trigger(self, engine):
        """测试低电量触发返回"""
        state = engine._robots["robot_002"]
        state.battery = 19.5  # 接近20%阈值

        # 消耗电量后应该触发返回
        engine._update_working_robot(state)

        # 电量低于20%时状态应该变为returning
        if state.battery < 20:
            assert state.status == "returning"

    @pytest.mark.asyncio
    async def test_task_completion(self, engine):
        """测试任务完成"""
        state = engine._robots["robot_002"]
        state.task_progress = 99.8

        # 更新后应该完成任务
        engine._update_working_robot(state)

        assert state.task_progress >= 100 or state.status == "idle"

    @pytest.mark.asyncio
    async def test_broadcast_callback(self, engine):
        """测试广播回调"""
        received_messages = []

        async def mock_broadcast(data):
            received_messages.append(data)

        engine.set_broadcast_callback(mock_broadcast)
        await engine._broadcast_updates([{"robot_id": "test", "status": "working"}])

        assert len(received_messages) == 1
        assert received_messages[0]["type"] == "robot_updates"

    @pytest.mark.asyncio
    async def test_simulation_tick(self, engine):
        """测试模拟tick"""
        # 设置广播回调
        received_updates = []

        async def mock_broadcast(data):
            received_updates.append(data)

        engine.set_broadcast_callback(mock_broadcast)

        # 执行一次tick
        await engine._tick()

        # 工作中的机器人应该有更新
        assert len(received_updates) > 0

    @pytest.mark.asyncio
    async def test_generate_cleaning_target(self, engine):
        """测试生成清洁目标"""
        current = Position(x=100, y=100)
        target = engine._generate_cleaning_target(current)

        # 目标应该在地图范围内
        assert engine.config.map_bounds["min_x"] <= target.x <= engine.config.map_bounds["max_x"]
        assert engine.config.map_bounds["min_y"] <= target.y <= engine.config.map_bounds["max_y"]

        # 目标应该在合理距离内
        distance = current.distance_to(target)
        assert 10 <= distance <= 100


class TestSimulationEngineIntegration:
    """集成测试"""

    @pytest_asyncio.fixture
    async def engine_with_demo(self):
        """创建带演示数据的引擎"""
        # 重置单例
        SimulationEngine._instance = None
        from src.demo.data_service import DemoDataService
        DemoDataService._instance = None

        from src.demo.data_service import demo_service
        from src.demo.scenarios import DemoScenario

        # 初始化演示数据
        await demo_service.init_demo_data(DemoScenario.FULL_DEMO)

        # 创建引擎
        engine = SimulationEngine()
        engine.setup_from_demo_service(demo_service)

        yield engine

        # 清理
        if engine.is_running:
            await engine.stop()
        SimulationEngine._instance = None
        DemoDataService._instance = None

    @pytest.mark.asyncio
    async def test_setup_from_demo_service(self, engine_with_demo):
        """测试从演示服务初始化"""
        states = engine_with_demo.get_all_states()

        # 应该有8个机器人
        assert len(states) == 8

        # 检查状态
        status_counts = {}
        for state in states:
            s = state["status"]
            status_counts[s] = status_counts.get(s, 0) + 1

        # 应该有多种状态
        assert len(status_counts) > 1

    @pytest.mark.asyncio
    async def test_full_simulation_cycle(self, engine_with_demo):
        """测试完整模拟周期"""
        engine = engine_with_demo

        # 启动
        result = await engine.start()
        assert result["success"] is True

        # 运行几个tick
        for _ in range(3):
            await engine._tick()
            await asyncio.sleep(0.1)

        # 检查状态更新
        status = engine.get_status()
        assert status["running"] is True

        # 暂停
        engine.pause()
        assert engine.is_paused is True

        # 恢复
        engine.resume()
        assert engine.is_paused is False

        # 停止
        await engine.stop()
        assert engine.is_running is False


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
