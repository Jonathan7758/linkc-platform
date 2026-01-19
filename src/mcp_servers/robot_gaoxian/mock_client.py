"""
M3: 高仙机器人 MCP Server - Mock 模拟器
========================================
基于规格书 docs/specs/M3-gaoxian-mcp.md 实现

模拟功能：
- 模拟3个机器人
- 模拟电量消耗和充电
- 模拟任务进度更新
- 模拟随机故障（1%概率）
"""

import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from uuid import uuid4

from .storage import (
    InMemoryRobotStorage,
    Robot,
    RobotStatus,
    RobotStatusSnapshot,
    RobotTask,
    RobotError,
    Location,
    CleaningMode,
    CleaningIntensity,
    ErrorSeverity,
)

logger = logging.getLogger(__name__)


class MockGaoxianClient:
    """
    高仙机器人 Mock 模拟器

    模拟真实机器人行为：
    - 任务执行进度
    - 电量消耗
    - 充电过程
    - 随机故障
    """

    def __init__(self, storage: InMemoryRobotStorage):
        self.storage = storage
        self._simulation_task: Optional[asyncio.Task] = None
        self._running = False

    async def start_simulation(self):
        """启动模拟循环"""
        if self._running:
            return
        self._running = True
        self._simulation_task = asyncio.create_task(self._simulation_loop())
        logger.info("Mock simulation started")

    async def stop_simulation(self):
        """停止模拟"""
        self._running = False
        if self._simulation_task:
            self._simulation_task.cancel()
            try:
                await self._simulation_task
            except asyncio.CancelledError:
                pass
        logger.info("Mock simulation stopped")

    async def _simulation_loop(self):
        """模拟循环 - 每秒更新一次"""
        while self._running:
            try:
                await self._simulate_tick()
                await asyncio.sleep(1)  # 每秒更新
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Simulation error: {e}")

    async def _simulate_tick(self):
        """单次模拟更新"""
        for robot_id in list(self.storage._status_snapshots.keys()):
            snapshot = await self.storage.get_status_snapshot(robot_id)
            if not snapshot:
                continue

            updates = {}

            # 1. 模拟任务进度
            if snapshot.status == RobotStatus.WORKING:
                task = await self.storage.get_current_task(robot_id)
                if task and task.status == "running":
                    # 进度增加（按预计时间）
                    progress_per_sec = 100.0 / (task.estimated_duration * 60)
                    new_progress = min(100.0, task.progress + progress_per_sec)

                    await self.storage.update_robot_task(task.robot_task_id, {
                        "progress": new_progress
                    })
                    updates["task_progress"] = new_progress

                    # 任务完成
                    if new_progress >= 100.0:
                        await self._complete_task(robot_id, task)
                        updates["status"] = RobotStatus.IDLE
                        updates["current_task_id"] = None
                        updates["current_zone_id"] = None
                        updates["task_progress"] = None

                # 电量消耗（工作时每分钟消耗约0.5%）
                battery_drain = 0.5 / 60  # 每秒消耗
                new_battery = max(0, snapshot.battery_level - battery_drain)
                updates["battery_level"] = int(new_battery)

                # 低电量自动返回充电
                if new_battery < 10:
                    logger.warning(f"Robot {robot_id} battery critical, auto returning to charge")
                    await self._force_return_to_charge(robot_id)

            # 2. 模拟充电过程
            elif snapshot.status == RobotStatus.CHARGING:
                if snapshot.battery_level < 100:
                    # 充电速率：每分钟约1%
                    charge_rate = 1.0 / 60
                    new_battery = min(100, snapshot.battery_level + charge_rate)
                    updates["battery_level"] = int(new_battery)

                    # 充满后自动变为 idle
                    if new_battery >= 100:
                        updates["status"] = RobotStatus.IDLE
                        robot = await self.storage.get_robot(robot_id)
                        if robot:
                            await self.storage.update_robot_status(robot_id, RobotStatus.IDLE)

            # 3. 模拟随机故障（1%概率，仅工作状态）
            if snapshot.status == RobotStatus.WORKING:
                if random.random() < 0.01:  # 1%概率
                    await self._simulate_random_error(robot_id, snapshot)

            # 4. 更新位置（工作时移动）
            if snapshot.status == RobotStatus.WORKING and snapshot.current_location:
                # 随机小幅移动
                updates["current_location"] = Location(
                    x=snapshot.current_location.x + random.uniform(-0.1, 0.1),
                    y=snapshot.current_location.y + random.uniform(-0.1, 0.1),
                    floor_id=snapshot.current_location.floor_id
                )
                updates["speed"] = random.uniform(0.3, 0.6)

            # 应用更新
            if updates:
                await self.storage.update_status_snapshot(robot_id, updates)

    async def _complete_task(self, robot_id: str, task: RobotTask):
        """完成任务"""
        await self.storage.update_robot_task(task.robot_task_id, {
            "status": "completed",
            "progress": 100.0,
            "completed_at": datetime.utcnow()
        })
        await self.storage.update_robot_status(robot_id, RobotStatus.IDLE)
        logger.info(f"Robot {robot_id} completed task {task.robot_task_id}")

    async def _force_return_to_charge(self, robot_id: str):
        """强制返回充电"""
        task = await self.storage.get_current_task(robot_id)
        if task:
            await self.storage.update_robot_task(task.robot_task_id, {
                "status": "cancelled",
                "cancel_reason": "Low battery - auto return to charge"
            })

        await self.storage.update_robot_status(robot_id, RobotStatus.CHARGING)
        await self.storage.update_status_snapshot(robot_id, {
            "status": RobotStatus.CHARGING,
            "current_task_id": None,
            "current_zone_id": None,
            "task_progress": None
        })

    async def _simulate_random_error(self, robot_id: str, snapshot: RobotStatusSnapshot):
        """模拟随机故障"""
        error_types = [
            ("E101", "sensor_fault", ErrorSeverity.WARNING, "左侧避障传感器异常"),
            ("E102", "sensor_fault", ErrorSeverity.WARNING, "右侧避障传感器异常"),
            ("E201", "motor_fault", ErrorSeverity.ERROR, "左轮电机过热"),
            ("E401", "cleaning_module", ErrorSeverity.WARNING, "滚刷缠绕检测"),
            ("E501", "navigation_error", ErrorSeverity.WARNING, "定位精度下降"),
        ]

        error_info = random.choice(error_types)
        robot = await self.storage.get_robot(robot_id)

        error = RobotError(
            error_id=f"error_{uuid4().hex[:8]}",
            robot_id=robot_id,
            robot_name=robot.name if robot else None,
            error_code=error_info[0],
            error_type=error_info[1],
            severity=error_info[2],
            message=error_info[3],
            location=snapshot.current_location,
            occurred_at=datetime.utcnow()
        )

        await self.storage.save_error(error)
        logger.warning(f"Random error simulated for robot {robot_id}: {error.error_code}")

        # 严重错误导致机器人停止
        if error_info[2] == ErrorSeverity.ERROR:
            await self.storage.update_robot_status(robot_id, RobotStatus.ERROR)
            await self.storage.update_status_snapshot(robot_id, {
                "status": RobotStatus.ERROR,
                "error_code": error.error_code,
                "error_message": error.message
            })

    # ============================================================
    # 模拟 API 调用
    # ============================================================

    async def get_robots(self, tenant_id: str) -> List[Robot]:
        """获取机器人列表"""
        await asyncio.sleep(0.05)  # 模拟网络延迟
        return await self.storage.list_robots(tenant_id)

    async def get_robot_status(self, robot_id: str) -> Optional[RobotStatusSnapshot]:
        """获取机器人状态"""
        await asyncio.sleep(0.05)
        return await self.storage.get_status_snapshot(robot_id)

    async def send_task(
        self,
        robot_id: str,
        zone_id: str,
        task_type: CleaningMode,
        cleaning_mode: CleaningIntensity = CleaningIntensity.STANDARD,
        task_id: Optional[str] = None
    ) -> Optional[RobotTask]:
        """发送任务到机器人"""
        await asyncio.sleep(0.1)

        robot = await self.storage.get_robot(robot_id)
        if not robot:
            return None

        # 创建任务
        robot_task = RobotTask(
            robot_task_id=f"gaoxian_task_{uuid4().hex[:8]}",
            robot_id=robot_id,
            zone_id=zone_id,
            task_id=task_id,
            task_type=task_type,
            cleaning_intensity=cleaning_mode,
            status="running",
            progress=0.0,
            started_at=datetime.utcnow(),
            estimated_duration=self._estimate_duration(zone_id, cleaning_mode)
        )

        await self.storage.save_robot_task(robot_task)

        # 更新机器人状态
        await self.storage.update_robot_status(robot_id, RobotStatus.WORKING)
        await self.storage.update_status_snapshot(robot_id, {
            "status": RobotStatus.WORKING,
            "current_task_id": robot_task.robot_task_id,
            "current_zone_id": zone_id,
            "task_progress": 0.0,
            "cleaning_mode": task_type,
            "cleaning_intensity": cleaning_mode
        })

        logger.info(f"Task started: robot={robot_id}, task={robot_task.robot_task_id}")
        return robot_task

    async def pause_task(self, robot_id: str, reason: Optional[str] = None) -> bool:
        """暂停任务"""
        await asyncio.sleep(0.05)

        task = await self.storage.get_current_task(robot_id)
        if not task:
            return False

        await self.storage.update_robot_task(task.robot_task_id, {"status": "paused"})
        await self.storage.update_robot_status(robot_id, RobotStatus.PAUSED)
        await self.storage.update_status_snapshot(robot_id, {"status": RobotStatus.PAUSED})

        logger.info(f"Task paused: robot={robot_id}, reason={reason}")
        return True

    async def resume_task(self, robot_id: str) -> bool:
        """恢复任务"""
        await asyncio.sleep(0.05)

        task = await self.storage.get_current_task(robot_id)
        if not task or task.status != "paused":
            return False

        await self.storage.update_robot_task(task.robot_task_id, {"status": "running"})
        await self.storage.update_robot_status(robot_id, RobotStatus.WORKING)
        await self.storage.update_status_snapshot(robot_id, {"status": RobotStatus.WORKING})

        logger.info(f"Task resumed: robot={robot_id}")
        return True

    async def cancel_task(self, robot_id: str, reason: Optional[str] = None) -> Optional[float]:
        """取消任务，返回进度"""
        await asyncio.sleep(0.05)

        task = await self.storage.get_current_task(robot_id)
        if not task:
            return None

        progress = task.progress
        await self.storage.update_robot_task(task.robot_task_id, {
            "status": "cancelled",
            "cancel_reason": reason
        })
        await self.storage.update_robot_status(robot_id, RobotStatus.IDLE)
        await self.storage.update_status_snapshot(robot_id, {
            "status": RobotStatus.IDLE,
            "current_task_id": None,
            "current_zone_id": None,
            "task_progress": None
        })

        logger.info(f"Task cancelled: robot={robot_id}, progress={progress}%, reason={reason}")
        return progress

    async def go_to_location(
        self,
        robot_id: str,
        target: Location,
        reason: Optional[str] = None
    ) -> bool:
        """移动到指定位置"""
        await asyncio.sleep(0.1)

        robot = await self.storage.get_robot(robot_id)
        if not robot or robot.status != RobotStatus.IDLE:
            return False

        # 模拟移动（直接更新位置）
        await self.storage.update_status_snapshot(robot_id, {
            "current_location": target
        })

        logger.info(f"Robot {robot_id} moved to ({target.x}, {target.y})")
        return True

    async def go_to_charge(self, robot_id: str, force: bool = False) -> bool:
        """返回充电"""
        await asyncio.sleep(0.05)

        robot = await self.storage.get_robot(robot_id)
        if not robot:
            return False

        # 如果正在工作，需要 force=True
        if robot.status == RobotStatus.WORKING and not force:
            return False

        # 取消当前任务
        if force and robot.status in [RobotStatus.WORKING, RobotStatus.PAUSED]:
            await self.cancel_task(robot_id, "Forced return to charge")

        # 更新状态
        await self.storage.update_robot_status(robot_id, RobotStatus.CHARGING)
        await self.storage.update_status_snapshot(robot_id, {
            "status": RobotStatus.CHARGING,
            "current_location": robot.home_location
        })

        logger.info(f"Robot {robot_id} returning to charge")
        return True

    def _estimate_duration(self, zone_id: str, intensity: CleaningIntensity) -> int:
        """估算任务时长"""
        base_duration = 30  # 基础30分钟
        intensity_factor = {
            CleaningIntensity.ECO: 0.8,
            CleaningIntensity.STANDARD: 1.0,
            CleaningIntensity.DEEP: 1.5
        }
        return int(base_duration * intensity_factor.get(intensity, 1.0))
