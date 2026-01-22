"""
G5: Agent交互API - 路由层
============================
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from .models import (
    AgentType, ActivityLevel, PendingItemPriority, PendingItemStatus,
    ConversationRequest, ConversationResponse,
    ActivitiesResponse,
    PendingItemsResponse, ResolveItemRequest, ResolveItemResponse,
    FeedbackRequest, FeedbackResponse,
    AgentStatusListResponse, AgentControlRequest, AgentControlResponse,
    DecisionsResponse, ApiResponse
)
from .service import AgentService

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

# 单例服务实例
_agent_service: AgentService = None


def get_agent_service() -> AgentService:
    """获取Agent服务实例（单例）"""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service


def get_tenant_id() -> str:
    """获取租户ID（实际应从认证中获取）"""
    return "tenant_001"


def get_current_user_id() -> str:
    """获取当前用户ID（实际应从认证中获取）"""
    return "user_001"


# ============================================================
# 对话接口
# ============================================================

@router.post("/conversation", response_model=ConversationResponse)
async def conversation(
    request: ConversationRequest,
    tenant_id: str = Depends(get_tenant_id),
    service: AgentService = Depends(get_agent_service)
):
    """
    与对话Agent交互

    发送消息到对话Agent，获取响应
    """
    return await service.chat(tenant_id, request)


@router.post("/conversation/stream")
async def conversation_stream(
    request: ConversationRequest,
    tenant_id: str = Depends(get_tenant_id),
    service: AgentService = Depends(get_agent_service)
):
    """
    流式对话响应

    使用Server-Sent Events返回流式响应
    """
    return StreamingResponse(
        service.chat_stream(tenant_id, request),
        media_type="text/event-stream"
    )


# ============================================================
# 活动日志
# ============================================================

@router.get("/activities", response_model=ActivitiesResponse)
async def get_activities(
    tenant_id: str = Depends(get_tenant_id),
    agent_type: Optional[AgentType] = Query(None, description="Agent类型"),
    level: Optional[ActivityLevel] = Query(None, description="活动级别"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    cursor: Optional[str] = Query(None, description="分页游标"),
    service: AgentService = Depends(get_agent_service)
):
    """
    获取Agent活动日志

    支持按Agent类型、级别、时间范围筛选
    """
    return await service.get_activities(
        tenant_id=tenant_id,
        agent_type=agent_type,
        level=level,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        cursor=cursor
    )


# ============================================================
# 待处理事项
# ============================================================

@router.get("/pending-items", response_model=PendingItemsResponse)
async def get_pending_items(
    tenant_id: str = Depends(get_tenant_id),
    priority: Optional[PendingItemPriority] = Query(None, description="优先级"),
    item_status: Optional[PendingItemStatus] = Query(None, alias="status", description="状态"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    service: AgentService = Depends(get_agent_service)
):
    """
    获取需要人工处理的事项

    返回待处理事项列表，包括升级事件、确认请求等
    """
    return await service.get_pending_items(
        tenant_id=tenant_id,
        priority=priority,
        status=item_status,
        limit=limit
    )


@router.post("/pending-items/{item_id}/resolve", response_model=ResolveItemResponse)
async def resolve_pending_item(
    item_id: str,
    request: ResolveItemRequest,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service)
):
    """
    处理待处理事项

    执行指定的动作来处理事项
    """
    result = await service.resolve_pending_item(item_id, request, user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pending item {item_id} not found"
        )
    return result


# ============================================================
# 反馈
# ============================================================

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service)
):
    """
    对Agent决策提交反馈

    支持批准、纠正、拒绝三种反馈类型
    """
    return await service.submit_feedback(request, user_id)


# ============================================================
# Agent状态
# ============================================================

@router.get("/status", response_model=AgentStatusListResponse)
async def get_agent_status(
    tenant_id: str = Depends(get_tenant_id),
    service: AgentService = Depends(get_agent_service)
):
    """
    获取所有Agent运行状态

    返回所有Agent的状态、统计信息和健康状况
    """
    return await service.get_agent_status(tenant_id)


@router.post("/{agent_id}/control", response_model=AgentControlResponse)
async def control_agent(
    agent_id: str,
    request: AgentControlRequest,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service)
):
    """
    控制Agent运行状态

    支持启动、暂停、恢复、重启操作
    """
    result = await service.control_agent(agent_id, request, user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    return result


# ============================================================
# 决策历史
# ============================================================

@router.get("/decisions", response_model=DecisionsResponse)
async def get_decisions(
    tenant_id: str = Depends(get_tenant_id),
    agent_type: Optional[AgentType] = Query(None, description="Agent类型"),
    decision_type: Optional[str] = Query(None, description="决策类型"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    service: AgentService = Depends(get_agent_service)
):
    """
    获取Agent决策历史

    查询指定时间范围内的决策记录，包含输入、输出、推理过程和结果
    """
    return await service.get_decisions(
        tenant_id=tenant_id,
        agent_type=agent_type,
        decision_type=decision_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )


# ============================================================
# WebSocket活动流
# ============================================================

class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, tenant_id: str):
        await websocket.accept()
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = []
        self.active_connections[tenant_id].append(websocket)

    def disconnect(self, websocket: WebSocket, tenant_id: str):
        if tenant_id in self.active_connections:
            if websocket in self.active_connections[tenant_id]:
                self.active_connections[tenant_id].remove(websocket)

    async def broadcast(self, tenant_id: str, message: dict):
        if tenant_id in self.active_connections:
            for connection in self.active_connections[tenant_id]:
                await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/activities")
async def websocket_activities(
    websocket: WebSocket,
    tenant_id: str = Query(...)
):
    """
    实时活动流WebSocket

    订阅Agent活动的实时推送
    """
    await manager.connect(websocket, tenant_id)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_id)
