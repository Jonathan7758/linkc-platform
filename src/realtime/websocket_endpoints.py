"""
G4 WebSocket/SSE 实时推送端点

向前端推送机器人实时事件:
- WebSocket: ws://host:port/ws/monitoring/{building_id}
- 客户端可通过消息筛选事件类型
- 支持多客户端并发连接
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Set, Optional

from .models import RobotEventType, RobotRealtimeEvent

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """单个 WebSocket 连接的状态管理"""

    def __init__(self, connection_id: str, building_id: str):
        self.connection_id = connection_id
        self.building_id = building_id
        self.subscribed_event_types: Set[str] = set()  # 空=接收全部
        self.connected_at = datetime.utcnow()
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._closed = False

    async def send_event(self, event_data: Dict[str, Any]) -> bool:
        """将事件放入队列等待发送"""
        if self._closed:
            return False

        event_type = event_data.get("event_type", "")
        if self.subscribed_event_types and event_type not in self.subscribed_event_types:
            return False

        try:
            self._queue.put_nowait(event_data)
            return True
        except asyncio.QueueFull:
            logger.warning(
                f"WebSocket queue full for connection {self.connection_id}, dropping event"
            )
            return False

    async def receive_event(self) -> Optional[Dict[str, Any]]:
        """从队列中取出事件"""
        if self._closed:
            return None
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=30.0)
        except asyncio.TimeoutError:
            return None

    def handle_client_message(self, message: Dict[str, Any]) -> None:
        """处理客户端发来的控制消息"""
        msg_type = message.get("type", "")

        if msg_type == "subscribe":
            event_types = message.get("event_types", [])
            self.subscribed_event_types.update(event_types)
            logger.info(
                f"Connection {self.connection_id} subscribed to: {event_types}"
            )
        elif msg_type == "unsubscribe":
            event_types = message.get("event_types", [])
            self.subscribed_event_types -= set(event_types)
            logger.info(
                f"Connection {self.connection_id} unsubscribed from: {event_types}"
            )
        elif msg_type == "ping":
            pass  # heartbeat, no action needed

    def close(self) -> None:
        self._closed = True

    @property
    def is_closed(self) -> bool:
        return self._closed


class MonitoringWebSocketManager:
    """
    WebSocket 连接管理器

    管理所有建筑的 WebSocket 连接，将机器人事件推送到
    对应建筑的所有连接客户端。
    """

    def __init__(self):
        # building_id -> {connection_id -> WebSocketConnection}
        self._connections: Dict[str, Dict[str, WebSocketConnection]] = {}
        # robot_id -> building_id 映射
        self._robot_building_map: Dict[str, str] = {}

    def register_robot(self, robot_id: str, building_id: str) -> None:
        """注册机器人所属建筑"""
        self._robot_building_map[robot_id] = building_id

    def connect(self, building_id: str) -> WebSocketConnection:
        """新建 WebSocket 连接"""
        conn_id = f"ws-{uuid.uuid4().hex[:8]}"
        conn = WebSocketConnection(conn_id, building_id)

        if building_id not in self._connections:
            self._connections[building_id] = {}
        self._connections[building_id][conn_id] = conn

        logger.info(
            f"WebSocket connected: {conn_id} for building {building_id} "
            f"(total: {len(self._connections[building_id])})"
        )
        return conn

    def disconnect(self, connection: WebSocketConnection) -> None:
        """断开 WebSocket 连接"""
        connection.close()
        building_conns = self._connections.get(connection.building_id, {})
        building_conns.pop(connection.connection_id, None)

        if not building_conns and connection.building_id in self._connections:
            del self._connections[connection.building_id]

        logger.info(f"WebSocket disconnected: {connection.connection_id}")

    async def broadcast_event(self, event: RobotRealtimeEvent) -> int:
        """
        将机器人事件广播到对应建筑的所有 WebSocket 连接

        Returns:
            成功发送的客户端数量
        """
        building_id = self._robot_building_map.get(event.robot_id)
        if building_id is None:
            # 未注册的机器人，广播到所有建筑
            building_id = "__all__"

        event_data = self._format_event(event)
        sent_count = 0

        if building_id == "__all__":
            for conns in self._connections.values():
                for conn in conns.values():
                    if await conn.send_event(event_data):
                        sent_count += 1
        else:
            conns = self._connections.get(building_id, {})
            for conn in conns.values():
                if await conn.send_event(event_data):
                    sent_count += 1

        return sent_count

    async def broadcast_to_building(
        self, building_id: str, event_data: Dict[str, Any]
    ) -> int:
        """向指定建筑的所有客户端广播"""
        conns = self._connections.get(building_id, {})
        sent_count = 0
        for conn in conns.values():
            if await conn.send_event(event_data):
                sent_count += 1
        return sent_count

    def get_connection_count(self, building_id: Optional[str] = None) -> int:
        """获取连接数"""
        if building_id:
            return len(self._connections.get(building_id, {}))
        return sum(len(conns) for conns in self._connections.values())

    def get_all_connections(
        self, building_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取连接列表"""
        result = []
        if building_id:
            conns = self._connections.get(building_id, {})
            for conn in conns.values():
                result.append(self._connection_info(conn))
        else:
            for conns in self._connections.values():
                for conn in conns.values():
                    result.append(self._connection_info(conn))
        return result

    @staticmethod
    def _format_event(event: RobotRealtimeEvent) -> Dict[str, Any]:
        """将 RobotRealtimeEvent 格式化为 WebSocket 消息"""
        return {
            "type": "robot_event",
            "event_type": event.event_type.value,
            "data": {
                "event_id": event.event_id,
                "robot_id": event.robot_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "payload": event.data,
            },
        }

    @staticmethod
    def _connection_info(conn: WebSocketConnection) -> Dict[str, Any]:
        return {
            "connection_id": conn.connection_id,
            "building_id": conn.building_id,
            "connected_at": conn.connected_at.isoformat(),
            "subscribed_event_types": list(conn.subscribed_event_types),
            "is_closed": conn.is_closed,
        }
