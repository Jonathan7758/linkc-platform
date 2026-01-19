"""
LinkC Platform - API Schema 定义
================================
定义 API 请求和响应的 Schema。
"""

from datetime import datetime
from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field

from interfaces.data_models import (
    RobotStatus, RobotBrand, TaskStatus, TaskPriority,
    ZoneType, CleaningMode
)


# ============================================================
# 通用响应
# ============================================================

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """通用 API 响应"""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: list[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_more: bool = False


# ============================================================
# 空间 API Schemas
# ============================================================

class BuildingCreate(BaseModel):
    """创建楼宇"""
    name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = None
    total_floors: int = Field(default=1, ge=1)
    total_area: Optional[float] = None


class BuildingUpdate(BaseModel):
    """更新楼宇"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = None
    total_floors: Optional[int] = Field(None, ge=1)
    total_area: Optional[float] = None


class BuildingResponse(BaseModel):
    """楼宇响应"""
    id: str
    tenant_id: str
    name: str
    address: Optional[str]
    total_floors: int
    total_area: Optional[float]
    created_at: datetime
    updated_at: datetime


class FloorCreate(BaseModel):
    """创建楼层"""
    building_id: str
    floor_number: int
    name: Optional[str] = None
    area: Optional[float] = None


class FloorResponse(BaseModel):
    """楼层响应"""
    id: str
    building_id: str
    floor_number: int
    name: Optional[str]
    area: Optional[float]
    created_at: datetime


class ZoneCreate(BaseModel):
    """创建区域"""
    floor_id: str
    name: str = Field(..., min_length=1, max_length=100)
    zone_type: ZoneType = ZoneType.OTHER
    area: Optional[float] = None
    cleaning_duration: Optional[int] = None


class ZoneResponse(BaseModel):
    """区域响应"""
    id: str
    floor_id: str
    name: str
    zone_type: ZoneType
    area: Optional[float]
    cleaning_duration: Optional[int]
    created_at: datetime


# ============================================================
# 机器人 API Schemas
# ============================================================

class RobotCreate(BaseModel):
    """注册机器人"""
    name: str = Field(..., min_length=1, max_length=100)
    brand: RobotBrand
    model: Optional[str] = None
    serial_number: Optional[str] = None
    external_id: Optional[str] = None
    assigned_building_id: Optional[str] = None


class RobotUpdate(BaseModel):
    """更新机器人"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    assigned_building_id: Optional[str] = None


class RobotResponse(BaseModel):
    """机器人响应"""
    id: str
    tenant_id: str
    name: str
    brand: RobotBrand
    model: Optional[str]
    status: RobotStatus
    battery_level: int
    current_zone_id: Optional[str]
    assigned_building_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class RobotStatusResponse(BaseModel):
    """机器人状态响应"""
    id: str
    status: RobotStatus
    battery_level: int
    current_zone_id: Optional[str]
    position: Optional[dict] = None
    last_updated: datetime


# ============================================================
# 任务 API Schemas
# ============================================================

class TaskCreate(BaseModel):
    """创建任务"""
    name: str = Field(..., min_length=1, max_length=200)
    zone_id: str
    priority: TaskPriority = TaskPriority.NORMAL
    cleaning_mode: CleaningMode = CleaningMode.STANDARD
    scheduled_start: Optional[datetime] = None
    notes: Optional[str] = None


class TaskUpdate(BaseModel):
    """更新任务"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    priority: Optional[TaskPriority] = None
    scheduled_start: Optional[datetime] = None
    notes: Optional[str] = None


class TaskAssign(BaseModel):
    """分配任务"""
    robot_id: str
    reason: Optional[str] = None


class TaskResponse(BaseModel):
    """任务响应"""
    id: str
    tenant_id: str
    name: str
    zone_id: str
    robot_id: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    cleaning_mode: CleaningMode
    scheduled_start: Optional[datetime]
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    completion_rate: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================================
# Agent API Schemas
# ============================================================

class AgentCommand(BaseModel):
    """Agent命令"""
    command: str = Field(..., description="命令内容")
    context: Optional[dict] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Agent响应"""
    message: str
    actions_taken: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class AgentDecisionResponse(BaseModel):
    """Agent决策响应"""
    id: str
    agent_id: str
    decision_type: str
    decision: dict
    confidence: float
    requires_approval: bool
    created_at: datetime


# ============================================================
# 导出
# ============================================================

__all__ = [
    # Common
    "ApiResponse", "PaginatedResponse",
    # Space
    "BuildingCreate", "BuildingUpdate", "BuildingResponse",
    "FloorCreate", "FloorResponse",
    "ZoneCreate", "ZoneResponse",
    # Robot
    "RobotCreate", "RobotUpdate", "RobotResponse", "RobotStatusResponse",
    # Task
    "TaskCreate", "TaskUpdate", "TaskAssign", "TaskResponse",
    # Agent
    "AgentCommand", "AgentResponse", "AgentDecisionResponse",
]
