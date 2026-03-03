"""
A1 实时事件通道

提供机器人实时事件推送能力:
- RealtimeClient: 与机器人建立WebSocket连接
- EventDrivenCollector: 事件驱动的数据采集
- WebSocket/SSE端点: 向前端推送实时事件
"""

from .models import (
    RobotEventType,
    RobotRealtimeEvent,
    ConnectionStatus,
    EventCallback,
)
from .realtime_client import RealtimeClient
from .event_driven_collector import EventDrivenCollector
from .websocket_endpoints import (
    WebSocketConnection,
    MonitoringWebSocketManager,
)

__all__ = [
    "RobotEventType",
    "RobotRealtimeEvent",
    "ConnectionStatus",
    "EventCallback",
    "RealtimeClient",
    "EventDrivenCollector",
    "WebSocketConnection",
    "MonitoringWebSocketManager",
]
