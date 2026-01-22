"""
G5: Agent交互API - 数据模型
============================
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================
# 枚举类型
# ============================================================

class AgentType(str, Enum):
    """Agent类型"""
    CLEANING_SCHEDULER = "cleaning_scheduler"
    CONVERSATION = "conversation"
    DATA_COLLECTOR = "data_collector"


class ActivityLevel(str, Enum):
    """活动级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ActivityType(str, Enum):
    """活动类型"""
    TOOL_CALL = "tool_call"
    DECISION = "decision"
    ESCALATION = "escalation"
    STATE_CHANGE = "state_change"


class PendingItemPriority(str, Enum):
    """待处理事项优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PendingItemStatus(str, Enum):
    """待处理事项状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    EXPIRED = "expired"


class FeedbackType(str, Enum):
    """反馈类型"""
    APPROVAL = "approval"
    CORRECTION = "correction"
    REJECTION = "rejection"


class AgentControlAction(str, Enum):
    """Agent控制动作"""
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    RESTART = "restart"


class AgentStatusEnum(str, Enum):
    """Agent状态"""
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


# ============================================================
# 请求模型
# ============================================================

class ConversationRequest(BaseModel):
    """对话请求"""
    tenant_id: str
    session_id: Optional[str] = None
    message: str = Field(max_length=2000)
    context: Optional[Dict[str, Any]] = None


class ResolveItemRequest(BaseModel):
    """处理待处理事项请求"""
    action: str
    comment: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


class FeedbackRequest(BaseModel):
    """反馈请求"""
    activity_id: str
    feedback_type: FeedbackType
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)
    correction_data: Optional[Dict[str, Any]] = None


class AgentControlRequest(BaseModel):
    """Agent控制请求"""
    action: AgentControlAction
    reason: Optional[str] = None


class ActivitySubscription(BaseModel):
    """活动订阅请求"""
    agent_types: Optional[List[AgentType]] = None
    levels: Optional[List[ActivityLevel]] = None


# ============================================================
# 响应模型
# ============================================================

class ConversationResponse(BaseModel):
    """对话响应"""
    session_id: str
    response: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    tools_used: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    timestamp: datetime


class AgentActivity(BaseModel):
    """Agent活动"""
    activity_id: str
    agent_type: AgentType
    agent_id: str
    activity_type: ActivityType
    level: ActivityLevel
    title: str
    description: str
    details: Dict[str, Any] = Field(default_factory=dict)
    requires_attention: bool = False
    escalation_id: Optional[str] = None
    timestamp: datetime


class ActivitiesResponse(BaseModel):
    """活动列表响应"""
    activities: List[AgentActivity]
    next_cursor: Optional[str] = None
    has_more: bool = False


class SuggestedAction(BaseModel):
    """建议动作"""
    action: str
    label: str
    params: Optional[Dict[str, Any]] = None


class PendingItem(BaseModel):
    """待处理事项"""
    item_id: str
    type: str
    priority: PendingItemPriority
    status: PendingItemStatus
    title: str
    description: str
    agent_type: AgentType
    related_entities: Dict[str, str] = Field(default_factory=dict)
    suggested_actions: List[SuggestedAction] = Field(default_factory=list)
    created_at: datetime
    expires_at: Optional[datetime] = None


class PendingItemsResponse(BaseModel):
    """待处理事项列表响应"""
    items: List[PendingItem]
    total: int
    by_priority: Dict[str, int] = Field(default_factory=dict)


class ResolveItemResponse(BaseModel):
    """处理事项响应"""
    item_id: str
    status: str
    resolved_by: str
    resolved_at: datetime
    execution_result: Optional[Dict[str, Any]] = None


class FeedbackResponse(BaseModel):
    """反馈响应"""
    feedback_id: str
    activity_id: str
    status: str
    will_affect_future: bool = False


class AgentHealth(BaseModel):
    """Agent健康状态"""
    status: str
    cpu_usage: Optional[float] = None
    memory_usage: Optional[int] = None
    error_message: Optional[str] = None


class AgentStatistics(BaseModel):
    """Agent统计"""
    decisions_today: int = 0
    escalations_today: int = 0
    feedback_score: Optional[float] = None
    conversations_today: int = 0
    avg_response_time: Optional[float] = None


class AgentStatus(BaseModel):
    """Agent状态"""
    agent_id: str
    agent_type: AgentType
    status: AgentStatusEnum
    last_activity_at: Optional[datetime] = None
    statistics: AgentStatistics = Field(default_factory=AgentStatistics)
    health: AgentHealth


class AgentStatusListResponse(BaseModel):
    """Agent状态列表响应"""
    agents: List[AgentStatus]


class AgentControlResponse(BaseModel):
    """Agent控制响应"""
    agent_id: str
    previous_status: str
    current_status: str
    action_by: str


class DecisionRecord(BaseModel):
    """决策记录"""
    decision_id: str
    agent_type: AgentType
    decision_type: str
    timestamp: datetime
    input: Dict[str, Any]
    output: Dict[str, Any]
    reasoning: Optional[str] = None
    outcome: Optional[Dict[str, Any]] = None
    feedback: Optional[Dict[str, Any]] = None


class DecisionsResponse(BaseModel):
    """决策历史响应"""
    decisions: List[DecisionRecord]
    total: int


# ============================================================
# 流式事件
# ============================================================

class StreamEventType(str, Enum):
    """流式事件类型"""
    THINKING = "thinking"
    TOKEN = "token"
    COMPLETE = "complete"
    ERROR = "error"


class StreamEvent(BaseModel):
    """流式事件"""
    type: StreamEventType
    data: Dict[str, Any]


# ============================================================
# WebSocket消息
# ============================================================

class WSMessageType(str, Enum):
    """WebSocket消息类型"""
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    ACTIVITY = "activity"
    PING = "ping"
    PONG = "pong"


class WSMessage(BaseModel):
    """WebSocket消息"""
    type: WSMessageType
    data: Optional[Dict[str, Any]] = None


# ============================================================
# 通用响应
# ============================================================

class ApiResponse(BaseModel):
    """通用API响应"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None
