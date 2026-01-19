"""
M2: 任务管理 MCP Server - Tool 实现
===================================
基于规格书 docs/specs/M2-task-mcp.md 实现

10个Tools:
1. task_list_schedules     - 获取排程列表
2. task_get_schedule       - 获取排程详情
3. task_create_schedule    - 创建排程
4. task_update_schedule    - 更新排程
5. task_list_tasks         - 获取任务列表
6. task_get_task           - 获取任务详情
7. task_create_task        - 创建任务
8. task_update_status      - 更新任务状态
9. task_get_pending_tasks  - 获取待执行任务
10. task_generate_daily_tasks - 生成每日任务
"""

from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime, date, timedelta
import logging

from .storage import (
    InMemoryTaskStorage,
    CleaningSchedule,
    CleaningTask,
    TaskStatus,
    TaskType,
    CleaningFrequency,
    TimeSlot
)

logger = logging.getLogger(__name__)


# ============================================================
# 返回结果模型
# ============================================================

class ToolResult:
    """Tool统一返回结果"""

    def __init__(
        self,
        success: bool,
        data: Optional[Any] = None,
        error: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        self.success = success
        self.data = data
        self.error = error
        self.error_code = error_code

    def model_dump(self) -> dict:
        result = {"success": self.success}
        if self.data is not None:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        if self.error_code:
            result["error_code"] = self.error_code
        return result


# ============================================================
# 状态流转规则
# ============================================================

VALID_TRANSITIONS = {
    TaskStatus.PENDING: [TaskStatus.ASSIGNED, TaskStatus.CANCELLED],
    TaskStatus.ASSIGNED: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
    TaskStatus.IN_PROGRESS: [TaskStatus.COMPLETED, TaskStatus.FAILED],
    TaskStatus.COMPLETED: [],
    TaskStatus.FAILED: [],
    TaskStatus.CANCELLED: [],
}


# ============================================================
# Tool 实现
# ============================================================

class TaskTools:
    """任务管理 Tool 实现"""

    def __init__(self, storage: InMemoryTaskStorage):
        self.storage = storage

    async def handle(self, name: str, arguments: dict) -> ToolResult:
        """路由 Tool 调用"""
        handlers = {
            "task_list_schedules": self._list_schedules,
            "task_get_schedule": self._get_schedule,
            "task_create_schedule": self._create_schedule,
            "task_update_schedule": self._update_schedule,
            "task_list_tasks": self._list_tasks,
            "task_get_task": self._get_task,
            "task_create_task": self._create_task,
            "task_update_status": self._update_status,
            "task_get_pending_tasks": self._get_pending_tasks,
            "task_generate_daily_tasks": self._generate_daily_tasks,
        }

        handler = handlers.get(name)
        if not handler:
            return ToolResult(
                success=False,
                error=f"Unknown tool: {name}",
                error_code="NOT_FOUND"
            )

        try:
            return await handler(arguments)
        except Exception as e:
            logger.exception(f"Error handling {name}")
            return ToolResult(
                success=False,
                error=str(e),
                error_code="INTERNAL_ERROR"
            )

    # ========== 排程相关 Tools ==========

    async def _list_schedules(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 1: 获取排程列表"""
        tenant_id = args.get("tenant_id")
        if not tenant_id:
            return ToolResult(
                success=False,
                error="tenant_id is required",
                error_code="INVALID_PARAM"
            )

        schedules = await self.storage.list_schedules(
            tenant_id=tenant_id,
            zone_id=args.get("zone_id"),
            building_id=args.get("building_id"),
            is_active=args.get("is_active", True)
        )

        return ToolResult(
            success=True,
            data={
                "schedules": [self._schedule_to_dict(s) for s in schedules],
                "total": len(schedules)
            }
        )

    async def _get_schedule(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 2: 获取排程详情"""
        schedule_id = args.get("schedule_id")
        if not schedule_id:
            return ToolResult(
                success=False,
                error="schedule_id is required",
                error_code="INVALID_PARAM"
            )

        schedule = await self.storage.get_schedule(schedule_id)
        if not schedule:
            return ToolResult(
                success=False,
                error=f"Schedule {schedule_id} not found",
                error_code="NOT_FOUND"
            )

        return ToolResult(
            success=True,
            data={"schedule": self._schedule_to_dict(schedule)}
        )

    async def _create_schedule(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 3: 创建排程"""
        required = ["tenant_id", "zone_id", "task_type", "frequency", "time_slots"]
        for field in required:
            if not args.get(field):
                return ToolResult(
                    success=False,
                    error=f"{field} is required",
                    error_code="INVALID_PARAM"
                )

        # 验证 priority 范围
        priority = args.get("priority", 5)
        if not 1 <= priority <= 10:
            return ToolResult(
                success=False,
                error="priority must be between 1 and 10",
                error_code="INVALID_PARAM"
            )

        # 验证 time_slots
        time_slots_data = args.get("time_slots", [])
        if not time_slots_data:
            return ToolResult(
                success=False,
                error="time_slots must have at least one item",
                error_code="INVALID_PARAM"
            )

        try:
            time_slots = [TimeSlot(**ts) for ts in time_slots_data]
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Invalid time_slots format: {e}",
                error_code="INVALID_PARAM"
            )

        now = datetime.utcnow()
        schedule = CleaningSchedule(
            schedule_id=f"schedule_{uuid4().hex[:8]}",
            tenant_id=args["tenant_id"],
            zone_id=args["zone_id"],
            zone_name=args.get("zone_name"),
            task_type=TaskType(args["task_type"]),
            frequency=CleaningFrequency(args["frequency"]),
            time_slots=time_slots,
            priority=priority,
            estimated_duration=args.get("estimated_duration", 30),
            is_active=True,
            created_by=args.get("created_by", "system"),
            created_at=now,
            updated_at=now
        )

        await self.storage.save_schedule(schedule)
        logger.info(f"Schedule created: {schedule.schedule_id}")

        return ToolResult(
            success=True,
            data={"schedule": self._schedule_to_dict(schedule)}
        )

    async def _update_schedule(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 4: 更新排程"""
        schedule_id = args.get("schedule_id")
        updates = args.get("updates", {})

        if not schedule_id:
            return ToolResult(
                success=False,
                error="schedule_id is required",
                error_code="INVALID_PARAM"
            )

        if not updates:
            return ToolResult(
                success=False,
                error="updates is required",
                error_code="INVALID_PARAM"
            )

        # 验证 priority 如果提供
        if "priority" in updates:
            if not 1 <= updates["priority"] <= 10:
                return ToolResult(
                    success=False,
                    error="priority must be between 1 and 10",
                    error_code="INVALID_PARAM"
                )

        schedule = await self.storage.update_schedule(schedule_id, updates)
        if not schedule:
            return ToolResult(
                success=False,
                error=f"Schedule {schedule_id} not found",
                error_code="NOT_FOUND"
            )

        logger.info(f"Schedule updated: {schedule_id}")
        return ToolResult(
            success=True,
            data={"schedule": self._schedule_to_dict(schedule)}
        )

    # ========== 任务相关 Tools ==========

    async def _list_tasks(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 5: 获取任务列表"""
        tenant_id = args.get("tenant_id")
        if not tenant_id:
            return ToolResult(
                success=False,
                error="tenant_id is required",
                error_code="INVALID_PARAM"
            )

        # 解析日期
        date_from = None
        date_to = None
        if args.get("date_from"):
            try:
                date_from = date.fromisoformat(args["date_from"])
            except ValueError:
                return ToolResult(
                    success=False,
                    error="Invalid date_from format, use YYYY-MM-DD",
                    error_code="INVALID_PARAM"
                )
        if args.get("date_to"):
            try:
                date_to = date.fromisoformat(args["date_to"])
            except ValueError:
                return ToolResult(
                    success=False,
                    error="Invalid date_to format, use YYYY-MM-DD",
                    error_code="INVALID_PARAM"
                )

        tasks, total = await self.storage.list_tasks(
            tenant_id=tenant_id,
            zone_id=args.get("zone_id"),
            robot_id=args.get("robot_id"),
            status=args.get("status"),
            date_from=date_from,
            date_to=date_to,
            limit=args.get("limit", 50),
            offset=args.get("offset", 0)
        )

        return ToolResult(
            success=True,
            data={
                "tasks": [self._task_to_dict(t) for t in tasks],
                "total": total,
                "limit": args.get("limit", 50),
                "offset": args.get("offset", 0)
            }
        )

    async def _get_task(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 6: 获取任务详情"""
        task_id = args.get("task_id")
        if not task_id:
            return ToolResult(
                success=False,
                error="task_id is required",
                error_code="INVALID_PARAM"
            )

        task = await self.storage.get_task(task_id)
        if not task:
            return ToolResult(
                success=False,
                error=f"Task {task_id} not found",
                error_code="NOT_FOUND"
            )

        return ToolResult(
            success=True,
            data={"task": self._task_to_dict(task)}
        )

    async def _create_task(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 7: 创建任务"""
        required = ["tenant_id", "zone_id", "task_type"]
        for field in required:
            if not args.get(field):
                return ToolResult(
                    success=False,
                    error=f"{field} is required",
                    error_code="INVALID_PARAM"
                )

        task_type = args["task_type"]
        priority = args.get("priority", 5)

        # emergency 任务自动设置 priority=1
        if task_type == "emergency":
            priority = 1

        # 验证 priority 范围
        if not 1 <= priority <= 10:
            return ToolResult(
                success=False,
                error="priority must be between 1 and 10",
                error_code="INVALID_PARAM"
            )

        # 解析 scheduled_start
        scheduled_start = None
        if args.get("scheduled_start"):
            try:
                scheduled_start = datetime.fromisoformat(args["scheduled_start"].replace("Z", "+00:00"))
            except ValueError:
                return ToolResult(
                    success=False,
                    error="Invalid scheduled_start format",
                    error_code="INVALID_PARAM"
                )

        now = datetime.utcnow()
        task = CleaningTask(
            task_id=f"task_{uuid4().hex[:8]}",
            tenant_id=args["tenant_id"],
            zone_id=args["zone_id"],
            zone_name=args.get("zone_name"),
            task_type=TaskType(task_type),
            status=TaskStatus.PENDING,
            priority=priority,
            scheduled_start=scheduled_start,
            schedule_id=args.get("schedule_id"),
            notes=args.get("notes"),
            created_by=args.get("created_by", "system"),
            created_at=now,
            updated_at=now
        )

        await self.storage.save_task(task)
        logger.info(f"Task created: {task.task_id}, type={task_type}, priority={priority}")

        return ToolResult(
            success=True,
            data={"task": self._task_to_dict(task)}
        )

    async def _update_status(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 8: 更新任务状态（状态机）"""
        task_id = args.get("task_id")
        new_status = args.get("status")

        if not task_id or not new_status:
            return ToolResult(
                success=False,
                error="task_id and status are required",
                error_code="INVALID_PARAM"
            )

        task = await self.storage.get_task(task_id)
        if not task:
            return ToolResult(
                success=False,
                error=f"Task {task_id} not found",
                error_code="NOT_FOUND"
            )

        # 验证状态流转
        try:
            new_status_enum = TaskStatus(new_status)
        except ValueError:
            return ToolResult(
                success=False,
                error=f"Invalid status: {new_status}",
                error_code="INVALID_PARAM"
            )

        valid_next = VALID_TRANSITIONS.get(task.status, [])
        if new_status_enum not in valid_next:
            return ToolResult(
                success=False,
                error=f"Invalid status transition: {task.status.value} → {new_status}. Valid: {[s.value for s in valid_next]}",
                error_code="INVALID_STATE"
            )

        # 特殊验证
        if new_status_enum == TaskStatus.ASSIGNED:
            if not args.get("robot_id"):
                return ToolResult(
                    success=False,
                    error="robot_id is required when assigning task",
                    error_code="INVALID_PARAM"
                )

        if new_status_enum == TaskStatus.COMPLETED:
            if args.get("completion_rate") is None:
                return ToolResult(
                    success=False,
                    error="completion_rate is required when completing task",
                    error_code="INVALID_PARAM"
                )

        if new_status_enum == TaskStatus.FAILED:
            if not args.get("failure_reason"):
                return ToolResult(
                    success=False,
                    error="failure_reason is required when task fails",
                    error_code="INVALID_PARAM"
                )

        # 构建更新
        updates = {
            "status": new_status_enum,
            "updated_at": datetime.utcnow()
        }

        if args.get("robot_id"):
            updates["assigned_robot_id"] = args["robot_id"]
            updates["assigned_robot_name"] = args.get("robot_name")

        if args.get("actual_start"):
            try:
                updates["actual_start"] = datetime.fromisoformat(args["actual_start"].replace("Z", "+00:00"))
            except ValueError:
                pass

        if args.get("actual_end"):
            try:
                updates["actual_end"] = datetime.fromisoformat(args["actual_end"].replace("Z", "+00:00"))
            except ValueError:
                pass

        if args.get("completion_rate") is not None:
            updates["completion_rate"] = args["completion_rate"]

        if args.get("failure_reason"):
            updates["failure_reason"] = args["failure_reason"]

        # 自动设置时间
        if new_status_enum == TaskStatus.IN_PROGRESS and not task.actual_start:
            updates["actual_start"] = datetime.utcnow()

        if new_status_enum in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            updates["actual_end"] = datetime.utcnow()

        updated_task = await self.storage.update_task(task_id, updates)
        logger.info(f"Task {task_id} status updated: {task.status.value} → {new_status}")

        return ToolResult(
            success=True,
            data={"task": self._task_to_dict(updated_task)}
        )

    async def _get_pending_tasks(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 9: 获取待执行任务列表（供Agent调度）"""
        tenant_id = args.get("tenant_id")
        if not tenant_id:
            return ToolResult(
                success=False,
                error="tenant_id is required",
                error_code="INVALID_PARAM"
            )

        tasks = await self.storage.get_pending_tasks(
            tenant_id=tenant_id,
            zone_ids=args.get("zone_ids"),
            max_count=args.get("max_count", 20)
        )

        return ToolResult(
            success=True,
            data={
                "tasks": [self._task_to_dict(t) for t in tasks],
                "count": len(tasks)
            }
        )

    async def _generate_daily_tasks(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 10: 根据排程生成每日任务"""
        tenant_id = args.get("tenant_id")
        date_str = args.get("date")

        if not tenant_id or not date_str:
            return ToolResult(
                success=False,
                error="tenant_id and date are required",
                error_code="INVALID_PARAM"
            )

        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            return ToolResult(
                success=False,
                error="Invalid date format, use YYYY-MM-DD",
                error_code="INVALID_PARAM"
            )

        # 获取该日期是星期几（1=周一，7=周日）
        weekday = target_date.isoweekday()

        # 获取活跃的排程
        schedules = await self.storage.get_active_schedules(tenant_id)

        generated_tasks = []
        skipped_count = 0

        for schedule in schedules:
            # 检查频率
            if schedule.frequency == CleaningFrequency.ONCE:
                # 一次性排程只在创建当天生成
                if schedule.created_at.date() != target_date:
                    continue

            # 检查是否已生成（幂等）
            if await self.storage.is_task_generated(schedule.schedule_id, target_date):
                skipped_count += 1
                continue

            # 检查时间段的days是否包含今天
            should_generate = False
            scheduled_start = None

            for slot in schedule.time_slots:
                if weekday in slot.days:
                    should_generate = True
                    # 计算 scheduled_start
                    try:
                        hour, minute = map(int, slot.start.split(":"))
                        scheduled_start = datetime.combine(
                            target_date,
                            datetime.min.time().replace(hour=hour, minute=minute)
                        )
                    except ValueError:
                        pass
                    break

            if not should_generate:
                continue

            # 创建任务
            now = datetime.utcnow()
            task = CleaningTask(
                task_id=f"task_{uuid4().hex[:8]}",
                tenant_id=tenant_id,
                zone_id=schedule.zone_id,
                zone_name=schedule.zone_name,
                task_type=schedule.task_type,
                status=TaskStatus.PENDING,
                priority=schedule.priority,
                scheduled_start=scheduled_start,
                schedule_id=schedule.schedule_id,
                created_by="schedule_generator",
                created_at=now,
                updated_at=now
            )

            await self.storage.save_task(task)
            await self.storage.mark_task_generated(schedule.schedule_id, target_date)
            generated_tasks.append(task)

        logger.info(f"Generated {len(generated_tasks)} tasks for {date_str}, skipped {skipped_count}")

        return ToolResult(
            success=True,
            data={
                "generated_count": len(generated_tasks),
                "skipped_count": skipped_count,
                "tasks": [self._task_to_dict(t) for t in generated_tasks]
            }
        )

    # ========== 辅助方法 ==========

    def _schedule_to_dict(self, schedule: CleaningSchedule) -> dict:
        """转换排程为字典"""
        return {
            "schedule_id": schedule.schedule_id,
            "tenant_id": schedule.tenant_id,
            "zone_id": schedule.zone_id,
            "zone_name": schedule.zone_name,
            "task_type": schedule.task_type.value,
            "frequency": schedule.frequency.value,
            "time_slots": [
                {"start": ts.start, "end": ts.end, "days": ts.days}
                for ts in schedule.time_slots
            ],
            "priority": schedule.priority,
            "estimated_duration": schedule.estimated_duration,
            "is_active": schedule.is_active,
            "created_by": schedule.created_by,
            "created_at": schedule.created_at.isoformat(),
            "updated_at": schedule.updated_at.isoformat(),
        }

    def _task_to_dict(self, task: CleaningTask) -> dict:
        """转换任务为字典"""
        return {
            "task_id": task.task_id,
            "tenant_id": task.tenant_id,
            "zone_id": task.zone_id,
            "zone_name": task.zone_name,
            "task_type": task.task_type.value,
            "status": task.status.value,
            "priority": task.priority,
            "scheduled_start": task.scheduled_start.isoformat() if task.scheduled_start else None,
            "scheduled_end": task.scheduled_end.isoformat() if task.scheduled_end else None,
            "actual_start": task.actual_start.isoformat() if task.actual_start else None,
            "actual_end": task.actual_end.isoformat() if task.actual_end else None,
            "assigned_robot_id": task.assigned_robot_id,
            "assigned_robot_name": task.assigned_robot_name,
            "completion_rate": task.completion_rate,
            "failure_reason": task.failure_reason,
            "schedule_id": task.schedule_id,
            "notes": task.notes,
            "created_by": task.created_by,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        }
