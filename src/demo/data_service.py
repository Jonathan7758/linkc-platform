"""
DM1: 演示数据服务 (Demo Data Service)

职责:
- 管理演示数据的加载、重置、场景切换
- 提供演示数据查询接口
- 触发演示事件
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
import logging
from copy import deepcopy

from .seed_data import DemoSeedData
from .scenarios import DemoScenario, DemoEvent, get_scenario_config

logger = logging.getLogger(__name__)


class DemoStatus:
    """演示状态"""

    def __init__(self):
        self.is_active: bool = False
        self.current_scenario: Optional[DemoScenario] = None
        self.started_at: Optional[datetime] = None
        self.simulation_speed: float = 1.0
        self.auto_events_enabled: bool = True
        self.pending_events: List[Dict[str, Any]] = []
        self.triggered_events: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "is_active": self.is_active,
            "current_scenario": self.current_scenario.value if self.current_scenario else None,
            "scenario_name": DemoScenario.get_description(self.current_scenario) if self.current_scenario else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "simulation_speed": self.simulation_speed,
            "auto_events_enabled": self.auto_events_enabled,
            "pending_events_count": len(self.pending_events),
            "triggered_events_count": len(self.triggered_events),
            "uptime_seconds": (datetime.now() - self.started_at).total_seconds() if self.started_at else 0
        }


class DemoDataService:
    """
    演示数据服务

    单例模式，管理演示数据的生命周期
    """

    _instance: Optional["DemoDataService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._status = DemoStatus()

        # 演示数据存储
        self._buildings: Dict[str, Dict[str, Any]] = {}
        self._floors: Dict[str, Dict[str, Any]] = {}
        self._zones: Dict[str, Dict[str, Any]] = {}
        self._robots: Dict[str, Dict[str, Any]] = {}
        self._tasks: List[Dict[str, Any]] = []
        self._alerts: List[Dict[str, Any]] = []
        self._kpi: Dict[str, Any] = {}

        # 原始数据备份 (用于重置)
        self._original_data: Optional[Dict[str, Any]] = None

        # 事件回调
        self._event_callbacks: List[callable] = []

        logger.info("DemoDataService initialized")

    @property
    def status(self) -> DemoStatus:
        """获取当前状态"""
        return self._status

    @property
    def tenant_id(self) -> str:
        """获取演示租户ID"""
        return DemoSeedData.DEMO_TENANT_ID

    # ==================== 数据初始化 ====================

    async def init_demo_data(self, scenario: DemoScenario = DemoScenario.FULL_DEMO) -> Dict[str, Any]:
        """
        初始化演示数据

        Args:
            scenario: 演示场景

        Returns:
            初始化结果
        """
        logger.info(f"Initializing demo data for scenario: {scenario.value}")

        try:
            # 加载种子数据
            seed_data = DemoSeedData.get_all_demo_data()

            self._buildings = seed_data["buildings"]
            self._floors = seed_data["floors"]
            self._zones = seed_data["zones"]
            self._robots = deepcopy(seed_data["robots"])
            self._tasks = seed_data["tasks"]
            self._alerts = seed_data["alerts"]
            self._kpi = seed_data["kpi"]

            # 保存原始数据备份
            self._original_data = deepcopy(seed_data)

            # 根据场景调整机器人状态
            await self._apply_scenario_config(scenario)

            # 更新状态
            self._status.is_active = True
            self._status.current_scenario = scenario
            self._status.started_at = datetime.now()

            # 设置自动事件
            config = get_scenario_config(scenario)
            if config.get("auto_events") and self._status.auto_events_enabled:
                self._status.pending_events = config["auto_events"]

            logger.info(f"Demo data initialized: {len(self._buildings)} buildings, "
                       f"{len(self._robots)} robots, {len(self._tasks)} tasks")

            return {
                "success": True,
                "scenario": scenario.value,
                "stats": {
                    "buildings": len(self._buildings),
                    "floors": len(self._floors),
                    "zones": len(self._zones),
                    "robots": len(self._robots),
                    "tasks": len(self._tasks),
                    "alerts": len(self._alerts)
                }
            }

        except Exception as e:
            logger.error(f"Failed to initialize demo data: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _apply_scenario_config(self, scenario: DemoScenario):
        """应用场景配置"""
        config = get_scenario_config(scenario)
        if not config:
            return

        robot_states = config.get("robot_states", {})

        # 重新分配机器人状态
        robots_list = list(self._robots.values())
        idx = 0

        for status, count in robot_states.items():
            for _ in range(count):
                if idx < len(robots_list):
                    robot_id = robots_list[idx]["id"]
                    self._robots[robot_id]["status"] = status

                    # 根据状态调整其他属性
                    if status == "charging":
                        self._robots[robot_id]["battery"] = 35
                        self._robots[robot_id]["position"] = {"x": 10, "y": 10}
                    elif status == "maintenance":
                        self._robots[robot_id]["battery"] = 100
                        self._robots[robot_id]["position"] = {"x": 0, "y": 0}
                    elif status == "idle":
                        self._robots[robot_id]["battery"] = min(95, self._robots[robot_id]["battery"] + 20)

                    idx += 1

    async def reset_demo(self) -> Dict[str, Any]:
        """
        重置演示数据到初始状态
        """
        logger.info("Resetting demo data")

        if self._original_data is None:
            return {
                "success": False,
                "error": "No original data to reset to. Please init first."
            }

        try:
            # 从备份恢复
            self._buildings = deepcopy(self._original_data["buildings"])
            self._floors = deepcopy(self._original_data["floors"])
            self._zones = deepcopy(self._original_data["zones"])
            self._robots = deepcopy(self._original_data["robots"])
            self._tasks = deepcopy(self._original_data["tasks"])
            self._alerts = deepcopy(self._original_data["alerts"])
            self._kpi = deepcopy(self._original_data["kpi"])

            # 重置状态
            self._status.triggered_events = []
            self._status.started_at = datetime.now()

            # 重新应用场景配置
            if self._status.current_scenario:
                await self._apply_scenario_config(self._status.current_scenario)

            logger.info("Demo data reset complete")

            return {
                "success": True,
                "message": "Demo data reset to initial state"
            }

        except Exception as e:
            logger.error(f"Failed to reset demo data: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def switch_scenario(self, scenario: DemoScenario) -> Dict[str, Any]:
        """
        切换演示场景

        Args:
            scenario: 目标场景
        """
        logger.info(f"Switching scenario to: {scenario.value}")

        if not self._status.is_active:
            # 如果演示未激活，先初始化
            return await self.init_demo_data(scenario)

        try:
            # 重置数据
            await self.reset_demo()

            # 应用新场景配置
            await self._apply_scenario_config(scenario)

            # 更新状态
            self._status.current_scenario = scenario
            self._status.started_at = datetime.now()

            # 设置新场景的自动事件
            config = get_scenario_config(scenario)
            if config.get("auto_events") and self._status.auto_events_enabled:
                self._status.pending_events = config["auto_events"]
            else:
                self._status.pending_events = []

            return {
                "success": True,
                "scenario": scenario.value,
                "scenario_name": DemoScenario.get_description(scenario)
            }

        except Exception as e:
            logger.error(f"Failed to switch scenario: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ==================== 事件触发 ====================

    async def trigger_event(self, event: DemoEvent, robot_id: Optional[str] = None) -> Dict[str, Any]:
        """
        触发演示事件

        Args:
            event: 事件类型
            robot_id: 目标机器人ID (可选)
        """
        logger.info(f"Triggering event: {event.value}, robot: {robot_id}")

        event_config = DemoEvent.get_event_config(event)
        target_robot_id = robot_id or event_config.get("default_robot")

        result = {
            "success": True,
            "event": event.value,
            "robot_id": target_robot_id,
            "timestamp": datetime.now().isoformat()
        }

        try:
            if event == DemoEvent.ROBOT_LOW_BATTERY:
                result.update(await self._handle_low_battery(target_robot_id, event_config))

            elif event == DemoEvent.ROBOT_OBSTACLE:
                result.update(await self._handle_obstacle(target_robot_id, event_config))

            elif event == DemoEvent.TASK_COMPLETED:
                result.update(await self._handle_task_completed(target_robot_id))

            elif event == DemoEvent.NEW_URGENT_TASK:
                result.update(await self._handle_urgent_task(event_config))

            elif event == DemoEvent.ROBOT_ERROR:
                result.update(await self._handle_robot_error(target_robot_id, event_config))

            elif event == DemoEvent.CHARGING_COMPLETE:
                result.update(await self._handle_charging_complete(target_robot_id))

            # 记录触发的事件
            self._status.triggered_events.append({
                "event": event.value,
                "robot_id": target_robot_id,
                "timestamp": result["timestamp"],
                "result": result
            })

            # 通知回调
            await self._notify_event(event, result)

            return result

        except Exception as e:
            logger.error(f"Failed to trigger event: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _handle_low_battery(self, robot_id: str, config: Dict) -> Dict[str, Any]:
        """处理低电量事件"""
        if robot_id not in self._robots:
            return {"error": f"Robot {robot_id} not found"}

        battery_level = config.get("battery_level", 15)
        self._robots[robot_id]["battery"] = battery_level
        self._robots[robot_id]["status"] = "returning"

        # 创建告警
        alert = {
            "id": f"alert_{datetime.now().strftime('%H%M%S')}",
            "tenant_id": self.tenant_id,
            "robot_id": robot_id,
            "robot_name": self._robots[robot_id]["name"],
            "building_id": self._robots[robot_id]["building_id"],
            "building_name": self._robots[robot_id]["building_name"],
            "alert_type": "low_battery",
            "severity": config.get("severity", "warning"),
            "title": "电量低",
            "message": f"机器人电量低于{battery_level}%，正在返回充电站",
            "status": "active",
            "created_at": datetime.now().isoformat() + "Z"
        }
        self._alerts.append(alert)

        return {
            "battery_level": battery_level,
            "robot_status": "returning",
            "alert_id": alert["id"],
            "message": f"机器人 {self._robots[robot_id]['name']} 电量低，正在返回充电"
        }

    async def _handle_obstacle(self, robot_id: str, config: Dict) -> Dict[str, Any]:
        """处理障碍物事件"""
        if robot_id not in self._robots:
            return {"error": f"Robot {robot_id} not found"}

        self._robots[robot_id]["status"] = "paused"

        alert = {
            "id": f"alert_{datetime.now().strftime('%H%M%S')}",
            "tenant_id": self.tenant_id,
            "robot_id": robot_id,
            "robot_name": self._robots[robot_id]["name"],
            "building_id": self._robots[robot_id]["building_id"],
            "building_name": self._robots[robot_id]["building_name"],
            "alert_type": "obstacle",
            "severity": config.get("severity", "warning"),
            "title": "遇到障碍物",
            "message": "机器人检测到前方有障碍物，已暂停等待处理",
            "status": "active",
            "created_at": datetime.now().isoformat() + "Z"
        }
        self._alerts.append(alert)

        return {
            "robot_status": "paused",
            "obstacle_type": config.get("obstacle_type", "unknown"),
            "alert_id": alert["id"],
            "message": f"机器人 {self._robots[robot_id]['name']} 遇到障碍物"
        }

    async def _handle_task_completed(self, robot_id: str) -> Dict[str, Any]:
        """处理任务完成事件"""
        if robot_id not in self._robots:
            return {"error": f"Robot {robot_id} not found"}

        # 找到该机器人的进行中任务
        for task in self._tasks:
            if task["robot_id"] == robot_id and task["status"] == "in_progress":
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat() + "Z"
                task["actual_duration"] = task.get("estimated_duration", 60)

                self._robots[robot_id]["status"] = "idle"
                self._robots[robot_id]["current_task_id"] = None
                self._robots[robot_id]["current_task"] = None
                self._robots[robot_id]["tasks_completed_today"] += 1

                return {
                    "task_id": task["id"],
                    "task_name": task["zone_name"],
                    "robot_status": "idle",
                    "message": f"任务完成: {task['zone_name']}"
                }

        return {"message": "No in-progress task found for this robot"}

    async def _handle_urgent_task(self, config: Dict) -> Dict[str, Any]:
        """处理紧急任务事件"""
        # 找一个空闲机器人
        idle_robots = [r for r in self._robots.values() if r["status"] == "idle"]
        if not idle_robots:
            return {"error": "No idle robot available"}

        robot = idle_robots[0]
        zone_id = config.get("zone", "zone_001")
        zone = self._zones.get(zone_id, {"name": "紧急区域", "area": 500})

        task = {
            "id": f"task_urgent_{datetime.now().strftime('%H%M%S')}",
            "tenant_id": self.tenant_id,
            "robot_id": robot["id"],
            "robot_name": robot["name"],
            "zone_id": zone_id,
            "zone_name": zone["name"],
            "building_id": robot["building_id"],
            "task_type": "emergency",
            "priority": "urgent",
            "status": "in_progress",
            "scheduled_start": datetime.now().isoformat() + "Z",
            "actual_start": datetime.now().isoformat() + "Z",
            "estimated_duration": 30,
            "created_at": datetime.now().isoformat() + "Z"
        }
        self._tasks.append(task)

        robot["status"] = "working"
        robot["current_task_id"] = task["id"]
        robot["current_task"] = f"紧急: {zone['name']}"

        return {
            "task_id": task["id"],
            "robot_id": robot["id"],
            "robot_name": robot["name"],
            "zone_name": zone["name"],
            "message": f"紧急任务已派发给 {robot['name']}"
        }

    async def _handle_robot_error(self, robot_id: str, config: Dict) -> Dict[str, Any]:
        """处理机器人故障事件"""
        if robot_id not in self._robots:
            return {"error": f"Robot {robot_id} not found"}

        self._robots[robot_id]["status"] = "error"

        alert = {
            "id": f"alert_{datetime.now().strftime('%H%M%S')}",
            "tenant_id": self.tenant_id,
            "robot_id": robot_id,
            "robot_name": self._robots[robot_id]["name"],
            "building_id": self._robots[robot_id]["building_id"],
            "building_name": self._robots[robot_id]["building_name"],
            "alert_type": "error",
            "severity": "critical",
            "title": "机器人故障",
            "message": f"故障类型: {config.get('error_type', '未知')}，需要人工处理",
            "status": "active",
            "created_at": datetime.now().isoformat() + "Z"
        }
        self._alerts.append(alert)

        return {
            "robot_status": "error",
            "error_type": config.get("error_type"),
            "alert_id": alert["id"],
            "message": f"机器人 {self._robots[robot_id]['name']} 发生故障"
        }

    async def _handle_charging_complete(self, robot_id: str) -> Dict[str, Any]:
        """处理充电完成事件"""
        if robot_id not in self._robots:
            return {"error": f"Robot {robot_id} not found"}

        self._robots[robot_id]["battery"] = 100
        self._robots[robot_id]["status"] = "idle"

        return {
            "robot_status": "idle",
            "battery_level": 100,
            "message": f"机器人 {self._robots[robot_id]['name']} 充电完成，可接受新任务"
        }

    async def _notify_event(self, event: DemoEvent, result: Dict[str, Any]):
        """通知事件回调"""
        for callback in self._event_callbacks:
            try:
                await callback(event, result)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

    def register_event_callback(self, callback: callable):
        """注册事件回调"""
        self._event_callbacks.append(callback)

    # ==================== 数据查询接口 ====================

    def get_buildings(self) -> Dict[str, Dict[str, Any]]:
        """获取楼宇数据"""
        return self._buildings

    def get_floors(self, building_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """获取楼层数据"""
        if building_id:
            return {k: v for k, v in self._floors.items() if v["building_id"] == building_id}
        return self._floors

    def get_zones(self, floor_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """获取区域数据"""
        if floor_id:
            return {k: v for k, v in self._zones.items() if v["floor_id"] == floor_id}
        return self._zones

    def get_robots(self, building_id: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """获取机器人数据"""
        robots = self._robots
        if building_id:
            robots = {k: v for k, v in robots.items() if v["building_id"] == building_id}
        if status:
            robots = {k: v for k, v in robots.items() if v["status"] == status}
        return robots

    def get_robot(self, robot_id: str) -> Optional[Dict[str, Any]]:
        """获取单个机器人"""
        return self._robots.get(robot_id)

    def get_tasks(self, status: Optional[str] = None, robot_id: Optional[str] = None,
                  limit: int = 100) -> List[Dict[str, Any]]:
        """获取任务数据"""
        tasks = self._tasks
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        if robot_id:
            tasks = [t for t in tasks if t["robot_id"] == robot_id]
        return tasks[:limit]

    def get_alerts(self, status: Optional[str] = None, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取告警数据"""
        alerts = self._alerts
        if status:
            alerts = [a for a in alerts if a["status"] == status]
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        return alerts

    def get_kpi(self) -> Dict[str, Any]:
        """获取KPI数据"""
        return self._kpi

    def get_status(self) -> Dict[str, Any]:
        """获取演示状态"""
        return self._status.to_dict()

    # ==================== 状态修改 ====================

    def set_simulation_speed(self, speed: float):
        """设置模拟速度"""
        if 0.1 <= speed <= 10:
            self._status.simulation_speed = speed
            logger.info(f"Simulation speed set to {speed}x")

    def set_auto_events(self, enabled: bool):
        """设置自动事件开关"""
        self._status.auto_events_enabled = enabled
        logger.info(f"Auto events {'enabled' if enabled else 'disabled'}")

    def update_robot(self, robot_id: str, updates: Dict[str, Any]) -> bool:
        """更新机器人状态"""
        if robot_id not in self._robots:
            return False

        for key, value in updates.items():
            if key in self._robots[robot_id]:
                self._robots[robot_id][key] = value

        return True


# 全局实例
demo_service = DemoDataService()
