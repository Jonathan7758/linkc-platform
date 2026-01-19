"""
M3: 高仙机器人 MCP Server - Tool 实现
=====================================
基于规格书 docs/specs/M3-gaoxian-mcp.md 实现

12个Tools:
1. robot_list_robots       - 获取机器人列表
2. robot_get_robot         - 获取机器人详情
3. robot_get_status        - 获取机器人实时状态
4. robot_batch_get_status  - 批量获取机器人状态
5. robot_start_task        - 启动清洁任务
6. robot_pause_task        - 暂停当前任务
7. robot_resume_task       - 恢复暂停的任务
8. robot_cancel_task       - 取消当前任务
9. robot_go_to_location    - 指挥机器人移动
10. robot_go_to_charge     - 指挥机器人返回充电
11. robot_get_errors       - 获取故障列表
12. robot_clear_error      - 清除故障
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from .storage import (
    InMemoryRobotStorage,
    Robot,
    RobotStatus,
    RobotStatusSnapshot,
    Location,
    CleaningMode,
    CleaningIntensity,
    ErrorSeverity,
    VALID_STATUS_TRANSITIONS
)
from .mock_client import MockGaoxianClient

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
# Tool 实现
# ============================================================

class RobotTools:
    """机器人管理 Tool 实现"""

    def __init__(self, client: MockGaoxianClient, storage: InMemoryRobotStorage):
        self.client = client
        self.storage = storage

    async def handle(self, name: str, arguments: dict) -> ToolResult:
        """路由 Tool 调用"""
        handlers = {
            "robot_list_robots": self._list_robots,
            "robot_get_robot": self._get_robot,
            "robot_get_status": self._get_status,
            "robot_batch_get_status": self._batch_get_status,
            "robot_start_task": self._start_task,
            "robot_pause_task": self._pause_task,
            "robot_resume_task": self._resume_task,
            "robot_cancel_task": self._cancel_task,
            "robot_go_to_location": self._go_to_location,
            "robot_go_to_charge": self._go_to_charge,
            "robot_get_errors": self._get_errors,
            "robot_clear_error": self._clear_error,
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

    # ========== 设备管理类 Tools ==========

    async def _list_robots(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 1: 获取机器人列表"""
        tenant_id = args.get("tenant_id")
        if not tenant_id:
            return ToolResult(
                success=False,
                error="tenant_id is required",
                error_code="INVALID_PARAM"
            )

        robots = await self.storage.list_robots(
            tenant_id=tenant_id,
            building_id=args.get("building_id"),
            status=args.get("status"),
            robot_type=args.get("robot_type")
        )

        return ToolResult(
            success=True,
            data={
                "robots": [self._robot_to_dict(r) for r in robots],
                "total": len(robots)
            }
        )

    async def _get_robot(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 2: 获取机器人详情"""
        robot_id = args.get("robot_id")
        if not robot_id:
            return ToolResult(
                success=False,
                error="robot_id is required",
                error_code="INVALID_PARAM"
            )

        robot = await self.storage.get_robot(robot_id)
        if not robot:
            return ToolResult(
                success=False,
                error=f"Robot {robot_id} not found",
                error_code="NOT_FOUND"
            )

        return ToolResult(
            success=True,
            data={"robot": self._robot_to_dict(robot)}
        )

    async def _get_status(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 3: 获取机器人实时状态"""
        robot_id = args.get("robot_id")
        if not robot_id:
            return ToolResult(
                success=False,
                error="robot_id is required",
                error_code="INVALID_PARAM"
            )

        # 检查机器人是否存在
        robot = await self.storage.get_robot(robot_id)
        if not robot:
            return ToolResult(
                success=False,
                error=f"Robot {robot_id} not found",
                error_code="NOT_FOUND"
            )

        snapshot = await self.storage.get_status_snapshot(robot_id)
        if not snapshot:
            return ToolResult(
                success=False,
                error=f"Status not available for robot {robot_id}",
                error_code="NOT_FOUND"
            )

        return ToolResult(
            success=True,
            data=self._snapshot_to_dict(snapshot)
        )

    async def _batch_get_status(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 4: 批量获取机器人状态"""
        robot_ids = args.get("robot_ids", [])
        if not robot_ids:
            return ToolResult(
                success=False,
                error="robot_ids is required",
                error_code="INVALID_PARAM"
            )

        if len(robot_ids) > 20:
            return ToolResult(
                success=False,
                error="Maximum 20 robots per batch",
                error_code="INVALID_PARAM"
            )

        snapshots = await self.storage.batch_get_status(robot_ids)

        return ToolResult(
            success=True,
            data={
                "statuses": [self._snapshot_to_dict(s) for s in snapshots],
                "count": len(snapshots)
            }
        )

    # ========== 任务控制类 Tools ==========

    async def _start_task(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 5: 启动清洁任务"""
        robot_id = args.get("robot_id")
        zone_id = args.get("zone_id")
        task_type = args.get("task_type")

        # 参数验证
        if not robot_id or not zone_id or not task_type:
            return ToolResult(
                success=False,
                error="robot_id, zone_id, and task_type are required",
                error_code="INVALID_PARAM"
            )

        # 验证 task_type
        try:
            cleaning_mode = CleaningMode(task_type)
        except ValueError:
            return ToolResult(
                success=False,
                error=f"Invalid task_type: {task_type}. Valid: vacuum, mop, vacuum_mop",
                error_code="INVALID_PARAM"
            )

        # 检查机器人
        robot = await self.storage.get_robot(robot_id)
        if not robot:
            return ToolResult(
                success=False,
                error=f"Robot {robot_id} not found",
                error_code="NOT_FOUND"
            )

        # 检查机器人状态
        if robot.status == RobotStatus.OFFLINE:
            return ToolResult(
                success=False,
                error="Robot is offline",
                error_code="ROBOT_OFFLINE"
            )

        if robot.status not in [RobotStatus.IDLE, RobotStatus.CHARGING]:
            return ToolResult(
                success=False,
                error=f"Robot is busy (status: {robot.status.value})",
                error_code="ROBOT_BUSY"
            )

        if robot.status == RobotStatus.ERROR:
            return ToolResult(
                success=False,
                error="Robot has unresolved errors",
                error_code="ROBOT_ERROR"
            )

        # 检查电量
        snapshot = await self.storage.get_status_snapshot(robot_id)
        if snapshot and snapshot.battery_level < 20:
            return ToolResult(
                success=False,
                error=f"Battery too low ({snapshot.battery_level}%), minimum 20% required",
                error_code="LOW_BATTERY"
            )

        # 检查故障
        errors = await self.storage.get_active_errors_for_robot(robot_id)
        critical_errors = [e for e in errors if e.severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]]
        if critical_errors:
            return ToolResult(
                success=False,
                error=f"Robot has {len(critical_errors)} unresolved error(s)",
                error_code="ROBOT_ERROR"
            )

        # 解析清洁强度
        cleaning_intensity = CleaningIntensity.STANDARD
        if args.get("cleaning_mode"):
            try:
                cleaning_intensity = CleaningIntensity(args["cleaning_mode"])
            except ValueError:
                pass

        # 启动任务
        robot_task = await self.client.send_task(
            robot_id=robot_id,
            zone_id=zone_id,
            task_type=cleaning_mode,
            cleaning_mode=cleaning_intensity,
            task_id=args.get("task_id")
        )

        if not robot_task:
            return ToolResult(
                success=False,
                error="Failed to start task",
                error_code="API_ERROR"
            )

        logger.info(f"Task started: robot={robot_id}, zone={zone_id}, type={task_type}")

        return ToolResult(
            success=True,
            data={
                "robot_task_id": robot_task.robot_task_id,
                "robot_id": robot_id,
                "zone_id": zone_id,
                "status": "started",
                "estimated_duration": robot_task.estimated_duration,
                "started_at": robot_task.started_at.isoformat()
            }
        )

    async def _pause_task(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 6: 暂停当前任务"""
        robot_id = args.get("robot_id")
        if not robot_id:
            return ToolResult(
                success=False,
                error="robot_id is required",
                error_code="INVALID_PARAM"
            )

        robot = await self.storage.get_robot(robot_id)
        if not robot:
            return ToolResult(
                success=False,
                error=f"Robot {robot_id} not found",
                error_code="NOT_FOUND"
            )

        if robot.status != RobotStatus.WORKING:
            return ToolResult(
                success=False,
                error=f"Robot is not working (status: {robot.status.value})",
                error_code="INVALID_STATE"
            )

        success = await self.client.pause_task(robot_id, args.get("reason"))
        if not success:
            return ToolResult(
                success=False,
                error="Failed to pause task",
                error_code="API_ERROR"
            )

        return ToolResult(
            success=True,
            data={
                "robot_id": robot_id,
                "status": "paused",
                "paused_at": datetime.utcnow().isoformat()
            }
        )

    async def _resume_task(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 7: 恢复暂停的任务"""
        robot_id = args.get("robot_id")
        if not robot_id:
            return ToolResult(
                success=False,
                error="robot_id is required",
                error_code="INVALID_PARAM"
            )

        robot = await self.storage.get_robot(robot_id)
        if not robot:
            return ToolResult(
                success=False,
                error=f"Robot {robot_id} not found",
                error_code="NOT_FOUND"
            )

        if robot.status != RobotStatus.PAUSED:
            return ToolResult(
                success=False,
                error=f"Robot is not paused (status: {robot.status.value})",
                error_code="INVALID_STATE"
            )

        success = await self.client.resume_task(robot_id)
        if not success:
            return ToolResult(
                success=False,
                error="Failed to resume task",
                error_code="API_ERROR"
            )

        return ToolResult(
            success=True,
            data={
                "robot_id": robot_id,
                "status": "resumed",
                "resumed_at": datetime.utcnow().isoformat()
            }
        )

    async def _cancel_task(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 8: 取消当前任务"""
        robot_id = args.get("robot_id")
        if not robot_id:
            return ToolResult(
                success=False,
                error="robot_id is required",
                error_code="INVALID_PARAM"
            )

        robot = await self.storage.get_robot(robot_id)
        if not robot:
            return ToolResult(
                success=False,
                error=f"Robot {robot_id} not found",
                error_code="NOT_FOUND"
            )

        if robot.status not in [RobotStatus.WORKING, RobotStatus.PAUSED]:
            return ToolResult(
                success=False,
                error=f"No active task to cancel (status: {robot.status.value})",
                error_code="INVALID_STATE"
            )

        progress = await self.client.cancel_task(robot_id, args.get("reason"))
        if progress is None:
            return ToolResult(
                success=False,
                error="Failed to cancel task",
                error_code="API_ERROR"
            )

        return ToolResult(
            success=True,
            data={
                "robot_id": robot_id,
                "status": "cancelled",
                "progress_at_cancel": progress,
                "cancelled_at": datetime.utcnow().isoformat()
            }
        )

    # ========== 导航控制类 Tools ==========

    async def _go_to_location(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 9: 指挥机器人移动到指定位置"""
        robot_id = args.get("robot_id")
        target_location = args.get("target_location")

        if not robot_id or not target_location:
            return ToolResult(
                success=False,
                error="robot_id and target_location are required",
                error_code="INVALID_PARAM"
            )

        robot = await self.storage.get_robot(robot_id)
        if not robot:
            return ToolResult(
                success=False,
                error=f"Robot {robot_id} not found",
                error_code="NOT_FOUND"
            )

        if robot.status != RobotStatus.IDLE:
            return ToolResult(
                success=False,
                error=f"Robot must be idle to navigate (status: {robot.status.value})",
                error_code="INVALID_STATE"
            )

        # 解析目标位置
        try:
            target = Location(
                x=target_location["x"],
                y=target_location["y"],
                floor_id=target_location.get("floor_id")
            )
        except (KeyError, TypeError) as e:
            return ToolResult(
                success=False,
                error=f"Invalid target_location format: {e}",
                error_code="INVALID_PARAM"
            )

        success = await self.client.go_to_location(robot_id, target, args.get("reason"))
        if not success:
            return ToolResult(
                success=False,
                error="Failed to navigate",
                error_code="API_ERROR"
            )

        return ToolResult(
            success=True,
            data={
                "robot_id": robot_id,
                "target_location": {"x": target.x, "y": target.y, "floor_id": target.floor_id},
                "status": "navigating",
                "started_at": datetime.utcnow().isoformat()
            }
        )

    async def _go_to_charge(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 10: 指挥机器人返回充电桩"""
        robot_id = args.get("robot_id")
        force = args.get("force", False)

        if not robot_id:
            return ToolResult(
                success=False,
                error="robot_id is required",
                error_code="INVALID_PARAM"
            )

        robot = await self.storage.get_robot(robot_id)
        if not robot:
            return ToolResult(
                success=False,
                error=f"Robot {robot_id} not found",
                error_code="NOT_FOUND"
            )

        # 非 force 模式下，只有 idle 状态可返回
        if not force and robot.status not in [RobotStatus.IDLE, RobotStatus.CHARGING]:
            return ToolResult(
                success=False,
                error=f"Robot is busy (status: {robot.status.value}). Use force=true to override.",
                error_code="ROBOT_BUSY"
            )

        success = await self.client.go_to_charge(robot_id, force)
        if not success:
            return ToolResult(
                success=False,
                error="Failed to return to charge",
                error_code="API_ERROR"
            )

        return ToolResult(
            success=True,
            data={
                "robot_id": robot_id,
                "status": "returning_to_charge",
                "force": force,
                "started_at": datetime.utcnow().isoformat()
            }
        )

    # ========== 故障处理类 Tools ==========

    async def _get_errors(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 11: 获取故障列表"""
        errors = await self.storage.list_errors(
            robot_id=args.get("robot_id"),
            tenant_id=args.get("tenant_id"),
            severity=args.get("severity"),
            resolved=args.get("resolved", False),
            limit=args.get("limit", 50)
        )

        return ToolResult(
            success=True,
            data={
                "errors": [self._error_to_dict(e) for e in errors],
                "total": len(errors)
            }
        )

    async def _clear_error(self, args: Dict[str, Any]) -> ToolResult:
        """Tool 12: 清除故障"""
        robot_id = args.get("robot_id")
        error_id = args.get("error_id")
        force = args.get("force", False)

        if not robot_id:
            return ToolResult(
                success=False,
                error="robot_id is required",
                error_code="INVALID_PARAM"
            )

        # 如果指定了 error_id，清除特定错误
        if error_id:
            error = await self.storage.get_error(error_id)
            if not error:
                return ToolResult(
                    success=False,
                    error=f"Error {error_id} not found",
                    error_code="NOT_FOUND"
                )

            if error.robot_id != robot_id:
                return ToolResult(
                    success=False,
                    error="Error does not belong to this robot",
                    error_code="INVALID_PARAM"
                )

            # 只能清除 warning 级别，除非 force
            if error.severity != ErrorSeverity.WARNING and not force:
                return ToolResult(
                    success=False,
                    error=f"Cannot clear {error.severity.value} level error without force=true",
                    error_code="INVALID_STATE"
                )

            await self.storage.clear_error(error_id, "operator")

            return ToolResult(
                success=True,
                data={
                    "cleared_count": 1,
                    "cleared_errors": [error_id]
                }
            )

        # 否则清除所有可清除的错误
        errors = await self.storage.get_active_errors_for_robot(robot_id)
        cleared = []

        for error in errors:
            if error.severity == ErrorSeverity.WARNING or force:
                await self.storage.clear_error(error.error_id, "operator")
                cleared.append(error.error_id)

        # 如果清除了所有错误且机器人处于 ERROR 状态，恢复为 IDLE
        robot = await self.storage.get_robot(robot_id)
        if robot and robot.status == RobotStatus.ERROR:
            remaining_errors = await self.storage.get_active_errors_for_robot(robot_id)
            if not remaining_errors:
                await self.storage.update_robot_status(robot_id, RobotStatus.IDLE)
                await self.storage.update_status_snapshot(robot_id, {
                    "status": RobotStatus.IDLE,
                    "error_code": None,
                    "error_message": None
                })

        return ToolResult(
            success=True,
            data={
                "cleared_count": len(cleared),
                "cleared_errors": cleared
            }
        )

    # ========== 辅助方法 ==========

    def _robot_to_dict(self, robot: Robot) -> dict:
        """转换机器人为字典"""
        return {
            "robot_id": robot.robot_id,
            "tenant_id": robot.tenant_id,
            "name": robot.name,
            "brand": robot.brand.value,
            "model": robot.model,
            "serial_number": robot.serial_number,
            "robot_type": robot.robot_type.value,
            "building_id": robot.building_id,
            "floor_ids": robot.floor_ids,
            "home_location": {
                "x": robot.home_location.x,
                "y": robot.home_location.y,
                "floor_id": robot.home_location.floor_id
            } if robot.home_location else None,
            "capabilities": {
                "can_vacuum": robot.capabilities.can_vacuum,
                "can_mop": robot.capabilities.can_mop,
                "can_auto_charge": robot.capabilities.can_auto_charge,
                "can_elevator": robot.capabilities.can_elevator,
                "max_area": robot.capabilities.max_area,
                "max_runtime": robot.capabilities.max_runtime
            },
            "status": robot.status.value,
            "registered_at": robot.registered_at.isoformat(),
            "last_seen_at": robot.last_seen_at.isoformat() if robot.last_seen_at else None
        }

    def _snapshot_to_dict(self, snapshot: RobotStatusSnapshot) -> dict:
        """转换状态快照为字典"""
        return {
            "robot_id": snapshot.robot_id,
            "status": snapshot.status.value,
            "current_location": {
                "x": snapshot.current_location.x,
                "y": snapshot.current_location.y,
                "floor_id": snapshot.current_location.floor_id
            } if snapshot.current_location else None,
            "battery_level": snapshot.battery_level,
            "water_level": snapshot.water_level,
            "dustbin_level": snapshot.dustbin_level,
            "current_task_id": snapshot.current_task_id,
            "current_zone_id": snapshot.current_zone_id,
            "task_progress": snapshot.task_progress,
            "speed": snapshot.speed,
            "cleaning_mode": snapshot.cleaning_mode.value if snapshot.cleaning_mode else None,
            "cleaning_intensity": snapshot.cleaning_intensity.value if snapshot.cleaning_intensity else None,
            "error_code": snapshot.error_code,
            "error_message": snapshot.error_message,
            "timestamp": snapshot.timestamp.isoformat()
        }

    def _error_to_dict(self, error) -> dict:
        """转换错误为字典"""
        return {
            "error_id": error.error_id,
            "robot_id": error.robot_id,
            "robot_name": error.robot_name,
            "error_code": error.error_code,
            "error_type": error.error_type,
            "severity": error.severity.value,
            "message": error.message,
            "location": {
                "x": error.location.x,
                "y": error.location.y
            } if error.location else None,
            "occurred_at": error.occurred_at.isoformat(),
            "resolved": error.resolved,
            "resolved_at": error.resolved_at.isoformat() if error.resolved_at else None,
            "resolved_by": error.resolved_by
        }
