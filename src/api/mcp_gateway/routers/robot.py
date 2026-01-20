"""
M3: 高仙机器人 MCP - HTTP Router
=================================
"""

from fastapi import APIRouter, Depends, Query, Body
from typing import Optional, List
from pydantic import BaseModel

from src.shared.auth import get_current_user, require_permission, TokenPayload, check_tenant_access
from src.mcp_servers.robot_gaoxian.storage import InMemoryRobotStorage
from src.mcp_servers.robot_gaoxian.mock_client import MockGaoxianClient
from src.mcp_servers.robot_gaoxian.tools import RobotTools

router = APIRouter()

# 共享存储实例
_storage = InMemoryRobotStorage()
_client = MockGaoxianClient(_storage)
_tools = RobotTools(_client, _storage)


# ============================================================
# Request Models
# ============================================================

class StartTaskRequest(BaseModel):
    """启动任务请求"""
    task_type: str  # vacuum/mop/vacuum_mop
    zone_id: str
    task_id: Optional[str] = None
    cleaning_mode: Optional[str] = None  # eco/standard/deep


class GoToLocationRequest(BaseModel):
    """移动到位置请求"""
    target_location: dict  # {"x": float, "y": float}


class ClearErrorRequest(BaseModel):
    """清除故障请求"""
    error_id: str


# ============================================================
# Robot List/Get Endpoints
# ============================================================

@router.get("/robots")
async def list_robots(
    tenant_id: str = Query(..., description="租户ID"),
    building_id: Optional[str] = Query(None, description="楼宇ID"),
    status: Optional[str] = Query(None, description="状态过滤"),
    robot_type: Optional[str] = Query(None, description="机器人类型"),
    current_user: TokenPayload = Depends(require_permission("robot:read"))
):
    """
    获取机器人列表

    权限: robot:read
    """
    await check_tenant_access(current_user, tenant_id)
    result = await _tools.handle("robot_list_robots", {
        "tenant_id": tenant_id,
        "building_id": building_id,
        "status": status,
        "robot_type": robot_type
    })
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


@router.get("/robots/{robot_id}")
async def get_robot(
    robot_id: str,
    current_user: TokenPayload = Depends(require_permission("robot:read"))
):
    """
    获取机器人详情

    权限: robot:read
    """
    result = await _tools.handle("robot_get_robot", {"robot_id": robot_id})
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


# ============================================================
# Robot Status Endpoints
# ============================================================

@router.get("/robots/{robot_id}/status")
async def get_robot_status(
    robot_id: str,
    current_user: TokenPayload = Depends(require_permission("robot:read"))
):
    """
    获取机器人实时状态

    权限: robot:read
    """
    result = await _tools.handle("robot_get_status", {"robot_id": robot_id})
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


@router.post("/robots/batch-status")
async def batch_get_status(
    robot_ids: List[str] = Body(..., description="机器人ID列表", max_length=20),
    current_user: TokenPayload = Depends(require_permission("robot:read"))
):
    """
    批量获取机器人状态

    权限: robot:read
    最多20个机器人
    """
    result = await _tools.handle("robot_batch_get_status", {"robot_ids": robot_ids})
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


# ============================================================
# Robot Task Control Endpoints
# ============================================================

@router.post("/robots/{robot_id}/start-task")
async def start_task(
    robot_id: str,
    request: StartTaskRequest,
    current_user: TokenPayload = Depends(require_permission("robot:control"))
):
    """
    启动清洁任务

    权限: robot:control
    """
    result = await _tools.handle("robot_start_task", {
        "robot_id": robot_id,
        "task_type": request.task_type,
        "zone_id": request.zone_id,
        "task_id": request.task_id,
        "cleaning_mode": request.cleaning_mode
    })
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


@router.post("/robots/{robot_id}/pause")
async def pause_task(
    robot_id: str,
    reason: Optional[str] = Query(None, description="暂停原因"),
    current_user: TokenPayload = Depends(require_permission("robot:control"))
):
    """
    暂停当前任务

    权限: robot:control
    """
    result = await _tools.handle("robot_pause_task", {
        "robot_id": robot_id,
        "reason": reason
    })
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


@router.post("/robots/{robot_id}/resume")
async def resume_task(
    robot_id: str,
    current_user: TokenPayload = Depends(require_permission("robot:control"))
):
    """
    恢复暂停的任务

    权限: robot:control
    """
    result = await _tools.handle("robot_resume_task", {"robot_id": robot_id})
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


@router.post("/robots/{robot_id}/cancel")
async def cancel_task(
    robot_id: str,
    reason: Optional[str] = Query(None, description="取消原因"),
    force: bool = Query(False, description="强制取消"),
    return_to_charge: bool = Query(False, description="返回充电站"),
    current_user: TokenPayload = Depends(require_permission("robot:control"))
):
    """
    取消当前任务

    权限: robot:control
    """
    result = await _tools.handle("robot_cancel_task", {
        "robot_id": robot_id,
        "reason": reason,
        "force": force,
        "return_to_charge": return_to_charge
    })
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


# ============================================================
# Robot Navigation Endpoints
# ============================================================

@router.post("/robots/{robot_id}/go-to")
async def go_to_location(
    robot_id: str,
    request: GoToLocationRequest,
    current_user: TokenPayload = Depends(require_permission("robot:control"))
):
    """
    指挥机器人移动到指定位置

    权限: robot:control
    """
    result = await _tools.handle("robot_go_to_location", {
        "robot_id": robot_id,
        "target_location": request.target_location
    })
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


@router.post("/robots/{robot_id}/go-to-charge")
async def go_to_charge(
    robot_id: str,
    force: bool = Query(False, description="强制返回（中断当前任务）"),
    current_user: TokenPayload = Depends(require_permission("robot:control"))
):
    """
    指挥机器人返回充电站

    权限: robot:control
    """
    result = await _tools.handle("robot_go_to_charge", {
        "robot_id": robot_id,
        "force": force
    })
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


# ============================================================
# Robot Error Endpoints
# ============================================================

@router.get("/robots/{robot_id}/errors")
async def get_errors(
    robot_id: str,
    active_only: bool = Query(False, description="仅活跃故障"),
    current_user: TokenPayload = Depends(require_permission("robot:read"))
):
    """
    获取机器人故障列表

    权限: robot:read
    """
    result = await _tools.handle("robot_get_errors", {
        "robot_id": robot_id,
        "active_only": active_only
    })
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


@router.post("/robots/{robot_id}/clear-error")
async def clear_error(
    robot_id: str,
    request: ClearErrorRequest,
    current_user: TokenPayload = Depends(require_permission("robot:control"))
):
    """
    清除故障

    权限: robot:control
    """
    result = await _tools.handle("robot_clear_error", {
        "robot_id": robot_id,
        "error_id": request.error_id
    })
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
