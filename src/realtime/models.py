"""
A1 实时事件通道 — 共享数据模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Callable, Awaitable, Optional
from enum import Enum
import uuid


class RobotEventType(Enum):
    """机器人实时事件类型"""
    STATUS_CHANGED = "robot.status.changed"
    BATTERY_UPDATE = "robot.battery.update"
    BATTERY_CRITICAL = "robot.battery.critical"
    TASK_PROGRESS = "robot.task.progress"
    TASK_COMPLETED = "robot.task.completed"
    ERROR_OCCURRED = "robot.error.occurred"
    POSITION_UPDATE = "robot.position.update"
    OBSTACLE_DETECTED = "robot.obstacle.detected"
    CONNECTIVITY_LOST = "robot.connectivity.lost"
    CONNECTIVITY_RESTORED = "robot.connectivity.restored"


@dataclass
class RobotRealtimeEvent:
    """机器人实时事件"""
    event_id: str
    robot_id: str
    event_type: RobotEventType
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, robot_id: str, event_type: RobotEventType, data: Dict[str, Any] = None):
        return cls(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            robot_id=robot_id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            data=data or {},
        )


@dataclass
class ConnectionStatus:
    """连接状态"""
    connected: bool = False
    last_heartbeat: Optional[datetime] = None
    reconnect_count: int = 0
    last_error: Optional[str] = None
    uptime_seconds: float = 0.0


# 回调类型
EventCallback = Callable[[RobotRealtimeEvent], Awaitable[None]]


# 重连配置
RECONNECT_CONFIG = {
    "max_retries": 10,
    "initial_delay_seconds": 1,
    "max_delay_seconds": 60,
    "backoff_multiplier": 2.0,
    "jitter": True,
    "health_check_interval": 30,
}

# 事件缓冲配置
EVENT_BUFFER_CONFIG = {
    "max_buffer_size": 1000,
    "max_buffer_age_seconds": 300,
    "overflow_strategy": "drop_oldest",
}
