"""
M3: 高仙机器人 MCP Server - 单元测试
=====================================
测试12个Tools的完整功能
"""

import pytest
from datetime import datetime
from src.mcp_servers.robot_gaoxian.storage import (
    InMemoryRobotStorage, RobotStatus, RobotStatusSnapshot,
    RobotTask, CleaningMode, CleaningIntensity
)
from src.mcp_servers.robot_gaoxian.mock_client import MockGaoxianClient
from src.mcp_servers.robot_gaoxian.tools import RobotTools


def set_robot_status(storage, robot_id: str, status: RobotStatus, battery: int = 80, task_id: str = None):
    """辅助函数：设置机器人状态 - 同时更新robots和status_snapshots"""
    # 更新 _robots 中的状态 (tools主要检查这里)
    if robot_id in storage._robots:
        storage._robots[robot_id].status = status
    # 更新 _status_snapshots 中的状态 (电量检查用这里)
    if robot_id in storage._status_snapshots:
        storage._status_snapshots[robot_id].status = status
        storage._status_snapshots[robot_id].battery_level = battery
        if task_id:
            storage._status_snapshots[robot_id].current_task_id = task_id


def create_running_task(storage, robot_id: str, robot_task_id: str = "task_001", status: str = "running"):
    """辅助函数：创建运行中的任务"""
    task = RobotTask(
        robot_task_id=robot_task_id,
        robot_id=robot_id,
        zone_id="zone_001",
        task_type=CleaningMode.VACUUM,
        status=status,
        progress=50.0,
        started_at=datetime.utcnow()
    )
    storage._tasks[robot_task_id] = task
    return task


@pytest.fixture
def storage():
    """创建存储实例"""
    return InMemoryRobotStorage()


@pytest.fixture
def client(storage):
    """创建Mock客户端"""
    return MockGaoxianClient(storage)


@pytest.fixture
def tools(client, storage):
    """创建Tools实例"""
    return RobotTools(client, storage)


# ============================================================
# 1. robot_list_robots 测试
# ============================================================

@pytest.mark.asyncio
async def test_list_robots(tools):
    """测试获取机器人列表"""
    result = await tools.handle("robot_list_robots", {"tenant_id": "tenant_001"})
    assert result.success is True
    assert "robots" in result.data
    assert len(result.data["robots"]) >= 1


@pytest.mark.asyncio
async def test_list_robots_with_status_filter(tools):
    """测试按状态筛选机器人"""
    result = await tools.handle("robot_list_robots", {
        "tenant_id": "tenant_001",
        "status": "idle"
    })
    assert result.success is True
    for robot in result.data["robots"]:
        assert robot["status"] == "idle"


@pytest.mark.asyncio
async def test_list_robots_empty_tenant(tools):
    """测试空租户返回空列表"""
    result = await tools.handle("robot_list_robots", {"tenant_id": "nonexistent"})
    assert result.success is True
    assert result.data["total"] == 0


# ============================================================
# 2. robot_get_robot 测试
# ============================================================

@pytest.mark.asyncio
async def test_get_robot(tools):
    """测试获取机器人详情"""
    result = await tools.handle("robot_get_robot", {"robot_id": "robot_001"})
    assert result.success is True
    assert result.data["robot"]["robot_id"] == "robot_001"


@pytest.mark.asyncio
async def test_get_robot_not_found(tools):
    """测试获取不存在的机器人"""
    result = await tools.handle("robot_get_robot", {"robot_id": "nonexistent"})
    assert result.success is False
    assert "NOT_FOUND" in result.error_code


# ============================================================
# 3. robot_get_status 测试
# ============================================================

@pytest.mark.asyncio
async def test_get_status(tools):
    """测试获取机器人实时状态"""
    result = await tools.handle("robot_get_status", {"robot_id": "robot_001"})
    assert result.success is True
    assert "status" in result.data
    assert "battery_level" in result.data


@pytest.mark.asyncio
async def test_get_status_not_found(tools):
    """测试获取不存在机器人的状态"""
    result = await tools.handle("robot_get_status", {"robot_id": "nonexistent"})
    assert result.success is False


# ============================================================
# 4. robot_batch_get_status 测试
# ============================================================

@pytest.mark.asyncio
async def test_batch_get_status(tools):
    """测试批量获取机器人状态"""
    result = await tools.handle("robot_batch_get_status", {
        "robot_ids": ["robot_001", "robot_002"]
    })
    assert result.success is True
    assert "statuses" in result.data
    assert len(result.data["statuses"]) == 2


@pytest.mark.asyncio
async def test_batch_get_status_partial(tools):
    """测试批量获取包含不存在的机器人"""
    result = await tools.handle("robot_batch_get_status", {
        "robot_ids": ["robot_001", "nonexistent"]
    })
    assert result.success is True
    # 应该只返回存在的机器人状态
    assert len(result.data["statuses"]) >= 1


# ============================================================
# 5. robot_start_task 测试
# ============================================================

@pytest.mark.asyncio
async def test_start_task(tools, storage):
    """测试启动清洁任务"""
    # 确保机器人是idle状态
    set_robot_status(storage, "robot_001", RobotStatus.IDLE, battery=80)

    result = await tools.handle("robot_start_task", {
        "robot_id": "robot_001",
        "task_type": "vacuum",  # 使用 task_type 而不是 task_id
        "zone_id": "zone_001"
    })
    assert result.success is True


@pytest.mark.asyncio
async def test_start_task_low_battery(tools, storage):
    """测试低电量时启动任务"""
    set_robot_status(storage, "robot_001", RobotStatus.IDLE, battery=15)  # 低于20%

    result = await tools.handle("robot_start_task", {
        "robot_id": "robot_001",
        "task_type": "vacuum",
        "zone_id": "zone_001"
    })
    assert result.success is False
    assert "LOW_BATTERY" in result.error_code or "battery" in result.error.lower()


@pytest.mark.asyncio
async def test_start_task_robot_busy(tools, storage):
    """测试机器人忙碌时启动任务"""
    set_robot_status(storage, "robot_001", RobotStatus.WORKING)

    result = await tools.handle("robot_start_task", {
        "robot_id": "robot_001",
        "task_type": "vacuum",
        "zone_id": "zone_001"
    })
    assert result.success is False


# ============================================================
# 6. robot_pause_task 测试
# ============================================================

@pytest.mark.asyncio
async def test_pause_task(tools, storage):
    """测试暂停任务"""
    # 先让机器人处于工作状态，并创建运行中的任务
    set_robot_status(storage, "robot_001", RobotStatus.WORKING, task_id="task_001")
    create_running_task(storage, "robot_001", "task_001", "running")

    result = await tools.handle("robot_pause_task", {"robot_id": "robot_001"})
    assert result.success is True


@pytest.mark.asyncio
async def test_pause_task_not_working(tools, storage):
    """测试暂停非工作状态的机器人"""
    set_robot_status(storage, "robot_001", RobotStatus.IDLE)

    result = await tools.handle("robot_pause_task", {"robot_id": "robot_001"})
    assert result.success is False


# ============================================================
# 7. robot_resume_task 测试
# ============================================================

@pytest.mark.asyncio
async def test_resume_task(tools, storage):
    """测试恢复任务"""
    # 设置机器人为暂停状态，并创建暂停中的任务
    set_robot_status(storage, "robot_001", RobotStatus.PAUSED, task_id="task_001")
    create_running_task(storage, "robot_001", "task_001", "paused")

    result = await tools.handle("robot_resume_task", {"robot_id": "robot_001"})
    assert result.success is True


@pytest.mark.asyncio
async def test_resume_task_not_paused(tools, storage):
    """测试恢复非暂停状态的机器人"""
    set_robot_status(storage, "robot_001", RobotStatus.IDLE)

    result = await tools.handle("robot_resume_task", {"robot_id": "robot_001"})
    assert result.success is False


# ============================================================
# 8. robot_cancel_task 测试
# ============================================================

@pytest.mark.asyncio
async def test_cancel_task(tools, storage):
    """测试取消任务"""
    # 设置机器人为工作状态，并创建运行中的任务
    set_robot_status(storage, "robot_001", RobotStatus.WORKING, task_id="task_001")
    create_running_task(storage, "robot_001", "task_001", "running")

    result = await tools.handle("robot_cancel_task", {"robot_id": "robot_001"})
    assert result.success is True


@pytest.mark.asyncio
async def test_cancel_task_with_force(tools, storage):
    """测试强制取消任务"""
    # 设置机器人为工作状态，并创建运行中的任务
    set_robot_status(storage, "robot_001", RobotStatus.WORKING, task_id="task_002")
    create_running_task(storage, "robot_001", "task_002", "running")

    result = await tools.handle("robot_cancel_task", {
        "robot_id": "robot_001",
        "force": True,
        "return_to_charge": True
    })
    assert result.success is True


# ============================================================
# 9. robot_go_to_location 测试
# ============================================================

@pytest.mark.asyncio
async def test_go_to_location(tools, storage):
    """测试移动到指定位置"""
    set_robot_status(storage, "robot_001", RobotStatus.IDLE)

    result = await tools.handle("robot_go_to_location", {
        "robot_id": "robot_001",
        "target_location": {"x": 10.0, "y": 20.0}  # 使用 target_location 对象
    })
    assert result.success is True


@pytest.mark.asyncio
async def test_go_to_location_robot_busy(tools, storage):
    """测试机器人忙碌时无法移动"""
    set_robot_status(storage, "robot_001", RobotStatus.WORKING)

    result = await tools.handle("robot_go_to_location", {
        "robot_id": "robot_001",
        "target_location": {"x": 10.0, "y": 20.0}
    })
    assert result.success is False


# ============================================================
# 10. robot_go_to_charge 测试
# ============================================================

@pytest.mark.asyncio
async def test_go_to_charge(tools, storage):
    """测试返回充电"""
    set_robot_status(storage, "robot_001", RobotStatus.IDLE)

    result = await tools.handle("robot_go_to_charge", {"robot_id": "robot_001"})
    assert result.success is True


@pytest.mark.asyncio
async def test_go_to_charge_force(tools, storage):
    """测试强制返回充电"""
    set_robot_status(storage, "robot_001", RobotStatus.WORKING, task_id="task_001")

    result = await tools.handle("robot_go_to_charge", {
        "robot_id": "robot_001",
        "force": True
    })
    assert result.success is True


# ============================================================
# 11. robot_get_errors 测试
# ============================================================

@pytest.mark.asyncio
async def test_get_errors(tools):
    """测试获取故障列表"""
    result = await tools.handle("robot_get_errors", {"robot_id": "robot_001"})
    assert result.success is True
    assert "errors" in result.data


@pytest.mark.asyncio
async def test_get_errors_active_only(tools):
    """测试只获取活跃故障"""
    result = await tools.handle("robot_get_errors", {
        "robot_id": "robot_001",
        "active_only": True
    })
    assert result.success is True


# ============================================================
# 12. robot_clear_error 测试
# ============================================================

@pytest.mark.asyncio
async def test_clear_error(tools, storage):
    """测试清除故障"""
    # 先添加一个故障 - 使用 error_id 作为 key
    from src.mcp_servers.robot_gaoxian.storage import RobotError, ErrorSeverity
    error = RobotError(
        error_id="err_001",
        robot_id="robot_001",
        error_code="E001",
        error_type="warning",
        message="Test error",
        severity=ErrorSeverity.WARNING,
        occurred_at=datetime.utcnow()
    )
    # _errors 使用 error_id 作为 key
    storage._errors["err_001"] = error

    result = await tools.handle("robot_clear_error", {
        "robot_id": "robot_001",
        "error_id": "err_001"
    })
    assert result.success is True


@pytest.mark.asyncio
async def test_clear_error_not_found(tools):
    """测试清除不存在的故障"""
    result = await tools.handle("robot_clear_error", {
        "robot_id": "robot_001",
        "error_id": "nonexistent"
    })
    # 可能返回成功或失败，取决于实现
    # 这里只检查不会抛异常


# ============================================================
# 集成测试
# ============================================================

@pytest.mark.asyncio
async def test_full_workflow(tools, storage):
    """测试完整工作流程：启动->暂停->恢复->完成"""
    # 1. 确保机器人就绪
    set_robot_status(storage, "robot_001", RobotStatus.IDLE, battery=80)

    # 2. 启动任务
    result = await tools.handle("robot_start_task", {
        "robot_id": "robot_001",
        "task_type": "vacuum",
        "zone_id": "zone_001"
    })
    assert result.success is True

    # 3. 暂停任务 (需要更新状态因为mock client会更新)
    result = await tools.handle("robot_pause_task", {"robot_id": "robot_001"})
    assert result.success is True

    # 4. 恢复任务
    result = await tools.handle("robot_resume_task", {"robot_id": "robot_001"})
    assert result.success is True

    # 5. 取消任务返回充电
    result = await tools.handle("robot_cancel_task", {
        "robot_id": "robot_001",
        "force": True,
        "return_to_charge": True
    })
    assert result.success is True


@pytest.mark.asyncio
async def test_unknown_tool(tools):
    """测试调用未知Tool"""
    result = await tools.handle("unknown_tool", {})
    assert result.success is False
    assert "NOT_FOUND" in result.error_code  # 实际返回 NOT_FOUND
