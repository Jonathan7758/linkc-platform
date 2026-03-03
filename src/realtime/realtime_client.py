"""
A1 实时事件通道 — 通用实时客户端

支持:
- 连接管理（connect/disconnect）
- 事件订阅（subscribe/unsubscribe）
- 断连重连（指数退避 + 抖动）
- 心跳保活
- 事件缓冲（断连期间缓存事件）
"""

import asyncio
import logging
import random
import time
import uuid
from collections import deque
from datetime import datetime
from typing import Dict, Any, List, Optional, Set

from .models import (
    RobotEventType,
    RobotRealtimeEvent,
    ConnectionStatus,
    EventCallback,
    RECONNECT_CONFIG,
    EVENT_BUFFER_CONFIG,
)

logger = logging.getLogger(__name__)


class RealtimeClient:
    """
    机器人实时通信客户端

    通用实现，通过 event_source 回调获取事件。
    M3/M4 各自提供事件源适配器。
    """

    def __init__(
        self,
        brand: str = "generic",
        reconnect_config: Optional[Dict] = None,
        buffer_config: Optional[Dict] = None,
    ):
        self.brand = brand
        self._reconnect_config = reconnect_config or RECONNECT_CONFIG
        self._buffer_config = buffer_config or EVENT_BUFFER_CONFIG

        # 连接状态
        self._connections: Dict[str, ConnectionStatus] = {}
        self._connected_robots: Set[str] = set()

        # 订阅管理
        self._subscriptions: Dict[str, Dict] = {}  # sub_id -> {robot_id, event_types, callback}
        self._robot_subscriptions: Dict[str, List[str]] = {}  # robot_id -> [sub_ids]

        # 事件缓冲
        self._event_buffers: Dict[str, deque] = {}  # robot_id -> deque of events

        # 后台任务
        self._heartbeat_tasks: Dict[str, asyncio.Task] = {}
        self._polling_tasks: Dict[str, asyncio.Task] = {}

        # 事件源回调（由适配器设置）
        self._event_source: Optional[Any] = None

        # 模拟状态（用于mock/测试）
        self._simulated_states: Dict[str, Dict[str, Any]] = {}

    @property
    def connected_robots(self) -> List[str]:
        return list(self._connected_robots)

    async def connect(self, robot_id: str) -> bool:
        """建立与机器人的实时连接"""
        if robot_id in self._connected_robots:
            return True

        try:
            self._connections[robot_id] = ConnectionStatus(
                connected=True,
                last_heartbeat=datetime.utcnow(),
            )
            self._connected_robots.add(robot_id)
            self._event_buffers[robot_id] = deque(
                maxlen=self._buffer_config["max_buffer_size"]
            )

            # 启动心跳
            self._heartbeat_tasks[robot_id] = asyncio.create_task(
                self._heartbeat_loop(robot_id)
            )

            logger.info(f"[{self.brand}] Connected to robot {robot_id}")
            return True
        except Exception as e:
            logger.error(f"[{self.brand}] Failed to connect to {robot_id}: {e}")
            return False

    async def disconnect(self, robot_id: str) -> bool:
        """断开实时连接"""
        if robot_id not in self._connected_robots:
            return False

        # 取消后台任务
        if robot_id in self._heartbeat_tasks:
            self._heartbeat_tasks[robot_id].cancel()
            del self._heartbeat_tasks[robot_id]

        if robot_id in self._polling_tasks:
            self._polling_tasks[robot_id].cancel()
            del self._polling_tasks[robot_id]

        self._connected_robots.discard(robot_id)
        if robot_id in self._connections:
            self._connections[robot_id].connected = False

        # 清理订阅
        sub_ids = self._robot_subscriptions.pop(robot_id, [])
        for sub_id in sub_ids:
            self._subscriptions.pop(sub_id, None)

        logger.info(f"[{self.brand}] Disconnected from robot {robot_id}")
        return True

    async def subscribe(
        self,
        robot_id: str,
        event_types: List[RobotEventType],
        callback: EventCallback,
    ) -> str:
        """订阅指定事件类型"""
        if robot_id not in self._connected_robots:
            raise ValueError(f"Robot {robot_id} not connected")

        sub_id = f"sub-{uuid.uuid4().hex[:8]}"
        self._subscriptions[sub_id] = {
            "robot_id": robot_id,
            "event_types": set(event_types),
            "callback": callback,
        }

        if robot_id not in self._robot_subscriptions:
            self._robot_subscriptions[robot_id] = []
        self._robot_subscriptions[robot_id].append(sub_id)

        logger.info(
            f"[{self.brand}] Subscription {sub_id} created for robot {robot_id}, "
            f"events: {[e.value for e in event_types]}"
        )
        return sub_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        sub = self._subscriptions.pop(subscription_id, None)
        if sub is None:
            return False

        robot_id = sub["robot_id"]
        if robot_id in self._robot_subscriptions:
            self._robot_subscriptions[robot_id] = [
                s for s in self._robot_subscriptions[robot_id] if s != subscription_id
            ]
        return True

    async def get_connection_status(self, robot_id: str) -> Dict[str, Any]:
        """获取连接状态"""
        conn = self._connections.get(robot_id)
        if conn is None:
            return {"connected": False}
        return {
            "connected": conn.connected,
            "last_heartbeat": conn.last_heartbeat.isoformat() if conn.last_heartbeat else None,
            "reconnect_count": conn.reconnect_count,
            "last_error": conn.last_error,
            "uptime_seconds": conn.uptime_seconds,
        }

    async def emit_event(self, event: RobotRealtimeEvent) -> None:
        """
        发送事件到所有匹配的订阅者

        由事件源（polling/websocket/mock）调用。
        """
        robot_id = event.robot_id

        if robot_id not in self._connected_robots:
            # 机器人未连接，缓冲事件
            if robot_id in self._event_buffers:
                self._event_buffers[robot_id].append(event)
            return

        sub_ids = self._robot_subscriptions.get(robot_id, [])
        for sub_id in sub_ids:
            sub = self._subscriptions.get(sub_id)
            if sub is None:
                continue

            if event.event_type in sub["event_types"]:
                try:
                    await sub["callback"](event)
                except Exception as e:
                    logger.error(f"Callback error for sub {sub_id}: {e}")

    async def simulate_disconnect(self, robot_id: str) -> None:
        """模拟断连（测试用）"""
        if robot_id in self._connected_robots:
            self._connected_robots.discard(robot_id)
            if robot_id in self._connections:
                self._connections[robot_id].connected = False

            # 发送断连事件
            event = RobotRealtimeEvent.create(
                robot_id, RobotEventType.CONNECTIVITY_LOST, {}
            )
            # 缓冲后续事件
            logger.info(f"[{self.brand}] Simulated disconnect for {robot_id}")

    async def simulate_reconnect(self, robot_id: str) -> None:
        """模拟重连（测试用）"""
        if robot_id not in self._connected_robots and robot_id in self._connections:
            self._connected_robots.add(robot_id)
            self._connections[robot_id].connected = True
            self._connections[robot_id].reconnect_count += 1
            self._connections[robot_id].last_heartbeat = datetime.utcnow()

            # 刷新缓冲事件
            await self._flush_buffer(robot_id)

            event = RobotRealtimeEvent.create(
                robot_id, RobotEventType.CONNECTIVITY_RESTORED, {}
            )
            await self.emit_event(event)
            logger.info(f"[{self.brand}] Simulated reconnect for {robot_id}")

    async def _flush_buffer(self, robot_id: str) -> None:
        """刷新缓冲事件"""
        buffer = self._event_buffers.get(robot_id)
        if not buffer:
            return

        events = list(buffer)
        buffer.clear()

        for event in events:
            await self.emit_event(event)

    async def _heartbeat_loop(self, robot_id: str) -> None:
        """心跳保活循环"""
        interval = self._reconnect_config.get("health_check_interval", 30)
        try:
            while robot_id in self._connected_robots:
                await asyncio.sleep(interval)
                if robot_id in self._connections:
                    self._connections[robot_id].last_heartbeat = datetime.utcnow()
        except asyncio.CancelledError:
            pass

    async def _reconnect_with_backoff(self, robot_id: str) -> bool:
        """指数退避重连"""
        config = self._reconnect_config
        delay = config["initial_delay_seconds"]

        for attempt in range(config["max_retries"]):
            if config.get("jitter"):
                actual_delay = delay * (0.5 + random.random())
            else:
                actual_delay = delay

            logger.info(
                f"[{self.brand}] Reconnect attempt {attempt + 1} for {robot_id} "
                f"in {actual_delay:.1f}s"
            )
            await asyncio.sleep(actual_delay)

            success = await self.connect(robot_id)
            if success:
                return True

            delay = min(delay * config["backoff_multiplier"], config["max_delay_seconds"])

        logger.error(f"[{self.brand}] Max reconnect attempts reached for {robot_id}")
        return False

    async def close(self) -> None:
        """关闭所有连接"""
        robots = list(self._connected_robots)
        for robot_id in robots:
            await self.disconnect(robot_id)
