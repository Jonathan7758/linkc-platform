"""
G2: 任务管理 API
================
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
from pydantic import BaseModel

from src.mcp_servers.task_manager.storage import TaskStorage
from src.mcp_servers.task_manager.tools import TaskManagerTools

router = APIRouter(prefix="/tasks", tags=["tasks"])

storage = TaskStorage()
tools = TaskManagerTools(storage)


class TaskCreate(BaseModel):
    """创建任务请求"""
    name: str
    zone_id: str
    priority: str = "normal"
    cleaning_mode: str = "standard"
    scheduled_start: Optional[str] = None
    estimated_duration: Optional[int] = None
    notes: Optional[str] = None


class TaskAssign(BaseModel):
    """分配任务请求"""
    robot_id: str
    assigned_by: str = "api_user"


class TaskStatusUpdate(BaseModel):
    """更新任务状态请求"""
    status: str
    completion_rate: Optional[float] = None
    notes: Optional[str] = None


@router.post("")
async def create_task(
    tenant_id: str = Query(...),
    task: TaskCreate = Body(...)
):
    """创建任务"""
    result = await tools.create_task(
        tenant_id=tenant_id,
        name=task.name,
        zone_id=task.zone_id,
        priority=task.priority,
        cleaning_mode=task.cleaning_mode,
        scheduled_start=task.scheduled_start,
        estimated_duration=task.estimated_duration,
        notes=task.notes
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("")
async def list_tasks(
    tenant_id: str = Query(...),
    status: Optional[str] = Query(None),
    zone_id: Optional[str] = Query(None),
    robot_id: Optional[str] = Query(None),
    limit: int = Query(50, le=100)
):
    """列出任务"""
    result = await tools.list_tasks(
        tenant_id=tenant_id,
        status=status,
        zone_id=zone_id,
        robot_id=robot_id,
        limit=limit
    )
    return result


@router.get("/pending")
async def get_pending_tasks(tenant_id: str = Query(...)):
    """获取待分配的任务"""
    result = await tools.get_pending_tasks(tenant_id)
    return result


@router.get("/{task_id}")
async def get_task(task_id: str):
    """获取任务详情"""
    result = await tools.get_task(task_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.post("/{task_id}/assign")
async def assign_task(task_id: str, assignment: TaskAssign = Body(...)):
    """分配任务给机器人"""
    result = await tools.assign_task(
        task_id=task_id,
        robot_id=assignment.robot_id,
        assigned_by=assignment.assigned_by
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.patch("/{task_id}/status")
async def update_task_status(task_id: str, update: TaskStatusUpdate = Body(...)):
    """更新任务状态"""
    result = await tools.update_task_status(
        task_id=task_id,
        status=update.status,
        completion_rate=update.completion_rate,
        notes=update.notes
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
