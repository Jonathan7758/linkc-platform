"""
G2: 任务管理 API (简化版)
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(prefix="/tasks", tags=["tasks"])

TASKS = {
    "task_001": {"id": "task_001", "tenant_id": "tenant_001", "name": "1F大堂日常清洁", "zone_id": "zone_001", "robot_id": None, "status": "pending", "priority": "normal", "cleaning_mode": "standard", "completion_rate": None},
    "task_002": {"id": "task_002", "tenant_id": "tenant_001", "name": "2F走廊深度清洁", "zone_id": "zone_003", "robot_id": "robot_001", "status": "in_progress", "priority": "high", "cleaning_mode": "deep", "completion_rate": 35.0},
    "task_003": {"id": "task_003", "tenant_id": "tenant_001", "name": "2F洗手间清洁", "zone_id": "zone_004", "robot_id": None, "status": "pending", "priority": "urgent", "cleaning_mode": "standard", "completion_rate": None},
}

class TaskCreate(BaseModel):
    name: str
    zone_id: str
    priority: str = "normal"
    cleaning_mode: str = "standard"

class TaskAssign(BaseModel):
    robot_id: str
    assigned_by: str = "api_user"

class TaskStatusUpdate(BaseModel):
    status: str
    completion_rate: Optional[float] = None

@router.post("")
async def create_task(tenant_id: str = Query(...), task: TaskCreate = Body(...)):
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    new_task = {"id": task_id, "tenant_id": tenant_id, "name": task.name, "zone_id": task.zone_id, "robot_id": None, "status": "pending", "priority": task.priority, "cleaning_mode": task.cleaning_mode, "completion_rate": None}
    TASKS[task_id] = new_task
    return {"success": True, "task_id": task_id, "task": new_task}

@router.get("")
async def list_tasks(tenant_id: str = Query(...), status: Optional[str] = None, limit: int = 50):
    tasks = [t for t in TASKS.values() if t["tenant_id"] == tenant_id]
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
    tasks.sort(key=lambda t: priority_order.get(t["priority"], 99))
    return {"success": True, "tasks": tasks[:limit], "total": len(tasks)}

@router.get("/pending")
async def get_pending_tasks(tenant_id: str = Query(...)):
    tasks = [t for t in TASKS.values() if t["tenant_id"] == tenant_id and t["status"] == "pending"]
    return {"success": True, "tasks": tasks, "total": len(tasks)}

@router.get("/{task_id}")
async def get_task(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "task": TASKS[task_id]}

@router.post("/{task_id}/assign")
async def assign_task(task_id: str, assignment: TaskAssign = Body(...)):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    TASKS[task_id]["robot_id"] = assignment.robot_id
    TASKS[task_id]["status"] = "assigned"
    return {"success": True, "task_id": task_id, "robot_id": assignment.robot_id}

@router.patch("/{task_id}/status")
async def update_task_status(task_id: str, update: TaskStatusUpdate = Body(...)):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    TASKS[task_id]["status"] = update.status
    if update.completion_rate is not None:
        TASKS[task_id]["completion_rate"] = update.completion_rate
    return {"success": True, "task": TASKS[task_id]}
