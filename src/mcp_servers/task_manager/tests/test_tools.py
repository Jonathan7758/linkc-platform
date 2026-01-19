"""
M2: 任务管理 MCP Server - 测试
"""

import pytest
from src.mcp_servers.task_manager.storage import TaskStorage
from src.mcp_servers.task_manager.tools import TaskManagerTools


@pytest.fixture
def storage():
    return TaskStorage()


@pytest.fixture
def tools(storage):
    return TaskManagerTools(storage)


@pytest.mark.asyncio
async def test_create_task(tools):
    """测试创建任务"""
    result = await tools.create_task(
        tenant_id="tenant_001",
        name="测试任务",
        zone_id="zone_001",
        priority="high"
    )
    assert result["success"] is True
    assert result["task"]["name"] == "测试任务"
    assert result["task"]["priority"] == "high"
    assert result["task"]["status"] == "pending"


@pytest.mark.asyncio
async def test_list_tasks(tools):
    """测试列出任务"""
    result = await tools.list_tasks(tenant_id="tenant_001")
    assert result["success"] is True
    assert result["total"] >= 1


@pytest.mark.asyncio
async def test_list_tasks_by_status(tools):
    """测试按状态筛选任务"""
    result = await tools.list_tasks(tenant_id="tenant_001", status="pending")
    assert result["success"] is True
    for task in result["tasks"]:
        assert task["status"] == "pending"


@pytest.mark.asyncio
async def test_get_task(tools):
    """测试获取任务详情"""
    result = await tools.get_task("task_001")
    assert result["success"] is True
    assert result["task"]["id"] == "task_001"


@pytest.mark.asyncio
async def test_assign_task(tools):
    """测试分配任务"""
    result = await tools.assign_task(
        task_id="task_001",
        robot_id="robot_001",
        assigned_by="agent_scheduler"
    )
    assert result["success"] is True
    assert result["robot_id"] == "robot_001"


@pytest.mark.asyncio
async def test_update_task_status(tools):
    """测试更新任务状态"""
    result = await tools.update_task_status(
        task_id="task_002",
        status="completed",
        completion_rate=100.0
    )
    assert result["success"] is True
    assert result["task"]["status"] == "completed"
    assert result["task"]["completion_rate"] == 100.0


@pytest.mark.asyncio
async def test_get_pending_tasks(tools):
    """测试获取待分配任务"""
    result = await tools.get_pending_tasks("tenant_001")
    assert result["success"] is True
    for task in result["tasks"]:
        assert task["status"] == "pending"
