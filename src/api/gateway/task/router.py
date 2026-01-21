"""
G3: 任务管理API - 路由定义
===========================
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import datetime

from .models import (
    ScheduleStatus, TaskStatus,
    ScheduleCreate, ScheduleUpdate, ScheduleResponse, ScheduleDetailResponse,
    ScheduleListResponse, ScheduleActionResponse,
    TaskResponse, TaskDetailResponse, TaskListResponse,
    TaskControlRequest, TaskControlResponse,
    ExecutionResponse, ExecutionListResponse,
    MessageResponse
)
from .service import TaskService

# 导入认证依赖
import sys
sys.path.insert(0, str(__file__).replace("task/router.py", ""))
try:
    from auth.router import require_permission
    from auth.models import CurrentUser
except ImportError:
    # 测试时的模拟依赖
    class CurrentUser:
        id: str = "user-admin"
        tenant_id: str = "tenant_001"

    def require_permission(perm: str):
        def dep():
            return CurrentUser()
        return dep


# ============================================================
# 路由器和依赖
# ============================================================

router = APIRouter(prefix="/tasks", tags=["任务管理"])

# 全局服务实例
_task_service: Optional[TaskService] = None


def get_task_service() -> TaskService:
    """获取任务服务"""
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service


def set_task_service(service: TaskService):
    """设置任务服务（测试用）"""
    global _task_service
    _task_service = service


# ============================================================
# 排程管理接口
# ============================================================

@router.get("/schedules", response_model=ScheduleListResponse)
async def list_schedules(
    building_id: Optional[str] = None,
    zone_id: Optional[str] = None,
    status: Optional[ScheduleStatus] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: CurrentUser = Depends(require_permission("tasks:read")),
    task_service: TaskService = Depends(get_task_service)
):
    """
    获取排程列表

    支持按楼宇、区域、状态筛选。
    """
    result = await task_service.list_schedules(
        tenant_id=current_user.tenant_id,
        building_id=building_id,
        zone_id=zone_id,
        status=status,
        page=page,
        page_size=page_size
    )
    return ScheduleListResponse(**result)


@router.post("/schedules", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    request: ScheduleCreate,
    current_user: CurrentUser = Depends(require_permission("tasks:write")),
    task_service: TaskService = Depends(get_task_service)
):
    """
    创建清洁排程
    """
    return await task_service.create_schedule(
        tenant_id=current_user.tenant_id,
        data=request
    )


@router.get("/schedules/{schedule_id}", response_model=ScheduleDetailResponse)
async def get_schedule(
    schedule_id: str,
    current_user: CurrentUser = Depends(require_permission("tasks:read")),
    task_service: TaskService = Depends(get_task_service)
):
    """
    获取排程详情
    """
    schedule = await task_service.get_schedule(schedule_id, current_user.tenant_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="排程不存在"
        )
    return schedule


@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str,
    request: ScheduleUpdate,
    current_user: CurrentUser = Depends(require_permission("tasks:write")),
    task_service: TaskService = Depends(get_task_service)
):
    """
    更新排程
    """
    schedule = await task_service.update_schedule(
        schedule_id=schedule_id,
        tenant_id=current_user.tenant_id,
        data=request
    )
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="排程不存在"
        )
    return schedule


@router.delete("/schedules/{schedule_id}", response_model=MessageResponse)
async def delete_schedule(
    schedule_id: str,
    current_user: CurrentUser = Depends(require_permission("tasks:delete")),
    task_service: TaskService = Depends(get_task_service)
):
    """
    删除排程
    """
    success = await task_service.delete_schedule(schedule_id, current_user.tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="排程不存在"
        )
    return MessageResponse(message="排程已删除")


@router.post("/schedules/{schedule_id}/enable", response_model=ScheduleActionResponse)
async def enable_schedule(
    schedule_id: str,
    current_user: CurrentUser = Depends(require_permission("tasks:write")),
    task_service: TaskService = Depends(get_task_service)
):
    """
    启用排程
    """
    result = await task_service.enable_schedule(schedule_id, current_user.tenant_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="排程不存在"
        )
    return ScheduleActionResponse(**result)


@router.post("/schedules/{schedule_id}/disable", response_model=ScheduleActionResponse)
async def disable_schedule(
    schedule_id: str,
    current_user: CurrentUser = Depends(require_permission("tasks:write")),
    task_service: TaskService = Depends(get_task_service)
):
    """
    禁用排程
    """
    result = await task_service.disable_schedule(schedule_id, current_user.tenant_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="排程不存在"
        )
    return ScheduleActionResponse(**result)


# ============================================================
# 执行记录接口（必须在 /{task_id} 之前定义）
# ============================================================

@router.get("/executions", response_model=ExecutionListResponse)
async def list_executions(
    schedule_id: Optional[str] = None,
    zone_id: Optional[str] = None,
    robot_id: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: CurrentUser = Depends(require_permission("tasks:read")),
    task_service: TaskService = Depends(get_task_service)
):
    """
    获取执行记录列表
    """
    result = await task_service.list_executions(
        tenant_id=current_user.tenant_id,
        schedule_id=schedule_id,
        zone_id=zone_id,
        robot_id=robot_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size
    )
    return ExecutionListResponse(**result)


# ============================================================
# 任务查询接口
# ============================================================

@router.get("", response_model=TaskListResponse)
async def list_tasks(
    building_id: Optional[str] = None,
    zone_id: Optional[str] = None,
    robot_id: Optional[str] = None,
    status: Optional[TaskStatus] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: CurrentUser = Depends(require_permission("tasks:read")),
    task_service: TaskService = Depends(get_task_service)
):
    """
    获取任务列表

    支持多种筛选条件。
    """
    result = await task_service.list_tasks(
        tenant_id=current_user.tenant_id,
        building_id=building_id,
        zone_id=zone_id,
        robot_id=robot_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size
    )
    return TaskListResponse(**result)


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: str,
    current_user: CurrentUser = Depends(require_permission("tasks:read")),
    task_service: TaskService = Depends(get_task_service)
):
    """
    获取任务详情
    """
    task = await task_service.get_task(task_id, current_user.tenant_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    return task


# ============================================================
# 任务控制接口
# ============================================================

@router.post("/{task_id}/pause", response_model=TaskControlResponse)
async def pause_task(
    task_id: str,
    request: TaskControlRequest = None,
    current_user: CurrentUser = Depends(require_permission("tasks:write")),
    task_service: TaskService = Depends(get_task_service)
):
    """
    暂停任务
    """
    try:
        result = await task_service.pause_task(
            task_id=task_id,
            tenant_id=current_user.tenant_id,
            reason=request.reason if request else None
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        return TaskControlResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{task_id}/resume", response_model=TaskControlResponse)
async def resume_task(
    task_id: str,
    current_user: CurrentUser = Depends(require_permission("tasks:write")),
    task_service: TaskService = Depends(get_task_service)
):
    """
    恢复任务
    """
    try:
        result = await task_service.resume_task(task_id, current_user.tenant_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        return TaskControlResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{task_id}/cancel", response_model=TaskControlResponse)
async def cancel_task(
    task_id: str,
    request: TaskControlRequest = None,
    current_user: CurrentUser = Depends(require_permission("tasks:write")),
    task_service: TaskService = Depends(get_task_service)
):
    """
    取消任务
    """
    try:
        result = await task_service.cancel_task(
            task_id=task_id,
            tenant_id=current_user.tenant_id,
            reason=request.reason if request else None
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        return TaskControlResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
