"""
M2: 任务管理 MCP Server - 存储层
================================
"""

from typing import Optional
from datetime import datetime
import uuid


class TaskStorage:
    """任务数据存储"""
    
    def __init__(self):
        self._tasks: dict[str, dict] = {}
        self._assignments: list[dict] = []
        self._init_sample_data()
    
    def _init_sample_data(self):
        """初始化示例数据"""
        tenant_id = "tenant_001"
        
        tasks_data = [
            {
                "id": "task_001",
                "tenant_id": tenant_id,
                "name": "1F大堂日常清洁",
                "zone_id": "zone_001",
                "robot_id": None,
                "status": "pending",
                "priority": "normal",
                "cleaning_mode": "standard",
                "scheduled_start": None,
                "actual_start": None,
                "actual_end": None,
                "estimated_duration": 30,
                "completion_rate": None,
                "notes": None,
            },
            {
                "id": "task_002",
                "tenant_id": tenant_id,
                "name": "2F走廊深度清洁",
                "zone_id": "zone_003",
                "robot_id": "robot_001",
                "status": "in_progress",
                "priority": "high",
                "cleaning_mode": "deep",
                "scheduled_start": datetime.utcnow().isoformat(),
                "actual_start": datetime.utcnow().isoformat(),
                "actual_end": None,
                "estimated_duration": 45,
                "completion_rate": 35.0,
                "notes": "重点清洁角落区域",
            },
            {
                "id": "task_003",
                "tenant_id": tenant_id,
                "name": "2F洗手间清洁",
                "zone_id": "zone_004",
                "robot_id": None,
                "status": "pending",
                "priority": "urgent",
                "cleaning_mode": "standard",
                "scheduled_start": None,
                "actual_start": None,
                "actual_end": None,
                "estimated_duration": 15,
                "completion_rate": None,
                "notes": None,
            },
        ]
        
        for task_data in tasks_data:
            task = {
                **task_data,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            self._tasks[task["id"]] = task
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        return f"task_{uuid.uuid4().hex[:8]}"
    
    async def create_task(self, task_data: dict) -> dict:
        """创建任务"""
        task_id = self._generate_id()
        now = datetime.utcnow().isoformat()
        
        task = {
            "id": task_id,
            "tenant_id": task_data.get("tenant_id"),
            "name": task_data.get("name"),
            "zone_id": task_data.get("zone_id"),
            "robot_id": None,
            "status": "pending",
            "priority": task_data.get("priority", "normal"),
            "cleaning_mode": task_data.get("cleaning_mode", "standard"),
            "scheduled_start": task_data.get("scheduled_start"),
            "actual_start": None,
            "actual_end": None,
            "estimated_duration": task_data.get("estimated_duration"),
            "completion_rate": None,
            "notes": task_data.get("notes"),
            "created_at": now,
            "updated_at": now,
        }
        
        self._tasks[task_id] = task
        return task
    
    async def get_task(self, task_id: str) -> Optional[dict]:
        """获取任务详情"""
        return self._tasks.get(task_id)
    
    async def list_tasks(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        zone_id: Optional[str] = None,
        robot_id: Optional[str] = None,
        limit: int = 50
    ) -> list[dict]:
        """列出任务"""
        tasks = [t for t in self._tasks.values() if t["tenant_id"] == tenant_id]
        
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        if zone_id:
            tasks = [t for t in tasks if t["zone_id"] == zone_id]
        if robot_id:
            tasks = [t for t in tasks if t["robot_id"] == robot_id]
        
        # 按优先级排序: urgent > high > normal > low
        priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        tasks.sort(key=lambda t: priority_order.get(t["priority"], 99))
        
        return tasks[:limit]
    
    async def assign_task(
        self,
        task_id: str,
        robot_id: str,
        assigned_by: str
    ) -> Optional[dict]:
        """分配任务"""
        task = self._tasks.get(task_id)
        if not task:
            return None
        
        now = datetime.utcnow().isoformat()
        task["robot_id"] = robot_id
        task["status"] = "assigned"
        task["updated_at"] = now
        
        # 记录分配历史
        self._assignments.append({
            "task_id": task_id,
            "robot_id": robot_id,
            "assigned_at": now,
            "assigned_by": assigned_by,
        })
        
        return task
    
    async def update_task_status(
        self,
        task_id: str,
        status: str,
        completion_rate: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Optional[dict]:
        """更新任务状态"""
        task = self._tasks.get(task_id)
        if not task:
            return None
        
        now = datetime.utcnow().isoformat()
        task["status"] = status
        task["updated_at"] = now
        
        if completion_rate is not None:
            task["completion_rate"] = completion_rate
        
        if notes:
            task["notes"] = notes
        
        # 状态变更时更新时间
        if status == "in_progress" and not task["actual_start"]:
            task["actual_start"] = now
        elif status in ("completed", "failed", "cancelled"):
            task["actual_end"] = now
            if status == "completed":
                task["completion_rate"] = 100.0
        
        return task
    
    async def get_pending_tasks(self, tenant_id: str) -> list[dict]:
        """获取待分配的任务"""
        return [
            t for t in self._tasks.values()
            if t["tenant_id"] == tenant_id and t["status"] == "pending"
        ]
