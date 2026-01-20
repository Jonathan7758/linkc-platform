"""
M2: 任务管理 MCP - HTTP Router
===============================
"""

from fastapi import APIRouter, Depends, Query, Body
from typing import Optional, List
from datetime import date
from pydantic import BaseModel

from src.shared.auth import get_current_user, require_permission, TokenPayload, check_tenant_access
from src.mcp_servers.task_manager.storage import InMemoryTaskStorage
from src.mcp_servers.task_manager.tools import TaskTools

router = APIRouter()

# 共享存储实例
_storage = InMemoryTaskStorage()
_tools = TaskTools(_storage)


# ============================================================
# Request Models
# ============================================================

class CreateScheduleRequest(BaseModel):
    """创建排班请求"""
    tenant_id: str
    zone_id: str
    name: str
    task_type: str  # routine/deep/emergency
    frequency: str  # daily/weekly/monthly/custom
    time_slots: List[dict]  # [{"start_time": "09:00", "end_time": "10:00"}]
    days_of_week: Optional[List[int]] = None
    priority: int = 5
    assigned_robot_id: Optional[str] = None
    cleaning_params: Optional[dict] = None


class CreateTaskRequest(BaseModel):
    """创建任务请求"""
    tenant_id: str
    zone_id: str
    task_type: str
    priority: int = 5
    scheduled_start: Optional[str] = None
    assigned_robot_id: Optional[str] = None
    cleaning_params: Optional[dict] = None
    notes: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    """更新任务状态请求"""
    new_status: str
    completion_rate: Optional[float] = None
    failure_reason: Optional[str] = None


# ============================================================
# Schedule Endpoints
# ============================================================

@router.get("/schedules")
async def list_schedules(
    tenant_id: str = Query(..., description="租户ID"),
    zone_id: Optional[str] = Query(None, description="区域ID"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: TokenPayload = Depends(require_permission("task:read"))
):
    """
    获取排班列表

    权限: task:read
    """
    await check_tenant_access(current_user, tenant_id)
    result = await _tools.handle("task_list_schedules", {
        "tenant_id": tenant_id,
        "zone_id": zone_id,
        "is_active": is_active
    })
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


@router.get("/schedules/{schedule_id}")
async def get_schedule(
    schedule_id: str,
    current_user: TokenPayload = Depends(require_permission("task:read"))
):
    """
    获取排班详情

    权限: task:read
    """
    result = await _tools.handle("task_get_schedule", {"schedule_id": schedule_id})
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


@router.post("/schedules")
async def create_schedule(
    request: CreateScheduleRequest,
    current_user: TokenPayload = Depends(require_permission("task:write"))
):
    """
    创建排班计划

    权限: task:write
    """
    await check_tenant_access(current_user, request.tenant_id)
    result = await _tools.handle("task_create_schedule", request.model_dump())
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


@router.put("/schedules/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    is_active: Optional[bool] = None,
    priority: Optional[int] = Query(None, ge=1, le=10),
    assigned_robot_id: Optional[str] = None,
    current_user: TokenPayload = Depends(require_permission("task:write"))
):
    """
    更新排班计划

    权限: task:write
    """
    result = await _tools.handle("task_update_schedule", {
        "schedule_id": schedule_id,
        "is_active": is_active,
        "priority": priority,
        "assigned_robot_id": assigned_robot_id
    })
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


# ============================================================
# Task Endpoints
# ============================================================

@router.get("/tasks")
async def list_tasks(
    tenant_id: str = Query(..., description="租户ID"),
    zone_id: Optional[str] = Query(None, description="区域ID"),
    status: Optional[str] = Query(None, description="任务状态"),
    task_date: Optional[str] = Query(None, description="任务日期 YYYY-MM-DD"),
    limit: int = Query(50, ge=1, le=200),
    current_user: TokenPayload = Depends(require_permission("task:read"))
):
    """
    获取任务列表

    权限: task:read
    """
    await check_tenant_access(current_user, tenant_id)
    result = await _tools.handle("task_list_tasks", {
        "tenant_id": tenant_id,
        "zone_id": zone_id,
        "status": status,
        "task_date": task_date,
        "limit": limit
    })
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


@router.get("/tasks/pending")
async def get_pending_tasks(
    tenant_id: str = Query(..., description="租户ID"),
    zone_id: Optional[str] = Query(None, description="区域ID"),
    robot_id: Optional[str] = Query(None, description="机器人ID"),
    limit: int = Query(20, ge=1, le=100),
    current_user: TokenPayload = Depends(require_permission("task:read"))
):
    """
    获取待执行任务

    权限: task:read
    """
    await check_tenant_access(current_user, tenant_id)
    result = await _tools.handle("task_get_pending_tasks", {
        "tenant_id": tenant_id,
        "zone_id": zone_id,
        "robot_id": robot_id,
        "limit": limit
    })
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    current_user: TokenPayload = Depends(require_permission("task:read"))
):
    """
    获取任务详情

    权限: task:read
    """
    result = await _tools.handle("task_get_task", {"task_id": task_id})
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


@router.post("/tasks")
async def create_task(
    request: CreateTaskRequest,
    current_user: TokenPayload = Depends(require_permission("task:write"))
):
    """
    创建任务

    权限: task:write
    """
    await check_tenant_access(current_user, request.tenant_id)
    result = await _tools.handle("task_create_task", request.model_dump())
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


@router.put("/tasks/{task_id}/status")
async def update_task_status(
    task_id: str,
    request: UpdateStatusRequest,
    current_user: TokenPayload = Depends(require_permission("task:write"))
):
    """
    更新任务状态

    权限: task:write
    """
    result = await _tools.handle("task_update_status", {
        "task_id": task_id,
        "new_status": request.new_status,
        "completion_rate": request.completion_rate,
        "failure_reason": request.failure_reason
    })
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__


@router.post("/tasks/generate")
async def generate_daily_tasks(
    tenant_id: str = Query(..., description="租户ID"),
    target_date: Optional[str] = Query(None, description="目标日期 YYYY-MM-DD"),
    current_user: TokenPayload = Depends(require_permission("task:write"))
):
    """
    生成每日任务

    权限: task:write
    """
    await check_tenant_access(current_user, tenant_id)
    result = await _tools.handle("task_generate_daily_tasks", {
        "tenant_id": tenant_id,
        "target_date": target_date
    })
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
