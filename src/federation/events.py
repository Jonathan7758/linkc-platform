"""
Federation Events - 事件发布
"""

import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import asyncio

logger = logging.getLogger("ecis_robot.federation.events")


class EventTypes:
    """事件类型常量"""
    # 任务事件
    TASK_STARTED = "ecis.task.started"
    TASK_PROGRESS = "ecis.task.progress"
    TASK_COMPLETED = "ecis.task.completed"
    TASK_FAILED = "ecis.task.failed"
    TASK_CANCELLED = "ecis.task.cancelled"

    # 机器人事件
    ROBOT_STATUS_CHANGED = "ecis.robot.status.changed"
    ROBOT_ERROR = "ecis.robot.error"
    ROBOT_LOCATION = "ecis.robot.location"

    # 系统事件
    SYSTEM_ONLINE = "ecis.system.online"
    SYSTEM_OFFLINE = "ecis.system.offline"


@dataclass
class QueuedEvent:
    """队列中的事件"""
    event: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 3


class EventPublisher:
    """
    事件发布器

    支持事件队列和重试机制
    """

    def __init__(
        self,
        federation_client,
        system_id: str,
        retry_count: int = 3,
        retry_delay: float = 1.0
    ):
        self._client = federation_client
        self._system_id = system_id
        self._retry_count = retry_count
        self._retry_delay = retry_delay
        self._event_queue: List[QueuedEvent] = []
        self._retry_task: Optional[asyncio.Task] = None

    def _build_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        subject: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """构建 CloudEvents 1.0 格式事件"""
        return {
            "specversion": "1.0",
            "id": str(uuid.uuid4()),
            "source": f"ecis://{self._system_id}",
            "type": event_type,
            "time": datetime.utcnow().isoformat() + "Z",
            "subject": subject,
            "datacontenttype": "application/json",
            "data": data,
            "correlationid": correlation_id
        }

    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        subject: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> Optional[str]:
        """
        发布事件

        Args:
            event_type: 事件类型
            data: 事件数据
            subject: 事件主题
            correlation_id: 关联 ID

        Returns:
            str: 事件 ID，失败返回 None
        """
        event = self._build_event(event_type, data, subject, correlation_id)

        if self._client and self._client.is_connected:
            event_id = await self._client.publish_event(event)
            if event_id:
                return event_id

        # 连接失败，加入队列
        self._event_queue.append(QueuedEvent(event=event))
        self._start_retry_loop()
        return None

    def _start_retry_loop(self) -> None:
        """启动重试循环"""
        if self._retry_task is None or self._retry_task.done():
            self._retry_task = asyncio.create_task(self._retry_loop())

    async def _retry_loop(self) -> None:
        """重试循环"""
        while self._event_queue:
            await asyncio.sleep(self._retry_delay)

            if not self._client or not self._client.is_connected:
                continue

            # 处理队列中的事件
            events_to_remove = []
            for queued in self._event_queue:
                event_id = await self._client.publish_event(queued.event)
                if event_id:
                    events_to_remove.append(queued)
                else:
                    queued.retry_count += 1
                    if queued.retry_count >= queued.max_retries:
                        logger.warning(f"Event dropped after {queued.max_retries} retries")
                        events_to_remove.append(queued)

            for queued in events_to_remove:
                self._event_queue.remove(queued)

    # ===== 便捷方法 =====

    async def publish_task_started(
        self,
        task_id: str,
        agent_id: str,
        task_type: str
    ) -> Optional[str]:
        """发布任务开始事件"""
        return await self.publish(
            EventTypes.TASK_STARTED,
            {
                "task_id": task_id,
                "agent_id": agent_id,
                "task_type": task_type,
                "started_at": datetime.utcnow().isoformat()
            },
            subject=task_id
        )

    async def publish_task_progress(
        self,
        task_id: str,
        progress: int,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """发布任务进度事件"""
        return await self.publish(
            EventTypes.TASK_PROGRESS,
            {
                "task_id": task_id,
                "progress": progress,
                "status": status,
                "details": details or {},
                "updated_at": datetime.utcnow().isoformat()
            },
            subject=task_id
        )

    async def publish_task_completed(
        self,
        task_id: str,
        result: Dict[str, Any],
        duration_seconds: int
    ) -> Optional[str]:
        """发布任务完成事件"""
        return await self.publish(
            EventTypes.TASK_COMPLETED,
            {
                "task_id": task_id,
                "result": result,
                "duration_seconds": duration_seconds,
                "completed_at": datetime.utcnow().isoformat()
            },
            subject=task_id
        )

    async def publish_task_failed(
        self,
        task_id: str,
        error_code: str,
        error_message: str
    ) -> Optional[str]:
        """发布任务失败事件"""
        return await self.publish(
            EventTypes.TASK_FAILED,
            {
                "task_id": task_id,
                "error_code": error_code,
                "error_message": error_message,
                "failed_at": datetime.utcnow().isoformat()
            },
            subject=task_id
        )

    async def publish_robot_status(
        self,
        agent_id: str,
        old_status: str,
        new_status: str,
        reason: Optional[str] = None
    ) -> Optional[str]:
        """发布机器人状态变更事件"""
        return await self.publish(
            EventTypes.ROBOT_STATUS_CHANGED,
            {
                "agent_id": agent_id,
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason,
                "changed_at": datetime.utcnow().isoformat()
            },
            subject=agent_id
        )
