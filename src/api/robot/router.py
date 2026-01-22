"""
G4: 机器人管理API - 路由层
============================
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from .models import (
    RobotCreate, RobotUpdate, RobotControlRequest,
    RobotListResponse, RobotDetail, RobotStatus2,
    ControlResponse, RobotError, ApiResponse,
    PositionHistory, StatusHistory,
    RobotBrand, RobotStatus
)
from .service import RobotService

router = APIRouter(prefix="/api/v1/robots", tags=["robots"])

# 单例服务实例
_robot_service: RobotService = None


def get_robot_service() -> RobotService:
    """获取机器人服务实例（单例）"""
    global _robot_service
    if _robot_service is None:
        _robot_service = RobotService()
    return _robot_service


def get_tenant_id() -> str:
    """获取租户ID（实际应从认证中获取）"""
    return "tenant_001"


# ============================================================
# 机器人列表和详情
# ============================================================

@router.get("", response_model=RobotListResponse)
async def list_robots(
    building_id: Optional[str] = Query(None, description="楼宇ID"),
    brand: Optional[str] = Query(None, description="品牌"),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    tenant_id: str = Depends(get_tenant_id),
    service: RobotService = Depends(get_robot_service)
):
    """
    获取机器人列表

    支持按楼宇、品牌、状态筛选，支持分页
    """
    return await service.list_robots(
        tenant_id=tenant_id,
        building_id=building_id,
        brand=brand,
        status=status,
        page=page,
        page_size=page_size
    )


@router.get("/{robot_id}", response_model=RobotDetail)
async def get_robot(
    robot_id: str,
    tenant_id: str = Depends(get_tenant_id),
    service: RobotService = Depends(get_robot_service)
):
    """获取机器人详情"""
    robot = await service.get_robot(robot_id, tenant_id)
    if not robot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Robot {robot_id} not found"
        )
    return robot


# ============================================================
# 机器人增删改
# ============================================================

@router.post("", response_model=RobotDetail, status_code=status.HTTP_201_CREATED)
async def create_robot(
    data: RobotCreate,
    tenant_id: str = Depends(get_tenant_id),
    service: RobotService = Depends(get_robot_service)
):
    """创建机器人"""
    # 覆盖租户ID
    data.tenant_id = tenant_id
    return await service.create_robot(data)


@router.put("/{robot_id}", response_model=RobotDetail)
async def update_robot(
    robot_id: str,
    data: RobotUpdate,
    tenant_id: str = Depends(get_tenant_id),
    service: RobotService = Depends(get_robot_service)
):
    """更新机器人"""
    robot = await service.update_robot(robot_id, tenant_id, data)
    if not robot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Robot {robot_id} not found"
        )
    return robot


@router.delete("/{robot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_robot(
    robot_id: str,
    tenant_id: str = Depends(get_tenant_id),
    service: RobotService = Depends(get_robot_service)
):
    """删除机器人"""
    success = await service.delete_robot(robot_id, tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Robot {robot_id} not found"
        )


# ============================================================
# 实时状态
# ============================================================

@router.get("/{robot_id}/status", response_model=RobotStatus2)
async def get_robot_status(
    robot_id: str,
    tenant_id: str = Depends(get_tenant_id),
    service: RobotService = Depends(get_robot_service)
):
    """获取机器人实时状态"""
    status_data = await service.get_status(robot_id, tenant_id)
    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Robot {robot_id} not found"
        )
    return status_data


# ============================================================
# 控制指令
# ============================================================

@router.post("/{robot_id}/control", response_model=ControlResponse)
async def send_control(
    robot_id: str,
    request: RobotControlRequest,
    tenant_id: str = Depends(get_tenant_id),
    service: RobotService = Depends(get_robot_service)
):
    """发送控制指令"""
    result = await service.send_control(robot_id, tenant_id, request)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Robot {robot_id} not found"
        )
    return result


# ============================================================
# 错误信息
# ============================================================

@router.get("/{robot_id}/errors", response_model=list[RobotError])
async def get_robot_errors(
    robot_id: str,
    active_only: bool = Query(False, description="仅活跃错误"),
    tenant_id: str = Depends(get_tenant_id),
    service: RobotService = Depends(get_robot_service)
):
    """获取机器人错误信息"""
    # 先检查机器人是否存在
    robot = await service.get_robot(robot_id, tenant_id)
    if not robot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Robot {robot_id} not found"
        )
    return await service.get_errors(robot_id, tenant_id, active_only)


# ============================================================
# 历史数据
# ============================================================

@router.get("/{robot_id}/position-history", response_model=list[PositionHistory])
async def get_position_history(
    robot_id: str,
    start_time: str = Query(..., description="开始时间 ISO格式"),
    end_time: str = Query(..., description="结束时间 ISO格式"),
    tenant_id: str = Depends(get_tenant_id),
    service: RobotService = Depends(get_robot_service)
):
    """获取位置历史"""
    from datetime import datetime

    robot = await service.get_robot(robot_id, tenant_id)
    if not robot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Robot {robot_id} not found"
        )

    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid datetime format"
        )

    return await service.get_position_history(robot_id, tenant_id, start, end)


@router.get("/{robot_id}/status-history", response_model=list[StatusHistory])
async def get_status_history(
    robot_id: str,
    start_time: str = Query(..., description="开始时间 ISO格式"),
    end_time: str = Query(..., description="结束时间 ISO格式"),
    tenant_id: str = Depends(get_tenant_id),
    service: RobotService = Depends(get_robot_service)
):
    """获取状态历史"""
    from datetime import datetime

    robot = await service.get_robot(robot_id, tenant_id)
    if not robot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Robot {robot_id} not found"
        )

    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid datetime format"
        )

    return await service.get_status_history(robot_id, tenant_id, start, end)
