"""
M2: 任务管理 MCP Server - Tool 实现
===================================
"""

from typing import Optional
from src.mcp_servers.task_manager.storage import TaskStorage


class TaskManagerTools:
    """任务管理 Tool 实现"""
    
    def __init__(self, storage: TaskStorage):
        self.storage = storage
    
    async def create_task(
        self,
        tenant_id: str,
        name: str,
        zone_id: str,
        priority: str = "normal",
        cleaning_mode: str = "standard",
        scheduled_start: Optional[str] = None,
        estimated_duration: Optional[int] = None,
        notes: Optional[str] = None
    ) -> dict:
        """创建任务"""
        task = await self.storage.create_task({
            "tenant_id": tenant_id,
            "name": name,
            "zone_id": zone_id,
            "priority": priority,
            "cleaning_mode": cleaning_mode,
            "scheduled_start": scheduled_start,
            "estimated_duration": estimated_duration,
            "notes": notes,
        })
        return {
            "success": True,
            "task_id": task["id"],
            "task": task
        }
    
    async def list_tasks(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        zone_id: Optional[str] = None,
        robot_id: Optional[str] = None,
        limit: int = 50
    ) -> dict:
        """列出任务"""
        tasks = await self.storage.list_tasks(
            tenant_id=tenant_id,
            status=status,
            zone_id=zone_id,
            robot_id=robot_id,
            limit=limit
        )
        return {
            "success": True,
            "tasks": tasks,
            "total": len(tasks)
        }
    
    async def get_task(self, task_id: str) -> dict:
        """获取任务详情"""
        task = await self.storage.get_task(task_id)
        if not task:
            return {
                "success": False,
                "error": f"Task {task_id} not found"
            }
        return {
            "success": True,
            "task": task
        }
    
    async def assign_task(
        self,
        task_id: str,
        robot_id: str,
        assigned_by: str
    ) -> dict:
        """分配任务给机器人"""
        task = await self.storage.assign_task(task_id, robot_id, assigned_by)
        if not task:
            return {
                "success": False,
                "error": f"Task {task_id} not found"
            }
        return {
            "success": True,
            "task_id": task_id,
            "robot_id": robot_id,
            "message": f"Task assigned to robot {robot_id}"
        }
    
    async def update_task_status(
        self,
        task_id: str,
        status: str,
        completion_rate: Optional[float] = None,
        notes: Optional[str] = None
    ) -> dict:
        """更新任务状态"""
        valid_statuses = ["pending", "assigned", "in_progress", "completed", "failed", "cancelled"]
        if status not in valid_statuses:
            return {
                "success": False,
                "error": f"Invalid status: {status}. Valid: {valid_statuses}"
            }
        
        task = await self.storage.update_task_status(
            task_id=task_id,
            status=status,
            completion_rate=completion_rate,
            notes=notes
        )
        if not task:
            return {
                "success": False,
                "error": f"Task {task_id} not found"
            }
        return {
            "success": True,
            "task": task
        }
    
    async def get_pending_tasks(self, tenant_id: str) -> dict:
        """获取待分配的任务"""
        tasks = await self.storage.get_pending_tasks(tenant_id)
        return {
            "success": True,
            "tasks": tasks,
            "total": len(tasks)
        }
