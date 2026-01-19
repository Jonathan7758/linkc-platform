"""
G5: Agent 交互 API (简化版)
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/agents", tags=["agents"])

AGENTS = {
    "scheduler_default": {
        "agent_id": "scheduler_default",
        "name": "默认清洁调度Agent",
        "state": "idle",
        "autonomy_level": "L2_LIMITED",
        "last_activity": datetime.utcnow().isoformat()
    }
}

PENDING_APPROVALS = {}

class ApprovalRequest(BaseModel):
    approved: bool
    approver: str

@router.get("")
async def list_agents():
    return {
        "success": True,
        "agents": list(AGENTS.values()),
        "stats": {"total_agents": len(AGENTS), "pending_approvals": len(PENDING_APPROVALS)}
    }

@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"success": True, "agent": AGENTS[agent_id]}

@router.post("/{agent_id}/run")
async def run_agent(agent_id: str, tenant_id: str = Query("tenant_001")):
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    AGENTS[agent_id]["last_activity"] = datetime.utcnow().isoformat()
    AGENTS[agent_id]["state"] = "idle"
    
    return {
        "success": True,
        "message": "Agent 执行完成: 找到 2 个待分配任务，1 个可用机器人",
        "result": {
            "actions_executed": 1,
            "actions_failed": 0
        },
        "requires_approval": False
    }

@router.get("/approvals/pending")
async def get_pending_approvals():
    return {"success": True, "approvals": list(PENDING_APPROVALS.values())}

@router.post("/approvals/{decision_id}")
async def approve_decision(decision_id: str, request: ApprovalRequest = Body(...)):
    if decision_id not in PENDING_APPROVALS:
        raise HTTPException(status_code=404, detail="Decision not found")
    del PENDING_APPROVALS[decision_id]
    return {"success": True, "message": "审批完成"}

@router.get("/stats")
async def get_agent_stats():
    return {
        "success": True,
        "stats": {
            "total_agents": len(AGENTS),
            "running_loops": 0,
            "pending_approvals": len(PENDING_APPROVALS)
        }
    }
