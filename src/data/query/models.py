"""
D3: 数据查询API - 数据模型
==========================
查询结果的数据模型定义
"""

from typing import List, Optional, Generic, TypeVar, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from enum import Enum

T = TypeVar('T')


# ============================================================
# 通用模型
# ============================================================

class PagedResult(BaseModel, Generic[T]):
    """分页结果"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: List[T], total: int, page: int, size: int):
        pages = (total + size - 1) // size if size > 0 else 0
        return cls(items=items, total=total, page=page, size=size, pages=pages)


class TimeRange(BaseModel):
    """时间范围"""
    start_time: datetime
    end_time: datetime


class TrendDirection(str, Enum):
    """趋势方向"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


# ============================================================
# 机器人数据模型
# ============================================================

class RobotCurrentStatus(BaseModel):
    """机器人当前状态"""
    robot_id: str
    name: str
    brand: str = "unknown"
    status: str
    battery_level: int
    position: Optional[Dict[str, Any]] = None
    current_task: Optional[Dict[str, Any]] = None
    last_updated: datetime


class RobotStatusPoint(BaseModel):
    """机器人状态时间点"""
    timestamp: datetime
    status: str
    battery_level: int


class PositionPoint(BaseModel):
    """位置点"""
    timestamp: datetime
    x: float
    y: float
    floor_id: str


class RobotUtilization(BaseModel):
    """机器人利用率"""
    robot_id: str
    name: str
    total_hours: float
    working_hours: float
    charging_hours: float
    idle_hours: float
    utilization_rate: float  # 百分比


# ============================================================
# 任务数据模型
# ============================================================

class TaskSummary(BaseModel):
    """任务汇总"""
    date: date
    total_tasks: int
    completed: int
    in_progress: int
    pending: int
    failed: int
    cancelled: int = 0
    completion_rate: float  # 百分比
    avg_completion_time: int  # 分钟
    total_area_cleaned: float  # 平方米


class TaskRecord(BaseModel):
    """任务记录"""
    task_id: str
    tenant_id: str
    zone_id: str
    zone_name: Optional[str] = None
    robot_id: Optional[str] = None
    robot_name: Optional[str] = None
    status: str
    task_type: str
    priority: int = 0
    scheduled_start: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    area_cleaned: float = 0.0
    created_at: datetime


class DailyTaskStats(BaseModel):
    """每日任务统计"""
    date: date
    total: int
    completed: int
    failed: int
    completion_rate: float


# ============================================================
# 空间数据模型
# ============================================================

class ZoneCoverage(BaseModel):
    """区域覆盖率"""
    zone_id: str
    zone_name: str
    area_sqm: float
    cleaned_area: float
    coverage_rate: float  # 百分比
    clean_count: int


class FloorHeatmapData(BaseModel):
    """楼层热力图数据"""
    floor_id: str
    metric: str
    data: List[Dict[str, Any]]  # [{zone_id, value, ...}]
    min_value: float
    max_value: float


# ============================================================
# 统计分析模型
# ============================================================

class EfficiencyMetrics(BaseModel):
    """效率指标"""
    period: str
    avg_task_duration: int  # 分钟
    avg_area_per_hour: float  # 平方米/小时
    avg_battery_usage: float  # 百分比
    robot_utilization: float  # 百分比
    task_completion_rate: float  # 百分比


class ComparisonResult(BaseModel):
    """对比结果"""
    metric: str
    current_value: float
    compare_value: float
    change: float
    change_percent: float
    trend: TrendDirection


class AnomalyType(str, Enum):
    """异常类型"""
    BATTERY_LOW = "battery_low"
    TASK_FAILED = "task_failed"
    ROBOT_OFFLINE = "offline"
    TASK_TIMEOUT = "task_timeout"
    ERROR_ALERT = "error_alert"


class AnomalyEvent(BaseModel):
    """异常事件"""
    event_id: str
    event_type: AnomalyType
    timestamp: datetime
    robot_id: Optional[str] = None
    task_id: Optional[str] = None
    description: str
    severity: str = "warning"  # info, warning, error, critical
    details: Dict[str, Any] = Field(default_factory=dict)
