"""
M3: 机器人控制 MCP Server - 存储层
==================================
"""

from typing import Optional
from datetime import datetime
import uuid
import random


class RobotStorage:
    """机器人数据存储"""
    
    def __init__(self):
        self._robots: dict[str, dict] = {}
        self._positions: dict[str, dict] = {}
        self._command_history: list[dict] = []
        self._init_sample_data()
    
    def _init_sample_data(self):
        """初始化示例数据"""
        tenant_id = "tenant_001"
        
        robots_data = [
            {
                "id": "robot_001",
                "tenant_id": tenant_id,
                "name": "清洁机器人A-01",
                "brand": "gaussi",
                "model": "GS-100",
                "serial_number": "GS100-2024-001",
                "status": "working",
                "battery_level": 75,
                "current_zone_id": "zone_003",
                "assigned_building_id": "building_001",
                "external_id": "gaussi_ext_001",
            },
            {
                "id": "robot_002",
                "tenant_id": tenant_id,
                "name": "清洁机器人A-02",
                "brand": "gaussi",
                "model": "GS-100",
                "serial_number": "GS100-2024-002",
                "status": "idle",
                "battery_level": 90,
                "current_zone_id": None,
                "assigned_building_id": "building_001",
                "external_id": "gaussi_ext_002",
            },
            {
                "id": "robot_003",
                "tenant_id": tenant_id,
                "name": "清洁机器人B-01",
                "brand": "ecovacs",
                "model": "EC-200",
                "serial_number": "EC200-2024-001",
                "status": "charging",
                "battery_level": 35,
                "current_zone_id": None,
                "assigned_building_id": "building_001",
                "external_id": "ecovacs_ext_001",
            },
            {
                "id": "robot_004",
                "tenant_id": tenant_id,
                "name": "清洁机器人B-02",
                "brand": "ecovacs",
                "model": "EC-200",
                "serial_number": "EC200-2024-002",
                "status": "offline",
                "battery_level": 0,
                "current_zone_id": None,
                "assigned_building_id": "building_001",
                "external_id": "ecovacs_ext_002",
            },
        ]
        
        for robot_data in robots_data:
            robot = {
                **robot_data,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            self._robots[robot["id"]] = robot
            
            # 初始化位置信息
            if robot["status"] not in ("offline", "charging"):
                self._positions[robot["id"]] = {
                    "robot_id": robot["id"],
                    "x": random.uniform(0, 100),
                    "y": random.uniform(0, 100),
                    "floor_id": "floor_001",
                    "heading": random.uniform(0, 360),
                    "timestamp": datetime.utcnow().isoformat()
                }
    
    async def list_robots(
        self,
        tenant_id: str,
        building_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> list[dict]:
        """列出机器人"""
        robots = [r for r in self._robots.values() if r["tenant_id"] == tenant_id]
        
        if building_id:
            robots = [r for r in robots if r["assigned_building_id"] == building_id]
        if status:
            robots = [r for r in robots if r["status"] == status]
        
        return robots
    
    async def get_robot(self, robot_id: str) -> Optional[dict]:
        """获取机器人详情"""
        return self._robots.get(robot_id)
    
    async def get_robot_status(self, robot_id: str) -> Optional[dict]:
        """获取机器人状态"""
        robot = self._robots.get(robot_id)
        if not robot:
            return None
        
        position = self._positions.get(robot_id)
        
        return {
            "robot_id": robot_id,
            "status": robot["status"],
            "battery_level": robot["battery_level"],
            "current_zone_id": robot["current_zone_id"],
            "position": position,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def update_robot_status(
        self,
        robot_id: str,
        status: str,
        battery_level: Optional[int] = None,
        current_zone_id: Optional[str] = None
    ) -> Optional[dict]:
        """更新机器人状态"""
        robot = self._robots.get(robot_id)
        if not robot:
            return None
        
        robot["status"] = status
        robot["updated_at"] = datetime.utcnow().isoformat()
        
        if battery_level is not None:
            robot["battery_level"] = battery_level
        if current_zone_id is not None:
            robot["current_zone_id"] = current_zone_id
        
        return robot
    
    async def send_command(
        self,
        robot_id: str,
        command: str,
        params: Optional[dict] = None
    ) -> dict:
        """发送命令到机器人"""
        robot = self._robots.get(robot_id)
        if not robot:
            return {"success": False, "error": "Robot not found"}
        
        if robot["status"] == "offline":
            return {"success": False, "error": "Robot is offline"}
        
        command_record = {
            "id": f"cmd_{uuid.uuid4().hex[:8]}",
            "robot_id": robot_id,
            "command": command,
            "params": params or {},
            "timestamp": datetime.utcnow().isoformat(),
            "status": "sent"
        }
        self._command_history.append(command_record)
        
        return {"success": True, "command_id": command_record["id"]}
    
    async def get_available_robots(self, tenant_id: str, min_battery: int = 20) -> list[dict]:
        """获取可用的机器人（空闲且电量充足）"""
        robots = await self.list_robots(tenant_id)
        return [
            r for r in robots
            if r["status"] == "idle" and r["battery_level"] >= min_battery
        ]
