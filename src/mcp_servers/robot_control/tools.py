"""
M3: 机器人控制 MCP Server - Tool 实现
=====================================
"""

from typing import Optional
from src.mcp_servers.robot_control.storage import RobotStorage


class RobotControlTools:
    """机器人控制 Tool 实现"""
    
    def __init__(self, storage: RobotStorage):
        self.storage = storage
    
    async def list_robots(
        self,
        tenant_id: str,
        building_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> dict:
        """列出机器人"""
        robots = await self.storage.list_robots(
            tenant_id=tenant_id,
            building_id=building_id,
            status=status
        )
        return {
            "success": True,
            "robots": robots,
            "total": len(robots)
        }
    
    async def get_robot_status(self, robot_id: str) -> dict:
        """获取机器人状态"""
        status = await self.storage.get_robot_status(robot_id)
        if not status:
            return {
                "success": False,
                "error": f"Robot {robot_id} not found"
            }
        return {
            "success": True,
            **status
        }
    
    async def start_cleaning(
        self,
        robot_id: str,
        zone_id: str,
        cleaning_mode: str = "standard"
    ) -> dict:
        """启动清洁任务"""
        robot = await self.storage.get_robot(robot_id)
        if not robot:
            return {"success": False, "error": f"Robot {robot_id} not found"}
        
        if robot["status"] == "offline":
            return {"success": False, "error": "Robot is offline"}
        
        if robot["status"] == "working":
            return {"success": False, "error": "Robot is already working"}
        
        if robot["battery_level"] < 20:
            return {"success": False, "error": f"Battery too low ({robot[battery_level]}%)"}
        
        # 发送清洁命令
        result = await self.storage.send_command(
            robot_id=robot_id,
            command="start_cleaning",
            params={"zone_id": zone_id, "mode": cleaning_mode}
        )
        
        if result["success"]:
            # 更新机器人状态
            await self.storage.update_robot_status(
                robot_id=robot_id,
                status="working",
                current_zone_id=zone_id
            )
        
        return {
            "success": result["success"],
            "robot_id": robot_id,
            "task_started": result["success"],
            "error": result.get("error")
        }
    
    async def stop_cleaning(
        self,
        robot_id: str,
        reason: Optional[str] = None
    ) -> dict:
        """停止清洁任务"""
        robot = await self.storage.get_robot(robot_id)
        if not robot:
            return {"success": False, "error": f"Robot {robot_id} not found"}
        
        if robot["status"] != "working":
            return {"success": False, "error": "Robot is not working"}
        
        result = await self.storage.send_command(
            robot_id=robot_id,
            command="stop_cleaning",
            params={"reason": reason}
        )
        
        if result["success"]:
            await self.storage.update_robot_status(
                robot_id=robot_id,
                status="idle",
                current_zone_id=None
            )
        
        return {
            "success": result["success"],
            "robot_id": robot_id,
            "stopped": result["success"],
            "error": result.get("error")
        }
    
    async def send_to_charger(self, robot_id: str) -> dict:
        """发送机器人去充电"""
        robot = await self.storage.get_robot(robot_id)
        if not robot:
            return {"success": False, "error": f"Robot {robot_id} not found"}
        
        if robot["status"] == "offline":
            return {"success": False, "error": "Robot is offline"}
        
        if robot["status"] == "charging":
            return {"success": True, "robot_id": robot_id, "message": "Already charging"}
        
        result = await self.storage.send_command(
            robot_id=robot_id,
            command="go_to_charger",
            params={}
        )
        
        if result["success"]:
            await self.storage.update_robot_status(
                robot_id=robot_id,
                status="charging",
                current_zone_id=None
            )
        
        return {
            "success": result["success"],
            "robot_id": robot_id,
            "command_sent": result["success"],
            "error": result.get("error")
        }
    
    async def get_available_robots(
        self,
        tenant_id: str,
        min_battery: int = 20
    ) -> dict:
        """获取可用的机器人"""
        robots = await self.storage.get_available_robots(tenant_id, min_battery)
        return {
            "success": True,
            "robots": robots,
            "total": len(robots)
        }
