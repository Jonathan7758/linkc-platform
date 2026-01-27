"""
TaskReceiver Mixin - 任务接收能力
"""

from abc import abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ValidationResult:
    """参数验证结果"""
    valid: bool
    message: str = ""


@dataclass
class TaskResponse:
    """任务响应"""
    status: str  # accepted, rejected, pending
    reason: str = ""
    message: str = ""
    estimated_duration: int = 0  # 分钟


class TaskReceiverMixin:
    """
    TaskReceiver 混入类

    为 Agent 添加接收编排任务的能力
    """

    _current_orchestration_task: Any = None
    _event_publisher: Any = None
    _task_started_at: Optional[datetime] = None

    def set_event_publisher(self, publisher) -> None:
        """设置事件发布器"""
        self._event_publisher = publisher

    async def receive_orchestration_task(self, task) -> TaskResponse:
        """
        接收编排任务

        流程:
        1. 检查当前状态
        2. 验证能力匹配
        3. 验证参数
        4. 接受或拒绝
        """
        # 检查状态
        if not await self._can_accept_task():
            return TaskResponse(
                status="rejected",
                reason="agent_busy",
                message="Agent 当前正在执行任务"
            )

        # 验证能力
        if not self._has_capability(task.required_capability):
            return TaskResponse(
                status="rejected",
                reason="capability_mismatch",
                message=f"Agent 不具备 {task.required_capability} 能力"
            )

        # 验证参数
        result = self._validate_task_parameters(task.parameters)
        if not result.valid:
            return TaskResponse(
                status="rejected",
                reason="invalid_parameters",
                message=result.message
            )

        # 接受任务
        self._current_orchestration_task = task
        self._task_started_at = datetime.utcnow()
        await self._on_task_accepted(task)

        return TaskResponse(
            status="accepted",
            estimated_duration=self._estimate_duration(task)
        )

    async def report_task_progress(
        self,
        task_id: str,
        progress: int,
        status: str,
        details: Dict[str, Any] = None
    ) -> None:
        """报告任务进度"""
        if self._event_publisher:
            await self._event_publisher.publish_task_progress(
                task_id=task_id,
                progress=progress,
                status=status,
                details=details
            )

    async def complete_orchestration_task(
        self,
        task_id: str,
        result: Dict[str, Any]
    ) -> None:
        """完成编排任务"""
        if self._event_publisher and self._current_orchestration_task:
            duration = self._calculate_duration()
            await self._event_publisher.publish_task_completed(
                task_id=task_id,
                result=result,
                duration_seconds=duration
            )
        self._current_orchestration_task = None
        self._task_started_at = None

    async def fail_orchestration_task(
        self,
        task_id: str,
        error_code: str,
        error_message: str
    ) -> None:
        """标记任务失败"""
        if self._event_publisher:
            await self._event_publisher.publish_task_failed(
                task_id=task_id,
                error_code=error_code,
                error_message=error_message
            )
        self._current_orchestration_task = None
        self._task_started_at = None

    def _calculate_duration(self) -> int:
        """计算任务执行时长（秒）"""
        if self._task_started_at:
            delta = datetime.utcnow() - self._task_started_at
            return int(delta.total_seconds())
        return 0

    # ===== 子类必须实现的方法 =====

    @abstractmethod
    async def _can_accept_task(self) -> bool:
        """检查是否可以接受任务"""
        pass

    @abstractmethod
    def _has_capability(self, capability_id: str) -> bool:
        """检查是否具备指定能力"""
        pass

    @abstractmethod
    def _validate_task_parameters(self, parameters: Dict[str, Any]) -> ValidationResult:
        """验证任务参数"""
        pass

    @abstractmethod
    def _estimate_duration(self, task) -> int:
        """估计执行时间（分钟）"""
        pass

    @abstractmethod
    async def _on_task_accepted(self, task) -> None:
        """任务接受后的处理"""
        pass
