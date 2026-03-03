"""
A1/D1 事件驱动数据采集器

响应实时事件执行采集动作:
- STATUS_CHANGED: 记录状态变更
- BATTERY_CRITICAL: 记录 + 触发告警
- ERROR_OCCURRED: 记录 + 触发异常处理
- TASK_COMPLETED: 记录 + 更新任务完成数据
"""

import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime

from .models import RobotEventType, RobotRealtimeEvent

logger = logging.getLogger(__name__)


class EventDrivenCollector:
    """
    事件驱动的数据采集器

    与D1定时采集共存。定时采集负责全量快照，
    事件驱动采集负责实时增量变更。
    """

    def __init__(self):
        self._handlers: Dict[RobotEventType, List[Callable]] = {}
        self._collected_events: List[Dict[str, Any]] = []  # 内存存储（后续接入TimescaleDB）
        self._alert_callbacks: List[Callable] = []

    def register_handler(
        self, event_type: RobotEventType, handler: Callable[[RobotRealtimeEvent], Awaitable[None]]
    ) -> None:
        """注册事件处理器"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def register_alert_callback(self, callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """注册告警回调"""
        self._alert_callbacks.append(callback)

    async def on_robot_event(self, event: RobotRealtimeEvent) -> None:
        """
        响应机器人实时事件

        根据事件类型执行不同的采集和处理动作。
        """
        # 记录所有事件
        record = {
            "event_id": event.event_id,
            "robot_id": event.robot_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "data": event.data,
            "collected_at": datetime.utcnow().isoformat(),
        }
        self._collected_events.append(record)

        logger.info(
            f"Collected event {event.event_type.value} from robot {event.robot_id}"
        )

        # 执行事件特定处理
        if event.event_type == RobotEventType.BATTERY_CRITICAL:
            await self._handle_battery_critical(event)
        elif event.event_type == RobotEventType.ERROR_OCCURRED:
            await self._handle_error(event)
        elif event.event_type == RobotEventType.TASK_COMPLETED:
            await self._handle_task_completed(event)

        # 调用注册的处理器
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Handler error for {event.event_type.value}: {e}")

    async def on_threshold_breach(
        self, metric: str, value: float, robot_id: str
    ) -> None:
        """阈值突破时的即时采集和告警"""
        alert = {
            "type": "threshold_breach",
            "metric": metric,
            "value": value,
            "robot_id": robot_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._collected_events.append(alert)

        for callback in self._alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

    async def _handle_battery_critical(self, event: RobotRealtimeEvent) -> None:
        """处理电量告警"""
        alert = {
            "type": "battery_critical",
            "robot_id": event.robot_id,
            "battery_level": event.data.get("battery_level", 0),
            "timestamp": event.timestamp.isoformat(),
            "severity": "high",
        }

        for callback in self._alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Battery alert callback error: {e}")

    async def _handle_error(self, event: RobotRealtimeEvent) -> None:
        """处理错误事件"""
        alert = {
            "type": "robot_error",
            "robot_id": event.robot_id,
            "error_code": event.data.get("error_code", "UNKNOWN"),
            "message": event.data.get("message", ""),
            "timestamp": event.timestamp.isoformat(),
            "severity": "critical",
        }

        for callback in self._alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Error alert callback error: {e}")

    async def _handle_task_completed(self, event: RobotRealtimeEvent) -> None:
        """处理任务完成事件"""
        logger.info(
            f"Task completed by robot {event.robot_id}: "
            f"task_id={event.data.get('task_id', 'unknown')}"
        )

    def get_collected_events(
        self,
        robot_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """查询已采集的事件"""
        result = self._collected_events

        if robot_id:
            result = [e for e in result if e.get("robot_id") == robot_id]
        if event_type:
            result = [e for e in result if e.get("event_type") == event_type]

        return result[-limit:]

    @property
    def event_count(self) -> int:
        return len(self._collected_events)
