"""
G4: 机器人管理API - 数据模型
============================
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================
# 枚举类型
# ============================================================

class RobotBrand(str, Enum):
    """机器人品牌"""
    GAOXIAN = "gaoxian"
    ECOVACS = "ecovacs"
    OTHER = "other"


class RobotStatus(str, Enum):
    """机器人状态"""
    OFFLINE = "offline"
    IDLE = "idle"
    WORKING = "working"
    PAUSED = "paused"
    CHARGING = "charging"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class ControlCommand(str, Enum):
    """控制指令"""
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    GO_CHARGE = "go_charge"
    GO_HOME = "go_home"
    GO_TO = "go_to"


# ============================================================
# 请求模型
# ============================================================

class RobotCreate(BaseModel):
    """创建机器人请求"""
    tenant_id: str
    name: str
    brand: RobotBrand = RobotBrand.GAOXIAN
    model: str
    serial_number: str
    building_id: str
    connection_config: Optional[Dict[str, Any]] = None


class RobotUpdate(BaseModel):
    """更新机器人请求"""
    name: Optional[str] = None
    building_id: Optional[str] = None
    connection_config: Optional[Dict[str, Any]] = None


class RobotControlRequest(BaseModel):
    """控制指令请求"""
    command: ControlCommand
    params: Optional[Dict[str, Any]] = None


# ============================================================
# 响应模型
# ============================================================

class Position(BaseModel):
    """位置信息"""
    x: float
    y: float
    orientation: float = 0.0
    floor_id: Optional[str] = None


class ConsumableStatus(BaseModel):
    """耗材状态"""
    remaining_percent: int
    estimated_hours: Optional[int] = None


class RobotStatistics(BaseModel):
    """机器人统计"""
    total_tasks: int = 0
    total_area_cleaned: float = 0.0
    total_working_hours: float = 0.0
    average_efficiency: float = 0.0


class RobotListItem(BaseModel):
    """机器人列表项"""
    robot_id: str
    name: str
    brand: str
    model: str
    serial_number: Optional[str] = None
    building_id: Optional[str] = None
    building_name: Optional[str] = None
    current_floor_id: Optional[str] = None
    current_floor_name: Optional[str] = None
    status: str
    battery_level: int = 0
    position: Optional[Position] = None
    current_task_id: Optional[str] = None
    last_active_at: Optional[datetime] = None
    created_at: datetime


class RobotDetail(RobotListItem):
    """机器人详情"""
    firmware_version: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    consumables: Optional[Dict[str, ConsumableStatus]] = None
    current_task: Optional[Dict[str, Any]] = None
    statistics: Optional[RobotStatistics] = None
    updated_at: Optional[datetime] = None


class RobotStatus2(BaseModel):
    """机器人实时状态"""
    robot_id: str
    status: str
    battery_level: int
    position: Optional[Position] = None
    speed: Optional[float] = None
    cleaning_mode: Optional[str] = None
    current_task_id: Optional[str] = None
    task_progress: Optional[float] = None
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime


class RobotListResponse(BaseModel):
    """机器人列表响应"""
    items: List[RobotListItem]
    total: int
    page: int
    page_size: int


class ControlResponse(BaseModel):
    """控制指令响应"""
    success: bool
    robot_id: str
    command: str
    message: str
    timestamp: datetime


class RobotError(BaseModel):
    """机器人错误"""
    error_id: str
    robot_id: str
    error_code: str
    error_message: str
    severity: str
    occurred_at: datetime
    resolved_at: Optional[datetime] = None


class PositionHistory(BaseModel):
    """位置历史"""
    timestamp: datetime
    x: float
    y: float
    floor_id: str


class StatusHistory(BaseModel):
    """状态历史"""
    timestamp: datetime
    status: str
    battery_level: int


# ============================================================
# 通用响应
# ============================================================

class ApiResponse(BaseModel):
    """通用API响应"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None
