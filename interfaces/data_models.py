"""
LinkC Platform - 核心数据模型
=============================
定义所有模块共享的数据结构。

修改此文件需要团队讨论，因为会影响所有模块。
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ============================================================
# 枚举定义
# ============================================================

class RobotStatus(str, Enum):
    """机器人状态"""
    IDLE = "idle"              # 空闲
    WORKING = "working"        # 工作中
    CHARGING = "charging"      # 充电中
    ERROR = "error"            # 故障
    OFFLINE = "offline"        # 离线


class RobotBrand(str, Enum):
    """机器人品牌"""
    GAUSSI = "gaussi"          # 高仙
    ECOVACS = "ecovacs"        # 科沃斯
    OTHER = "other"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"        # 待执行
    ASSIGNED = "assigned"      # 已分配
    IN_PROGRESS = "in_progress"  # 执行中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败
    CANCELLED = "cancelled"    # 已取消


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ZoneType(str, Enum):
    """区域类型"""
    LOBBY = "lobby"            # 大堂
    CORRIDOR = "corridor"      # 走廊
    OFFICE = "office"          # 办公室
    RESTROOM = "restroom"      # 洗手间
    ELEVATOR = "elevator"      # 电梯厅
    PARKING = "parking"        # 停车场
    OTHER = "other"


class CleaningMode(str, Enum):
    """清洁模式"""
    STANDARD = "standard"      # 标准清洁
    DEEP = "deep"              # 深度清洁
    QUICK = "quick"            # 快速清洁
    SPOT = "spot"              # 定点清洁


# ============================================================
# 基础模型
# ============================================================

class BaseEntityModel(BaseModel):
    """实体基类"""
    id: str = Field(..., description="唯一标识符")
    tenant_id: str = Field(..., description="租户ID，用于多租户隔离")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# 空间管理模型
# ============================================================

class Building(BaseEntityModel):
    """楼宇"""
    name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = None
    total_floors: int = Field(default=1, ge=1)
    total_area: Optional[float] = Field(None, description="总面积(平方米)")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()


class Floor(BaseEntityModel):
    """楼层"""
    building_id: str = Field(..., description="所属楼宇ID")
    floor_number: int = Field(..., description="楼层号")
    name: Optional[str] = Field(None, description="楼层名称，如 B1, 1F")
    area: Optional[float] = Field(None, description="楼层面积(平方米)")


class Zone(BaseEntityModel):
    """清洁区域"""
    floor_id: str = Field(..., description="所属楼层ID")
    name: str = Field(..., min_length=1, max_length=100)
    zone_type: ZoneType = Field(default=ZoneType.OTHER)
    area: Optional[float] = Field(None, description="区域面积(平方米)")
    cleaning_duration: Optional[int] = Field(None, description="预计清洁时长(分钟)")
    coordinates: Optional[dict] = Field(None, description="区域坐标/边界")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()


# ============================================================
# 机器人模型
# ============================================================

class Robot(BaseEntityModel):
    """机器人"""
    name: str = Field(..., min_length=1, max_length=100)
    brand: RobotBrand = Field(...)
    model: Optional[str] = Field(None, description="机器人型号")
    serial_number: Optional[str] = Field(None, description="序列号")
    status: RobotStatus = Field(default=RobotStatus.OFFLINE)
    battery_level: int = Field(default=0, ge=0, le=100)
    current_zone_id: Optional[str] = Field(None, description="当前所在区域")
    assigned_building_id: Optional[str] = Field(None, description="分配的楼宇")
    
    # 外部系统ID
    external_id: Optional[str] = Field(None, description="品牌云平台的机器人ID")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()
    
    @field_validator("battery_level")
    @classmethod
    def validate_battery(cls, v: int) -> int:
        return max(0, min(100, v))


class RobotPosition(BaseModel):
    """机器人位置信息"""
    robot_id: str
    x: float
    y: float
    floor_id: Optional[str] = None
    heading: Optional[float] = Field(None, description="朝向角度(0-360)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# 任务模型
# ============================================================

class Task(BaseEntityModel):
    """清洁任务"""
    name: str = Field(..., min_length=1, max_length=200)
    zone_id: str = Field(..., description="目标区域ID")
    robot_id: Optional[str] = Field(None, description="分配的机器人ID")
    
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: TaskPriority = Field(default=TaskPriority.NORMAL)
    cleaning_mode: CleaningMode = Field(default=CleaningMode.STANDARD)
    
    scheduled_start: Optional[datetime] = Field(None, description="计划开始时间")
    actual_start: Optional[datetime] = Field(None, description="实际开始时间")
    actual_end: Optional[datetime] = Field(None, description="实际结束时间")
    
    estimated_duration: Optional[int] = Field(None, description="预计时长(分钟)")
    actual_duration: Optional[int] = Field(None, description="实际时长(分钟)")
    
    completion_rate: Optional[float] = Field(None, ge=0, le=100, description="完成率(%)")
    notes: Optional[str] = Field(None, description="备注")


class TaskAssignment(BaseModel):
    """任务分配记录"""
    task_id: str
    robot_id: str
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: str = Field(..., description="分配者(agent_id或user_id)")
    reason: Optional[str] = Field(None, description="分配原因")


# ============================================================
# Agent决策模型
# ============================================================

class AgentDecision(BaseModel):
    """Agent决策记录"""
    id: str
    agent_id: str = Field(..., description="做出决策的Agent ID")
    decision_type: str = Field(..., description="决策类型")
    context: dict = Field(default_factory=dict, description="决策上下文")
    decision: dict = Field(..., description="决策内容")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    requires_approval: bool = Field(default=False, description="是否需要人工审批")
    approved: Optional[bool] = Field(None, description="审批结果")
    approved_by: Optional[str] = Field(None, description="审批人")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = Field(None, description="执行时间")


# ============================================================
# 事件模型
# ============================================================

class SystemEvent(BaseModel):
    """系统事件"""
    id: str
    event_type: str = Field(..., description="事件类型")
    source: str = Field(..., description="事件来源(模块/组件)")
    tenant_id: str
    payload: dict = Field(default_factory=dict, description="事件数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# 导出
# ============================================================

__all__ = [
    # Enums
    "RobotStatus", "RobotBrand", "TaskStatus", "TaskPriority",
    "ZoneType", "CleaningMode",
    # Base
    "BaseEntityModel",
    # Space
    "Building", "Floor", "Zone",
    # Robot
    "Robot", "RobotPosition",
    # Task
    "Task", "TaskAssignment",
    # Agent
    "AgentDecision",
    # Event
    "SystemEvent",
]
