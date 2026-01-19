"""
G1: 空间管理 API
================
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from src.mcp_servers.space_manager.storage import SpaceStorage
from src.mcp_servers.space_manager.tools import SpaceManagerTools

router = APIRouter(prefix="/spaces", tags=["spaces"])

# 初始化 MCP Server 工具
storage = SpaceStorage()
tools = SpaceManagerTools(storage)


@router.get("/buildings")
async def list_buildings(tenant_id: str = Query(..., description="租户ID")):
    """列出所有楼宇"""
    result = await tools.list_buildings(tenant_id)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/buildings/{building_id}")
async def get_building(building_id: str):
    """获取楼宇详情"""
    result = await tools.get_building(building_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.get("/buildings/{building_id}/floors")
async def list_floors(building_id: str):
    """列出楼宇的所有楼层"""
    result = await tools.list_floors(building_id)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/zones")
async def list_zones(
    floor_id: Optional[str] = Query(None, description="楼层ID"),
    building_id: Optional[str] = Query(None, description="楼宇ID"),
    zone_type: Optional[str] = Query(None, description="区域类型")
):
    """列出区域"""
    result = await tools.list_zones(
        floor_id=floor_id,
        building_id=building_id,
        zone_type=zone_type
    )
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/zones/{zone_id}")
async def get_zone(zone_id: str):
    """获取区域详情"""
    result = await tools.get_zone(zone_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result
