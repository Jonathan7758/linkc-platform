"""
M3: 高仙机器人 MCP Server - 存储层
==================================
基于规格书 docs/specs/M3-gaoxian-mcp.md 实现
"""

from typing import Dict, List, Optional
from uuid import uuid4
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================
# 枚举定义
# ============================================================

class RobotBrand(str, Enum):
    """机器人品牌"""
    GAOXIAN = "gaoxian"
    ECOVACS = "ecovacs"
    PUDU = "pudu"
    OTHER = "other"


class RobotType(str, Enum):
    """机器人类型"""
    CLEANING = "cleaning"
    SECURITY = "security"
    DELIVERY = "delivery"
    DISINFECTION = "disinfection"


class RobotStatus(str, Enum):
    """机器人状态"""
    OFFLINE = "offline"
    IDLE = "idle"
    WORKING = "working"
    PAUSED = "paused"
    CHARGING = "charging"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class CleaningMode(str, Enum):
    """清洁模式"""
    VACUUM = "vacuum"
    MOP = "mop"
    VACUUM_MOP = "vacuum_mop"


class CleaningIntensity(str, Enum):
    """清洁强度"""
    ECO = "eco"
    STANDARD = "standard"
    DEEP = "deep"


class ErrorSeverity(str, Enum):
    """错误严重级别"""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================
# 数据模型
# ============================================================

class Location(BaseModel):
    """位置信息"""
    x: float
    y: float
    floor_id: Optional[str] = None
    heading: Optional[float] = None


class RobotCapability(BaseModel):
    """机器人能力"""
    can_vacuum: bool = True
    can_mop: bool = True
    can_auto_charge: bool = True
    can_elevator: bool = False
    max_area: float = 500
    max_runtime: int = 180


class Robot(BaseModel):
    """机器人基础信息"""
    robot_id: str
    tenant_id: str

    name: str
    brand: RobotBrand
    model: str
    serial_number: str
    robot_type: RobotType

    building_id: Optional[str] = None
    floor_ids: List[str] = Field(default_factory=list)
    home_location: Optional[Location] = None

    capabilities: RobotCapability = Field(default_factory=RobotCapability)
    status: RobotStatus = RobotStatus.OFFLINE

    registered_at: datetime
    last_seen_at: Optional[datetime] = None


class RobotStatusSnapshot(BaseModel):
    """机器人状态快照"""
    robot_id: str
    status: RobotStatus

    current_location: Optional[Location] = None

    battery_level: int = Field(..., ge=0, le=100)
    water_level: Optional[int] = Field(None, ge=0, le=100)
    dustbin_level: Optional[int] = Field(None, ge=0, le=100)

    current_task_id: Optional[str] = None
    current_zone_id: Optional[str] = None
    task_progress: Optional[float] = None

    speed: Optional[float] = None
    cleaning_mode: Optional[CleaningMode] = None
    cleaning_intensity: Optional[CleaningIntensity] = None

    error_code: Optional[str] = None
    error_message: Optional[str] = None

    timestamp: datetime


class RobotError(BaseModel):
    """机器人错误"""
    error_id: str
    robot_id: str
    robot_name: Optional[str] = None

    error_code: str
    error_type: str
    severity: ErrorSeverity
    message: str

    location: Optional[Location] = None
    occurred_at: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


class RobotTask(BaseModel):
    """机器人执行的任务"""
    robot_task_id: str
    robot_id: str
    zone_id: str
    task_id: Optional[str] = None  # 关联的M2任务ID

    task_type: CleaningMode
    cleaning_intensity: CleaningIntensity = CleaningIntensity.STANDARD

    status: str = "started"  # started, running, paused, completed, cancelled, failed
    progress: float = 0.0  # 0-100

    started_at: datetime
    estimated_duration: int = 30  # 分钟
    completed_at: Optional[datetime] = None

    cancel_reason: Optional[str] = None
    failure_reason: Optional[str] = None


# ============================================================
# 状态流转规则
# ============================================================

VALID_STATUS_TRANSITIONS = {
    RobotStatus.OFFLINE: [RobotStatus.IDLE],
    RobotStatus.IDLE: [RobotStatus.WORKING, RobotStatus.CHARGING, RobotStatus.OFFLINE],
    RobotStatus.WORKING: [RobotStatus.PAUSED, RobotStatus.IDLE, RobotStatus.ERROR],
    RobotStatus.PAUSED: [RobotStatus.WORKING, RobotStatus.IDLE],
    RobotStatus.CHARGING: [RobotStatus.IDLE, RobotStatus.OFFLINE],
    RobotStatus.ERROR: [RobotStatus.IDLE, RobotStatus.OFFLINE],
    RobotStatus.MAINTENANCE: [RobotStatus.IDLE, RobotStatus.OFFLINE],
}


# ============================================================
# 存储层实现
# ============================================================

class InMemoryRobotStorage:
    """内存存储实现"""

    def __init__(self):
        self._robots: Dict[str, Robot] = {}
        self._status_snapshots: Dict[str, RobotStatusSnapshot] = {}
        self._errors: Dict[str, RobotError] = {}
        self._tasks: Dict[str, RobotTask] = {}
        self._init_sample_data()

    def _init_sample_data(self):
        """初始化示例数据"""
        tenant_id = "tenant_001"
        now = datetime.utcnow()

        # 示例机器人
        robots = [
            Robot(
                robot_id="robot_001",
                tenant_id=tenant_id,
                name="清洁机器人A-01",
                brand=RobotBrand.GAOXIAN,
                model="GS-50",
                serial_number="GX2024010001",
                robot_type=RobotType.CLEANING,
                building_id="building_001",
                floor_ids=["floor_001", "floor_002"],
                home_location=Location(x=5.0, y=5.0, floor_id="floor_001"),
                capabilities=RobotCapability(
                    can_vacuum=True,
                    can_mop=True,
                    can_auto_charge=True,
                    can_elevator=True,
                    max_area=600,
                    max_runtime=240
                ),
                status=RobotStatus.IDLE,
                registered_at=now,
                last_seen_at=now
            ),
            Robot(
                robot_id="robot_002",
                tenant_id=tenant_id,
                name="清洁机器人A-02",
                brand=RobotBrand.GAOXIAN,
                model="GS-50",
                serial_number="GX2024010002",
                robot_type=RobotType.CLEANING,
                building_id="building_001",
                floor_ids=["floor_001"],
                home_location=Location(x=8.0, y=5.0, floor_id="floor_001"),
                capabilities=RobotCapability(
                    can_vacuum=True,
                    can_mop=True,
                    can_auto_charge=True,
                    can_elevator=False,
                    max_area=500,
                    max_runtime=180
                ),
                status=RobotStatus.CHARGING,
                registered_at=now,
                last_seen_at=now
            ),
            Robot(
                robot_id="robot_003",
                tenant_id=tenant_id,
                name="清洁机器人B-01",
                brand=RobotBrand.GAOXIAN,
                model="GS-75",
                serial_number="GX2024010003",
                robot_type=RobotType.CLEANING,
                building_id="building_001",
                floor_ids=["floor_002", "floor_003"],
                home_location=Location(x=10.0, y=8.0, floor_id="floor_002"),
                capabilities=RobotCapability(
                    can_vacuum=True,
                    can_mop=True,
                    can_auto_charge=True,
                    can_elevator=True,
                    max_area=800,
                    max_runtime=300
                ),
                status=RobotStatus.WORKING,
                registered_at=now,
                last_seen_at=now
            ),
        ]

        for r in robots:
            self._robots[r.robot_id] = r

        # 初始状态快照
        status_snapshots = [
            RobotStatusSnapshot(
                robot_id="robot_001",
                status=RobotStatus.IDLE,
                current_location=Location(x=5.0, y=5.0, floor_id="floor_001"),
                battery_level=85,
                water_level=70,
                dustbin_level=30,
                timestamp=now
            ),
            RobotStatusSnapshot(
                robot_id="robot_002",
                status=RobotStatus.CHARGING,
                current_location=Location(x=8.0, y=5.0, floor_id="floor_001"),
                battery_level=45,
                water_level=80,
                dustbin_level=20,
                timestamp=now
            ),
            RobotStatusSnapshot(
                robot_id="robot_003",
                status=RobotStatus.WORKING,
                current_location=Location(x=15.0, y=12.0, floor_id="floor_002"),
                battery_level=72,
                water_level=60,
                dustbin_level=45,
                current_task_id="robot_task_001",
                current_zone_id="zone_003",
                task_progress=35.0,
                speed=0.5,
                cleaning_mode=CleaningMode.VACUUM_MOP,
                cleaning_intensity=CleaningIntensity.STANDARD,
                timestamp=now
            ),
        ]

        for s in status_snapshots:
            self._status_snapshots[s.robot_id] = s

        # 示例任务（机器人正在执行）
        task = RobotTask(
            robot_task_id="robot_task_001",
            robot_id="robot_003",
            zone_id="zone_003",
            task_type=CleaningMode.VACUUM_MOP,
            cleaning_intensity=CleaningIntensity.STANDARD,
            status="running",
            progress=35.0,
            started_at=now,
            estimated_duration=45
        )
        self._tasks[task.robot_task_id] = task

        # 示例错误
        error = RobotError(
            error_id="error_001",
            robot_id="robot_002",
            robot_name="清洁机器人A-02",
            error_code="E101",
            error_type="sensor_fault",
            severity=ErrorSeverity.WARNING,
            message="左侧避障传感器信号弱",
            location=Location(x=8.0, y=5.0, floor_id="floor_001"),
            occurred_at=now,
            resolved=False
        )
        self._errors[error.error_id] = error

    # ========== 机器人操作 ==========

    async def get_robot(self, robot_id: str) -> Optional[Robot]:
        """获取机器人"""
        return self._robots.get(robot_id)

    async def list_robots(
        self,
        tenant_id: str,
        building_id: Optional[str] = None,
        status: Optional[str] = None,
        robot_type: Optional[str] = None
    ) -> List[Robot]:
        """列出机器人"""
        result = []
        for robot in self._robots.values():
            if robot.tenant_id != tenant_id:
                continue
            if building_id and robot.building_id != building_id:
                continue
            if status and robot.status.value != status:
                continue
            if robot_type and robot.robot_type.value != robot_type:
                continue
            result.append(robot)
        return result

    async def update_robot_status(
        self,
        robot_id: str,
        new_status: RobotStatus
    ) -> Optional[Robot]:
        """更新机器人状态"""
        robot = self._robots.get(robot_id)
        if not robot:
            return None
        robot.status = new_status
        robot.last_seen_at = datetime.utcnow()
        return robot

    # ========== 状态快照操作 ==========

    async def get_status_snapshot(self, robot_id: str) -> Optional[RobotStatusSnapshot]:
        """获取状态快照"""
        return self._status_snapshots.get(robot_id)

    async def update_status_snapshot(
        self,
        robot_id: str,
        updates: dict
    ) -> Optional[RobotStatusSnapshot]:
        """更新状态快照"""
        snapshot = self._status_snapshots.get(robot_id)
        if not snapshot:
            return None

        for key, value in updates.items():
            if hasattr(snapshot, key):
                setattr(snapshot, key, value)

        snapshot.timestamp = datetime.utcnow()
        return snapshot

    async def batch_get_status(self, robot_ids: List[str]) -> List[RobotStatusSnapshot]:
        """批量获取状态"""
        return [
            self._status_snapshots[rid]
            for rid in robot_ids
            if rid in self._status_snapshots
        ]

    # ========== 任务操作 ==========

    async def save_robot_task(self, task: RobotTask) -> RobotTask:
        """保存机器人任务"""
        self._tasks[task.robot_task_id] = task
        return task

    async def get_robot_task(self, robot_task_id: str) -> Optional[RobotTask]:
        """获取机器人任务"""
        return self._tasks.get(robot_task_id)

    async def get_current_task(self, robot_id: str) -> Optional[RobotTask]:
        """获取机器人当前任务"""
        for task in self._tasks.values():
            if task.robot_id == robot_id and task.status in ["started", "running", "paused"]:
                return task
        return None

    async def update_robot_task(
        self,
        robot_task_id: str,
        updates: dict
    ) -> Optional[RobotTask]:
        """更新机器人任务"""
        task = self._tasks.get(robot_task_id)
        if not task:
            return None

        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)

        return task

    # ========== 错误操作 ==========

    async def save_error(self, error: RobotError) -> RobotError:
        """保存错误"""
        self._errors[error.error_id] = error
        return error

    async def get_error(self, error_id: str) -> Optional[RobotError]:
        """获取错误"""
        return self._errors.get(error_id)

    async def list_errors(
        self,
        robot_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        severity: Optional[str] = None,
        resolved: Optional[bool] = None,
        limit: int = 50
    ) -> List[RobotError]:
        """列出错误"""
        result = []
        for error in self._errors.values():
            if robot_id and error.robot_id != robot_id:
                continue
            if severity and error.severity.value != severity:
                continue
            if resolved is not None and error.resolved != resolved:
                continue
            result.append(error)
            if len(result) >= limit:
                break

        # 按发生时间倒序
        result.sort(key=lambda e: e.occurred_at, reverse=True)
        return result

    async def clear_error(
        self,
        error_id: str,
        resolved_by: str = "system"
    ) -> Optional[RobotError]:
        """清除错误"""
        error = self._errors.get(error_id)
        if not error:
            return None

        error.resolved = True
        error.resolved_at = datetime.utcnow()
        error.resolved_by = resolved_by
        return error

    async def get_active_errors_for_robot(self, robot_id: str) -> List[RobotError]:
        """获取机器人的活跃错误"""
        return [
            e for e in self._errors.values()
            if e.robot_id == robot_id and not e.resolved
        ]
