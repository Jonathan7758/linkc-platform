"""
M1: 空间管理 MCP - HTTP Router
===============================
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from src.shared.auth import get_current_user, require_permission, TokenPayload, check_tenant_access
from src.mcp_servers.space_manager.storage import SpaceStorage
from src.mcp_servers.space_manager.tools import SpaceManagerTools

router = APIRouter()

# 共享存储实例
_storage = SpaceStorage()
_tools = SpaceManagerTools(_storage)


# ============================================================
# Building Endpoints
# ============================================================

@router.get("/buildings")
async def list_buildings(
    tenant_id: str = Query(..., description="租户ID"),
    current_user: TokenPayload = Depends(require_permission("space:read"))
):
    """
    获取楼宇列表

    权限: space:read
    """
    await check_tenant_access(current_user, tenant_id)
    result = await _tools.list_buildings(tenant_id)
    return result


@router.get("/buildings/{building_id}")
async def get_building(
    building_id: str,
    current_user: TokenPayload = Depends(require_permission("space:read"))
):
    """
    获取楼宇详情

    权限: space:read
    """
    result = await _tools.get_building(building_id)
    return result


# ============================================================
# Floor Endpoints
# ============================================================

@router.get("/buildings/{building_id}/floors")
async def list_floors(
    building_id: str,
    current_user: TokenPayload = Depends(require_permission("space:read"))
):
    """
    获取楼层列表

    权限: space:read
    """
    result = await _tools.list_floors(building_id)
    return result


@router.get("/floors/{floor_id}")
async def get_floor(
    floor_id: str,
    current_user: TokenPayload = Depends(require_permission("space:read"))
):
    """
    获取楼层详情

    权限: space:read
    """
    result = await _tools.get_floor(floor_id)
    return result


# ============================================================
# Zone Endpoints
# ============================================================

@router.get("/zones")
async def list_zones(
    floor_id: Optional[str] = Query(None, description="楼层ID"),
    building_id: Optional[str] = Query(None, description="楼宇ID"),
    zone_type: Optional[str] = Query(None, description="区域类型"),
    current_user: TokenPayload = Depends(require_permission("space:read"))
):
    """
    获取区域列表

    权限: space:read
    """
    result = await _tools.list_zones(
        floor_id=floor_id,
        building_id=building_id,
        zone_type=zone_type
    )
    return result


@router.get("/zones/{zone_id}")
async def get_zone(
    zone_id: str,
    current_user: TokenPayload = Depends(require_permission("space:read"))
):
    """
    获取区域详情

    权限: space:read
    """
    result = await _tools.get_zone(zone_id)
    return result


@router.put("/zones/{zone_id}")
async def update_zone(
    zone_id: str,
    name: Optional[str] = None,
    zone_type: Optional[str] = None,
    cleanable: Optional[bool] = None,
    clean_priority: Optional[int] = Query(None, ge=1, le=10),
    clean_frequency: Optional[str] = None,
    current_user: TokenPayload = Depends(require_permission("space:write"))
):
    """
    更新区域信息

    权限: space:write
    """
    result = await _tools.update_zone(
        zone_id=zone_id,
        name=name,
        zone_type=zone_type,
        cleanable=cleanable,
        clean_priority=clean_priority,
        clean_frequency=clean_frequency
    )
    return result


# ============================================================
# Point Endpoints
# ============================================================

@router.get("/points")
async def list_points(
    zone_id: Optional[str] = Query(None, description="区域ID"),
    floor_id: Optional[str] = Query(None, description="楼层ID"),
    point_type: Optional[str] = Query(None, description="点位类型"),
    current_user: TokenPayload = Depends(require_permission("space:read"))
):
    """
    获取点位列表

    权限: space:read
    """
    result = await _tools.list_points(
        zone_id=zone_id,
        floor_id=floor_id,
        point_type=point_type
    )
    return result
