"""
G5: Agent交互API
==================
提供与AI Agent的交互接口，包括对话、活动流、反馈等功能
"""

from .models import (
    # 枚举
    AgentType,
    ActivityLevel,
    ActivityType,
    PendingItemPriority,
    PendingItemStatus,
    FeedbackType,
    AgentControlAction,
    AgentStatusEnum,
    StreamEventType,
    WSMessageType,
    # 请求模型
    ConversationRequest,
    ResolveItemRequest,
    FeedbackRequest,
    AgentControlRequest,
    ActivitySubscription,
    # 响应模型
    ConversationResponse,
    AgentActivity,
    ActivitiesResponse,
    SuggestedAction,
    PendingItem,
    PendingItemsResponse,
    ResolveItemResponse,
    FeedbackResponse,
    AgentHealth,
    AgentStatistics,
    AgentStatus,
    AgentStatusListResponse,
    AgentControlResponse,
    DecisionRecord,
    DecisionsResponse,
    StreamEvent,
    WSMessage,
    ApiResponse,
)

from .service import AgentService
from .router import router

__all__ = [
    # 枚举
    "AgentType",
    "ActivityLevel",
    "ActivityType",
    "PendingItemPriority",
    "PendingItemStatus",
    "FeedbackType",
    "AgentControlAction",
    "AgentStatusEnum",
    "StreamEventType",
    "WSMessageType",
    # 请求模型
    "ConversationRequest",
    "ResolveItemRequest",
    "FeedbackRequest",
    "AgentControlRequest",
    "ActivitySubscription",
    # 响应模型
    "ConversationResponse",
    "AgentActivity",
    "ActivitiesResponse",
    "SuggestedAction",
    "PendingItem",
    "PendingItemsResponse",
    "ResolveItemResponse",
    "FeedbackResponse",
    "AgentHealth",
    "AgentStatistics",
    "AgentStatus",
    "AgentStatusListResponse",
    "AgentControlResponse",
    "DecisionRecord",
    "DecisionsResponse",
    "StreamEvent",
    "WSMessage",
    "ApiResponse",
    # 服务
    "AgentService",
    # 路由
    "router",
]
