"""
A1: 异常升级系统
================
自动检测异常并升级处理
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, TYPE_CHECKING
import uuid
import logging
import asyncio

if TYPE_CHECKING:
    from .runtime import AgentRuntime

logger = logging.getLogger(__name__)


class EscalationLevel(str, Enum):
    """升级级别"""
    INFO = "info"           # 信息通知
    WARNING = "warning"     # 警告，需关注
    ERROR = "error"         # 错误，需处理
    CRITICAL = "critical"   # 严重，需立即处理


@dataclass
class EscalationRule:
    """升级规则"""
    rule_id: str
    trigger_type: str       # error_type / threshold / pattern
    trigger_config: dict
    level: EscalationLevel
    actions: List[str] = field(default_factory=list)  # notify / pause_agent / human_approval


@dataclass
class EscalationEvent:
    """升级事件"""
    event_id: str = field(default_factory=lambda: f"esc_{uuid.uuid4().hex[:12]}")
    agent_id: str = ""
    tenant_id: str = ""
    level: EscalationLevel = EscalationLevel.INFO
    reason: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending / acknowledged / resolved
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "agent_id": self.agent_id,
            "tenant_id": self.tenant_id,
            "level": self.level.value,
            "reason": self.reason,
            "context": self.context,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "resolution": self.resolution,
        }


class EscalationHandler:
    """升级处理器"""

    def __init__(self, runtime: Optional['AgentRuntime'] = None):
        self.runtime = runtime
        self.rules: List[EscalationRule] = []
        self._events: Dict[str, EscalationEvent] = {}
        self._notification_handlers: List[callable] = []

    def add_rule(self, rule: EscalationRule) -> None:
        """添加升级规则"""
        self.rules.append(rule)
        logger.info(f"Added escalation rule: {rule.rule_id}")

    def add_notification_handler(self, handler: callable) -> None:
        """添加通知处理器"""
        self._notification_handlers.append(handler)

    async def handle(
        self,
        agent_id: str,
        level: EscalationLevel,
        reason: str,
        context: Dict[str, Any]
    ) -> str:
        """
        处理升级事件

        Args:
            agent_id: 触发升级的 Agent ID
            level: 升级级别
            reason: 升级原因
            context: 上下文信息

        Returns:
            事件 ID
        """
        # 获取租户 ID
        tenant_id = ""
        if self.runtime and agent_id in self.runtime._agents:
            tenant_id = self.runtime._agents[agent_id].config.tenant_id

        # 创建升级事件
        event = EscalationEvent(
            agent_id=agent_id,
            tenant_id=tenant_id,
            level=level,
            reason=reason,
            context=context
        )

        # 保存事件
        self._events[event.event_id] = event

        logger.warning(
            f"Escalation event: {event.event_id} - {level.value} - {reason}",
            extra={"agent_id": agent_id, "level": level.value}
        )

        # 根据级别执行动作
        await self._execute_actions(event)

        return event.event_id

    async def _execute_actions(self, event: EscalationEvent) -> None:
        """执行升级动作"""
        try:
            if event.level == EscalationLevel.CRITICAL:
                # 暂停 Agent
                if self.runtime:
                    agent = self.runtime._agents.get(event.agent_id)
                    if agent:
                        agent.state = AgentState.ERROR
                        logger.info(f"Paused agent {event.agent_id} due to critical escalation")

                # 发送紧急通知
                await self._send_notification(event, urgent=True)

            elif event.level == EscalationLevel.ERROR:
                # 发送通知
                await self._send_notification(event, urgent=False)

            elif event.level == EscalationLevel.WARNING:
                # 记录，可选通知
                await self._send_notification(event, urgent=False)

        except Exception as e:
            logger.error(f"Error executing escalation actions: {e}")

    async def _send_notification(self, event: EscalationEvent, urgent: bool = False) -> None:
        """发送通知"""
        for handler in self._notification_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event, urgent)
                else:
                    handler(event, urgent)
            except Exception as e:
                logger.error(f"Notification handler error: {e}")

        # 默认日志通知
        log_msg = f"[{'URGENT ' if urgent else ''}ESCALATION] {event.level.value}: {event.reason}"
        if urgent:
            logger.critical(log_msg)
        else:
            logger.warning(log_msg)

    async def acknowledge(self, event_id: str, user_id: str) -> bool:
        """确认升级事件"""
        event = self._events.get(event_id)
        if not event:
            return False

        event.status = "acknowledged"
        event.acknowledged_at = datetime.utcnow()
        event.acknowledged_by = user_id

        logger.info(f"Escalation {event_id} acknowledged by {user_id}")
        return True

    async def resolve(
        self,
        event_id: str,
        user_id: str,
        resolution: str
    ) -> bool:
        """解决升级事件"""
        event = self._events.get(event_id)
        if not event:
            return False

        event.status = "resolved"
        event.resolved_at = datetime.utcnow()
        event.resolved_by = user_id
        event.resolution = resolution

        logger.info(f"Escalation {event_id} resolved by {user_id}: {resolution}")
        return True

    def list_events(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[str] = None,
        level: Optional[EscalationLevel] = None,
        limit: int = 100
    ) -> List[EscalationEvent]:
        """列出升级事件"""
        events = list(self._events.values())

        if tenant_id:
            events = [e for e in events if e.tenant_id == tenant_id]
        if status:
            events = [e for e in events if e.status == status]
        if level:
            events = [e for e in events if e.level == level]

        # 按时间倒序
        events.sort(key=lambda x: x.created_at, reverse=True)
        return events[:limit]

    def get_event(self, event_id: str) -> Optional[EscalationEvent]:
        """获取单个事件"""
        return self._events.get(event_id)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        events = list(self._events.values())
        return {
            "total": len(events),
            "pending": sum(1 for e in events if e.status == "pending"),
            "acknowledged": sum(1 for e in events if e.status == "acknowledged"),
            "resolved": sum(1 for e in events if e.status == "resolved"),
            "by_level": {
                level.value: sum(1 for e in events if e.level == level)
                for level in EscalationLevel
            }
        }


# 需要避免循环导入
from .base import AgentState
