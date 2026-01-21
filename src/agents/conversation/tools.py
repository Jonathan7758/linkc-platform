from typing import List
from src.shared.llm.base import Tool

class MCPToolRegistry:
    @staticmethod
    def get_robot_tools() -> List[Tool]:
        return [
            Tool(name="robot_list_robots", description="Get all robots", parameters={"type": "object", "properties": {"tenant_id": {"type": "string"}}, "required": ["tenant_id"]}),
            Tool(name="robot_get_status", description="Get robot status including position and battery", parameters={"type": "object", "properties": {"robot_id": {"type": "string"}}, "required": ["robot_id"]}),
            Tool(name="robot_go_to_charge", description="Send robot to charging station", parameters={"type": "object", "properties": {"robot_id": {"type": "string"}}, "required": ["robot_id"]}),
        ]
    
    @staticmethod
    def get_task_tools() -> List[Tool]:
        return [
            Tool(name="task_list_tasks", description="List tasks with optional status filter", parameters={"type": "object", "properties": {"tenant_id": {"type": "string"}, "status": {"type": "string"}}, "required": ["tenant_id"]}),
            Tool(name="task_create_task", description="Create a cleaning task", parameters={"type": "object", "properties": {"tenant_id": {"type": "string"}, "zone_id": {"type": "string"}, "task_type": {"type": "string"}}, "required": ["tenant_id", "zone_id", "task_type"]}),
            Tool(name="task_get_pending_tasks", description="Get pending tasks", parameters={"type": "object", "properties": {"tenant_id": {"type": "string"}}, "required": ["tenant_id"]}),
        ]
    
    @staticmethod
    def get_space_tools() -> List[Tool]:
        return [
            Tool(name="space_list_zones", description="List zones", parameters={"type": "object", "properties": {"floor_id": {"type": "string"}}, "required": ["floor_id"]}),
        ]
    
    @classmethod
    def get_all_tools(cls) -> List[Tool]:
        return cls.get_robot_tools() + cls.get_task_tools() + cls.get_space_tools()

