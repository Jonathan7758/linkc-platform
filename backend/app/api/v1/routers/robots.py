"""
G3: 机器人管理 API
==================
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
from pydantic import BaseModel

from src.mcp_servers.robot_control.storage import RobotStorage
from src.mcp_servers.robot_control.tools import RobotControlTools

router = APIRouter(prefix="/robots", tags=["robots"])

storage = RobotStorage()
tools = RobotControlTools(storage)


class StartCleaningRequest(BaseModel):
    """启动清洁请求"""
    zone_id: str
    cleaning_mode: str = "standard"


class StopCleaningRequest(BaseModel):
    """停止清洁请求"""
    reason: Optional[str] = None


@router.get("")
async def list_robots(
    tenant_id: str = Query(...),
    building_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """列出机器人"""
    result = await tools.list_robots(
        tenant_id=tenant_id,
        building_id=building_id,
        status=status
    )
    return result


@router.get("/available")
async def get_available_robots(
    tenant_id: str = Query(...),
    min_battery: int = Query(20, ge=0, le=100)
):
    """获取可用的机器人"""
    result = await tools.get_available_robots(
        tenant_id=tenant_id,
        min_battery=min_battery
    )
    return result


@router.get("/{robot_id}")
async def get_robot_status(robot_id: str):
    """获取机器人状态"""
    result = await tools.get_robot_status(robot_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.post("/{robot_id}/start-cleaning")
async def start_cleaning(robot_id: str, request: StartCleaningRequest = Body(...)):
    """启动机器人清洁"""
    result = await tools.start_cleaning(
        robot_id=robot_id,
        zone_id=request.zone_id,
        cleaning_mode=request.cleaning_mode
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{robot_id}/stop-cleaning")
async def stop_cleaning(robot_id: str, request: StopCleaningRequest = Body(default=None)):
    """停止机器人清洁"""
    reason = request.reason if request else None
    result = await tools.stop_cleaning(robot_id=robot_id, reason=reason)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{robot_id}/charge")
async def send_to_charger(robot_id: str):
    """发送机器人去充电"""
    result = await tools.send_to_charger(robot_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
