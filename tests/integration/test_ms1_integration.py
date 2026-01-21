"""
MS1 里程碑集成测试
==================
验证 M1(空间管理) + M2(任务管理) + M3(机器人控制) 联调通过

测试场景:
1. 创建空间层级结构
2. 创建清洁任务计划
3. 分配机器人执行任务
4. 完成任务流程
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Any, Optional

# MCP Server imports
from src.mcp_servers.space_manager.storage import SpaceStorage
from src.mcp_servers.space_manager.tools import SpaceManagerTools

from src.mcp_servers.task_manager.storage import InMemoryTaskStorage
from src.mcp_servers.task_manager.tools import TaskTools

from src.mcp_servers.robot_gaoxian.storage import InMemoryRobotStorage
from src.mcp_servers.robot_gaoxian.mock_client import MockGaoxianClient
from src.mcp_servers.robot_gaoxian.tools import RobotTools


@dataclass
class ToolResult:
    """统一的工具结果"""
    success: bool
    data: dict
    error: Optional[str] = None


class SpaceToolsWrapper:
    """SpaceManagerTools 的 handle 方法包装器"""

    def __init__(self, tools: SpaceManagerTools):
        self._tools = tools

    async def handle(self, name: str, arguments: dict) -> ToolResult:
        """统一的 handle 接口"""
        method_map = {
            "space_list_buildings": self._tools.list_buildings,
            "space_get_building": self._tools.get_building,
            "space_list_floors": self._tools.list_floors,
            "space_get_floor": self._tools.get_floor,
            "space_list_zones": self._tools.list_zones,
            "space_get_zone": self._tools.get_zone,
            "space_update_zone": self._tools.update_zone,
            "space_list_points": self._tools.list_points,
        }

        method = method_map.get(name)
        if not method:
            return ToolResult(success=False, data={}, error=f"Unknown tool: {name}")

        try:
            result = await method(**arguments)
            success = result.get("success", True)
            error = result.get("error") if not success else None
            return ToolResult(success=success, data=result, error=error)
        except Exception as e:
            return ToolResult(success=False, data={}, error=str(e))


class TestMS1Integration:
    """MS1 里程碑集成测试"""

    @pytest.fixture
    def tenant_id(self):
        return "tenant_001"  # 与 SpaceStorage 示例数据一致

    @pytest.fixture
    def space_tools(self, tenant_id):
        """空间管理 MCP"""
        storage = SpaceStorage()  # 自动初始化示例数据
        tools = SpaceManagerTools(storage)
        return SpaceToolsWrapper(tools)

    @pytest.fixture
    def task_tools(self):
        """任务管理 MCP"""
        storage = InMemoryTaskStorage()
        return TaskTools(storage)

    @pytest.fixture
    def robot_tools(self, tenant_id):
        """机器人控制 MCP"""
        storage = InMemoryRobotStorage()  # 自动初始化示例数据
        client = MockGaoxianClient(storage)
        return RobotTools(client, storage)

    @pytest.mark.asyncio
    async def test_scenario_1_space_to_task_flow(
        self, space_tools, task_tools, robot_tools, tenant_id
    ):
        """
        场景1: 空间 → 任务 → 机器人 完整流程

        1. 获取空间信息
        2. 创建清洁计划
        3. 生成任务
        4. 查看可用机器人
        5. 分配任务给机器人
        """
        # Step 1: 获取空间层级
        buildings = await space_tools.handle("space_list_buildings", {
            "tenant_id": tenant_id
        })
        assert buildings.success
        assert len(buildings.data["buildings"]) > 0
        building_id = buildings.data["buildings"][0]["id"]

        # 获取楼层
        floors = await space_tools.handle("space_list_floors", {
            "building_id": building_id
        })
        assert floors.success
        assert len(floors.data["floors"]) > 0
        floor_id = floors.data["floors"][0]["id"]

        # 获取区域
        zones = await space_tools.handle("space_list_zones", {
            "floor_id": floor_id
        })
        assert zones.success
        assert len(zones.data["zones"]) > 0
        zone = zones.data["zones"][0]
        zone_id = zone["id"]

        # Step 2: 创建清洁计划
        schedule_result = await task_tools.handle("task_create_schedule", {
            "tenant_id": tenant_id,
            "zone_id": zone_id,
            "task_type": "routine",
            "frequency": "daily",
            "time_slots": [{"start": "08:00", "end": "10:00"}],
            "priority": 5
        })
        assert schedule_result.success
        schedule_id = schedule_result.data["schedule"]["schedule_id"]

        # Step 3: 手动创建任务 (模拟计划触发)
        task_result = await task_tools.handle("task_create_task", {
            "tenant_id": tenant_id,
            "schedule_id": schedule_id,
            "zone_id": zone_id,
            "task_type": "routine",
            "priority": 5
        })
        assert task_result.success
        task_id = task_result.data["task"]["task_id"]

        # Step 4: 查看可用机器人
        robots = await robot_tools.handle("robot_list_robots", {
            "tenant_id": tenant_id,
            "status": "idle"
        })
        assert robots.success
        available_robots = robots.data["robots"]
        assert len(available_robots) > 0
        robot_id = available_robots[0]["robot_id"]

        # Step 5: 派发任务给机器人
        start_result = await robot_tools.handle("robot_start_task", {
            "robot_id": robot_id,
            "task_id": task_id,
            "zone_id": zone_id,
            "task_type": "vacuum"
        })
        assert start_result.success

        # 验证机器人状态变为工作中
        status = await robot_tools.handle("robot_get_status", {
            "robot_id": robot_id
        })
        assert status.success
        assert status.data["status"] in ["working", "navigating"]

    @pytest.mark.asyncio
    async def test_scenario_2_multi_robot_coordination(
        self, space_tools, task_tools, robot_tools, tenant_id
    ):
        """
        场景2: 多机器人协调

        1. 获取多个区域
        2. 创建多个任务
        3. 分配给不同机器人
        4. 验证并行执行
        """
        # 获取楼层和区域
        buildings = await space_tools.handle("space_list_buildings", {
            "tenant_id": tenant_id
        })
        building_id = buildings.data["buildings"][0]["id"]

        floors = await space_tools.handle("space_list_floors", {
            "building_id": building_id
        })
        floor_id = floors.data["floors"][0]["id"]

        zones = await space_tools.handle("space_list_zones", {
            "floor_id": floor_id
        })
        zone_ids = [z["id"] for z in zones.data["zones"][:2]]  # 取前2个区域

        # 获取所有空闲机器人
        robots = await robot_tools.handle("robot_list_robots", {
            "tenant_id": tenant_id,
            "status": "idle"
        })
        idle_robots = robots.data["robots"]

        # 为每个区域创建任务并分配机器人
        assignments = []
        for i, zone_id in enumerate(zone_ids):
            if i >= len(idle_robots):
                break

            # 创建任务
            task_result = await task_tools.handle("task_create_task", {
                "tenant_id": tenant_id,
                "zone_id": zone_id,
                "task_type": "routine",
                "priority": 5
            })
            assert task_result.success
            task_id = task_result.data["task"]["task_id"]

            # 分配机器人
            robot_id = idle_robots[i]["robot_id"]
            start_result = await robot_tools.handle("robot_start_task", {
                "robot_id": robot_id,
                "task_id": task_id,
                "zone_id": zone_id,
                "task_type": "vacuum"
            })
            assert start_result.success

            assignments.append({
                "task_id": task_id,
                "robot_id": robot_id,
                "zone_id": zone_id
            })

        # 验证所有分配的机器人都在工作
        for assignment in assignments:
            status = await robot_tools.handle("robot_get_status", {
                "robot_id": assignment["robot_id"]
            })
            assert status.success
            assert status.data["status"] in ["working", "navigating"]

        assert len(assignments) >= 1, "至少应该有1个机器人被分配任务"

    @pytest.mark.asyncio
    async def test_scenario_3_task_lifecycle(
        self, space_tools, task_tools, robot_tools, tenant_id
    ):
        """
        场景3: 任务生命周期管理

        1. 创建任务
        2. 分配机器人
        3. 暂停任务
        4. 恢复任务
        5. 完成任务
        """
        # 获取区域
        buildings = await space_tools.handle("space_list_buildings", {
            "tenant_id": tenant_id
        })
        building_id = buildings.data["buildings"][0]["id"]

        floors = await space_tools.handle("space_list_floors", {
            "building_id": building_id
        })
        floor_id = floors.data["floors"][0]["id"]

        zones = await space_tools.handle("space_list_zones", {
            "floor_id": floor_id
        })
        zone_id = zones.data["zones"][0]["id"]

        # 创建任务
        task_result = await task_tools.handle("task_create_task", {
            "tenant_id": tenant_id,
            "zone_id": zone_id,
            "task_type": "routine",
            "priority": 1
        })
        task_id = task_result.data["task"]["task_id"]

        # 获取机器人
        robots = await robot_tools.handle("robot_list_robots", {
            "tenant_id": tenant_id,
            "status": "idle"
        })
        robot_id = robots.data["robots"][0]["robot_id"]

        # 开始任务
        await robot_tools.handle("robot_start_task", {
            "robot_id": robot_id,
            "task_id": task_id,
            "zone_id": zone_id,
            "task_type": "vacuum"
        })

        # 更新任务状态为执行中
        await task_tools.handle("task_update_status", {
            "task_id": task_id,
            "status": "in_progress",
            "robot_id": robot_id
        })

        # 暂停任务
        pause_result = await robot_tools.handle("robot_pause_task", {
            "robot_id": robot_id
        })
        assert pause_result.success

        # 验证机器人状态
        status = await robot_tools.handle("robot_get_status", {
            "robot_id": robot_id
        })
        assert status.data["status"] == "paused"

        # 恢复任务
        resume_result = await robot_tools.handle("robot_resume_task", {
            "robot_id": robot_id
        })
        assert resume_result.success

        # 验证机器人继续工作
        status = await robot_tools.handle("robot_get_status", {
            "robot_id": robot_id
        })
        assert status.data["status"] == "working"

        # 取消任务 (模拟完成)
        cancel_result = await robot_tools.handle("robot_cancel_task", {
            "robot_id": robot_id,
            "reason": "Task completed for testing"
        })
        assert cancel_result.success

    @pytest.mark.asyncio
    async def test_scenario_4_error_handling(
        self, space_tools, task_tools, robot_tools, tenant_id
    ):
        """
        场景4: 错误处理

        1. 尝试分配任务给忙碌的机器人
        2. 尝试获取不存在的资源
        3. 验证错误响应
        """
        # 获取区域
        buildings = await space_tools.handle("space_list_buildings", {
            "tenant_id": tenant_id
        })
        building_id = buildings.data["buildings"][0]["id"]

        floors = await space_tools.handle("space_list_floors", {
            "building_id": building_id
        })
        floor_id = floors.data["floors"][0]["id"]

        zones = await space_tools.handle("space_list_zones", {
            "floor_id": floor_id
        })
        zone_id = zones.data["zones"][0]["id"]

        # 获取机器人并让它开始工作
        robots = await robot_tools.handle("robot_list_robots", {
            "tenant_id": tenant_id,
            "status": "idle"
        })
        robot_id = robots.data["robots"][0]["robot_id"]

        # 创建任务1并分配
        task1 = await task_tools.handle("task_create_task", {
            "tenant_id": tenant_id,
            "zone_id": zone_id,
            "task_type": "routine"
        })
        await robot_tools.handle("robot_start_task", {
            "robot_id": robot_id,
            "task_id": task1.data["task"]["task_id"],
            "zone_id": zone_id,
            "task_type": "vacuum"
        })

        # 尝试再次分配任务给同一机器人 (应该失败)
        task2 = await task_tools.handle("task_create_task", {
            "tenant_id": tenant_id,
            "zone_id": zone_id,
            "task_type": "routine"
        })
        result = await robot_tools.handle("robot_start_task", {
            "robot_id": robot_id,
            "task_id": task2.data["task"]["task_id"],
            "zone_id": zone_id,
            "task_type": "vacuum"
        })
        assert not result.success
        assert "busy" in result.error.lower() or "working" in result.error.lower()

        # 尝试获取不存在的机器人
        result = await robot_tools.handle("robot_get_status", {
            "robot_id": "non_existent_robot"
        })
        assert not result.success

        # 尝试获取不存在的建筑
        result = await space_tools.handle("space_get_building", {
            "building_id": "non_existent_building"
        })
        assert not result.success

    @pytest.mark.asyncio
    async def test_scenario_5_batch_operations(
        self, space_tools, task_tools, robot_tools, tenant_id
    ):
        """
        场景5: 批量操作

        1. 批量获取机器人状态
        2. 批量创建任务
        3. 验证数据一致性
        """
        # 获取所有机器人
        robots = await robot_tools.handle("robot_list_robots", {
            "tenant_id": tenant_id
        })
        robot_ids = [r["robot_id"] for r in robots.data["robots"][:3]]

        # 批量获取状态
        batch_result = await robot_tools.handle("robot_batch_get_status", {
            "robot_ids": robot_ids
        })
        assert batch_result.success
        assert len(batch_result.data["statuses"]) == len(robot_ids)

        # 获取区域
        buildings = await space_tools.handle("space_list_buildings", {
            "tenant_id": tenant_id
        })
        building_id = buildings.data["buildings"][0]["id"]

        floors = await space_tools.handle("space_list_floors", {
            "building_id": building_id
        })
        floor_id = floors.data["floors"][0]["id"]

        zones = await space_tools.handle("space_list_zones", {
            "floor_id": floor_id
        })
        zone_ids = [z["id"] for z in zones.data["zones"]]

        # 创建计划覆盖第一个区域
        schedule_result = await task_tools.handle("task_create_schedule", {
            "tenant_id": tenant_id,
            "zone_id": zone_ids[0] if zone_ids else "zone_001",
            "task_type": "routine",
            "frequency": "daily",
            "time_slots": [{"start": "09:00", "end": "11:00"}],
            "priority": 5
        })
        assert schedule_result.success

        # 列出计划
        schedules = await task_tools.handle("task_list_schedules", {
            "tenant_id": tenant_id
        })
        assert schedules.success
        assert len(schedules.data["schedules"]) > 0

    @pytest.mark.asyncio
    async def test_scenario_6_cross_module_data_consistency(
        self, space_tools, task_tools, robot_tools, tenant_id
    ):
        """
        场景6: 跨模块数据一致性

        验证空间、任务、机器人三个模块的数据引用一致
        """
        # 获取空间数据
        buildings = await space_tools.handle("space_list_buildings", {
            "tenant_id": tenant_id
        })
        building = buildings.data["buildings"][0]

        floors = await space_tools.handle("space_list_floors", {
            "building_id": building["id"]
        })
        floor = floors.data["floors"][0]

        zones = await space_tools.handle("space_list_zones", {
            "floor_id": floor["id"]
        })
        zone = zones.data["zones"][0]

        # 获取机器人数据
        robots = await robot_tools.handle("robot_list_robots", {
            "tenant_id": tenant_id
        })
        robot = robots.data["robots"][0]

        # 创建任务引用空间和机器人
        task_result = await task_tools.handle("task_create_task", {
            "tenant_id": tenant_id,
            "zone_id": zone["id"],
            "task_type": "routine",
            "priority": 5
        })
        assert task_result.success
        task_id = task_result.data["task"]["task_id"]

        # 获取任务详情
        task_detail = await task_tools.handle("task_get_task", {
            "task_id": task_id
        })
        assert task_detail.success
        assert task_detail.data["task"]["zone_id"] == zone["id"]

        # 分配机器人
        if robot["status"] == "idle":
            start_result = await robot_tools.handle("robot_start_task", {
                "robot_id": robot["robot_id"],
                "task_id": task_id,
                "zone_id": zone["id"],
                "task_type": "vacuum"
            })
            assert start_result.success

            # 更新任务状态: pending -> assigned (需要遵循状态机)
            assign_result = await task_tools.handle("task_update_status", {
                "task_id": task_id,
                "status": "assigned",
                "robot_id": robot["robot_id"]
            })
            assert assign_result.success

            # 再次获取任务，验证机器人ID已记录
            task_detail = await task_tools.handle("task_get_task", {
                "task_id": task_id
            })
            assert task_detail.data["task"]["assigned_robot_id"] == robot["robot_id"]

            # 继续更新状态: assigned -> in_progress
            update_result = await task_tools.handle("task_update_status", {
                "task_id": task_id,
                "status": "in_progress"
            })
            assert update_result.success


class TestMS1PerformanceBaseline:
    """MS1 性能基准测试"""

    @pytest.fixture
    def tenant_id(self):
        return "tenant_001"

    @pytest.fixture
    def space_tools(self, tenant_id):
        storage = SpaceStorage()
        tools = SpaceManagerTools(storage)
        return SpaceToolsWrapper(tools)

    @pytest.fixture
    def task_tools(self):
        storage = InMemoryTaskStorage()
        return TaskTools(storage)

    @pytest.fixture
    def robot_tools(self, tenant_id):
        storage = InMemoryRobotStorage()
        client = MockGaoxianClient(storage)
        return RobotTools(client, storage)

    @pytest.mark.asyncio
    async def test_concurrent_operations(
        self, space_tools, task_tools, robot_tools, tenant_id
    ):
        """测试并发操作性能"""
        import time

        # 获取基础数据
        buildings = await space_tools.handle("space_list_buildings", {
            "tenant_id": tenant_id
        })
        building_id = buildings.data["buildings"][0]["id"]

        floors = await space_tools.handle("space_list_floors", {
            "building_id": building_id
        })
        floor_id = floors.data["floors"][0]["id"]

        zones = await space_tools.handle("space_list_zones", {
            "floor_id": floor_id
        })
        zone_id = zones.data["zones"][0]["id"]

        # 并发创建10个任务
        start_time = time.time()

        tasks = []
        for i in range(10):
            tasks.append(
                task_tools.handle("task_create_task", {
                    "tenant_id": tenant_id,
                    "zone_id": zone_id,
                    "task_type": "routine",
                    "priority": 5
                })
            )

        results = await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

        # 验证所有任务创建成功
        assert all(r.success for r in results)

        # 性能基准: 10个并发操作应在2秒内完成
        assert elapsed < 2.0, f"并发操作耗时 {elapsed:.2f}s 超过2s基准"

    @pytest.mark.asyncio
    async def test_query_performance(
        self, space_tools, task_tools, robot_tools, tenant_id
    ):
        """测试查询性能"""
        import time

        # 预先创建一些数据
        buildings = await space_tools.handle("space_list_buildings", {
            "tenant_id": tenant_id
        })
        building_id = buildings.data["buildings"][0]["id"]

        floors = await space_tools.handle("space_list_floors", {
            "building_id": building_id
        })
        floor_id = floors.data["floors"][0]["id"]

        zones = await space_tools.handle("space_list_zones", {
            "floor_id": floor_id
        })
        zone_id = zones.data["zones"][0]["id"]

        # 创建50个任务
        for i in range(50):
            await task_tools.handle("task_create_task", {
                "tenant_id": tenant_id,
                "zone_id": zone_id,
                "task_type": "routine"
            })

        # 测试列表查询性能
        start_time = time.time()

        for _ in range(100):
            await task_tools.handle("task_list_tasks", {
                "tenant_id": tenant_id,
                "limit": 20
            })

        elapsed = time.time() - start_time

        # 性能基准: 100次查询应在1秒内完成
        assert elapsed < 1.0, f"查询操作耗时 {elapsed:.2f}s 超过1s基准"
