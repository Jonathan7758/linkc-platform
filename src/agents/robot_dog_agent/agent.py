"""
Robot Dog Agent - 机器狗 Agent

实现机器狗的任务接收和执行能力
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from ..task_receiver import TaskReceiverMixin, ValidationResult
from ...adapters.robot_dog import (
    RobotDogAdapter,
    MockRobotDogAdapter,
    RobotDogPosition,
    GroundTask,
    RobotDogStatus,
    MovementMode,
    GaitType,
)
from ...capabilities.robot_dog import get_robot_dog_capability_ids

logger = logging.getLogger("ecis_robot.agents.robot_dog")


@dataclass
class OrchestrationTask:
    """编排任务"""
    task_id: str
    required_capability: str
    parameters: Dict[str, Any]
    priority: int = 3
    timeout_sec: int = 3600


class RobotDogAgent(TaskReceiverMixin):
    """
    机器狗 Agent

    功能:
    - 接收编排任务
    - 控制机器狗执行任务
    - 报告任务进度和结果
    """

    CAPABILITIES = get_robot_dog_capability_ids()

    def __init__(
        self,
        agent_id: str,
        adapter: RobotDogAdapter = None,
        config: Dict[str, Any] = None
    ):
        self.agent_id = agent_id
        self.config = config or {}
        self._adapter = adapter
        self._status = "ready"
        self._current_task: Optional[OrchestrationTask] = None

        # 如果没有提供适配器，创建模拟适配器
        if self._adapter is None:
            self._adapter = MockRobotDogAdapter(
                robot_id=f"robotdog-{agent_id}",
                config=self.config.get("adapter_config")
            )

    @property
    def capabilities(self) -> List[str]:
        """获取支持的能力列表"""
        return self.CAPABILITIES

    @property
    def status(self) -> str:
        """获取当前状态"""
        return self._status

    async def start(self) -> bool:
        """启动 Agent"""
        try:
            connected = await self._adapter.connect()
            if connected:
                self._status = "ready"
                logger.info(f"RobotDogAgent {self.agent_id} started")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to start RobotDogAgent {self.agent_id}: {e}")
            self._status = "error"
            return False

    async def stop(self) -> None:
        """停止 Agent"""
        await self._adapter.disconnect()
        self._status = "offline"
        logger.info(f"RobotDogAgent {self.agent_id} stopped")

    # ===== TaskReceiverMixin 实现 =====

    async def _can_accept_task(self) -> bool:
        """检查是否可以接受任务"""
        if self._status != "ready":
            return False
        if self._current_task is not None:
            return False
        state = await self._adapter.get_status()
        return state.status in [RobotDogStatus.IDLE, RobotDogStatus.STANDING, RobotDogStatus.RESTING]

    def _has_capability(self, capability_id: str) -> bool:
        """检查是否具备指定能力"""
        # 支持通配符匹配
        if capability_id.endswith(".*"):
            prefix = capability_id[:-2]
            return any(cap.startswith(prefix) for cap in self.CAPABILITIES)
        return capability_id in self.CAPABILITIES

    def _validate_task_parameters(self, parameters: Dict[str, Any]) -> ValidationResult:
        """验证任务参数"""
        # 基本验证
        if not parameters:
            return ValidationResult(valid=False, message="Parameters cannot be empty")

        # 根据能力类型验证必需参数
        capability = parameters.get("capability", "")

        if capability == "robotdog.patrol.rough":
            if "route_id" not in parameters:
                return ValidationResult(valid=False, message="Missing required parameter: route_id")

        elif capability == "robotdog.inspection.underground":
            if "area_id" not in parameters:
                return ValidationResult(valid=False, message="Missing required parameter: area_id")

        elif capability == "robotdog.escort.security":
            required = ["person_id", "start_location", "end_location"]
            missing = [p for p in required if p not in parameters]
            if missing:
                return ValidationResult(valid=False, message=f"Missing required parameters: {missing}")

        elif capability == "robotdog.care.companion":
            required = ["person_id", "location"]
            missing = [p for p in required if p not in parameters]
            if missing:
                return ValidationResult(valid=False, message=f"Missing required parameters: {missing}")

        return ValidationResult(valid=True)

    def _estimate_duration(self, task) -> int:
        """估计执行时间（分钟）"""
        capability = task.parameters.get("capability", "")

        if "patrol" in capability:
            return 45  # 30-60 分钟
        elif "inspection" in capability:
            return 30  # 20-40 分钟
        elif "escort" in capability:
            return 20  # 可变
        elif "companion" in capability:
            duration_min = task.parameters.get("duration_min", 30)
            return duration_min
        return 30

    async def _on_task_accepted(self, task) -> None:
        """任务接受后的处理"""
        self._status = "busy"
        self._current_task = task
        logger.info(f"RobotDogAgent {self.agent_id} accepted task {task.task_id}")

        # 异步执行任务
        asyncio.create_task(self._execute_task(task))

    async def _execute_task(self, task: OrchestrationTask) -> None:
        """执行任务"""
        try:
            capability = task.parameters.get("capability", task.required_capability)
            logger.info(f"RobotDogAgent {self.agent_id} executing {capability}")

            # 报告开始
            await self.report_task_progress(
                task_id=task.task_id,
                progress=0,
                status="started",
                details={"capability": capability}
            )

            # 构建地面任务
            ground_task = self._build_ground_task(task)

            # 报告准备中
            await self.report_task_progress(
                task_id=task.task_id,
                progress=10,
                status="preparing",
                details={"message": "Preparing robot dog"}
            )

            # 执行任务
            result = await self._adapter.execute_ground_task(ground_task)

            if result.success:
                # 任务成功
                await self.complete_orchestration_task(
                    task_id=task.task_id,
                    result={
                        "success": True,
                        "duration_sec": result.duration_sec,
                        "distance_m": result.distance_m,
                        "images_captured": result.images_captured,
                        "anomalies": result.anomalies_detected,
                        "health_data": result.health_data,
                        "gas_readings": result.gas_readings,
                    }
                )
            else:
                # 任务失败
                await self.fail_orchestration_task(
                    task_id=task.task_id,
                    error_code="TASK_FAILED",
                    error_message=result.error_message
                )

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            await self.fail_orchestration_task(
                task_id=task.task_id,
                error_code="EXECUTION_ERROR",
                error_message=str(e)
            )
        finally:
            self._status = "ready"
            self._current_task = None

    def _build_ground_task(self, task: OrchestrationTask) -> GroundTask:
        """构建地面任务"""
        params = task.parameters
        capability = params.get("capability", task.required_capability)

        # 确定任务类型
        if "patrol" in capability:
            task_type = "patrol"
        elif "inspection" in capability:
            task_type = "inspect"
        elif "escort" in capability:
            task_type = "escort"
        elif "companion" in capability:
            task_type = "companion"
        else:
            task_type = "custom"

        # 构建路点
        waypoints = []
        if "waypoints" in params:
            for wp in params["waypoints"]:
                waypoints.append(RobotDogPosition(
                    x=wp.get("x", 0),
                    y=wp.get("y", 0),
                    z=wp.get("z", 0),
                ))
        elif "checkpoints" in params:
            # 如果只有检查点名称，生成模拟坐标
            for i, cp in enumerate(params["checkpoints"]):
                waypoints.append(RobotDogPosition(
                    x=i * 5.0,
                    y=i * 2.0,
                    z=0,
                ))
        elif "start_location" in params and "end_location" in params:
            # 护送任务：起点到终点
            waypoints.append(RobotDogPosition(x=0, y=0, z=0))
            waypoints.append(RobotDogPosition(x=20, y=10, z=0))
        else:
            # 默认单点任务
            waypoints.append(RobotDogPosition(
                x=params.get("x", 0),
                y=params.get("y", 0),
                z=params.get("z", 0),
            ))

        # 确定速度模式
        speed_mode = params.get("speed_mode", "normal")
        if params.get("urgent", False):
            speed_mode = "fast"

        return GroundTask(
            task_id=task.task_id,
            task_type=task_type,
            waypoints=waypoints,
            parameters=params,
            speed_mode=speed_mode,
        )

    # ===== 直接控制方法 =====

    async def stand_up(self) -> bool:
        """站立"""
        return await self._adapter.stand_up()

    async def sit_down(self) -> bool:
        """坐下"""
        return await self._adapter.sit_down()

    async def lie_down(self) -> bool:
        """卧下"""
        return await self._adapter.lie_down()

    async def set_movement_mode(self, mode: str) -> bool:
        """设置运动模式"""
        mode_enum = MovementMode(mode)
        return await self._adapter.set_movement_mode(mode_enum)

    async def set_gait(self, gait: str) -> bool:
        """设置步态"""
        gait_enum = GaitType(gait)
        return await self._adapter.set_gait(gait_enum)

    async def emergency_stop(self) -> bool:
        """紧急停止"""
        result = await self._adapter.emergency_stop()
        self._status = "ready"
        self._current_task = None
        return result

    async def play_sound(self, sound_type: str) -> bool:
        """播放声音"""
        return await self._adapter.play_sound(sound_type)

    async def get_robot_dog_status(self) -> Dict[str, Any]:
        """获取机器狗状态"""
        state = await self._adapter.get_status()
        return {
            "robot_id": state.robot_id,
            "status": state.status.value,
            "battery_percent": state.battery_percent,
            "position": {
                "x": state.position.x if state.position else None,
                "y": state.position.y if state.position else None,
                "z": state.position.z if state.position else None,
            },
            "movement_mode": state.movement_mode.value,
            "gait_type": state.gait_type.value,
            "speed_ms": state.speed_ms,
            "temperature_c": state.temperature_c,
            "camera_active": state.camera_active,
            "lidar_active": state.lidar_active,
        }

    async def get_gas_readings(self) -> Dict[str, float]:
        """获取气体传感器读数"""
        return await self._adapter.get_gas_readings()
