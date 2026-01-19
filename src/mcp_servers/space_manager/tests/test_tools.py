"""
M1: 空间管理 MCP Server - 测试
"""

import pytest
from src.mcp_servers.space_manager.storage import SpaceStorage
from src.mcp_servers.space_manager.tools import SpaceManagerTools


@pytest.fixture
def storage():
    return SpaceStorage()


@pytest.fixture
def tools(storage):
    return SpaceManagerTools(storage)


@pytest.mark.asyncio
async def test_list_buildings(tools):
    """测试列出楼宇"""
    result = await tools.list_buildings("tenant_001")
    assert result["success"] is True
    assert result["total"] >= 1
    assert len(result["buildings"]) == result["total"]


@pytest.mark.asyncio
async def test_get_building(tools):
    """测试获取楼宇详情"""
    result = await tools.get_building("building_001")
    assert result["success"] is True
    assert result["building"]["name"] == "港湾中心A座"


@pytest.mark.asyncio
async def test_get_building_not_found(tools):
    """测试获取不存在的楼宇"""
    result = await tools.get_building("nonexistent")
    assert result["success"] is False
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_list_floors(tools):
    """测试列出楼层"""
    result = await tools.list_floors("building_001")
    assert result["success"] is True
    assert result["total"] >= 1


@pytest.mark.asyncio
async def test_list_zones(tools):
    """测试列出区域"""
    result = await tools.list_zones(floor_id="floor_001")
    assert result["success"] is True
    assert result["total"] >= 1


@pytest.mark.asyncio
async def test_list_zones_by_type(tools):
    """测试按类型筛选区域"""
    result = await tools.list_zones(zone_type="lobby")
    assert result["success"] is True
    for zone in result["zones"]:
        assert zone["zone_type"] == "lobby"


@pytest.mark.asyncio
async def test_get_zone(tools):
    """测试获取区域详情"""
    result = await tools.get_zone("zone_001")
    assert result["success"] is True
    assert result["zone"]["name"] == "1F大堂"
