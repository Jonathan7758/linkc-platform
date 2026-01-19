"""
M3: 机器人控制 MCP Server - 测试
"""

import pytest
from src.mcp_servers.robot_control.storage import RobotStorage
from src.mcp_servers.robot_control.tools import RobotControlTools


@pytest.fixture
def storage():
    return RobotStorage()


@pytest.fixture
def tools(storage):
    return RobotControlTools(storage)


@pytest.mark.asyncio
async def test_list_robots(tools):
    """测试列出机器人"""
    result = await tools.list_robots(tenant_id="tenant_001")
    assert result["success"] is True
    assert result["total"] >= 1


@pytest.mark.asyncio
async def test_list_robots_by_status(tools):
    """测试按状态筛选机器人"""
    result = await tools.list_robots(tenant_id="tenant_001", status="idle")
    assert result["success"] is True
    for robot in result["robots"]:
        assert robot["status"] == "idle"


@pytest.mark.asyncio
async def test_get_robot_status(tools):
    """测试获取机器人状态"""
    result = await tools.get_robot_status("robot_001")
    assert result["success"] is True
    assert result["robot_id"] == "robot_001"
    assert "battery_level" in result


@pytest.mark.asyncio
async def test_start_cleaning(tools):
    """测试启动清洁"""
    result = await tools.start_cleaning(
        robot_id="robot_002",  # idle robot
        zone_id="zone_001",
        cleaning_mode="standard"
    )
    assert result["success"] is True
    assert result["task_started"] is True


@pytest.mark.asyncio
async def test_start_cleaning_busy_robot(tools):
    """测试启动已在工作的机器人"""
    result = await tools.start_cleaning(
        robot_id="robot_001",  # working robot
        zone_id="zone_001"
    )
    assert result["success"] is False
    assert "already working" in result["error"]


@pytest.mark.asyncio
async def test_stop_cleaning(tools, storage):
    """测试停止清洁"""
    # robot_001 is working
    result = await tools.stop_cleaning(robot_id="robot_001", reason="test")
    assert result["success"] is True
    assert result["stopped"] is True


@pytest.mark.asyncio
async def test_send_to_charger(tools):
    """测试发送去充电"""
    result = await tools.send_to_charger("robot_002")
    assert result["success"] is True


@pytest.mark.asyncio
async def test_get_available_robots(tools):
    """测试获取可用机器人"""
    result = await tools.get_available_robots(tenant_id="tenant_001", min_battery=20)
    assert result["success"] is True
    for robot in result["robots"]:
        assert robot["status"] == "idle"
        assert robot["battery_level"] >= 20
