"""
DM2: 实时模拟引擎 (Real-time Simulation Engine)

职责:
- 模拟机器人实时移动
- 模拟电量消耗
- 模拟任务进度
- 通过WebSocket广播状态更新
"""

import asyncio
import logging
import math
import random
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RobotMovementPattern(str, Enum):
    """机器人移动模式"""
    CLEANING = "cleaning"      # 清洁模式 - 规律移动
    RETURNING = "returning"    # 返回模式 - 直线返回
    IDLE = "idle"              # 空闲模式 - 静止
    RANDOM = "random"          # 随机移动


@dataclass
class Position:
    """位置"""
    x: float
    y: float
    floor_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"x": self.x, "y": self.y, "floor_id": self.floor_id}

    def distance_to(self, other: "Position") -> float:
        """计算到另一点的距离"""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


@dataclass
class RobotSimState:
    """机器人模拟状态"""
    robot_id: str
    name: str
    position: Position
    target_position: Optional[Position] = None
    status: str = "idle"
    battery: float = 100.0
    task_progress: float = 0.0
    task_id: Optional[str] = None
    movement_pattern: RobotMovementPattern = RobotMovementPattern.IDLE
    speed: float = 5.0  # 单位/秒
    cleaning_trail: List[Dict[str, float]] = field(default_factory=list)
    last_update: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "robot_id": self.robot_id,
            "name": self.name,
            "position": self.position.to_dict(),
            "status": self.status,
            "battery": round(self.battery, 1),
            "task_progress": round(self.task_progress, 1),
            "task_id": self.task_id,
            "movement_pattern": self.movement_pattern.value
        }


@dataclass
class SimulationConfig:
    """模拟配置"""
    tick_interval: float = 1.0          # 更新间隔 (秒)
    speed_multiplier: float = 1.0       # 速度倍率
    battery_drain_rate: float = 0.02    # 每秒电量消耗 (工作状态)
    battery_charge_rate: float = 0.5    # 每秒充电速度
    task_progress_rate: float = 0.5     # 每秒任务进度增加
    trail_max_length: int = 50          # 清洁轨迹最大长度
    map_bounds: Dict[str, float] = field(default_factory=lambda: {
        "min_x": 0, "max_x": 300,
        "min_y": 0, "max_y": 200
    })


class SimulationEngine:
    """
    实时模拟引擎

    负责模拟机器人的实时移动、状态变化，并通过WebSocket广播更新
    """

    _instance: Optional["SimulationEngine"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._running = False
        self._paused = False
        self._task: Optional[asyncio.Task] = None

        self._config = SimulationConfig()
        self._robots: Dict[str, RobotSimState] = {}
        self._broadcast_callback: Optional[Callable] = None
        self._event_callbacks: List[Callable] = []

        # 充电站位置 (每个楼层)
        self._charging_stations: Dict[str, Position] = {}

        logger.info("SimulationEngine initialized")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def config(self) -> SimulationConfig:
        return self._config

    # ==================== 初始化 ====================

    def setup_from_demo_service(self, demo_service) -> None:
        """从演示数据服务初始化机器人状态"""
        robots = demo_service.get_robots()

        for robot_id, robot_data in robots.items():
            pos = robot_data.get("position", {"x": 100, "y": 100})
            floor_id = robot_data.get("current_floor", "")

            state = RobotSimState(
                robot_id=robot_id,
                name=robot_data.get("name", robot_id),
                position=Position(x=pos.get("x", 100), y=pos.get("y", 100), floor_id=floor_id),
                status=robot_data.get("status", "idle"),
                battery=robot_data.get("battery", 100),
                task_id=robot_data.get("current_task_id"),
                task_progress=robot_data.get("task_progress", 0) if robot_data.get("status") == "working" else 0
            )

            # 设置移动模式
            if state.status == "working":
                state.movement_pattern = RobotMovementPattern.CLEANING
                state.target_position = self._generate_cleaning_target(state.position)
            elif state.status == "returning":
                state.movement_pattern = RobotMovementPattern.RETURNING
                state.target_position = self._get_charging_station(floor_id)
            elif state.status == "charging":
                state.movement_pattern = RobotMovementPattern.IDLE
                state.position = Position(x=10, y=10, floor_id=floor_id)  # 充电站位置

            self._robots[robot_id] = state

            # 设置充电站
            if floor_id and floor_id not in self._charging_stations:
                self._charging_stations[floor_id] = Position(x=10, y=10, floor_id=floor_id)

        logger.info(f"Initialized {len(self._robots)} robots for simulation")

    def set_broadcast_callback(self, callback: Callable) -> None:
        """设置广播回调函数"""
        self._broadcast_callback = callback

    def register_event_callback(self, callback: Callable) -> None:
        """注册事件回调"""
        self._event_callbacks.append(callback)

    # ==================== 控制方法 ====================

    async def start(self) -> Dict[str, Any]:
        """启动模拟引擎"""
        if self._running:
            return {"success": False, "message": "Simulation already running"}

        self._running = True
        self._paused = False
        self._task = asyncio.create_task(self._simulation_loop())

        logger.info("Simulation engine started")
        return {
            "success": True,
            "message": "Simulation started",
            "robots_count": len(self._robots)
        }

    async def stop(self) -> Dict[str, Any]:
        """停止模拟引擎"""
        if not self._running:
            return {"success": False, "message": "Simulation not running"}

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("Simulation engine stopped")
        return {"success": True, "message": "Simulation stopped"}

    def pause(self) -> Dict[str, Any]:
        """暂停模拟"""
        if not self._running:
            return {"success": False, "message": "Simulation not running"}

        self._paused = True
        logger.info("Simulation paused")
        return {"success": True, "message": "Simulation paused"}

    def resume(self) -> Dict[str, Any]:
        """恢复模拟"""
        if not self._running:
            return {"success": False, "message": "Simulation not running"}

        self._paused = False
        logger.info("Simulation resumed")
        return {"success": True, "message": "Simulation resumed"}

    def set_speed(self, multiplier: float) -> Dict[str, Any]:
        """设置模拟速度"""
        if not 0.1 <= multiplier <= 10:
            return {"success": False, "message": "Speed must be between 0.1 and 10"}

        self._config.speed_multiplier = multiplier
        logger.info(f"Simulation speed set to {multiplier}x")
        return {
            "success": True,
            "speed": multiplier,
            "message": f"Speed set to {multiplier}x"
        }

    # ==================== 模拟循环 ====================

    async def _simulation_loop(self) -> None:
        """主模拟循环"""
        logger.info("Simulation loop started")

        while self._running:
            try:
                if not self._paused:
                    await self._tick()

                # 根据速度调整间隔
                interval = self._config.tick_interval / self._config.speed_multiplier
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Simulation tick error: {e}")
                await asyncio.sleep(1)

        logger.info("Simulation loop ended")

    async def _tick(self) -> None:
        """单次更新"""
        updates = []

        for robot_id, state in self._robots.items():
            changed = False

            # 根据状态更新
            if state.status == "working":
                changed = self._update_working_robot(state)
            elif state.status == "returning":
                changed = self._update_returning_robot(state)
            elif state.status == "charging":
                changed = self._update_charging_robot(state)
            elif state.status == "idle":
                # 空闲机器人偶尔小幅移动
                if random.random() < 0.1:
                    changed = self._update_idle_robot(state)

            # 更新时间戳
            state.last_update = datetime.now()

            if changed:
                updates.append(state.to_dict())

        # 广播更新
        if updates and self._broadcast_callback:
            await self._broadcast_updates(updates)

    def _update_working_robot(self, state: RobotSimState) -> bool:
        """更新工作中的机器人"""
        changed = False

        # 移动
        if state.target_position:
            moved = self._move_towards_target(state)
            if moved:
                changed = True
                # 添加清洁轨迹
                state.cleaning_trail.append({
                    "x": state.position.x,
                    "y": state.position.y,
                    "timestamp": datetime.now().timestamp()
                })
                # 限制轨迹长度
                if len(state.cleaning_trail) > self._config.trail_max_length:
                    state.cleaning_trail.pop(0)

            # 到达目标，生成新目标
            if state.position.distance_to(state.target_position) < 2:
                state.target_position = self._generate_cleaning_target(state.position)

        # 消耗电量
        drain = self._config.battery_drain_rate * self._config.speed_multiplier
        if state.battery > drain:
            state.battery -= drain
            changed = True

            # 电量低时触发返回
            if state.battery < 20:
                state.status = "returning"
                state.movement_pattern = RobotMovementPattern.RETURNING
                state.target_position = self._get_charging_station(state.position.floor_id)
                asyncio.create_task(self._notify_event("low_battery", state))

        # 更新任务进度
        progress_rate = self._config.task_progress_rate * self._config.speed_multiplier
        if state.task_progress < 100:
            state.task_progress = min(100, state.task_progress + progress_rate)
            changed = True

            # 任务完成
            if state.task_progress >= 100:
                state.status = "idle"
                state.movement_pattern = RobotMovementPattern.IDLE
                state.task_id = None
                state.task_progress = 0
                asyncio.create_task(self._notify_event("task_completed", state))

        return changed

    def _update_returning_robot(self, state: RobotSimState) -> bool:
        """更新返回中的机器人"""
        changed = False

        if state.target_position:
            moved = self._move_towards_target(state, speed_factor=1.5)
            if moved:
                changed = True

            # 到达充电站
            if state.position.distance_to(state.target_position) < 3:
                state.status = "charging"
                state.movement_pattern = RobotMovementPattern.IDLE
                state.position = state.target_position
                changed = True

        return changed

    def _update_charging_robot(self, state: RobotSimState) -> bool:
        """更新充电中的机器人"""
        changed = False

        # 充电
        if state.battery < 100:
            charge = self._config.battery_charge_rate * self._config.speed_multiplier
            state.battery = min(100, state.battery + charge)
            changed = True

            # 充电完成
            if state.battery >= 100:
                state.status = "idle"
                asyncio.create_task(self._notify_event("charging_complete", state))

        return changed

    def _update_idle_robot(self, state: RobotSimState) -> bool:
        """更新空闲机器人 (小幅随机移动)"""
        dx = random.uniform(-2, 2)
        dy = random.uniform(-2, 2)

        new_x = max(self._config.map_bounds["min_x"],
                   min(self._config.map_bounds["max_x"], state.position.x + dx))
        new_y = max(self._config.map_bounds["min_y"],
                   min(self._config.map_bounds["max_y"], state.position.y + dy))

        if new_x != state.position.x or new_y != state.position.y:
            state.position.x = new_x
            state.position.y = new_y
            return True

        return False

    def _move_towards_target(self, state: RobotSimState, speed_factor: float = 1.0) -> bool:
        """向目标移动"""
        if not state.target_position:
            return False

        distance = state.position.distance_to(state.target_position)
        if distance < 0.1:
            return False

        # 计算移动距离
        speed = state.speed * self._config.speed_multiplier * speed_factor
        move_distance = min(speed, distance)

        # 计算方向
        dx = state.target_position.x - state.position.x
        dy = state.target_position.y - state.position.y

        # 归一化并移动
        ratio = move_distance / distance
        state.position.x += dx * ratio
        state.position.y += dy * ratio

        return True

    def _generate_cleaning_target(self, current: Position) -> Position:
        """生成清洁目标位置"""
        bounds = self._config.map_bounds

        # 生成附近的随机目标 (模拟清洁路径)
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(20, 50)

        new_x = current.x + distance * math.cos(angle)
        new_y = current.y + distance * math.sin(angle)

        # 确保在边界内
        new_x = max(bounds["min_x"] + 10, min(bounds["max_x"] - 10, new_x))
        new_y = max(bounds["min_y"] + 10, min(bounds["max_y"] - 10, new_y))

        return Position(x=new_x, y=new_y, floor_id=current.floor_id)

    def _get_charging_station(self, floor_id: str) -> Position:
        """获取充电站位置"""
        if floor_id in self._charging_stations:
            return self._charging_stations[floor_id]
        return Position(x=10, y=10, floor_id=floor_id)

    # ==================== 广播和事件 ====================

    async def _broadcast_updates(self, updates: List[Dict[str, Any]]) -> None:
        """广播状态更新"""
        if self._broadcast_callback:
            try:
                await self._broadcast_callback({
                    "type": "robot_updates",
                    "updates": updates,
                    "timestamp": datetime.now().isoformat(),
                    "simulation_speed": self._config.speed_multiplier
                })
            except Exception as e:
                logger.error(f"Broadcast error: {e}")

    async def _notify_event(self, event_type: str, state: RobotSimState) -> None:
        """通知事件"""
        event_data = {
            "event": event_type,
            "robot_id": state.robot_id,
            "robot_name": state.name,
            "battery": state.battery,
            "position": state.position.to_dict(),
            "timestamp": datetime.now().isoformat()
        }

        for callback in self._event_callbacks:
            try:
                await callback(event_type, event_data)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

        # 广播事件
        if self._broadcast_callback:
            await self._broadcast_callback({
                "type": "simulation_event",
                "event": event_type,
                "data": event_data,
                "timestamp": datetime.now().isoformat()
            })

    # ==================== 机器人控制 ====================

    def assign_task(self, robot_id: str, task_id: str, target: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """分配任务给机器人"""
        if robot_id not in self._robots:
            return {"success": False, "error": f"Robot {robot_id} not found"}

        state = self._robots[robot_id]

        if state.status not in ["idle", "charging"]:
            return {"success": False, "error": f"Robot is {state.status}, cannot assign task"}

        state.status = "working"
        state.movement_pattern = RobotMovementPattern.CLEANING
        state.task_id = task_id
        state.task_progress = 0

        if target:
            state.target_position = Position(x=target.get("x", 100), y=target.get("y", 100),
                                            floor_id=state.position.floor_id)
        else:
            state.target_position = self._generate_cleaning_target(state.position)

        state.cleaning_trail = []

        logger.info(f"Assigned task {task_id} to robot {robot_id}")
        return {
            "success": True,
            "robot_id": robot_id,
            "task_id": task_id,
            "message": f"Task assigned to {state.name}"
        }

    def recall_robot(self, robot_id: str) -> Dict[str, Any]:
        """召回机器人到充电站"""
        if robot_id not in self._robots:
            return {"success": False, "error": f"Robot {robot_id} not found"}

        state = self._robots[robot_id]
        state.status = "returning"
        state.movement_pattern = RobotMovementPattern.RETURNING
        state.target_position = self._get_charging_station(state.position.floor_id)
        state.task_id = None
        state.task_progress = 0

        logger.info(f"Recalled robot {robot_id}")
        return {
            "success": True,
            "robot_id": robot_id,
            "message": f"{state.name} is returning to charging station"
        }

    def set_robot_status(self, robot_id: str, status: str) -> Dict[str, Any]:
        """设置机器人状态"""
        if robot_id not in self._robots:
            return {"success": False, "error": f"Robot {robot_id} not found"}

        valid_statuses = ["idle", "working", "charging", "returning", "paused", "error", "maintenance"]
        if status not in valid_statuses:
            return {"success": False, "error": f"Invalid status: {status}"}

        state = self._robots[robot_id]
        old_status = state.status
        state.status = status

        # 根据状态设置移动模式
        if status == "working":
            state.movement_pattern = RobotMovementPattern.CLEANING
            state.target_position = self._generate_cleaning_target(state.position)
        elif status == "returning":
            state.movement_pattern = RobotMovementPattern.RETURNING
            state.target_position = self._get_charging_station(state.position.floor_id)
        else:
            state.movement_pattern = RobotMovementPattern.IDLE

        logger.info(f"Robot {robot_id} status changed: {old_status} -> {status}")
        return {
            "success": True,
            "robot_id": robot_id,
            "old_status": old_status,
            "new_status": status
        }

    def get_robot_state(self, robot_id: str) -> Optional[Dict[str, Any]]:
        """获取机器人状态"""
        if robot_id not in self._robots:
            return None
        return self._robots[robot_id].to_dict()

    def get_all_states(self) -> List[Dict[str, Any]]:
        """获取所有机器人状态"""
        return [state.to_dict() for state in self._robots.values()]

    def get_status(self) -> Dict[str, Any]:
        """获取模拟引擎状态"""
        return {
            "running": self._running,
            "paused": self._paused,
            "speed": self._config.speed_multiplier,
            "tick_interval": self._config.tick_interval,
            "robots_count": len(self._robots),
            "robots_by_status": self._count_robots_by_status()
        }

    def _count_robots_by_status(self) -> Dict[str, int]:
        """统计各状态机器人数量"""
        counts: Dict[str, int] = {}
        for state in self._robots.values():
            counts[state.status] = counts.get(state.status, 0) + 1
        return counts


# 全局实例
simulation_engine = SimulationEngine()
