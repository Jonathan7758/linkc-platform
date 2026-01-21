"""
G3: 任务管理API - 数据模型
===========================
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# 枚举类型
# ============================================================

class ScheduleType(str, Enum):
    """排程类型"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class CleaningMode(str, Enum):
    """清洁模式"""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduleStatus(str, Enum):
    """排程状态"""
    ENABLED = "enabled"
    DISABLED = "disabled"


class TaskPriority(str, Enum):
    """任务优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================
# 重复配置模型
# ============================================================

class RepeatConfig(BaseModel):
    """重复配置"""
    type: str  # daily, weekly, monthly
    days_of_week: Optional[List[int]] = None  # 0-6, 0=Monday
    days_of_month: Optional[List[int]] = None  # 1-31


# ============================================================
# 排程模型
# ============================================================

class ScheduleBase(BaseModel):
    """排程基础模型"""
    name: str = Field(min_length=1, max_length=200)
    zone_id: str
    schedule_type: ScheduleType
    start_time: str  # HH:MM format
    cleaning_mode: CleaningMode = CleaningMode.STANDARD
    duration_minutes: int = Field(default=60, ge=10, le=480)
    repeat_config: Optional[RepeatConfig] = None
    assigned_robot_id: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScheduleCreate(ScheduleBase):
    """创建排程请求"""
    pass


class ScheduleUpdate(BaseModel):
    """更新排程请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    start_time: Optional[str] = None
    cleaning_mode: Optional[CleaningMode] = None
    duration_minutes: Optional[int] = Field(default=None, ge=10, le=480)
    repeat_config: Optional[RepeatConfig] = None
    assigned_robot_id: Optional[str] = None
    priority: Optional[TaskPriority] = None
    metadata: Optional[Dict[str, Any]] = None


class ScheduleInDB(ScheduleBase):
    """数据库中的排程"""
    id: str
    tenant_id: str
    status: ScheduleStatus = ScheduleStatus.ENABLED
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ZoneInfo(BaseModel):
    """区域信息"""
    id: str
    name: str
    floor_name: Optional[str] = None
    building_name: Optional[str] = None


class ScheduleResponse(BaseModel):
    """排程响应"""
    id: str
    name: str
    zone_id: str
    zone_name: Optional[str] = None
    building_name: Optional[str] = None
    schedule_type: ScheduleType
    start_time: str
    cleaning_mode: CleaningMode
    duration_minutes: int
    priority: TaskPriority
    status: ScheduleStatus
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    created_at: datetime


class ExecutionSummary(BaseModel):
    """执行摘要"""
    id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    robot_id: Optional[str] = None


class ScheduleDetailResponse(ScheduleResponse):
    """排程详情响应"""
    zone: Optional[ZoneInfo] = None
    repeat_config: Optional[RepeatConfig] = None
    assigned_robot_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    statistics: Dict[str, Any] = {}
    recent_executions: List[ExecutionSummary] = []
    updated_at: Optional[datetime] = None


class ScheduleListResponse(BaseModel):
    """排程列表响应"""
    items: List[ScheduleResponse]
    total: int
    page: int
    page_size: int


class ScheduleActionResponse(BaseModel):
    """排程操作响应"""
    id: str
    status: ScheduleStatus
    next_run_at: Optional[datetime] = None
    message: str


# ============================================================
# 任务模型
# ============================================================

class TaskInDB(BaseModel):
    """数据库中的任务"""
    id: str
    tenant_id: str
    schedule_id: str
    zone_id: str
    robot_id: Optional[str] = None
    cleaning_mode: CleaningMode
    status: TaskStatus = TaskStatus.PENDING
    progress_percent: int = 0
    cleaned_area_sqm: float = 0
    total_area_sqm: float
    scheduled_start: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class RobotInfo(BaseModel):
    """机器人信息"""
    id: str
    name: str
    model: Optional[str] = None


class TaskEvent(BaseModel):
    """任务事件"""
    timestamp: datetime
    event_type: str
    message: str


class TaskResponse(BaseModel):
    """任务响应"""
    id: str
    schedule_id: str
    schedule_name: Optional[str] = None
    zone_id: str
    zone_name: Optional[str] = None
    robot_id: Optional[str] = None
    robot_name: Optional[str] = None
    status: TaskStatus
    progress_percent: int
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    created_at: datetime


class RouteInfo(BaseModel):
    """路径信息"""
    planned_path: Optional[List[Dict[str, float]]] = None
    actual_path: Optional[List[Dict[str, float]]] = None
    current_position: Optional[Dict[str, float]] = None


class TaskDetailResponse(TaskResponse):
    """任务详情响应"""
    zone: Optional[ZoneInfo] = None
    robot: Optional[RobotInfo] = None
    cleaning_mode: CleaningMode
    cleaned_area_sqm: float
    total_area_sqm: float
    completed_at: Optional[datetime] = None
    route: Optional[RouteInfo] = None
    events: List[TaskEvent] = []
    metadata: Dict[str, Any] = {}


class TaskListResponse(BaseModel):
    """任务列表响应"""
    items: List[TaskResponse]
    total: int
    page: int
    page_size: int


class TaskControlRequest(BaseModel):
    """任务控制请求"""
    reason: Optional[str] = Field(default=None, max_length=500)


class TaskControlResponse(BaseModel):
    """任务控制响应"""
    id: str
    status: TaskStatus
    paused_at: Optional[datetime] = None
    resumed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    message: str


# ============================================================
# 执行记录模型
# ============================================================

class ExecutionInDB(BaseModel):
    """数据库中的执行记录"""
    id: str
    task_id: str
    schedule_id: str
    zone_id: str
    robot_id: str
    tenant_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    cleaned_area_sqm: float = 0
    coverage_rate: float = 0
    route_data: Optional[Dict[str, Any]] = None
    events: List[Dict[str, Any]] = Field(default_factory=list)


class ExecutionResponse(BaseModel):
    """执行记录响应"""
    id: str
    task_id: str
    schedule_name: Optional[str] = None
    zone_name: Optional[str] = None
    robot_name: Optional[str] = None
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    cleaned_area_sqm: float
    coverage_rate: float


class ExecutionListResponse(BaseModel):
    """执行记录列表响应"""
    items: List[ExecutionResponse]
    total: int
    page: int
    page_size: int


# ============================================================
# 通用响应
# ============================================================

class MessageResponse(BaseModel):
    """消息响应"""
    message: str
