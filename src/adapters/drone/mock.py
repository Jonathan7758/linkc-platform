"""
Mock Drone Adapter - 模拟无人机适配器
"""

import asyncio
import random
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from .base import (
    DroneAdapter,
    DroneState,
    DroneStatus,
    DronePosition,
    FlightMode,
    FlightTask,
    FlightResult,
)

logger = logging.getLogger("ecis_robot.adapters.drone")


class MockDroneAdapter(DroneAdapter):
    """
    模拟无人机适配器

    用于开发和测试，模拟真实无人机的行为
    """

    def __init__(self, drone_id: str, config: Dict[str, Any] = None):
        super().__init__(drone_id, config)
        self._connected = False
        self._home_position = DronePosition(
            latitude=31.2304,
            longitude=121.4737,
            altitude=0
        )
        # 模拟配置
        self._sim_config = {
            "takeoff_time_sec": 5,
            "land_time_sec": 5,
            "speed_ms": 5.0,
            "battery_drain_per_min": 2,
            "simulate_failures": config.get("simulate_failures", False) if config else False,
        }

    async def connect(self) -> bool:
        """连接无人机"""
        await asyncio.sleep(0.5)  # 模拟连接延迟
        self._connected = True
        self._state = DroneState(
            drone_id=self.drone_id,
            status=DroneStatus.IDLE,
            position=DronePosition(
                latitude=self._home_position.latitude,
                longitude=self._home_position.longitude,
                altitude=0
            ),
            battery_percent=100,
            flight_mode=FlightMode.MANUAL,
            signal_strength=95,
        )
        logger.info(f"Mock drone {self.drone_id} connected")
        return True

    async def disconnect(self) -> None:
        """断开连接"""
        self._connected = False
        self._state.status = DroneStatus.OFFLINE
        logger.info(f"Mock drone {self.drone_id} disconnected")

    async def get_status(self) -> DroneState:
        """获取状态"""
        if not self._connected:
            return DroneState(
                drone_id=self.drone_id,
                status=DroneStatus.OFFLINE
            )
        self._state.last_updated = datetime.utcnow()
        return self._state

    async def arm(self) -> bool:
        """解锁电机"""
        if not self._connected:
            return False
        await asyncio.sleep(0.5)
        self._state.is_armed = True
        logger.info(f"Mock drone {self.drone_id} armed")
        return True

    async def disarm(self) -> bool:
        """锁定电机"""
        if not self._connected:
            return False
        await asyncio.sleep(0.5)
        self._state.is_armed = False
        logger.info(f"Mock drone {self.drone_id} disarmed")
        return True

    async def takeoff(self, altitude_m: float = 10.0) -> bool:
        """起飞到指定高度"""
        if not self._connected or not self._state.is_armed:
            return False

        self._state.status = DroneStatus.TAKING_OFF
        logger.info(f"Mock drone {self.drone_id} taking off to {altitude_m}m")

        # 模拟起飞过程
        steps = int(self._sim_config["takeoff_time_sec"])
        altitude_per_step = altitude_m / steps

        for i in range(steps):
            await asyncio.sleep(1)
            if self._state.position:
                self._state.position.altitude += altitude_per_step
            self._drain_battery(0.1)

        self._state.status = DroneStatus.HOVERING
        self._state.flight_mode = FlightMode.AUTO
        logger.info(f"Mock drone {self.drone_id} reached altitude {altitude_m}m")
        return True

    async def land(self) -> bool:
        """降落"""
        if not self._connected:
            return False

        self._state.status = DroneStatus.LANDING
        logger.info(f"Mock drone {self.drone_id} landing")

        if self._state.position:
            current_alt = self._state.position.altitude
            steps = max(1, int(current_alt / 2))

            for i in range(steps):
                await asyncio.sleep(1)
                self._state.position.altitude = max(0, self._state.position.altitude - 2)
                self._drain_battery(0.1)

        self._state.status = DroneStatus.IDLE
        self._state.flight_mode = FlightMode.MANUAL
        self._state.is_armed = False
        if self._state.position:
            self._state.position.altitude = 0
        logger.info(f"Mock drone {self.drone_id} landed")
        return True

    async def return_to_home(self) -> bool:
        """返回起飞点"""
        if not self._connected:
            return False

        self._state.flight_mode = FlightMode.RETURN_HOME
        logger.info(f"Mock drone {self.drone_id} returning to home")

        # 模拟返回
        await asyncio.sleep(3)
        self._state.position = DronePosition(
            latitude=self._home_position.latitude,
            longitude=self._home_position.longitude,
            altitude=self._state.position.altitude if self._state.position else 10
        )
        self._drain_battery(1)

        return await self.land()

    async def goto_position(
        self,
        position: DronePosition,
        speed_ms: float = 5.0
    ) -> bool:
        """飞往指定位置"""
        if not self._connected or self._state.status not in [DroneStatus.HOVERING, DroneStatus.FLYING]:
            return False

        self._state.status = DroneStatus.FLYING
        self._state.speed_ms = speed_ms
        logger.info(f"Mock drone {self.drone_id} flying to ({position.latitude}, {position.longitude}, {position.altitude})")

        # 模拟飞行
        await asyncio.sleep(2)
        self._state.position = position
        self._drain_battery(0.5)

        self._state.status = DroneStatus.HOVERING
        self._state.speed_ms = 0
        return True

    async def execute_flight_task(self, task: FlightTask) -> FlightResult:
        """执行飞行任务"""
        if not self._connected:
            return FlightResult(
                success=False,
                task_id=task.task_id,
                error_message="Drone not connected"
            )

        start_time = datetime.utcnow()
        images_captured = 0
        anomalies = []
        total_distance = 0.0

        logger.info(f"Mock drone {self.drone_id} executing task {task.task_id} ({task.task_type})")

        # 起飞
        if self._state.status == DroneStatus.IDLE:
            if not await self.arm():
                return FlightResult(
                    success=False,
                    task_id=task.task_id,
                    error_message="Failed to arm"
                )
            if not await self.takeoff(task.altitude_m):
                return FlightResult(
                    success=False,
                    task_id=task.task_id,
                    error_message="Failed to takeoff"
                )

        # 设置飞行模式
        if task.task_type == "patrol":
            self._state.flight_mode = FlightMode.PATROL
        elif task.task_type in ["inspect", "facade", "roof"]:
            self._state.flight_mode = FlightMode.INSPECTION
        elif task.task_type == "deliver":
            self._state.flight_mode = FlightMode.DELIVERY

        # 执行航点飞行
        for i, waypoint in enumerate(task.waypoints):
            logger.info(f"Mock drone {self.drone_id} flying to waypoint {i+1}/{len(task.waypoints)}")

            await self.goto_position(waypoint, task.speed_ms)
            total_distance += 100  # 模拟距离

            # 模拟拍照
            if task.task_type in ["patrol", "inspect", "photograph", "facade", "roof"]:
                await self.capture_image()
                images_captured += 1

                # 模拟检测异常
                if random.random() < 0.1:
                    anomalies.append({
                        "type": "detected_object",
                        "location": {"lat": waypoint.latitude, "lon": waypoint.longitude},
                        "confidence": random.uniform(0.7, 0.95),
                    })

        # 返回降落
        await self.return_to_home()

        duration = int((datetime.utcnow() - start_time).total_seconds())

        logger.info(f"Mock drone {self.drone_id} completed task {task.task_id}")
        return FlightResult(
            success=True,
            task_id=task.task_id,
            duration_sec=duration,
            distance_m=total_distance,
            images_captured=images_captured,
            anomalies_detected=anomalies,
        )

    async def start_camera(self, mode: str = "visible") -> bool:
        """启动相机"""
        if not self._connected:
            return False
        await asyncio.sleep(0.5)
        self._state.camera_active = True
        logger.info(f"Mock drone {self.drone_id} camera started ({mode})")
        return True

    async def stop_camera(self) -> bool:
        """停止相机"""
        if not self._connected:
            return False
        await asyncio.sleep(0.2)
        self._state.camera_active = False
        logger.info(f"Mock drone {self.drone_id} camera stopped")
        return True

    async def capture_image(self) -> Optional[str]:
        """拍照，返回图片路径或 URL"""
        if not self._connected or not self._state.camera_active:
            if not self._state.camera_active:
                await self.start_camera()

        await asyncio.sleep(0.3)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        image_path = f"/tmp/drone_{self.drone_id}_img_{timestamp}.jpg"
        logger.debug(f"Mock drone {self.drone_id} captured image: {image_path}")
        return image_path

    async def start_video_recording(self) -> bool:
        """开始录像"""
        if not self._connected:
            return False
        await self.start_camera()
        logger.info(f"Mock drone {self.drone_id} started video recording")
        return True

    async def stop_video_recording(self) -> Optional[str]:
        """停止录像，返回视频路径或 URL"""
        if not self._connected:
            return None
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        video_path = f"/tmp/drone_{self.drone_id}_video_{timestamp}.mp4"
        logger.info(f"Mock drone {self.drone_id} stopped video recording: {video_path}")
        return video_path

    async def emergency_stop(self) -> bool:
        """紧急停止"""
        logger.warning(f"Mock drone {self.drone_id} EMERGENCY STOP")
        self._state.status = DroneStatus.HOVERING
        self._state.speed_ms = 0
        self._state.flight_mode = FlightMode.MANUAL
        return True

    def _drain_battery(self, percent: float) -> None:
        """消耗电量"""
        self._state.battery_percent = max(0, self._state.battery_percent - percent)
