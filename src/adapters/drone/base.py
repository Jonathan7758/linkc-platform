"""
Drone Adapter Base - 无人机适配器基类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class DroneStatus(Enum):
    """无人机状态"""
    IDLE = "idle"
    TAKING_OFF = "taking_off"
    FLYING = "flying"
    HOVERING = "hovering"
    LANDING = "landing"
    CHARGING = "charging"
    ERROR = "error"
    OFFLINE = "offline"


class FlightMode(Enum):
    """飞行模式"""
    MANUAL = "manual"
    AUTO = "auto"
    PATROL = "patrol"
    INSPECTION = "inspection"
    DELIVERY = "delivery"
    RETURN_HOME = "return_home"


@dataclass
class DronePosition:
    """无人机位置"""
    latitude: float
    longitude: float
    altitude: float  # 米
    heading: float = 0.0  # 航向角度 0-360


@dataclass
class DroneState:
    """无人机状态信息"""
    drone_id: str
    status: DroneStatus
    position: Optional[DronePosition] = None
    battery_percent: int = 100
    flight_mode: FlightMode = FlightMode.MANUAL
    speed_ms: float = 0.0
    is_armed: bool = False
    signal_strength: int = 100
    camera_active: bool = False
    payload_attached: bool = False
    error_code: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FlightTask:
    """飞行任务"""
    task_id: str
    task_type: str  # patrol, inspect, deliver, photograph
    waypoints: List[DronePosition] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    altitude_m: float = 50.0
    speed_ms: float = 5.0


@dataclass
class FlightResult:
    """飞行结果"""
    success: bool
    task_id: str
    duration_sec: int = 0
    distance_m: float = 0.0
    images_captured: int = 0
    video_duration_sec: int = 0
    anomalies_detected: List[Dict[str, Any]] = field(default_factory=list)
    error_message: str = ""


class DroneAdapter(ABC):
    """
    无人机适配器基类
    
    为不同品牌的无人机提供统一的接口
    支持的操作:
    - 起飞/降落
    - 航点飞行
    - 巡逻/检查任务
    - 相机控制
    - 配送任务
    """
    
    def __init__(self, drone_id: str, config: Dict[str, Any] = None):
        self.drone_id = drone_id
        self.config = config or {}
        self._state = DroneState(
            drone_id=drone_id,
            status=DroneStatus.OFFLINE
        )
    
    @property
    def state(self) -> DroneState:
        """获取当前状态"""
        return self._state
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接无人机"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    async def get_status(self) -> DroneState:
        """获取状态"""
        pass
    
    @abstractmethod
    async def arm(self) -> bool:
        """解锁电机"""
        pass
    
    @abstractmethod
    async def disarm(self) -> bool:
        """锁定电机"""
        pass
    
    @abstractmethod
    async def takeoff(self, altitude_m: float = 10.0) -> bool:
        """起飞到指定高度"""
        pass
    
    @abstractmethod
    async def land(self) -> bool:
        """降落"""
        pass
    
    @abstractmethod
    async def return_to_home(self) -> bool:
        """返回起飞点"""
        pass
    
    @abstractmethod
    async def goto_position(
        self,
        position: DronePosition,
        speed_ms: float = 5.0
    ) -> bool:
        """飞往指定位置"""
        pass
    
    @abstractmethod
    async def execute_flight_task(self, task: FlightTask) -> FlightResult:
        """执行飞行任务"""
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
        """拍照，返回图片路径或 URL"""
        pass
    
    @abstractmethod
    async def start_video_recording(self) -> bool:
        """开始录像"""
        pass
    
    @abstractmethod
    async def stop_video_recording(self) -> Optional[str]:
        """停止录像，返回视频路径或 URL"""
        pass
    
    @abstractmethod
    async def emergency_stop(self) -> bool:
        """紧急停止"""
        pass
    
    # ===== 辅助方法 =====
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return (
            self._state.status in [DroneStatus.IDLE, DroneStatus.HOVERING]
            and self._state.battery_percent >= 20
            and not self._state.error_code
        )
    
    def can_fly(self) -> bool:
        """检查是否可以飞行"""
        return (
            self._state.status in [DroneStatus.IDLE, DroneStatus.HOVERING]
            and self._state.battery_percent >= 30
            and self._state.signal_strength >= 50
        )
