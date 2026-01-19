"""
M2: 任务管理 MCP Server - 存储层
================================
基于规格书 docs/specs/M2-task-mcp.md 实现
"""

from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================
# 数据模型
# ============================================================

class TaskType(str, Enum):
    """任务类型"""
    ROUTINE = "routine"      # 日常清洁
    DEEP = "deep"            # 深度清洁
    SPOT = "spot"            # 局部清洁
    EMERGENCY = "emergency"  # 紧急清洁


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"          # 待分配
    ASSIGNED = "assigned"        # 已分配
    IN_PROGRESS = "in_progress"  # 执行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消


class CleaningFrequency(str, Enum):
    """清洁频率"""
    ONCE = "once"        # 一次性
    DAILY = "daily"      # 每天
    WEEKLY = "weekly"    # 每周
    MONTHLY = "monthly"  # 每月


class TimeSlot(BaseModel):
    """时间段"""
    start: str = Field(..., description="开始时间 HH:MM")
    end: str = Field(..., description="结束时间 HH:MM")
    days: List[int] = Field(
        default=[1, 2, 3, 4, 5, 6, 7],
        description="星期几执行，1=周一，7=周日"
    )


class CleaningSchedule(BaseModel):
    """清洁排程"""
    schedule_id: str
    tenant_id: str
    zone_id: str
    zone_name: Optional[str] = None

    task_type: TaskType
    frequency: CleaningFrequency
    time_slots: List[TimeSlot]
    priority: int = Field(default=5, ge=1, le=10)
    estimated_duration: int = Field(default=30, description="预计时长(分钟)")

    is_active: bool = True
    created_by: str = "system"
    created_at: datetime
    updated_at: datetime


class CleaningTask(BaseModel):
    """清洁任务"""
    task_id: str
    tenant_id: str
    zone_id: str
    zone_name: Optional[str] = None

    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    priority: int = Field(default=5, ge=1, le=10)

    # 时间相关
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None

    # 执行相关
    assigned_robot_id: Optional[str] = None
    assigned_robot_name: Optional[str] = None
    completion_rate: Optional[float] = None  # 0-100
    failure_reason: Optional[str] = None

    # 关联
    schedule_id: Optional[str] = None  # 关联的排程

    # 元信息
    notes: Optional[str] = None
    created_by: str = "system"
    created_at: datetime
    updated_at: datetime


# ============================================================
# 存储层实现
# ============================================================

class InMemoryTaskStorage:
    """内存存储实现（MVP阶段）"""

    def __init__(self):
        self._schedules: Dict[str, CleaningSchedule] = {}
        self._tasks: Dict[str, CleaningTask] = {}
        self._generated_tasks: set = set()  # (schedule_id, date_str) 用于幂等检查
        self._init_sample_data()

    def _init_sample_data(self):
        """初始化示例数据"""
        tenant_id = "tenant_001"
        now = datetime.utcnow()

        # 示例排程
        schedules = [
            CleaningSchedule(
                schedule_id="schedule_001",
                tenant_id=tenant_id,
                zone_id="zone_001",
                zone_name="1F大堂",
                task_type=TaskType.ROUTINE,
                frequency=CleaningFrequency.DAILY,
                time_slots=[TimeSlot(start="08:00", end="10:00", days=[1, 2, 3, 4, 5])],
                priority=3,
                estimated_duration=45,
                is_active=True,
                created_at=now,
                updated_at=now
            ),
            CleaningSchedule(
                schedule_id="schedule_002",
                tenant_id=tenant_id,
                zone_id="zone_003",
                zone_name="2F走廊",
                task_type=TaskType.DEEP,
                frequency=CleaningFrequency.WEEKLY,
                time_slots=[TimeSlot(start="14:00", end="16:00", days=[1, 4])],
                priority=5,
                estimated_duration=60,
                is_active=True,
                created_at=now,
                updated_at=now
            ),
        ]

        for s in schedules:
            self._schedules[s.schedule_id] = s

        # 示例任务
        tasks = [
            CleaningTask(
                task_id="task_001",
                tenant_id=tenant_id,
                zone_id="zone_001",
                zone_name="1F大堂",
                task_type=TaskType.ROUTINE,
                status=TaskStatus.PENDING,
                priority=3,
                schedule_id="schedule_001",
                created_at=now,
                updated_at=now
            ),
            CleaningTask(
                task_id="task_002",
                tenant_id=tenant_id,
                zone_id="zone_003",
                zone_name="2F走廊",
                task_type=TaskType.DEEP,
                status=TaskStatus.IN_PROGRESS,
                priority=5,
                assigned_robot_id="robot_001",
                assigned_robot_name="清洁机器人A-01",
                actual_start=now,
                completion_rate=35.0,
                created_at=now,
                updated_at=now
            ),
            CleaningTask(
                task_id="task_003",
                tenant_id=tenant_id,
                zone_id="zone_004",
                zone_name="2F洗手间",
                task_type=TaskType.EMERGENCY,
                status=TaskStatus.PENDING,
                priority=1,  # emergency自动为1
                notes="客户投诉需要紧急清洁",
                created_at=now,
                updated_at=now
            ),
        ]

        for t in tasks:
            self._tasks[t.task_id] = t

    # ========== 排程操作 ==========

    async def save_schedule(self, schedule: CleaningSchedule) -> CleaningSchedule:
        """保存排程"""
        self._schedules[schedule.schedule_id] = schedule
        return schedule

    async def get_schedule(self, schedule_id: str) -> Optional[CleaningSchedule]:
        """获取排程"""
        return self._schedules.get(schedule_id)

    async def list_schedules(
        self,
        tenant_id: str,
        zone_id: Optional[str] = None,
        building_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[CleaningSchedule]:
        """列出排程"""
        result = []
        for schedule in self._schedules.values():
            if schedule.tenant_id != tenant_id:
                continue
            if zone_id and schedule.zone_id != zone_id:
                continue
            if is_active is not None and schedule.is_active != is_active:
                continue
            result.append(schedule)
        return result

    async def update_schedule(
        self,
        schedule_id: str,
        updates: dict
    ) -> Optional[CleaningSchedule]:
        """更新排程"""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return None

        # 更新允许的字段
        allowed_fields = ["is_active", "priority", "time_slots", "frequency"]
        for key, value in updates.items():
            if key in allowed_fields and hasattr(schedule, key):
                setattr(schedule, key, value)

        schedule.updated_at = datetime.utcnow()
        return schedule

    async def delete_schedule(self, schedule_id: str) -> bool:
        """删除排程"""
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            return True
        return False

    # ========== 任务操作 ==========

    async def save_task(self, task: CleaningTask) -> CleaningTask:
        """保存任务"""
        self._tasks[task.task_id] = task
        return task

    async def get_task(self, task_id: str) -> Optional[CleaningTask]:
        """获取任务"""
        return self._tasks.get(task_id)

    async def list_tasks(
        self,
        tenant_id: str,
        zone_id: Optional[str] = None,
        robot_id: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[CleaningTask], int]:
        """列出任务"""
        result = []
        for task in self._tasks.values():
            if task.tenant_id != tenant_id:
                continue
            if zone_id and task.zone_id != zone_id:
                continue
            if robot_id and task.assigned_robot_id != robot_id:
                continue
            if status and task.status.value != status:
                continue
            if date_from and task.created_at.date() < date_from:
                continue
            if date_to and task.created_at.date() > date_to:
                continue
            result.append(task)

        total = len(result)
        # 按优先级和创建时间排序
        result.sort(key=lambda t: (t.priority, t.created_at))
        result = result[offset:offset + limit]
        return result, total

    async def update_task(
        self,
        task_id: str,
        updates: dict
    ) -> Optional[CleaningTask]:
        """更新任务"""
        task = self._tasks.get(task_id)
        if not task:
            return None

        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)

        task.updated_at = datetime.utcnow()
        return task

    async def get_pending_tasks(
        self,
        tenant_id: str,
        zone_ids: Optional[List[str]] = None,
        max_count: int = 20
    ) -> List[CleaningTask]:
        """获取待执行任务"""
        result = []
        for task in self._tasks.values():
            if task.tenant_id != tenant_id:
                continue
            if task.status != TaskStatus.PENDING:
                continue
            if zone_ids and task.zone_id not in zone_ids:
                continue
            result.append(task)
            if len(result) >= max_count:
                break

        # 按优先级、计划时间、创建时间排序
        result.sort(key=lambda t: (
            t.priority,
            t.scheduled_start or datetime.max,
            t.created_at
        ))
        return result

    # ========== 任务生成 ==========

    async def is_task_generated(self, schedule_id: str, task_date: date) -> bool:
        """检查是否已生成任务（幂等检查）"""
        return (schedule_id, task_date.isoformat()) in self._generated_tasks

    async def mark_task_generated(self, schedule_id: str, task_date: date):
        """标记任务已生成"""
        self._generated_tasks.add((schedule_id, task_date.isoformat()))

    async def get_active_schedules(self, tenant_id: str) -> List[CleaningSchedule]:
        """获取活跃的排程"""
        return [
            s for s in self._schedules.values()
            if s.tenant_id == tenant_id and s.is_active
        ]
