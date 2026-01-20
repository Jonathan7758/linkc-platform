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


# ============================================================
# Building Tests
# ============================================================

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


# ============================================================
# Floor Tests
# ============================================================

@pytest.mark.asyncio
async def test_list_floors(tools):
    """测试列出楼层"""
    result = await tools.list_floors("building_001")
    assert result["success"] is True
    assert result["total"] >= 1


@pytest.mark.asyncio
async def test_get_floor(tools):
    """测试获取楼层详情"""
    result = await tools.get_floor("floor_001")
    assert result["success"] is True
    assert result["floor"]["name"] == "1F"
    assert result["floor"]["level"] == 1


@pytest.mark.asyncio
async def test_get_floor_not_found(tools):
    """测试获取不存在的楼层"""
    result = await tools.get_floor("nonexistent")
    assert result["success"] is False
    assert "not found" in result["error"]


# ============================================================
# Zone Tests
# ============================================================

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


@pytest.mark.asyncio
async def test_get_zone_not_found(tools):
    """测试获取不存在的区域"""
    result = await tools.get_zone("nonexistent")
    assert result["success"] is False
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_update_zone(tools):
    """测试更新区域"""
    result = await tools.update_zone(
        zone_id="zone_001",
        name="1F大堂(已更新)",
        clean_priority=10
    )
    assert result["success"] is True
    assert result["zone"]["name"] == "1F大堂(已更新)"
    assert result["zone"]["clean_priority"] == 10


@pytest.mark.asyncio
async def test_update_zone_not_found(tools):
    """测试更新不存在的区域"""
    result = await tools.update_zone(
        zone_id="nonexistent",
        name="test"
    )
    assert result["success"] is False
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_update_zone_invalid_priority(tools):
    """测试更新区域时优先级无效"""
    result = await tools.update_zone(
        zone_id="zone_001",
        clean_priority=15  # 超出1-10范围
    )
    assert result["success"] is False
    assert "VALIDATION_ERROR" in result.get("error_code", "")


@pytest.mark.asyncio
async def test_update_zone_invalid_frequency(tools):
    """测试更新区域时频率无效"""
    result = await tools.update_zone(
        zone_id="zone_001",
        clean_frequency="invalid"  # 不在有效列表中
    )
    assert result["success"] is False
    assert "VALIDATION_ERROR" in result.get("error_code", "")


# ============================================================
# Point Tests
# ============================================================

@pytest.mark.asyncio
async def test_list_points(tools):
    """测试列出点位"""
    result = await tools.list_points()
    assert result["success"] is True
    assert result["total"] >= 1


@pytest.mark.asyncio
async def test_list_points_by_zone(tools):
    """测试按区域筛选点位"""
    result = await tools.list_points(zone_id="zone_001")
    assert result["success"] is True
    for point in result["points"]:
        assert point["zone_id"] == "zone_001"


@pytest.mark.asyncio
async def test_list_points_by_floor(tools):
    """测试按楼层筛选点位"""
    result = await tools.list_points(floor_id="floor_001")
    assert result["success"] is True
    for point in result["points"]:
        assert point["floor_id"] == "floor_001"


@pytest.mark.asyncio
async def test_list_points_by_type(tools):
    """测试按类型筛选点位"""
    result = await tools.list_points(point_type="charging")
    assert result["success"] is True
    assert result["total"] >= 1
    for point in result["points"]:
        assert point["point_type"] == "charging"
