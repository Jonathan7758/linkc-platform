"""
Federation API Routes
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter(prefix="/federation", tags=["Federation"])

# 全局变量，在 main.py 中设置
_federation_client = None


def get_federation_client():
    return _federation_client


def set_federation_client(client):
    global _federation_client
    _federation_client = client


@router.get("/status")
async def get_federation_status():
    """获取 Federation 连接状态"""
    client = get_federation_client()
    if client is None:
        return {
            "connected": False,
            "message": "Federation is disabled",
            "system_id": None
        }
    return {
        "connected": client.is_connected,
        "system_id": client.system_id,
        "registered_agents": len(client.registered_agents) if hasattr(client, "registered_agents") else 0,
        "last_heartbeat": client.last_heartbeat.isoformat() if client.last_heartbeat else None
    }


@router.post("/reconnect")
async def reconnect_federation():
    """手动重连 Federation"""
    client = get_federation_client()
    if client is None:
        raise HTTPException(status_code=400, detail="Federation is disabled")

    success = await client.reconnect()
    return {"success": success, "connected": client.is_connected}


@router.get("/agents")
async def list_registered_agents():
    """获取已注册的 Agent 列表"""
    client = get_federation_client()
    if client is None:
        return {"agents": []}

    agents = await client.list_registered_agents() if hasattr(client, "list_registered_agents") else []
    return {"agents": agents}
