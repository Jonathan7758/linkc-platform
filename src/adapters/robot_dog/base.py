"""
Robot Dog Adapter Base - 机器狗适配器基类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class RobotDogStatus(Enum):
    """机器狗状态"""
    IDLE = "idle"
    STANDING = "standing"
    WALKING = "walking"
    RUNNING = "running"
    CLIMBING = "climbing"
    RESTING = "resting"
    CHARGING = "charging"
    ERROR = "error"
    OFFLINE = "offline"


class MovementMode(Enum):
    """运动模式"""
    WALK = "walk"
    TROT = "trot"
    RUN = "run"
    CRAWL = "crawl"
    CLIMB = "climb"


class GaitType(Enum):
    """步态类型"""
    NORMAL = "normal"
    STABLE = "stable"
    FAST = "fast"
    STAIR = "stair"
    SLOPE = "slope"


@dataclass
class RobotDogPosition:
    """机器狗位置"""
    x: float  # 米
    y: float  # 米
    z: float  # 米 (高度)
    yaw: float = 0.0  # 航向角
    pitch: float = 0.0  # 俯仰角
    roll: float = 0.0  # 横滚角


@dataclass
class RobotDogState:
    """机器狗状态信息"""
    robot_id: str
    status: RobotDogStatus
    position: Optional[RobotDogPosition] = None
    battery_percent: int = 100
    movement_mode: MovementMode = MovementMode.WALK
    gait_type: GaitType = GaitType.NORMAL
    speed_ms: float = 0.0
    temperature_c: float = 25.0
    camera_active: bool = False
    lidar_active: bool = False
    has_payload: bool = False
    error_code: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GroundTask:
    """地面任务"""
    task_id: str
    task_type: str  # patrol, inspect, escort, companion
    waypoints: List[RobotDogPosition] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    speed_mode: str = "normal"  # slow, normal, fast


@dataclass
class GroundTaskResult:
    """地面任务结果"""
    success: bool
    task_id: str
    duration_sec: int = 0
    distance_m: float = 0.0
    images_captured: int = 0
    anomalies_detected: List[Dict[str, Any]] = field(default_factory=list)
    health_data: Dict[str, Any] = field(default_factory=dict)
    gas_readings: Dict[str, float] = field(default_factory=dict)
    error_message: str = ""


class RobotDogAdapter(ABC):
    """
    机器狗适配器基类

    为不同品牌的机器狗提供统一的接口
    支持的操作:
    - 站立/卧下
    - 行走/跑步
    - 爬楼梯/斜坡
    - 巡逻/检查/护送任务
    - 传感器数据采集
    """

    def __init__(self, robot_id: str, config: Dict[str, Any] = None):
        self.robot_id = robot_id
        self.config = config or {}
        self._state = RobotDogState(
            robot_id=robot_id,
            status=RobotDogStatus.OFFLINE
        )

    @property
    def state(self) -> RobotDogState:
        """获取当前状态"""
        return self._state

    @abstractmethod
    async def connect(self) -> bool:
        """连接机器狗"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass

    @abstractmethod
    async def get_status(self) -> RobotDogState:
        """获取状态"""
        pass

    @abstractmethod
    async def stand_up(self) -> bool:
        """站立"""
        pass

    @abstractmethod
    async def sit_down(self) -> bool:
        """坐下"""
        pass

    @abstractmethod
    async def lie_down(self) -> bool:
        """卧下"""
        pass

    @abstractmethod
    async def set_movement_mode(self, mode: MovementMode) -> bool:
        """设置运动模式"""
        pass

    @abstractmethod
    async def set_gait(self, gait: GaitType) -> bool:
        """设置步态"""
        pass

    @abstractmethod
    async def goto_position(
        self,
        position: RobotDogPosition,
        speed_mode: str = "normal"
    ) -> bool:
        """移动到指定位置"""
        pass

    @abstractmethod
    async def execute_ground_task(self, task: GroundTask) -> GroundTaskResult:
        """执行地面任务"""
        pass

    @abstractmethod
    async def start_camera(self, mode: str = "visible") -> bool:
        """启动相机"""
        pass

    @abstractmethod
    async def stop_camera(self) -> bool:
        """停止相机"""
        pass

    @abstractmethod
    async def capture_image(self) -> Optional[str]:
        """拍照"""
        pass

    @abstractmethod
    async def start_lidar(self) -> bool:
        """启动激光雷达"""
        pass

    @abstractmethod
    async def stop_lidar(self) -> bool:
        """停止激光雷达"""
        pass

    @abstractmethod
    async def get_gas_readings(self) -> Dict[str, float]:
        """获取气体传感器读数"""
        pass

    @abstractmethod
    async def play_sound(self, sound_type: str) -> bool:
        """播放声音"""
        pass

    @abstractmethod
    async def emergency_stop(self) -> bool:
        """紧急停止"""
        pass

    # ===== 辅助方法 =====

    def is_available(self) -> bool:
        """检查是否可用"""
        return (
            self._state.status in [RobotDogStatus.IDLE, RobotDogStatus.STANDING]
            and self._state.battery_percent >= 20
            and not self._state.error_code
        )

    def can_move(self) -> bool:
        """检查是否可以移动"""
        return (
            self._state.status in [RobotDogStatus.IDLE, RobotDogStatus.STANDING, RobotDogStatus.WALKING]
            and self._state.battery_percent >= 30
        )
