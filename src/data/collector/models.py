"""
D1: 数据采集引擎 - 数据模型
============================
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4


class CollectorType(str, Enum):
    """采集器类型"""
    ROBOT_STATUS = "robot_status"      # 机器人状态采集
    ROBOT_POSITION = "robot_position"  # 机器人位置采集
    TASK_PROGRESS = "task_progress"    # 任务进度采集
    CONSUMABLES = "consumables"        # 耗材状态采集
    EVENTS = "events"                  # 事件采集


class CollectorStatus(str, Enum):
    """采集器状态"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    PAUSED = "paused"


class MCPTarget(str, Enum):
    """目标MCP"""
    GAOXIAN = "gaoxian"
    ECOVACS = "ecovacs"


class CollectorConfig(BaseModel):
    """采集器配置"""
    collector_id: str = Field(default_factory=lambda: f"col_{uuid4().hex[:8]}")
    name: str
    collector_type: CollectorType
    tenant_id: str
    enabled: bool = True
    interval_seconds: int = 30  # 采集间隔
    target_mcp: MCPTarget = MCPTarget.GAOXIAN
    filters: Optional[Dict[str, Any]] = None  # 筛选条件
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CollectorState(BaseModel):
    """采集器运行状态"""
    collector_id: str
    status: CollectorStatus = CollectorStatus.STOPPED
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    records_collected: int = 0
    error_count: int = 0
    last_error: Optional[str] = None


class CollectedData(BaseModel):
    """采集到的数据"""
    data_id: str = Field(default_factory=lambda: f"data_{uuid4().hex[:12]}")
    collector_id: str
    tenant_id: str
    data_type: CollectorType
    source: str  # 数据来源MCP
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]  # 实际数据内容
    metadata: Optional[Dict[str, Any]] = None


class RobotStatusData(BaseModel):
    """机器人状态数据（标准化后）"""
    robot_id: str
    tenant_id: str
    timestamp: datetime
    status: str
    battery_level: int
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    floor_id: Optional[str] = None
    zone_id: Optional[str] = None
    current_task_id: Optional[str] = None
    error_code: Optional[str] = None


class RobotPositionData(BaseModel):
    """机器人位置数据"""
    robot_id: str
    tenant_id: str
    timestamp: datetime
    x: float
    y: float
    floor_id: Optional[str] = None
    heading: Optional[float] = None  # 朝向角度
    speed: Optional[float] = None  # 移动速度


class TaskProgressData(BaseModel):
    """任务进度数据"""
    task_id: str
    robot_id: str
    tenant_id: str
    timestamp: datetime
    status: str
    progress: float  # 0-100
    zone_id: Optional[str] = None
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
