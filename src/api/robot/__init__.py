"""
G4: 机器人管理API
==================
提供机器人的增删改查、状态监控、控制指令等功能
"""

from .models import (
    # 枚举
    RobotBrand,
    RobotStatus,
    ControlCommand,
    # 请求模型
    RobotCreate,
    RobotUpdate,
    RobotControlRequest,
    # 响应模型
    Position,
    ConsumableStatus,
    RobotStatistics,
    RobotListItem,
    RobotDetail,
    RobotStatus2,
    RobotListResponse,
    ControlResponse,
    RobotError,
    PositionHistory,
    StatusHistory,
    ApiResponse,
)

from .service import RobotService
from .router import router

__all__ = [
    # 枚举
    "RobotBrand",
    "RobotStatus",
    "ControlCommand",
    # 请求模型
    "RobotCreate",
    "RobotUpdate",
    "RobotControlRequest",
    # 响应模型
    "Position",
    "ConsumableStatus",
    "RobotStatistics",
    "RobotListItem",
    "RobotDetail",
    "RobotStatus2",
    "RobotListResponse",
    "ControlResponse",
    "RobotError",
    "PositionHistory",
    "StatusHistory",
    "ApiResponse",
    # 服务
    "RobotService",
    # 路由
    "router",
]
