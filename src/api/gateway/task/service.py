"""
G3: 任务管理API - 业务逻辑
===========================
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import logging

from .models import (
    ScheduleType, CleaningMode, TaskStatus, ScheduleStatus, TaskPriority,
    RepeatConfig, ScheduleCreate, ScheduleUpdate, ScheduleInDB, ScheduleResponse,
    ScheduleDetailResponse, ZoneInfo, ExecutionSummary,
    TaskInDB, TaskResponse, TaskDetailResponse, TaskEvent, RobotInfo, RouteInfo,
    ExecutionInDB, ExecutionResponse
)

logger = logging.getLogger(__name__)


# ============================================================
# 内存存储（测试用）
# ============================================================

class InMemoryTaskStorage:
    """内存任务存储"""

    def __init__(self):
        self.schedules: Dict[str, ScheduleInDB] = {}
        self.tasks: Dict[str, TaskInDB] = {}
        self.executions: Dict[str, ExecutionInDB] = {}
        self._init_default_data()

    def _init_default_data(self):
        """初始化默认数据"""
        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(days=1)

        # 创建默认排程
        schedule = ScheduleInDB(
            id="schedule-001",
            tenant_id="tenant_001",
            name="大堂日常清洁",
            zone_id="zone-001",
            schedule_type=ScheduleType.DAILY,
            start_time="08:00",
            cleaning_mode=CleaningMode.STANDARD,
            duration_minutes=60,
            repeat_config=RepeatConfig(type="weekly", days_of_week=[1, 2, 3, 4, 5]),
            priority=TaskPriority.HIGH,
            status=ScheduleStatus.ENABLED,
            next_run_at=tomorrow.replace(hour=8, minute=0, second=0, microsecond=0),
            last_run_at=now - timedelta(hours=2),
            last_run_status="completed",
            metadata={"notify_on_complete": True},
            created_at=now - timedelta(days=30),
            updated_at=now
        )
        self.schedules["schedule-001"] = schedule

        # 创建默认任务
        task = TaskInDB(
            id="task-001",
            tenant_id="tenant_001",
            schedule_id="schedule-001",
            zone_id="zone-001",
            robot_id="robot-001",
            cleaning_mode=CleaningMode.STANDARD,
            status=TaskStatus.IN_PROGRESS,
            progress_percent=65,
            cleaned_area_sqm=325,
            total_area_sqm=500,
            scheduled_start=now - timedelta(hours=1),
            started_at=now - timedelta(hours=1),
            estimated_completion=now + timedelta(minutes=30),
            metadata={},
            created_at=now - timedelta(hours=1)
        )
        self.tasks["task-001"] = task

        # 创建历史任务
        completed_task = TaskInDB(
            id="task-002",
            tenant_id="tenant_001",
            schedule_id="schedule-001",
            zone_id="zone-001",
            robot_id="robot-001",
            cleaning_mode=CleaningMode.STANDARD,
            status=TaskStatus.COMPLETED,
            progress_percent=100,
            cleaned_area_sqm=480,
            total_area_sqm=500,
            scheduled_start=now - timedelta(days=1, hours=1),
            started_at=now - timedelta(days=1, hours=1),
            completed_at=now - timedelta(days=1),
            metadata={},
            created_at=now - timedelta(days=1, hours=1)
        )
        self.tasks["task-002"] = completed_task

        # 创建执行记录
        execution = ExecutionInDB(
            id="exec-001",
            task_id="task-002",
            schedule_id="schedule-001",
            zone_id="zone-001",
            robot_id="robot-001",
            tenant_id="tenant_001",
            status="completed",
            started_at=now - timedelta(days=1, hours=1),
            completed_at=now - timedelta(days=1),
            duration_minutes=52,
            cleaned_area_sqm=480,
            coverage_rate=0.96,
            events=[
                {"timestamp": (now - timedelta(days=1, hours=1)).isoformat(),
                 "event_type": "task_started", "message": "任务开始执行"},
                {"timestamp": (now - timedelta(days=1)).isoformat(),
                 "event_type": "task_completed", "message": "任务完成"}
            ]
        )
        self.executions["exec-001"] = execution


# ============================================================
# 任务服务
# ============================================================

class TaskService:
    """任务服务"""

    def __init__(self, storage: Optional[InMemoryTaskStorage] = None):
        self.storage = storage or InMemoryTaskStorage()
        # 模拟区域数据
        self._zones = {
            "zone-001": {"name": "大堂A区", "floor_name": "1F", "building_name": "新鸿基中心", "area_sqm": 500}
        }
        # 模拟机器人数据
        self._robots = {
            "robot-001": {"name": "清洁机器人A", "model": "GS-100"}
        }

    # ==================== 排程管理 ====================

    async def list_schedules(
        self,
        tenant_id: str,
        building_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        status: Optional[ScheduleStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取排程列表"""
        schedules = [s for s in self.storage.schedules.values()
                     if s.tenant_id == tenant_id]

        # 过滤
        if zone_id:
            schedules = [s for s in schedules if s.zone_id == zone_id]
        if status:
            schedules = [s for s in schedules if s.status == status]

        # 分页
        total = len(schedules)
        start = (page - 1) * page_size
        schedules = schedules[start:start + page_size]

        return {
            "items": [self._schedule_to_response(s) for s in schedules],
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def create_schedule(self, tenant_id: str, data: ScheduleCreate) -> ScheduleResponse:
        """创建排程"""
        now = datetime.now(timezone.utc)
        schedule_id = f"schedule_{uuid.uuid4().hex[:8]}"

        # 计算下次运行时间
        next_run_at = self._calculate_next_run(
            data.schedule_type,
            data.start_time,
            data.repeat_config
        )

        schedule = ScheduleInDB(
            id=schedule_id,
            tenant_id=tenant_id,
            name=data.name,
            zone_id=data.zone_id,
            schedule_type=data.schedule_type,
            start_time=data.start_time,
            cleaning_mode=data.cleaning_mode,
            duration_minutes=data.duration_minutes,
            repeat_config=data.repeat_config,
            assigned_robot_id=data.assigned_robot_id,
            priority=data.priority,
            status=ScheduleStatus.ENABLED,
            next_run_at=next_run_at,
            metadata=data.metadata,
            created_at=now,
            updated_at=now
        )

        self.storage.schedules[schedule_id] = schedule
        return self._schedule_to_response(schedule)

    async def get_schedule(self, schedule_id: str, tenant_id: str) -> Optional[ScheduleDetailResponse]:
        """获取排程详情"""
        schedule = self.storage.schedules.get(schedule_id)
        if not schedule or schedule.tenant_id != tenant_id:
            return None

        # 获取区域信息
        zone_data = self._zones.get(schedule.zone_id, {})
        zone_info = ZoneInfo(
            id=schedule.zone_id,
            name=zone_data.get("name", "未知区域"),
            floor_name=zone_data.get("floor_name"),
            building_name=zone_data.get("building_name")
        )

        # 获取最近执行记录
        executions = [e for e in self.storage.executions.values()
                      if e.schedule_id == schedule_id]
        executions.sort(key=lambda e: e.started_at, reverse=True)
        recent_executions = [
            ExecutionSummary(
                id=e.id,
                started_at=e.started_at,
                completed_at=e.completed_at,
                status=e.status,
                robot_id=e.robot_id
            ) for e in executions[:5]
        ]

        # 统计信息
        total_runs = len(executions)
        successful_runs = sum(1 for e in executions if e.status == "completed")
        failed_runs = sum(1 for e in executions if e.status == "failed")
        avg_duration = sum(e.duration_minutes or 0 for e in executions) / total_runs if total_runs > 0 else 0
        avg_coverage = sum(e.coverage_rate for e in executions) / total_runs if total_runs > 0 else 0

        return ScheduleDetailResponse(
            id=schedule.id,
            name=schedule.name,
            zone_id=schedule.zone_id,
            zone_name=zone_info.name,
            building_name=zone_info.building_name,
            zone=zone_info,
            schedule_type=schedule.schedule_type,
            start_time=schedule.start_time,
            cleaning_mode=schedule.cleaning_mode,
            duration_minutes=schedule.duration_minutes,
            repeat_config=schedule.repeat_config,
            assigned_robot_id=schedule.assigned_robot_id,
            priority=schedule.priority,
            status=schedule.status,
            next_run_at=schedule.next_run_at,
            last_run_at=schedule.last_run_at,
            last_run_status=schedule.last_run_status,
            metadata=schedule.metadata,
            statistics={
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "avg_duration_minutes": round(avg_duration, 1),
                "avg_coverage_rate": round(avg_coverage, 2)
            },
            recent_executions=recent_executions,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at
        )

    async def update_schedule(
        self,
        schedule_id: str,
        tenant_id: str,
        data: ScheduleUpdate
    ) -> Optional[ScheduleResponse]:
        """更新排程"""
        schedule = self.storage.schedules.get(schedule_id)
        if not schedule or schedule.tenant_id != tenant_id:
            return None

        if data.name is not None:
            schedule.name = data.name
        if data.start_time is not None:
            schedule.start_time = data.start_time
        if data.cleaning_mode is not None:
            schedule.cleaning_mode = data.cleaning_mode
        if data.duration_minutes is not None:
            schedule.duration_minutes = data.duration_minutes
        if data.repeat_config is not None:
            schedule.repeat_config = data.repeat_config
        if data.assigned_robot_id is not None:
            schedule.assigned_robot_id = data.assigned_robot_id
        if data.priority is not None:
            schedule.priority = data.priority
        if data.metadata is not None:
            schedule.metadata = data.metadata

        # 重新计算下次运行时间
        schedule.next_run_at = self._calculate_next_run(
            schedule.schedule_type,
            schedule.start_time,
            schedule.repeat_config
        )

        schedule.updated_at = datetime.now(timezone.utc)
        return self._schedule_to_response(schedule)

    async def delete_schedule(self, schedule_id: str, tenant_id: str) -> bool:
        """删除排程"""
        schedule = self.storage.schedules.get(schedule_id)
        if not schedule or schedule.tenant_id != tenant_id:
            return False

        del self.storage.schedules[schedule_id]
        return True

    async def enable_schedule(self, schedule_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """启用排程"""
        schedule = self.storage.schedules.get(schedule_id)
        if not schedule or schedule.tenant_id != tenant_id:
            return None

        schedule.status = ScheduleStatus.ENABLED
        schedule.next_run_at = self._calculate_next_run(
            schedule.schedule_type,
            schedule.start_time,
            schedule.repeat_config
        )
        schedule.updated_at = datetime.now(timezone.utc)

        return {
            "id": schedule.id,
            "status": schedule.status,
            "next_run_at": schedule.next_run_at,
            "message": "排程已启用"
        }

    async def disable_schedule(self, schedule_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """禁用排程"""
        schedule = self.storage.schedules.get(schedule_id)
        if not schedule or schedule.tenant_id != tenant_id:
            return None

        schedule.status = ScheduleStatus.DISABLED
        schedule.next_run_at = None
        schedule.updated_at = datetime.now(timezone.utc)

        return {
            "id": schedule.id,
            "status": schedule.status,
            "message": "排程已禁用"
        }

    # ==================== 任务管理 ====================

    async def list_tasks(
        self,
        tenant_id: str,
        building_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        robot_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取任务列表"""
        tasks = [t for t in self.storage.tasks.values()
                 if t.tenant_id == tenant_id]

        # 过滤
        if zone_id:
            tasks = [t for t in tasks if t.zone_id == zone_id]
        if robot_id:
            tasks = [t for t in tasks if t.robot_id == robot_id]
        if status:
            tasks = [t for t in tasks if t.status == status]
        if date_from:
            tasks = [t for t in tasks if t.created_at >= date_from]
        if date_to:
            tasks = [t for t in tasks if t.created_at <= date_to]

        # 按创建时间倒序
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        # 分页
        total = len(tasks)
        start = (page - 1) * page_size
        tasks = tasks[start:start + page_size]

        return {
            "items": [self._task_to_response(t) for t in tasks],
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def get_task(self, task_id: str, tenant_id: str) -> Optional[TaskDetailResponse]:
        """获取任务详情"""
        task = self.storage.tasks.get(task_id)
        if not task or task.tenant_id != tenant_id:
            return None

        # 获取排程信息
        schedule = self.storage.schedules.get(task.schedule_id)

        # 获取区域信息
        zone_data = self._zones.get(task.zone_id, {})
        zone_info = ZoneInfo(
            id=task.zone_id,
            name=zone_data.get("name", "未知区域"),
            floor_name=zone_data.get("floor_name"),
            building_name=zone_data.get("building_name")
        )

        # 获取机器人信息
        robot_info = None
        if task.robot_id:
            robot_data = self._robots.get(task.robot_id, {})
            robot_info = RobotInfo(
                id=task.robot_id,
                name=robot_data.get("name", "未知机器人"),
                model=robot_data.get("model")
            )

        # 任务事件
        events = [
            TaskEvent(
                timestamp=task.created_at,
                event_type="task_created",
                message="任务已创建"
            )
        ]
        if task.started_at:
            events.append(TaskEvent(
                timestamp=task.started_at,
                event_type="task_started",
                message="任务开始执行"
            ))
        if task.status == TaskStatus.COMPLETED and task.completed_at:
            events.append(TaskEvent(
                timestamp=task.completed_at,
                event_type="task_completed",
                message="任务完成"
            ))

        return TaskDetailResponse(
            id=task.id,
            schedule_id=task.schedule_id,
            schedule_name=schedule.name if schedule else None,
            zone_id=task.zone_id,
            zone_name=zone_info.name,
            zone=zone_info,
            robot_id=task.robot_id,
            robot_name=robot_info.name if robot_info else None,
            robot=robot_info,
            cleaning_mode=task.cleaning_mode,
            status=task.status,
            progress_percent=task.progress_percent,
            cleaned_area_sqm=task.cleaned_area_sqm,
            total_area_sqm=task.total_area_sqm,
            started_at=task.started_at,
            completed_at=task.completed_at,
            estimated_completion=task.estimated_completion,
            route=RouteInfo(
                current_position={"x": 5.5, "y": 8.2} if task.status == TaskStatus.IN_PROGRESS else None
            ),
            events=events,
            metadata=task.metadata,
            created_at=task.created_at
        )

    async def pause_task(
        self,
        task_id: str,
        tenant_id: str,
        reason: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """暂停任务"""
        task = self.storage.tasks.get(task_id)
        if not task or task.tenant_id != tenant_id:
            return None

        if task.status != TaskStatus.IN_PROGRESS:
            raise ValueError("只能暂停进行中的任务")

        now = datetime.now(timezone.utc)
        task.status = TaskStatus.PAUSED
        task.metadata["pause_reason"] = reason
        task.metadata["paused_at"] = now.isoformat()

        return {
            "id": task_id,
            "status": TaskStatus.PAUSED,
            "paused_at": now,
            "message": "任务已暂停"
        }

    async def resume_task(self, task_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """恢复任务"""
        task = self.storage.tasks.get(task_id)
        if not task or task.tenant_id != tenant_id:
            return None

        if task.status != TaskStatus.PAUSED:
            raise ValueError("只能恢复已暂停的任务")

        now = datetime.now(timezone.utc)
        task.status = TaskStatus.IN_PROGRESS
        task.metadata["resumed_at"] = now.isoformat()

        return {
            "id": task_id,
            "status": TaskStatus.IN_PROGRESS,
            "resumed_at": now,
            "message": "任务已恢复"
        }

    async def cancel_task(
        self,
        task_id: str,
        tenant_id: str,
        reason: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """取消任务"""
        task = self.storage.tasks.get(task_id)
        if not task or task.tenant_id != tenant_id:
            return None

        if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            raise ValueError("无法取消已完成或已取消的任务")

        now = datetime.now(timezone.utc)
        task.status = TaskStatus.CANCELLED
        task.metadata["cancel_reason"] = reason
        task.metadata["cancelled_at"] = now.isoformat()

        return {
            "id": task_id,
            "status": TaskStatus.CANCELLED,
            "cancelled_at": now,
            "message": "任务已取消"
        }

    # ==================== 执行记录管理 ====================

    async def list_executions(
        self,
        tenant_id: str,
        schedule_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        robot_id: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取执行记录列表"""
        executions = [e for e in self.storage.executions.values()
                      if e.tenant_id == tenant_id]

        # 过滤
        if schedule_id:
            executions = [e for e in executions if e.schedule_id == schedule_id]
        if zone_id:
            executions = [e for e in executions if e.zone_id == zone_id]
        if robot_id:
            executions = [e for e in executions if e.robot_id == robot_id]
        if status:
            executions = [e for e in executions if e.status == status]
        if date_from:
            executions = [e for e in executions if e.started_at >= date_from]
        if date_to:
            executions = [e for e in executions if e.started_at <= date_to]

        # 按开始时间倒序
        executions.sort(key=lambda e: e.started_at, reverse=True)

        # 分页
        total = len(executions)
        start = (page - 1) * page_size
        executions = executions[start:start + page_size]

        return {
            "items": [self._execution_to_response(e) for e in executions],
            "total": total,
            "page": page,
            "page_size": page_size
        }

    # ==================== 辅助方法 ====================

    def _calculate_next_run(
        self,
        schedule_type: ScheduleType,
        start_time: str,
        repeat_config: Optional[RepeatConfig]
    ) -> datetime:
        """计算下次运行时间"""
        now = datetime.now(timezone.utc)
        hour, minute = map(int, start_time.split(":"))

        # 简化实现：返回明天的指定时间
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)

        return next_run

    def _schedule_to_response(self, schedule: ScheduleInDB) -> ScheduleResponse:
        """转换排程为响应"""
        zone_data = self._zones.get(schedule.zone_id, {})
        return ScheduleResponse(
            id=schedule.id,
            name=schedule.name,
            zone_id=schedule.zone_id,
            zone_name=zone_data.get("name"),
            building_name=zone_data.get("building_name"),
            schedule_type=schedule.schedule_type,
            start_time=schedule.start_time,
            cleaning_mode=schedule.cleaning_mode,
            duration_minutes=schedule.duration_minutes,
            priority=schedule.priority,
            status=schedule.status,
            next_run_at=schedule.next_run_at,
            last_run_at=schedule.last_run_at,
            last_run_status=schedule.last_run_status,
            created_at=schedule.created_at
        )

    def _task_to_response(self, task: TaskInDB) -> TaskResponse:
        """转换任务为响应"""
        schedule = self.storage.schedules.get(task.schedule_id)
        zone_data = self._zones.get(task.zone_id, {})
        robot_data = self._robots.get(task.robot_id, {}) if task.robot_id else {}

        return TaskResponse(
            id=task.id,
            schedule_id=task.schedule_id,
            schedule_name=schedule.name if schedule else None,
            zone_id=task.zone_id,
            zone_name=zone_data.get("name"),
            robot_id=task.robot_id,
            robot_name=robot_data.get("name"),
            status=task.status,
            progress_percent=task.progress_percent,
            started_at=task.started_at,
            estimated_completion=task.estimated_completion,
            created_at=task.created_at
        )

    def _execution_to_response(self, execution: ExecutionInDB) -> ExecutionResponse:
        """转换执行记录为响应"""
        schedule = self.storage.schedules.get(execution.schedule_id)
        zone_data = self._zones.get(execution.zone_id, {})
        robot_data = self._robots.get(execution.robot_id, {})

        return ExecutionResponse(
            id=execution.id,
            task_id=execution.task_id,
            schedule_name=schedule.name if schedule else None,
            zone_name=zone_data.get("name"),
            robot_name=robot_data.get("name"),
            status=execution.status,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            duration_minutes=execution.duration_minutes,
            cleaned_area_sqm=execution.cleaned_area_sqm,
            coverage_rate=execution.coverage_rate
        )
