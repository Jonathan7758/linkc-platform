"""
Capabilities API Routes
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter(prefix="/capabilities", tags=["Capabilities"])

# 全局服务实例
_capability_service = None


def get_capability_service():
    global _capability_service
    if _capability_service is None:
        from src.capabilities.service import CapabilityService
        _capability_service = CapabilityService()
    return _capability_service


@router.get("")
async def list_capabilities():
    """获取所有能力定义"""
    service = get_capability_service()
    capabilities = service.list_all_capabilities()
    return {
        "capabilities": [
            {
                "id": cap.id,
                "name": cap.name,
                "category": cap.category,
                "action": cap.action,
                "parameters": cap.parameters,
                "constraints": cap.constraints,
                "description": cap.description
            }
            for cap in capabilities
        ]
    }


@router.get("/{capability_id}")
async def get_capability(capability_id: str):
    """获取单个能力定义"""
    service = get_capability_service()
    cap = service.get_capability(capability_id)
    if cap is None:
        raise HTTPException(status_code=404, detail="Capability not found")
    return {
        "id": cap.id,
        "name": cap.name,
        "category": cap.category,
        "action": cap.action,
        "parameters": cap.parameters,
        "constraints": cap.constraints,
        "description": cap.description
    }


@router.get("/agents/{agent_id}")
async def get_agent_capabilities(agent_id: str):
    """获取指定 Agent 的能力"""
    service = get_capability_service()
    info = service.get_agent_capabilities(agent_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "agent_id": info.agent_id,
        "agent_type": info.agent_type,
        "capabilities": info.capabilities,
        "status": info.status,
        "current_task": info.current_task,
        "last_updated": info.last_updated.isoformat()
    }


@router.get("/search/agents")
async def search_agents_by_capability(
    capability: str = Query(..., description="能力 ID，支持通配符如 cleaning.*"),
    status: str = Query("ready", description="Agent 状态过滤")
):
    """按能力搜索 Agent"""
    service = get_capability_service()
    agents = service.find_agents_by_capability(capability, status)
    return {
        "capability": capability,
        "status_filter": status,
        "agents": [
            {
                "agent_id": a.agent_id,
                "agent_type": a.agent_type,
                "capabilities": a.capabilities,
                "status": a.status
            }
            for a in agents
        ]
    }
