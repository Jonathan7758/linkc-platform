"""
G3: 机器人管理 API (简化版)
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/robots", tags=["robots"])

ROBOTS = {
    "robot_001": {"id": "robot_001", "tenant_id": "tenant_001", "name": "清洁机器人A-01", "brand": "gaussi", "model": "GS-100", "status": "working", "battery_level": 75, "current_zone_id": "zone_003"},
    "robot_002": {"id": "robot_002", "tenant_id": "tenant_001", "name": "清洁机器人A-02", "brand": "gaussi", "model": "GS-100", "status": "idle", "battery_level": 90, "current_zone_id": None},
    "robot_003": {"id": "robot_003", "tenant_id": "tenant_001", "name": "清洁机器人B-01", "brand": "ecovacs", "model": "EC-200", "status": "charging", "battery_level": 35, "current_zone_id": None},
    "robot_004": {"id": "robot_004", "tenant_id": "tenant_001", "name": "清洁机器人B-02", "brand": "ecovacs", "model": "EC-200", "status": "offline", "battery_level": 0, "current_zone_id": None},
}

class StartCleaningRequest(BaseModel):
    zone_id: str
    cleaning_mode: str = "standard"

class StopCleaningRequest(BaseModel):
    reason: Optional[str] = None

@router.get("")
async def list_robots(tenant_id: str = Query(...), building_id: Optional[str] = None, status: Optional[str] = None):
    robots = [r for r in ROBOTS.values() if r["tenant_id"] == tenant_id]
    if status:
        robots = [r for r in robots if r["status"] == status]
    return {"success": True, "robots": robots, "total": len(robots)}

@router.get("/available")
async def get_available_robots(tenant_id: str = Query(...), min_battery: int = 20):
    robots = [r for r in ROBOTS.values() if r["tenant_id"] == tenant_id and r["status"] == "idle" and r["battery_level"] >= min_battery]
    return {"success": True, "robots": robots, "total": len(robots)}

@router.get("/{robot_id}")
async def get_robot_status(robot_id: str):
    if robot_id not in ROBOTS:
        raise HTTPException(status_code=404, detail="Robot not found")
    r = ROBOTS[robot_id]
    return {"success": True, "robot_id": robot_id, "status": r["status"], "battery_level": r["battery_level"], "current_zone_id": r["current_zone_id"]}

@router.post("/{robot_id}/start-cleaning")
async def start_cleaning(robot_id: str, request: StartCleaningRequest = Body(...)):
    if robot_id not in ROBOTS:
        raise HTTPException(status_code=404, detail="Robot not found")
    r = ROBOTS[robot_id]
    if r["status"] == "offline":
        raise HTTPException(status_code=400, detail="Robot is offline")
    if r["status"] == "working":
        raise HTTPException(status_code=400, detail="Robot is already working")
    ROBOTS[robot_id]["status"] = "working"
    ROBOTS[robot_id]["current_zone_id"] = request.zone_id
    return {"success": True, "robot_id": robot_id, "task_started": True}

@router.post("/{robot_id}/stop-cleaning")
async def stop_cleaning(robot_id: str, request: StopCleaningRequest = Body(default=None)):
    if robot_id not in ROBOTS:
        raise HTTPException(status_code=404, detail="Robot not found")
    ROBOTS[robot_id]["status"] = "idle"
    ROBOTS[robot_id]["current_zone_id"] = None
    return {"success": True, "robot_id": robot_id, "stopped": True}

@router.post("/{robot_id}/charge")
async def send_to_charger(robot_id: str):
    if robot_id not in ROBOTS:
        raise HTTPException(status_code=404, detail="Robot not found")
    ROBOTS[robot_id]["status"] = "charging"
    ROBOTS[robot_id]["current_zone_id"] = None
    return {"success": True, "robot_id": robot_id, "command_sent": True}
