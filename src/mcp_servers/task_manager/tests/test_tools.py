"""
M2: 任务管理 MCP Server - 单元测试
==================================
"""

import pytest
import asyncio
from datetime import datetime, date, timedelta

# 直接导入模块（测试时需要调整路径）
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage import (
    InMemoryTaskStorage,
    CleaningSchedule,
    CleaningTask,
    TaskType,
    TaskStatus,
    CleaningFrequency,
    TimeSlot
)
from tools import TaskTools, ToolResult, VALID_TRANSITIONS


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def storage():
    """创建新的存储实例"""
    return InMemoryTaskStorage()


@pytest.fixture
def tools(storage):
    """创建工具实例"""
    return TaskTools(storage)


@pytest.fixture
def tenant_id():
    return "tenant_001"


# ============================================================
# Storage 测试
# ============================================================

class TestStorage:
    """存储层测试"""

    @pytest.mark.asyncio
    async def test_init_sample_data(self, storage):
        """测试初始化示例数据"""
        schedules = await storage.list_schedules("tenant_001")
        assert len(schedules) == 2

        tasks, total = await storage.list_tasks("tenant_001")
        assert total == 3

    @pytest.mark.asyncio
    async def test_save_and_get_schedule(self, storage):
        """测试保存和获取排程"""
        schedule = CleaningSchedule(
            schedule_id="test_schedule",
            tenant_id="test_tenant",
            zone_id="zone_test",
            zone_name="测试区域",
            task_type=TaskType.ROUTINE,
            frequency=CleaningFrequency.DAILY,
            time_slots=[TimeSlot(start="09:00", end="11:00")],
            priority=3,
            estimated_duration=45,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        await storage.save_schedule(schedule)
        retrieved = await storage.get_schedule("test_schedule")

        assert retrieved is not None
        assert retrieved.schedule_id == "test_schedule"
        assert retrieved.zone_name == "测试区域"

    @pytest.mark.asyncio
    async def test_save_and_get_task(self, storage):
        """测试保存和获取任务"""
        task = CleaningTask(
            task_id="test_task",
            tenant_id="test_tenant",
            zone_id="zone_test",
            zone_name="测试区域",
            task_type=TaskType.SPOT,
            status=TaskStatus.PENDING,
            priority=2,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        await storage.save_task(task)
        retrieved = await storage.get_task("test_task")

        assert retrieved is not None
        assert retrieved.task_id == "test_task"
        assert retrieved.status == TaskStatus.PENDING

    @pytest.mark.asyncio
    async def test_task_idempotency(self, storage):
        """测试任务生成幂等性"""
        today = date.today()

        # 第一次标记
        assert not await storage.is_task_generated("schedule_001", today)
        await storage.mark_task_generated("schedule_001", today)

        # 第二次检查应该返回True
        assert await storage.is_task_generated("schedule_001", today)


# ============================================================
# Tools 测试
# ============================================================

class TestTools:
    """工具层测试"""

    @pytest.mark.asyncio
    async def test_list_schedules(self, tools, tenant_id):
        """测试获取排程列表"""
        result = await tools.handle("task_list_schedules", {
            "tenant_id": tenant_id
        })

        assert result.success
        assert "schedules" in result.data
        assert len(result.data["schedules"]) == 2

    @pytest.mark.asyncio
    async def test_get_schedule(self, tools):
        """测试获取单个排程"""
        result = await tools.handle("task_get_schedule", {
            "schedule_id": "schedule_001"
        })

        assert result.success
        assert result.data["schedule"]["schedule_id"] == "schedule_001"

    @pytest.mark.asyncio
    async def test_get_schedule_not_found(self, tools):
        """测试获取不存在的排程"""
        result = await tools.handle("task_get_schedule", {
            "schedule_id": "nonexistent"
        })

        assert not result.success
        assert result.error_code == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_create_schedule(self, tools, tenant_id):
        """测试创建排程"""
        result = await tools.handle("task_create_schedule", {
            "tenant_id": tenant_id,
            "zone_id": "zone_new",
            "zone_name": "新区域",
            "task_type": "routine",
            "frequency": "weekly",
            "time_slots": [{"start": "10:00", "end": "12:00", "days": [1, 3, 5]}],
            "priority": 4
        })

        assert result.success
        assert result.data["schedule"]["zone_name"] == "新区域"
        assert result.data["schedule"]["priority"] == 4

    @pytest.mark.asyncio
    async def test_create_task(self, tools, tenant_id):
        """测试创建任务"""
        result = await tools.handle("task_create_task", {
            "tenant_id": tenant_id,
            "zone_id": "zone_test",
            "zone_name": "测试区域",
            "task_type": "spot",
            "priority": 3
        })

        assert result.success
        assert result.data["task"]["task_type"] == "spot"
        assert result.data["task"]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_emergency_task_priority(self, tools, tenant_id):
        """测试紧急任务自动设置priority=1"""
        result = await tools.handle("task_create_task", {
            "tenant_id": tenant_id,
            "zone_id": "zone_test",
            "task_type": "emergency",
            "priority": 5  # 应该被忽略
        })

        assert result.success
        assert result.data["task"]["priority"] == 1  # 自动设为1

    @pytest.mark.asyncio
    async def test_update_status_valid_transition(self, tools):
        """测试有效的状态转换"""
        # pending → assigned
        result = await tools.handle("task_update_status", {
            "task_id": "task_001",
            "status": "assigned",
            "robot_id": "robot_001",
            "robot_name": "测试机器人"
        })

        assert result.success
        assert result.data["task"]["status"] == "assigned"
        assert result.data["task"]["assigned_robot_id"] == "robot_001"

    @pytest.mark.asyncio
    async def test_update_status_invalid_transition(self, tools):
        """测试无效的状态转换"""
        # pending → completed (跳过中间状态)
        result = await tools.handle("task_update_status", {
            "task_id": "task_001",
            "status": "completed",
            "completion_rate": 100
        })

        assert not result.success
        assert result.error_code == "INVALID_STATE"

    @pytest.mark.asyncio
    async def test_complete_requires_completion_rate(self, tools):
        """测试完成任务需要completion_rate"""
        # 先将 task_002 (in_progress) 完成
        result = await tools.handle("task_update_status", {
            "task_id": "task_002",
            "status": "completed"
            # 缺少 completion_rate
        })

        assert not result.success
        assert "completion_rate" in result.error

    @pytest.mark.asyncio
    async def test_complete_with_completion_rate(self, tools):
        """测试正确完成任务"""
        result = await tools.handle("task_update_status", {
            "task_id": "task_002",
            "status": "completed",
            "completion_rate": 95.5
        })

        assert result.success
        assert result.data["task"]["completion_rate"] == 95.5

    @pytest.mark.asyncio
    async def test_failed_requires_reason(self, tools, storage):
        """测试失败任务需要failure_reason"""
        # 创建一个 in_progress 的任务
        task = CleaningTask(
            task_id="task_fail_test",
            tenant_id="tenant_001",
            zone_id="zone_test",
            task_type=TaskType.ROUTINE,
            status=TaskStatus.IN_PROGRESS,
            priority=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await storage.save_task(task)

        # 尝试无 reason 失败
        result = await tools.handle("task_update_status", {
            "task_id": "task_fail_test",
            "status": "failed"
        })

        assert not result.success
        assert "failure_reason" in result.error

    @pytest.mark.asyncio
    async def test_get_pending_tasks(self, tools, tenant_id):
        """测试获取待执行任务"""
        result = await tools.handle("task_get_pending_tasks", {
            "tenant_id": tenant_id
        })

        assert result.success
        # 按优先级排序，priority=1的应该在前面
        tasks = result.data["tasks"]
        if len(tasks) > 1:
            assert tasks[0]["priority"] <= tasks[1]["priority"]

    @pytest.mark.asyncio
    async def test_generate_daily_tasks(self, tools, tenant_id):
        """测试生成每日任务"""
        today = date.today().isoformat()

        result = await tools.handle("task_generate_daily_tasks", {
            "tenant_id": tenant_id,
            "date": today
        })

        assert result.success
        assert "generated_count" in result.data

        # 再次调用应该幂等，skipped_count增加
        result2 = await tools.handle("task_generate_daily_tasks", {
            "tenant_id": tenant_id,
            "date": today
        })

        assert result2.success
        assert result2.data["skipped_count"] >= result.data["generated_count"]

    @pytest.mark.asyncio
    async def test_unknown_tool(self, tools):
        """测试未知工具"""
        result = await tools.handle("unknown_tool", {})

        assert not result.success
        assert result.error_code == "NOT_FOUND"


# ============================================================
# 状态机测试
# ============================================================

class TestStateMachine:
    """状态机规则测试"""

    def test_valid_transitions_defined(self):
        """测试状态转换规则已定义"""
        assert TaskStatus.PENDING in VALID_TRANSITIONS
        assert TaskStatus.ASSIGNED in VALID_TRANSITIONS
        assert TaskStatus.IN_PROGRESS in VALID_TRANSITIONS
        assert TaskStatus.COMPLETED in VALID_TRANSITIONS
        assert TaskStatus.FAILED in VALID_TRANSITIONS
        assert TaskStatus.CANCELLED in VALID_TRANSITIONS

    def test_terminal_states_no_transitions(self):
        """测试终态没有后续状态"""
        assert len(VALID_TRANSITIONS[TaskStatus.COMPLETED]) == 0
        assert len(VALID_TRANSITIONS[TaskStatus.FAILED]) == 0
        assert len(VALID_TRANSITIONS[TaskStatus.CANCELLED]) == 0

    def test_pending_valid_transitions(self):
        """测试 pending 的有效转换"""
        valid = VALID_TRANSITIONS[TaskStatus.PENDING]
        assert TaskStatus.ASSIGNED in valid
        assert TaskStatus.CANCELLED in valid
        assert TaskStatus.COMPLETED not in valid


# ============================================================
# 运行测试
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
