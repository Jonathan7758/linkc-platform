"""
Drone Agent - 无人机 Agent

实现无人机的任务接收和执行能力
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from ..task_receiver import TaskReceiverMixin, ValidationResult
from ...adapters.drone import (
    DroneAdapter,
    MockDroneAdapter,
    DronePosition,
    FlightTask,
    DroneStatus,
)
from ...capabilities.drone import get_drone_capability_ids

logger = logging.getLogger("ecis_robot.agents.drone")


@dataclass
class OrchestrationTask:
    """编排任务"""
    task_id: str
    required_capability: str
    parameters: Dict[str, Any]
    priority: int = 3
    timeout_sec: int = 3600


class DroneAgent(TaskReceiverMixin):
    """
    无人机 Agent

    功能:
    - 接收编排任务
    - 控制无人机执行任务
    - 报告任务进度和结果
    """

    CAPABILITIES = get_drone_capability_ids()

    def __init__(
        self,
        agent_id: str,
        adapter: DroneAdapter = None,
        config: Dict[str, Any] = None
    ):
        self.agent_id = agent_id
        self.config = config or {}
        self._adapter = adapter
        self._status = "ready"
        self._current_task: Optional[OrchestrationTask] = None

        # 如果没有提供适配器，创建模拟适配器
        if self._adapter is None:
            self._adapter = MockDroneAdapter(
                drone_id=f"drone-{agent_id}",
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
                logger.info(f"DroneAgent {self.agent_id} started")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to start DroneAgent {self.agent_id}: {e}")
            self._status = "error"
            return False

    async def stop(self) -> None:
        """停止 Agent"""
        await self._adapter.disconnect()
        self._status = "offline"
        logger.info(f"DroneAgent {self.agent_id} stopped")

    # ===== TaskReceiverMixin 实现 =====

    async def _can_accept_task(self) -> bool:
        """检查是否可以接受任务"""
        if self._status != "ready":
            return False
        if self._current_task is not None:
            return False
        state = await self._adapter.get_status()
        return state.status in [DroneStatus.IDLE, DroneStatus.HOVERING]

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

        if capability.startswith("drone.patrol"):
            if "route_id" not in parameters:
                return ValidationResult(valid=False, message="Missing required parameter: route_id")

        elif capability.startswith("drone.inspection"):
            if "building_id" not in parameters:
                return ValidationResult(valid=False, message="Missing required parameter: building_id")

        elif capability == "drone.delivery.aerial":
            required = ["pickup_location", "delivery_location", "recipient"]
            missing = [p for p in required if p not in parameters]
            if missing:
                return ValidationResult(valid=False, message=f"Missing required parameters: {missing}")

        elif capability == "drone.photography.aerial":
            if "target_area" not in parameters:
                return ValidationResult(valid=False, message="Missing required parameter: target_area")

        return ValidationResult(valid=True)

    def _estimate_duration(self, task) -> int:
        """估计执行时间（分钟）"""
        capability = task.parameters.get("capability", "")

        if "patrol" in capability:
            return 45  # 30-60 分钟
        elif "inspection.facade" in capability:
            return 25  # 15-30 分钟
        elif "inspection.roof" in capability:
            return 15  # 10-20 分钟
        elif "delivery" in capability:
            return 10  # 5-15 分钟
        elif "photography" in capability:
            return 20  # 10-30 分钟
        return 30

    async def _on_task_accepted(self, task) -> None:
        """任务接受后的处理"""
        self._status = "busy"
        self._current_task = task
        logger.info(f"DroneAgent {self.agent_id} accepted task {task.task_id}")

        # 异步执行任务
        asyncio.create_task(self._execute_task(task))

    async def _execute_task(self, task: OrchestrationTask) -> None:
        """执行任务"""
        try:
            capability = task.parameters.get("capability", task.required_capability)
            logger.info(f"DroneAgent {self.agent_id} executing {capability}")

            # 报告开始
            await self.report_task_progress(
                task_id=task.task_id,
                progress=0,
                status="started",
                details={"capability": capability}
            )

            # 构建飞行任务
            flight_task = self._build_flight_task(task)

            # 报告准备中
            await self.report_task_progress(
                task_id=task.task_id,
                progress=10,
                status="preparing",
                details={"message": "Preparing for flight"}
            )

            # 执行飞行
            result = await self._adapter.execute_flight_task(flight_task)

            if result.success:
                # 任务成功
                await self.complete_orchestration_task(
                    task_id=task.task_id,
                    result={
                        "success": True,
                        "duration_sec": result.duration_sec,
                        "distance_m": result.distance_m,
                        "images_captured": result.images_captured,
                        "video_duration_sec": result.video_duration_sec,
                        "anomalies": result.anomalies_detected,
                    }
                )
            else:
                # 任务失败
                await self.fail_orchestration_task(
                    task_id=task.task_id,
                    error_code="FLIGHT_FAILED",
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

    def _build_flight_task(self, task: OrchestrationTask) -> FlightTask:
        """构建飞行任务"""
        params = task.parameters
        capability = params.get("capability", task.required_capability)

        # 确定任务类型
        if "patrol" in capability:
            task_type = "patrol"
        elif "inspection" in capability:
            task_type = "inspect"
        elif "delivery" in capability:
            task_type = "deliver"
        elif "photography" in capability:
            task_type = "photograph"
        else:
            task_type = "custom"

        # 构建航点
        waypoints = []
        if "waypoints" in params:
            for wp in params["waypoints"]:
                waypoints.append(DronePosition(
                    latitude=wp.get("lat", 0),
                    longitude=wp.get("lon", 0),
                    altitude=wp.get("alt", params.get("altitude_m", 50)),
                ))
        elif "checkpoints" in params:
            # 如果只有检查点名称，生成模拟坐标
            base_lat, base_lon = 31.2304, 121.4737
            for i, cp in enumerate(params["checkpoints"]):
                waypoints.append(DronePosition(
                    latitude=base_lat + i * 0.001,
                    longitude=base_lon + i * 0.001,
                    altitude=params.get("altitude_m", 50),
                ))
        else:
            # 默认单点任务
            waypoints.append(DronePosition(
                latitude=params.get("latitude", 31.2304),
                longitude=params.get("longitude", 121.4737),
                altitude=params.get("altitude_m", 50),
            ))

        return FlightTask(
            task_id=task.task_id,
            task_type=task_type,
            waypoints=waypoints,
            parameters=params,
            altitude_m=params.get("altitude_m", 50),
            speed_ms=params.get("speed_ms", 5.0),
        )

    # ===== 直接控制方法 =====

    async def takeoff(self, altitude_m: float = 10.0) -> bool:
        """起飞"""
        if not await self._adapter.arm():
            return False
        return await self._adapter.takeoff(altitude_m)

    async def land(self) -> bool:
        """降落"""
        return await self._adapter.land()

    async def return_home(self) -> bool:
        """返航"""
        return await self._adapter.return_to_home()

    async def emergency_stop(self) -> bool:
        """紧急停止"""
        result = await self._adapter.emergency_stop()
        self._status = "ready"
        self._current_task = None
        return result

    async def get_drone_status(self) -> Dict[str, Any]:
        """获取无人机状态"""
        state = await self._adapter.get_status()
        return {
            "drone_id": state.drone_id,
            "status": state.status.value,
            "battery_percent": state.battery_percent,
            "position": {
                "latitude": state.position.latitude if state.position else None,
                "longitude": state.position.longitude if state.position else None,
                "altitude": state.position.altitude if state.position else None,
            },
            "flight_mode": state.flight_mode.value,
            "is_armed": state.is_armed,
            "camera_active": state.camera_active,
            "signal_strength": state.signal_strength,
        }
