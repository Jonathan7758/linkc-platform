"""
A1: 活动日志系统
================
记录 Agent 的所有活动，用于追踪和审计
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class AgentActivity:
    """Agent 活动记录"""
    activity_id: str = field(default_factory=lambda: f"act_{uuid.uuid4().hex[:12]}")
    agent_id: str = ""
    tenant_id: str = ""
    activity_type: str = ""  # tool_call / decision / escalation / state_change
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # 工具调用相关
    tool_name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    result_success: Optional[bool] = None
    result_data: Optional[Dict[str, Any]] = None

    # 决策相关
    decision_type: Optional[str] = None
    decision_reason: Optional[str] = None
    decision_confidence: Optional[float] = None

    # 其他
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            "activity_id": self.activity_id,
            "agent_id": self.agent_id,
            "tenant_id": self.tenant_id,
            "activity_type": self.activity_type,
            "timestamp": self.timestamp.isoformat(),
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result_success": self.result_success,
            "result_data": self.result_data,
            "decision_type": self.decision_type,
            "decision_reason": self.decision_reason,
            "decision_confidence": self.decision_confidence,
            "metadata": self.metadata,
        }


class ActivityLogger:
    """
    活动日志记录器

    带缓冲的异步日志记录，定期刷新到存储
    """

    def __init__(self, storage=None, buffer_size: int = 100, flush_interval: int = 30):
        """
        初始化活动记录器

        Args:
            storage: 存储服务 (可选)
            buffer_size: 缓冲区大小
            flush_interval: 刷新间隔 (秒)
        """
        self.storage = storage
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self._buffer: List[AgentActivity] = []
        self._all_activities: List[AgentActivity] = []  # 内存存储
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """启动定时刷新任务"""
        self._running = True
        self._flush_task = asyncio.create_task(self._periodic_flush())
        logger.info("Activity logger started")

    async def stop(self) -> None:
        """停止并刷新所有数据"""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        await self._flush()
        logger.info("Activity logger stopped")

    def log(self, activity: AgentActivity) -> None:
        """
        记录活动 (带缓冲)

        Args:
            activity: 活动记录
        """
        self._buffer.append(activity)
        self._all_activities.append(activity)  # 同时保存到内存

        if len(self._buffer) >= self.buffer_size:
            asyncio.create_task(self._flush())

        logger.debug(
            f"Activity logged: {activity.activity_type} - {activity.agent_id}",
            extra={"activity_id": activity.activity_id}
        )

    def log_tool_call(
        self,
        agent_id: str,
        tenant_id: str,
        tool_name: str,
        arguments: dict,
        success: bool,
        result_data: Optional[dict] = None
    ) -> None:
        """记录工具调用"""
        self.log(AgentActivity(
            agent_id=agent_id,
            tenant_id=tenant_id,
            activity_type="tool_call",
            tool_name=tool_name,
            arguments=arguments,
            result_success=success,
            result_data=result_data
        ))

    def log_decision(
        self,
        agent_id: str,
        tenant_id: str,
        decision_type: str,
        reason: str,
        confidence: float
    ) -> None:
        """记录决策"""
        self.log(AgentActivity(
            agent_id=agent_id,
            tenant_id=tenant_id,
            activity_type="decision",
            decision_type=decision_type,
            decision_reason=reason,
            decision_confidence=confidence
        ))

    def log_state_change(
        self,
        agent_id: str,
        tenant_id: str,
        old_state: str,
        new_state: str
    ) -> None:
        """记录状态变更"""
        self.log(AgentActivity(
            agent_id=agent_id,
            tenant_id=tenant_id,
            activity_type="state_change",
            metadata={"old_state": old_state, "new_state": new_state}
        ))

    async def _flush(self) -> None:
        """刷新缓冲区到存储"""
        if not self._buffer:
            return

        activities = self._buffer.copy()
        self._buffer.clear()

        if self.storage:
            try:
                await self.storage.save_activities(activities)
                logger.debug(f"Flushed {len(activities)} activities to storage")
            except Exception as e:
                logger.error(f"Failed to flush activities: {e}")
                # 重新放回缓冲区
                self._buffer.extend(activities)

    async def _periodic_flush(self) -> None:
        """定期刷新"""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic flush error: {e}")

    async def query(
        self,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        activity_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AgentActivity]:
        """
        查询活动日志

        Args:
            agent_id: Agent ID 筛选
            tenant_id: 租户 ID 筛选
            activity_type: 活动类型筛选
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制

        Returns:
            活动记录列表
        """
        # 如果有外部存储，从存储查询
        if self.storage:
            return await self.storage.query_activities(
                agent_id=agent_id,
                tenant_id=tenant_id,
                activity_type=activity_type,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )

        # 否则从内存查询
        results = self._all_activities.copy()

        if agent_id:
            results = [a for a in results if a.agent_id == agent_id]
        if tenant_id:
            results = [a for a in results if a.tenant_id == tenant_id]
        if activity_type:
            results = [a for a in results if a.activity_type == activity_type]
        if start_time:
            results = [a for a in results if a.timestamp >= start_time]
        if end_time:
            results = [a for a in results if a.timestamp <= end_time]

        # 按时间倒序
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        activities = self._all_activities
        return {
            "total": len(activities),
            "buffered": len(self._buffer),
            "by_type": {
                "tool_call": sum(1 for a in activities if a.activity_type == "tool_call"),
                "decision": sum(1 for a in activities if a.activity_type == "decision"),
                "state_change": sum(1 for a in activities if a.activity_type == "state_change"),
                "escalation": sum(1 for a in activities if a.activity_type == "escalation"),
            }
        }
