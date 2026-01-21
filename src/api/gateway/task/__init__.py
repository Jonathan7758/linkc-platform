"""
G3: 任务管理API
===============
提供清洁排程、任务管理、执行记录查询功能。
"""

from .models import (
    ScheduleType, CleaningMode, TaskStatus, ScheduleStatus, TaskPriority,
    RepeatConfig,
    ScheduleCreate, ScheduleUpdate, ScheduleResponse, ScheduleDetailResponse,
    ScheduleListResponse, ScheduleActionResponse,
    TaskResponse, TaskDetailResponse, TaskListResponse,
    TaskControlRequest, TaskControlResponse,
    ExecutionResponse, ExecutionListResponse,
    MessageResponse
)
from .service import TaskService, InMemoryTaskStorage
from .router import (
    router,
    get_task_service, set_task_service
)

__all__ = [
    # Enums
    "ScheduleType", "CleaningMode", "TaskStatus", "ScheduleStatus", "TaskPriority",
    # Config
    "RepeatConfig",
    # Schedule Models
    "ScheduleCreate", "ScheduleUpdate", "ScheduleResponse", "ScheduleDetailResponse",
    "ScheduleListResponse", "ScheduleActionResponse",
    # Task Models
    "TaskResponse", "TaskDetailResponse", "TaskListResponse",
    "TaskControlRequest", "TaskControlResponse",
    # Execution Models
    "ExecutionResponse", "ExecutionListResponse",
    # Common
    "MessageResponse",
    # Service
    "TaskService", "InMemoryTaskStorage",
    # Router
    "router",
    "get_task_service", "set_task_service",
]
