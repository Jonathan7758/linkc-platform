"""
A2: 清洁调度Agent - 单元测试
============================
"""

import pytest
import asyncio
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from src.agents.runtime.base import AgentConfig, AgentState, AutonomyLevel
from src.agents.runtime.decision import Decision, DecisionResult
from src.agents.cleaning_scheduler.agent import (
    CleaningSchedulerAgent,
    PriorityBasedStrategy,
    SchedulingContext,
    TaskAssignment
)


# ============================================================
# Mock MCP Tools
# ============================================================

@dataclass
class ToolResult:
    """Mock tool result"""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None


class MockTaskTools:
    """Mock 任务管理工具"""

    def __init__(self):
        self.pending_tasks = []
        self.task_states = {}  # task_id -> status

    async def handle(self, name: str, args: dict) -> ToolResult:
        if name == "task_get_pending_tasks":
            return ToolResult(
                success=True,
                data={"tasks": self.pending_tasks}
            )
        elif name == "task_update_status":
            task_id = args.get("task_id")
            status = args.get("status")
            robot_id = args.get("robot_id")

            self.task_states[task_id] = {
                "status": status,
                "robot_id": robot_id
            }
            return ToolResult(success=True, data={"updated": True})

        return ToolResult(success=False, data={}, error=f"Unknown tool: {name}")

    def add_task(self, task_id: str, zone_id: str, task_type: str = "routine", priority: int = 5):
        """添加待分配任务"""
        self.pending_tasks.append({
            "task_id": task_id,
            "zone_id": zone_id,
            "task_type": task_type,
            "priority": priority,
            "tenant_id": "tenant_001",
            "status": "pending"
        })


class MockRobotTools:
    """Mock 机器人控制工具"""

    def __init__(self):
        self.robots = []
        self.robot_tasks = {}  # robot_id -> current_task

    async def handle(self, name: str, args: dict) -> ToolResult:
        if name == "robot_list_robots":
            status = args.get("status")
            robots = self.robots
            if status:
                robots = [r for r in robots if r.get("status") == status]
            return ToolResult(success=True, data={"robots": robots})

        elif name == "robot_start_task":
            robot_id = args.get("robot_id")
            task_id = args.get("task_id")
            zone_id = args.get("zone_id")

            # 检查机器人是否存在且空闲
            robot = next((r for r in self.robots if r["robot_id"] == robot_id), None)
            if not robot:
                return ToolResult(success=False, data={}, error="Robot not found")
            if robot.get("status") != "idle":
                return ToolResult(success=False, data={}, error="Robot is busy")

            # 更新机器人状态
            robot["status"] = "working"
            self.robot_tasks[robot_id] = task_id

            return ToolResult(success=True, data={
                "robot_id": robot_id,
                "task_id": task_id,
                "status": "started"
            })

        return ToolResult(success=False, data={}, error=f"Unknown tool: {name}")

    def add_robot(
        self,
        robot_id: str,
        status: str = "idle",
        battery_level: int = 80,
        current_zone_id: str = None,
        capabilities: dict = None
    ):
        """添加机器人"""
        self.robots.append({
            "robot_id": robot_id,
            "status": status,
            "battery_level": battery_level,
            "current_zone_id": current_zone_id,
            "capabilities": capabilities or {"vacuum": True, "mop": True},
            "tenant_id": "tenant_001"
        })


class MockSpaceTools:
    """Mock 空间管理工具"""

    def __init__(self):
        self.zones = {}  # zone_id -> zone info

    async def handle(self, name: str, args: dict) -> ToolResult:
        if name == "space_get_zone":
            zone_id = args.get("zone_id")
            zone = self.zones.get(zone_id)
            if zone:
                return ToolResult(success=True, data={"zone": zone})
            return ToolResult(success=False, data={}, error="Zone not found")

        return ToolResult(success=False, data={}, error=f"Unknown tool: {name}")

    def add_zone(self, zone_id: str, floor_id: str, name: str = "Zone"):
        """添加区域"""
        self.zones[zone_id] = {
            "zone_id": zone_id,
            "floor_id": floor_id,
            "name": name
        }


# ============================================================
# Strategy Tests
# ============================================================

class TestPriorityBasedStrategy:
    """优先级调度策略测试"""

    @pytest.fixture
    def strategy(self):
        return PriorityBasedStrategy()

    @pytest.fixture
    def context(self):
        return SchedulingContext(
            tenant_id="tenant_001",
            zone_info={
                "zone_001": {"zone_id": "zone_001", "floor_id": "floor_001"},
                "zone_002": {"zone_id": "zone_002", "floor_id": "floor_001"},
                "zone_003": {"zone_id": "zone_003", "floor_id": "floor_002"}
            }
        )

    def test_match_prefers_high_battery(self, strategy, context):
        """测试优先选择高电量机器人"""
        task = {"task_id": "task_001", "zone_id": "zone_001", "priority": 5}
        robots = [
            {"robot_id": "robot_001", "battery_level": 30, "current_zone_id": "zone_001"},
            {"robot_id": "robot_002", "battery_level": 90, "current_zone_id": "zone_002"},
        ]

        assignment = strategy.match(task, robots, context)

        assert assignment is not None
        assert assignment.robot_id == "robot_002"  # 高电量
        assert "高电量" in assignment.reason

    def test_match_prefers_same_zone(self, strategy, context):
        """测试优先选择同区域机器人"""
        task = {"task_id": "task_001", "zone_id": "zone_001", "priority": 5}
        robots = [
            {"robot_id": "robot_001", "battery_level": 80, "current_zone_id": "zone_001"},
            {"robot_id": "robot_002", "battery_level": 80, "current_zone_id": "zone_003"},
        ]

        assignment = strategy.match(task, robots, context)

        assert assignment is not None
        assert assignment.robot_id == "robot_001"  # 同区域
        assert "同区域" in assignment.reason

    def test_match_prefers_same_floor(self, strategy, context):
        """测试优先选择同楼层机器人"""
        task = {"task_id": "task_001", "zone_id": "zone_001", "priority": 5}
        robots = [
            {"robot_id": "robot_001", "battery_level": 80, "current_zone_id": "zone_002"},  # 同楼层
            {"robot_id": "robot_002", "battery_level": 80, "current_zone_id": "zone_003"},  # 跨楼层
        ]

        assignment = strategy.match(task, robots, context)

        assert assignment is not None
        assert assignment.robot_id == "robot_001"  # 同楼层
        assert "同楼层" in assignment.reason

    def test_match_no_robots(self, strategy, context):
        """测试没有可用机器人"""
        task = {"task_id": "task_001", "zone_id": "zone_001", "priority": 5}

        assignment = strategy.match(task, [], context)

        assert assignment is None


# ============================================================
# Agent Tests
# ============================================================

class TestCleaningSchedulerAgent:
    """清洁调度Agent测试"""

    @pytest.fixture
    def task_tools(self):
        return MockTaskTools()

    @pytest.fixture
    def robot_tools(self):
        return MockRobotTools()

    @pytest.fixture
    def space_tools(self):
        return MockSpaceTools()

    @pytest.fixture
    def agent(self, task_tools, robot_tools, space_tools):
        config = AgentConfig(
            agent_id="scheduler_001",
            name="Test Scheduler",
            tenant_id="tenant_001",
            autonomy_level=AutonomyLevel.L2_LIMITED,
            max_tasks_per_decision=5,
            max_battery_threshold=20
        )
        return CleaningSchedulerAgent(
            config=config,
            task_tools=task_tools,
            robot_tools=robot_tools,
            space_tools=space_tools
        )

    @pytest.mark.asyncio
    async def test_think_no_tasks(self, agent):
        """测试没有待分配任务"""
        decision = await agent.think({"tenant_id": "tenant_001"})

        assert decision.decision_type == "task_scheduling"
        assert "没有待分配的任务" in decision.description
        assert decision.confidence == 1.0
        assert len(decision.actions) == 0

    @pytest.mark.asyncio
    async def test_think_no_robots(self, agent, task_tools):
        """测试没有可用机器人"""
        task_tools.add_task("task_001", "zone_001")

        decision = await agent.think({"tenant_id": "tenant_001"})

        assert "没有可用的机器人" in decision.description
        assert len(decision.actions) == 0

    @pytest.mark.asyncio
    async def test_think_generates_assignments(self, agent, task_tools, robot_tools, space_tools):
        """测试生成分配方案"""
        # 准备数据
        task_tools.add_task("task_001", "zone_001", priority=1)
        task_tools.add_task("task_002", "zone_002", priority=5)
        robot_tools.add_robot("robot_001", battery_level=80, current_zone_id="zone_001")
        robot_tools.add_robot("robot_002", battery_level=90, current_zone_id="zone_002")
        space_tools.add_zone("zone_001", "floor_001")
        space_tools.add_zone("zone_002", "floor_001")

        decision = await agent.think({"tenant_id": "tenant_001"})

        assert len(decision.actions) == 2
        assert decision.confidence > 0.5

        # 验证高优先级任务先分配
        first_action = decision.actions[0]
        assert first_action["params"]["task_id"] == "task_001"  # 优先级1

    @pytest.mark.asyncio
    async def test_think_filters_low_battery_robots(self, agent, task_tools, robot_tools):
        """测试过滤低电量机器人"""
        task_tools.add_task("task_001", "zone_001")
        robot_tools.add_robot("robot_001", battery_level=10)  # 低于阈值20
        robot_tools.add_robot("robot_002", battery_level=50)  # 高于阈值

        decision = await agent.think({"tenant_id": "tenant_001"})

        assert len(decision.actions) == 1
        assert decision.actions[0]["params"]["robot_id"] == "robot_002"

    @pytest.mark.asyncio
    async def test_think_exceeds_boundary(self, agent, task_tools, robot_tools):
        """测试超出自主边界"""
        # 添加超过限制的任务
        for i in range(10):
            task_tools.add_task(f"task_{i}", f"zone_{i % 3}")
            robot_tools.add_robot(f"robot_{i}", battery_level=80)

        decision = await agent.think({"tenant_id": "tenant_001"})

        # 超过max_tasks_per_decision=5
        assert decision.exceeds_boundary is True

    @pytest.mark.asyncio
    async def test_execute_success(self, agent, task_tools, robot_tools, space_tools):
        """测试成功执行分配"""
        task_tools.add_task("task_001", "zone_001")
        robot_tools.add_robot("robot_001", battery_level=80, current_zone_id="zone_001")
        space_tools.add_zone("zone_001", "floor_001")

        # 先思考
        decision = await agent.think({"tenant_id": "tenant_001"})
        assert len(decision.actions) == 1

        # 再执行
        result = await agent.execute(decision)

        assert result.success is True
        assert len(result.actions_executed) == 1
        assert len(result.actions_failed) == 0

        # 验证任务状态更新
        assert "task_001" in task_tools.task_states
        assert task_tools.task_states["task_001"]["status"] == "in_progress"

        # 验证机器人状态更新
        robot = next(r for r in robot_tools.robots if r["robot_id"] == "robot_001")
        assert robot["status"] == "working"

    @pytest.mark.asyncio
    async def test_execute_robot_busy(self, agent, task_tools, robot_tools, space_tools):
        """测试机器人忙碌时执行失败"""
        task_tools.add_task("task_001", "zone_001")
        robot_tools.add_robot("robot_001", status="working", battery_level=80)

        # 手动构建决策
        decision = Decision(decision_type="task_scheduling")
        decision.add_action("assign_task", {
            "task_id": "task_001",
            "robot_id": "robot_001",
            "zone_id": "zone_001",
            "task_type": "routine"
        })

        result = await agent.execute(decision)

        assert result.success is False
        assert len(result.actions_failed) == 1
        assert "busy" in result.actions_failed[0]["error"].lower()

    @pytest.mark.asyncio
    async def test_full_scheduling_cycle(self, agent, task_tools, robot_tools, space_tools):
        """测试完整的调度周期"""
        # 准备多个任务和机器人
        task_tools.add_task("task_001", "zone_001", priority=1)
        task_tools.add_task("task_002", "zone_002", priority=3)
        task_tools.add_task("task_003", "zone_001", priority=5)

        robot_tools.add_robot("robot_001", battery_level=90, current_zone_id="zone_001")
        robot_tools.add_robot("robot_002", battery_level=80, current_zone_id="zone_002")

        space_tools.add_zone("zone_001", "floor_001")
        space_tools.add_zone("zone_002", "floor_001")

        # 运行完整周期
        result = await agent.run_cycle({"tenant_id": "tenant_001"})

        # 应该成功分配2个任务（2个机器人）
        assert result.success is True
        assert len(result.actions_executed) == 2

        # 验证统计
        stats = agent.get_stats()
        assert stats["successful_assignments"] == 2
        assert stats["last_run"] is not None

    @pytest.mark.asyncio
    async def test_state_transitions(self, agent, task_tools, robot_tools):
        """测试Agent状态转换"""
        # 初始状态
        assert agent.state == AgentState.IDLE

        # 准备数据
        task_tools.add_task("task_001", "zone_001")
        robot_tools.add_robot("robot_001", battery_level=80)

        # 运行周期后应该回到IDLE
        await agent.run_cycle({"tenant_id": "tenant_001"})
        assert agent.state == AgentState.IDLE


# ============================================================
# Integration Tests
# ============================================================

class TestSchedulerIntegration:
    """调度器集成测试"""

    @pytest.mark.asyncio
    async def test_multiple_cycles(self):
        """测试多个调度周期"""
        task_tools = MockTaskTools()
        robot_tools = MockRobotTools()
        space_tools = MockSpaceTools()

        agent = CleaningSchedulerAgent(
            task_tools=task_tools,
            robot_tools=robot_tools,
            space_tools=space_tools
        )

        # 第一轮：添加任务和机器人
        task_tools.add_task("task_001", "zone_001", priority=1)
        robot_tools.add_robot("robot_001", battery_level=80, current_zone_id="zone_001")
        space_tools.add_zone("zone_001", "floor_001")

        result1 = await agent.run_cycle({"tenant_id": "tenant_001"})
        assert result1.success is True
        assert len(result1.actions_executed) == 1

        # 第二轮：机器人已忙，添加新任务
        task_tools.pending_tasks = []  # 清空已分配任务
        task_tools.add_task("task_002", "zone_002", priority=2)

        result2 = await agent.run_cycle({"tenant_id": "tenant_001"})
        # 机器人忙碌，应该没有新分配
        assert result2.success is True
        assert len(result2.actions_executed) == 0

        # 第三轮：添加新机器人
        robot_tools.add_robot("robot_002", battery_level=90)

        result3 = await agent.run_cycle({"tenant_id": "tenant_001"})
        assert result3.success is True
        assert len(result3.actions_executed) == 1

        # 验证总统计
        stats = agent.get_stats()
        assert stats["total_assignments"] == 2
