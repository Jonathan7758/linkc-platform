"""
Mock Robot Dog Adapter - 模拟机器狗适配器
"""

import asyncio
import random
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from .base import (
    RobotDogAdapter,
    RobotDogState,
    RobotDogStatus,
    RobotDogPosition,
    MovementMode,
    GaitType,
    GroundTask,
    GroundTaskResult,
)

logger = logging.getLogger("ecis_robot.adapters.robot_dog")


class MockRobotDogAdapter(RobotDogAdapter):
    """
    模拟机器狗适配器

    用于开发和测试，模拟真实机器狗的行为
    """

    def __init__(self, robot_id: str, config: Dict[str, Any] = None):
        super().__init__(robot_id, config)
        self._connected = False
        self._home_position = RobotDogPosition(x=0, y=0, z=0)
        # 模拟配置
        self._sim_config = {
            "stand_up_time_sec": 2,
            "sit_down_time_sec": 2,
            "walk_speed_ms": 1.0,
            "run_speed_ms": 3.0,
            "battery_drain_per_min": 1.5,
            "simulate_failures": config.get("simulate_failures", False) if config else False,
        }
        # 模拟传感器数据
        self._gas_sensors = {
            "co": 0.0,
            "co2": 400.0,
            "ch4": 0.0,
            "h2s": 0.0,
            "o2": 20.9,
        }

    async def connect(self) -> bool:
        """连接机器狗"""
        await asyncio.sleep(0.5)
        self._connected = True
        self._state = RobotDogState(
            robot_id=self.robot_id,
            status=RobotDogStatus.IDLE,
            position=RobotDogPosition(x=0, y=0, z=0),
            battery_percent=100,
            movement_mode=MovementMode.WALK,
            gait_type=GaitType.NORMAL,
            temperature_c=25.0,
        )
        logger.info(f"Mock robot dog {self.robot_id} connected")
        return True

    async def disconnect(self) -> None:
        """断开连接"""
        self._connected = False
        self._state.status = RobotDogStatus.OFFLINE
        logger.info(f"Mock robot dog {self.robot_id} disconnected")

    async def get_status(self) -> RobotDogState:
        """获取状态"""
        if not self._connected:
            return RobotDogState(
                robot_id=self.robot_id,
                status=RobotDogStatus.OFFLINE
            )
        self._state.last_updated = datetime.utcnow()
        return self._state

    async def stand_up(self) -> bool:
        """站立"""
        if not self._connected:
            return False
        logger.info(f"Mock robot dog {self.robot_id} standing up")
        await asyncio.sleep(self._sim_config["stand_up_time_sec"])
        self._state.status = RobotDogStatus.STANDING
        return True

    async def sit_down(self) -> bool:
        """坐下"""
        if not self._connected:
            return False
        logger.info(f"Mock robot dog {self.robot_id} sitting down")
        await asyncio.sleep(self._sim_config["sit_down_time_sec"])
        self._state.status = RobotDogStatus.RESTING
        return True

    async def lie_down(self) -> bool:
        """卧下"""
        if not self._connected:
            return False
        logger.info(f"Mock robot dog {self.robot_id} lying down")
        await asyncio.sleep(self._sim_config["sit_down_time_sec"])
        self._state.status = RobotDogStatus.IDLE
        return True

    async def set_movement_mode(self, mode: MovementMode) -> bool:
        """设置运动模式"""
        if not self._connected:
            return False
        self._state.movement_mode = mode
        logger.info(f"Mock robot dog {self.robot_id} movement mode set to {mode.value}")
        return True

    async def set_gait(self, gait: GaitType) -> bool:
        """设置步态"""
        if not self._connected:
            return False
        self._state.gait_type = gait
        logger.info(f"Mock robot dog {self.robot_id} gait set to {gait.value}")
        return True

    async def goto_position(
        self,
        position: RobotDogPosition,
        speed_mode: str = "normal"
    ) -> bool:
        """移动到指定位置"""
        if not self._connected:
            return False

        if self._state.status not in [RobotDogStatus.STANDING, RobotDogStatus.WALKING]:
            await self.stand_up()

        self._state.status = RobotDogStatus.WALKING

        # 计算速度
        if speed_mode == "fast":
            self._state.speed_ms = self._sim_config["run_speed_ms"]
        else:
            self._state.speed_ms = self._sim_config["walk_speed_ms"]

        logger.info(f"Mock robot dog {self.robot_id} moving to ({position.x}, {position.y}, {position.z})")

        # 模拟移动
        await asyncio.sleep(2)
        self._state.position = position
        self._drain_battery(0.5)

        self._state.status = RobotDogStatus.STANDING
        self._state.speed_ms = 0
        return True

    async def execute_ground_task(self, task: GroundTask) -> GroundTaskResult:
        """执行地面任务"""
        if not self._connected:
            return GroundTaskResult(
                success=False,
                task_id=task.task_id,
                error_message="Robot dog not connected"
            )

        start_time = datetime.utcnow()
        images_captured = 0
        anomalies = []
        total_distance = 0.0
        health_data = {}
        gas_readings = {}

        logger.info(f"Mock robot dog {self.robot_id} executing task {task.task_id} ({task.task_type})")

        # 站立准备
        if self._state.status == RobotDogStatus.IDLE:
            await self.stand_up()

        # 根据任务类型设置步态
        if task.task_type == "patrol":
            if "stairs" in str(task.parameters.get("terrain_type", "")):
                await self.set_gait(GaitType.STAIR)
            elif "slope" in str(task.parameters.get("terrain_type", "")):
                await self.set_gait(GaitType.SLOPE)
        elif task.task_type == "inspect":
            await self.set_gait(GaitType.STABLE)
            # 启动传感器
            if task.parameters.get("gas_detection", False):
                await asyncio.sleep(0.5)  # 模拟传感器预热

        # 执行路点移动
        for i, waypoint in enumerate(task.waypoints):
            logger.info(f"Mock robot dog {self.robot_id} moving to waypoint {i+1}/{len(task.waypoints)}")

            await self.goto_position(waypoint, task.speed_mode)
            total_distance += 10  # 模拟距离

            # 模拟拍照/扫描
            if task.task_type in ["patrol", "inspect"]:
                await self.capture_image()
                images_captured += 1

                # 模拟检测异常
                if random.random() < 0.1:
                    anomalies.append({
                        "type": "detected_anomaly",
                        "location": {"x": waypoint.x, "y": waypoint.y, "z": waypoint.z},
                        "confidence": random.uniform(0.7, 0.95),
                    })

            # 模拟气体检测
            if task.task_type == "inspect" and task.parameters.get("gas_detection", False):
                gas_readings = await self.get_gas_readings()

            # 模拟健康监测
            if task.task_type == "companion":
                health_data = {
                    "movement_detected": True,
                    "fall_detected": False,
                    "activity_level": random.choice(["low", "normal", "high"]),
                }

        # 返回待机
        await self.sit_down()

        duration = int((datetime.utcnow() - start_time).total_seconds())

        logger.info(f"Mock robot dog {self.robot_id} completed task {task.task_id}")
        return GroundTaskResult(
            success=True,
            task_id=task.task_id,
            duration_sec=duration,
            distance_m=total_distance,
            images_captured=images_captured,
            anomalies_detected=anomalies,
            health_data=health_data,
            gas_readings=gas_readings,
        )

    async def start_camera(self, mode: str = "visible") -> bool:
        """启动相机"""
        if not self._connected:
            return False
        await asyncio.sleep(0.5)
        self._state.camera_active = True
        logger.info(f"Mock robot dog {self.robot_id} camera started ({mode})")
        return True

    async def stop_camera(self) -> bool:
        """停止相机"""
        if not self._connected:
            return False
        await asyncio.sleep(0.2)
        self._state.camera_active = False
        logger.info(f"Mock robot dog {self.robot_id} camera stopped")
        return True

    async def capture_image(self) -> Optional[str]:
        """拍照"""
        if not self._connected or not self._state.camera_active:
            if not self._state.camera_active:
                await self.start_camera()

        await asyncio.sleep(0.3)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        image_path = f"/tmp/robotdog_{self.robot_id}_img_{timestamp}.jpg"
        logger.debug(f"Mock robot dog {self.robot_id} captured image: {image_path}")
        return image_path

    async def start_lidar(self) -> bool:
        """启动激光雷达"""
        if not self._connected:
            return False
        await asyncio.sleep(1)
        self._state.lidar_active = True
        logger.info(f"Mock robot dog {self.robot_id} LiDAR started")
        return True

    async def stop_lidar(self) -> bool:
        """停止激光雷达"""
        if not self._connected:
            return False
        self._state.lidar_active = False
        logger.info(f"Mock robot dog {self.robot_id} LiDAR stopped")
        return True

    async def get_gas_readings(self) -> Dict[str, float]:
        """获取气体传感器读数"""
        if not self._connected:
            return {}

        # 模拟一些随机波动
        readings = {}
        for gas, base_value in self._gas_sensors.items():
            readings[gas] = base_value + random.uniform(-0.1 * base_value, 0.1 * base_value)
        return readings

    async def play_sound(self, sound_type: str) -> bool:
        """播放声音"""
        if not self._connected:
            return False
        logger.info(f"Mock robot dog {self.robot_id} playing sound: {sound_type}")
        await asyncio.sleep(1)
        return True

    async def emergency_stop(self) -> bool:
        """紧急停止"""
        logger.warning(f"Mock robot dog {self.robot_id} EMERGENCY STOP")
        self._state.status = RobotDogStatus.STANDING
        self._state.speed_ms = 0
        return True

    def _drain_battery(self, percent: float) -> None:
        """消耗电量"""
        self._state.battery_percent = max(0, self._state.battery_percent - percent)
