# 模块开发规格书：G5 Agent交互API

## 文档信息
| 项目 | 内容 |
|-----|------|
| 模块ID | G5 |
| 模块名称 | Agent交互API |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | F1数据模型, F4认证授权, A1-A3 Agent模块 |

---

## 1. 模块概述

### 1.1 职责描述
Agent交互API提供与AI Agent的交互接口，包括对话、活动流查看、反馈提交、异常升级处理等功能，是训练工作台与Agent系统的核心桥梁。

### 1.2 在系统中的位置
```
训练工作台 / 运营控制台
         │
         ▼
┌─────────────────────────────────────┐
│         G5 Agent交互API             │  ← 本模块
│   /api/v1/agents/*                  │
└─────────────────────────────────────┘
         │
         ├──────────────────┬──────────────────┐
         ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  A2 调度Agent   │ │  A3 对话Agent   │ │  D3 数据查询    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 1.3 输入/输出概述
| 方向 | 内容 |
|-----|------|
| 输入 | HTTP请求（前端）、WebSocket消息 |
| 输出 | Agent响应、活动日志、升级事件 |
| 依赖 | Agent运行时、活动日志存储 |

---

## 2. API定义

### 2.1 对话接口
```yaml
POST /api/v1/agents/conversation
描述: 与对话Agent交互
权限: agents:chat

请求体:
  {
    "tenant_id": "tenant_001",
    "session_id": "session_001",  # 可选，不传则创建新会话
    "message": "今天1号机器人的清洁情况如何？",
    "context": {
      "building_id": "building_001",
      "floor_id": "floor_001"
    }
  }

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "session_id": "session_001",
      "response": "1号机器人今天完成了5个清洁任务，清洁总面积1,250平方米，效率为148.5平方米/小时，表现良好。",
      "intent": "query_robot_status",
      "confidence": 0.95,
      "tools_used": ["get_robot_status", "get_task_statistics"],
      "suggestions": [
        "查看详细任务记录",
        "对比历史表现",
        "查看其他机器人状态"
      ],
      "timestamp": "2026-01-20T10:30:00Z"
    }
  }
```

### 2.2 流式对话（SSE）
```yaml
POST /api/v1/agents/conversation/stream
描述: 流式对话响应
权限: agents:chat
Content-Type: text/event-stream

请求体:
  {
    "tenant_id": "tenant_001",
    "session_id": "session_001",
    "message": "分析一下本周的清洁效率趋势"
  }

响应 (SSE):
  event: thinking
  data: {"status": "analyzing", "step": "fetching_data"}

  event: token
  data: {"content": "根据"}

  event: token
  data: {"content": "本周"}

  event: token
  data: {"content": "数据..."}

  event: complete
  data: {"session_id": "session_001", "total_tokens": 256}
```

### 2.3 获取活动流
```yaml
GET /api/v1/agents/activities
描述: 获取Agent活动日志
权限: agents:read

查询参数:
  - tenant_id: string (required)
  - agent_type: string (optional) - cleaning_scheduler/conversation/data_collector
  - level: string (optional) - info/warning/error/critical
  - start_time: datetime (optional)
  - end_time: datetime (optional)
  - limit: integer (default: 50, max: 200)
  - cursor: string (optional) - 分页游标

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "activities": [
        {
          "activity_id": "act_001",
          "agent_type": "cleaning_scheduler",
          "agent_id": "agent_scheduler_001",
          "activity_type": "decision",
          "level": "info",
          "title": "任务分配决策",
          "description": "将任务task_001分配给robot_001",
          "details": {
            "task_id": "task_001",
            "robot_id": "robot_001",
            "match_score": 0.85,
            "reasoning": "距离最近且电量充足"
          },
          "requires_attention": false,
          "timestamp": "2026-01-20T10:30:00Z"
        },
        {
          "activity_id": "act_002",
          "agent_type": "cleaning_scheduler",
          "agent_id": "agent_scheduler_001",
          "activity_type": "escalation",
          "level": "warning",
          "title": "机器人电量异常",
          "description": "robot_002电量骤降，需要人工确认",
          "details": {
            "robot_id": "robot_002",
            "battery_drop": 15,
            "time_window": "5min"
          },
          "requires_attention": true,
          "escalation_id": "esc_001",
          "timestamp": "2026-01-20T10:25:00Z"
        }
      ],
      "next_cursor": "cursor_abc123",
      "has_more": true
    }
  }
```

### 2.4 获取待处理事项
```yaml
GET /api/v1/agents/pending-items
描述: 获取需要人工处理的事项
权限: agents:read

查询参数:
  - tenant_id: string (required)
  - priority: string (optional) - low/medium/high/critical
  - status: string (optional) - pending/in_progress/resolved
  - limit: integer (default: 20)

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "items": [
        {
          "item_id": "pending_001",
          "type": "escalation",
          "priority": "high",
          "status": "pending",
          "title": "机器人电量异常",
          "description": "robot_002电量骤降15%，可能存在硬件问题",
          "agent_type": "cleaning_scheduler",
          "related_entities": {
            "robot_id": "robot_002",
            "task_id": "task_005"
          },
          "suggested_actions": [
            {"action": "pause_robot", "label": "暂停机器人"},
            {"action": "return_charge", "label": "返回充电"},
            {"action": "ignore", "label": "忽略"}
          ],
          "created_at": "2026-01-20T10:25:00Z",
          "expires_at": "2026-01-20T11:25:00Z"
        }
      ],
      "total": 3,
      "by_priority": {
        "critical": 0,
        "high": 1,
        "medium": 1,
        "low": 1
      }
    }
  }
```

### 2.5 处理待处理事项
```yaml
POST /api/v1/agents/pending-items/{item_id}/resolve
描述: 处理待处理事项
权限: agents:write

请求体:
  {
    "action": "return_charge",
    "comment": "已联系现场人员检查",
    "params": {}
  }

响应 200:
  {
    "code": 0,
    "message": "Item resolved successfully",
    "data": {
      "item_id": "pending_001",
      "status": "resolved",
      "resolved_by": "user_001",
      "resolved_at": "2026-01-20T10:35:00Z",
      "execution_result": {
        "success": true,
        "robot_status": "returning"
      }
    }
  }
```

### 2.6 提交反馈
```yaml
POST /api/v1/agents/feedback
描述: 对Agent决策提交反馈
权限: agents:feedback

请求体:
  {
    "activity_id": "act_001",
    "feedback_type": "correction",  # approval/correction/rejection
    "rating": 3,  # 1-5
    "comment": "这个任务应该分配给robot_003，因为它更擅长大面积清洁",
    "correction_data": {
      "suggested_robot_id": "robot_003",
      "reason": "large_area_preference"
    }
  }

响应 200:
  {
    "code": 0,
    "message": "Feedback submitted successfully",
    "data": {
      "feedback_id": "fb_001",
      "activity_id": "act_001",
      "status": "recorded",
      "will_affect_future": true
    }
  }
```

### 2.7 获取Agent状态
```yaml
GET /api/v1/agents/status
描述: 获取所有Agent运行状态
权限: agents:read

查询参数:
  - tenant_id: string (required)

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "agents": [
        {
          "agent_id": "agent_scheduler_001",
          "agent_type": "cleaning_scheduler",
          "status": "running",
          "last_activity_at": "2026-01-20T10:30:00Z",
          "statistics": {
            "decisions_today": 45,
            "escalations_today": 2,
            "feedback_score": 4.2
          },
          "health": {
            "status": "healthy",
            "cpu_usage": 15.5,
            "memory_usage": 256
          }
        },
        {
          "agent_id": "agent_conversation_001",
          "agent_type": "conversation",
          "status": "running",
          "last_activity_at": "2026-01-20T10:28:00Z",
          "statistics": {
            "conversations_today": 12,
            "avg_response_time": 1.2
          },
          "health": {
            "status": "healthy"
          }
        }
      ]
    }
  }
```

### 2.8 控制Agent
```yaml
POST /api/v1/agents/{agent_id}/control
描述: 控制Agent运行状态
权限: agents:admin

请求体:
  {
    "action": "pause",  # start/pause/resume/restart
    "reason": "系统维护"
  }

响应 200:
  {
    "code": 0,
    "message": "Agent paused successfully",
    "data": {
      "agent_id": "agent_scheduler_001",
      "previous_status": "running",
      "current_status": "paused",
      "action_by": "user_001"
    }
  }
```

### 2.9 获取决策历史
```yaml
GET /api/v1/agents/decisions
描述: 获取Agent决策历史
权限: agents:read

查询参数:
  - tenant_id: string (required)
  - agent_type: string (optional)
  - decision_type: string (optional) - task_assignment/schedule_change/anomaly_response
  - start_time: datetime (required)
  - end_time: datetime (required)
  - limit: integer (default: 50)

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "decisions": [
        {
          "decision_id": "dec_001",
          "agent_type": "cleaning_scheduler",
          "decision_type": "task_assignment",
          "timestamp": "2026-01-20T10:30:00Z",
          "input": {
            "task_id": "task_001",
            "available_robots": ["robot_001", "robot_002", "robot_003"]
          },
          "output": {
            "assigned_robot": "robot_001",
            "confidence": 0.85
          },
          "reasoning": "robot_001距离最近(15m)，电量充足(85%)，历史表现良好(4.5分)",
          "outcome": {
            "status": "completed",
            "actual_duration": 45,
            "efficiency": 148.5
          },
          "feedback": {
            "rating": 5,
            "comment": null
          }
        }
      ],
      "total": 156
    }
  }
```

### 2.10 WebSocket活动流
```yaml
WebSocket /api/v1/agents/ws/activities
描述: 实时活动流推送
权限: agents:read

连接参数:
  - token: string (required)
  - tenant_id: string (required)

客户端消息:
  {
    "type": "subscribe",
    "filters": {
      "agent_types": ["cleaning_scheduler"],
      "levels": ["warning", "error", "critical"]
    }
  }

服务端推送:
  {
    "type": "activity",
    "data": {
      "activity_id": "act_003",
      "agent_type": "cleaning_scheduler",
      "activity_type": "escalation",
      "level": "warning",
      "title": "任务超时预警",
      "description": "task_008执行时间已超过预期30%",
      "requires_attention": true,
      "timestamp": "2026-01-20T10:35:00Z"
    }
  }
```

---

## 3. 数据模型

### 3.1 请求/响应模型
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AgentType(str, Enum):
    CLEANING_SCHEDULER = "cleaning_scheduler"
    CONVERSATION = "conversation"
    DATA_COLLECTOR = "data_collector"

class ActivityLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ActivityType(str, Enum):
    TOOL_CALL = "tool_call"
    DECISION = "decision"
    ESCALATION = "escalation"
    STATE_CHANGE = "state_change"

class PendingItemPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PendingItemStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    EXPIRED = "expired"

class FeedbackType(str, Enum):
    APPROVAL = "approval"
    CORRECTION = "correction"
    REJECTION = "rejection"

class AgentControlAction(str, Enum):
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    RESTART = "restart"

# 对话请求/响应
class ConversationRequest(BaseModel):
    tenant_id: str
    session_id: Optional[str] = None
    message: str = Field(max_length=2000)
    context: Optional[Dict[str, Any]] = None

class ConversationResponse(BaseModel):
    session_id: str
    response: str
    intent: Optional[str]
    confidence: Optional[float]
    tools_used: List[str]
    suggestions: List[str]
    timestamp: datetime

# 活动日志
class AgentActivity(BaseModel):
    activity_id: str
    agent_type: AgentType
    agent_id: str
    activity_type: ActivityType
    level: ActivityLevel
    title: str
    description: str
    details: Dict[str, Any]
    requires_attention: bool
    escalation_id: Optional[str] = None
    timestamp: datetime

class ActivitiesResponse(BaseModel):
    activities: List[AgentActivity]
    next_cursor: Optional[str]
    has_more: bool

# 待处理事项
class SuggestedAction(BaseModel):
    action: str
    label: str
    params: Optional[Dict[str, Any]] = None

class PendingItem(BaseModel):
    item_id: str
    type: str
    priority: PendingItemPriority
    status: PendingItemStatus
    title: str
    description: str
    agent_type: AgentType
    related_entities: Dict[str, str]
    suggested_actions: List[SuggestedAction]
    created_at: datetime
    expires_at: Optional[datetime]

class ResolveItemRequest(BaseModel):
    action: str
    comment: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

# 反馈
class FeedbackRequest(BaseModel):
    activity_id: str
    feedback_type: FeedbackType
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)
    correction_data: Optional[Dict[str, Any]] = None

# Agent状态
class AgentHealth(BaseModel):
    status: str
    cpu_usage: Optional[float] = None
    memory_usage: Optional[int] = None

class AgentStatus(BaseModel):
    agent_id: str
    agent_type: AgentType
    status: str
    last_activity_at: Optional[datetime]
    statistics: Dict[str, Any]
    health: AgentHealth

class AgentControlRequest(BaseModel):
    action: AgentControlAction
    reason: Optional[str] = None
```

---

## 4. 实现要求

### 4.1 技术栈
- Python 3.11+
- FastAPI
- Pydantic v2
- SSE (Server-Sent Events)
- WebSocket
- Redis (活动流缓存)

### 4.2 核心实现

#### 路由器结构
```python
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

@router.post("/conversation", response_model=ApiResponse[ConversationResponse])
async def conversation(
    request: ConversationRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """与对话Agent交互"""
    pass

@router.post("/conversation/stream")
async def conversation_stream(
    request: ConversationRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """流式对话响应"""
    return StreamingResponse(
        agent_service.conversation_stream(request),
        media_type="text/event-stream"
    )

@router.get("/activities", response_model=ApiResponse[ActivitiesResponse])
async def get_activities(
    tenant_id: str,
    agent_type: Optional[AgentType] = None,
    level: Optional[ActivityLevel] = None,
    limit: int = 50,
    cursor: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """获取Agent活动日志"""
    pass

@router.get("/pending-items", response_model=ApiResponse[dict])
async def get_pending_items(
    tenant_id: str,
    priority: Optional[PendingItemPriority] = None,
    status: Optional[PendingItemStatus] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """获取待处理事项"""
    pass

@router.post("/pending-items/{item_id}/resolve")
async def resolve_pending_item(
    item_id: str,
    request: ResolveItemRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """处理待处理事项"""
    pass

@router.post("/feedback", response_model=ApiResponse[dict])
async def submit_feedback(
    request: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """提交反馈"""
    pass
```

#### 服务层
```python
class AgentService:
    def __init__(
        self,
        conversation_agent: ConversationAgent,
        scheduler_agent: CleaningSchedulerAgent,
        activity_repo: ActivityRepository,
        pending_repo: PendingItemRepository,
        feedback_repo: FeedbackRepository
    ):
        self.conversation_agent = conversation_agent
        self.scheduler_agent = scheduler_agent
        self.activity_repo = activity_repo
        self.pending_repo = pending_repo
        self.feedback_repo = feedback_repo
    
    async def chat(self, request: ConversationRequest) -> ConversationResponse:
        """处理对话请求"""
        session = await self._get_or_create_session(request.session_id)
        response = await self.conversation_agent.process_message(
            session_id=session.id,
            message=request.message,
            context=request.context
        )
        return ConversationResponse(
            session_id=session.id,
            response=response.text,
            intent=response.intent,
            confidence=response.confidence,
            tools_used=response.tools_used,
            suggestions=response.suggestions,
            timestamp=datetime.utcnow()
        )
    
    async def conversation_stream(self, request: ConversationRequest):
        """流式对话生成器"""
        async for event in self.conversation_agent.process_message_stream(
            session_id=request.session_id,
            message=request.message,
            context=request.context
        ):
            yield f"event: {event.type}\ndata: {event.data.json()}\n\n"
    
    async def get_activities(
        self,
        tenant_id: str,
        filters: dict,
        limit: int,
        cursor: Optional[str]
    ) -> ActivitiesResponse:
        """获取活动日志"""
        pass
    
    async def resolve_pending_item(
        self,
        item_id: str,
        action: str,
        user_id: str,
        params: dict
    ) -> dict:
        """处理待处理事项"""
        item = await self.pending_repo.get(item_id)
        if not item:
            raise HTTPException(404, "Item not found")
        
        # 执行相应动作
        result = await self._execute_action(item, action, params)
        
        # 更新状态
        await self.pending_repo.update(item_id, {
            "status": "resolved",
            "resolved_by": user_id,
            "resolved_at": datetime.utcnow(),
            "resolution_action": action
        })
        
        return result
```

### 4.3 SSE流式响应
```python
from fastapi.responses import StreamingResponse
import asyncio

class StreamEvent(BaseModel):
    type: str  # thinking/token/complete/error
    data: dict

async def generate_stream_response(agent, request):
    """生成SSE流式响应"""
    try:
        # 发送思考状态
        yield format_sse_event("thinking", {"status": "analyzing"})
        
        # 流式生成响应
        async for token in agent.generate_stream(request.message):
            yield format_sse_event("token", {"content": token})
            await asyncio.sleep(0.01)  # 控制发送速率
        
        # 发送完成事件
        yield format_sse_event("complete", {"session_id": request.session_id})
        
    except Exception as e:
        yield format_sse_event("error", {"message": str(e)})

def format_sse_event(event_type: str, data: dict) -> str:
    import json
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
```

### 4.4 WebSocket活动流
```python
class ActivityWebSocketManager:
    def __init__(self):
        self.connections: dict[str, set[WebSocket]] = {}  # tenant_id -> connections
        self.filters: dict[WebSocket, dict] = {}
    
    async def connect(self, websocket: WebSocket, tenant_id: str):
        await websocket.accept()
        if tenant_id not in self.connections:
            self.connections[tenant_id] = set()
        self.connections[tenant_id].add(websocket)
    
    async def set_filters(self, websocket: WebSocket, filters: dict):
        self.filters[websocket] = filters
    
    async def broadcast_activity(self, tenant_id: str, activity: AgentActivity):
        if tenant_id not in self.connections:
            return
        
        message = {
            "type": "activity",
            "data": activity.dict()
        }
        
        for ws in self.connections[tenant_id]:
            if self._matches_filter(ws, activity):
                await ws.send_json(message)
    
    def _matches_filter(self, ws: WebSocket, activity: AgentActivity) -> bool:
        filters = self.filters.get(ws, {})
        if not filters:
            return True
        
        agent_types = filters.get("agent_types", [])
        if agent_types and activity.agent_type not in agent_types:
            return False
        
        levels = filters.get("levels", [])
        if levels and activity.level not in levels:
            return False
        
        return True
```

---

## 5. 测试要求

### 5.1 单元测试用例
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_conversation(client: AsyncClient, auth_headers: dict):
    """测试对话接口"""
    response = await client.post(
        "/api/v1/agents/conversation",
        json={
            "tenant_id": "tenant_001",
            "message": "今天有几个清洁任务？"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data["data"]
    assert "response" in data["data"]

@pytest.mark.asyncio
async def test_get_activities(client: AsyncClient, auth_headers: dict):
    """测试获取活动日志"""
    response = await client.get(
        "/api/v1/agents/activities",
        params={"tenant_id": "tenant_001", "limit": 10},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "activities" in response.json()["data"]

@pytest.mark.asyncio
async def test_resolve_pending_item(client: AsyncClient, auth_headers: dict):
    """测试处理待处理事项"""
    response = await client.post(
        "/api/v1/agents/pending-items/pending_001/resolve",
        json={"action": "return_charge", "comment": "测试"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "resolved"

@pytest.mark.asyncio
async def test_submit_feedback(client: AsyncClient, auth_headers: dict):
    """测试提交反馈"""
    response = await client.post(
        "/api/v1/agents/feedback",
        json={
            "activity_id": "act_001",
            "feedback_type": "approval",
            "rating": 5,
            "comment": "决策正确"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
```

---

## 6. 验收标准

### 6.1 功能验收
- [ ] 对话接口正常响应
- [ ] 流式对话正常工作
- [ ] 活动日志分页查询正确
- [ ] 待处理事项CRUD正常
- [ ] 反馈提交和记录正确
- [ ] Agent状态监控正常
- [ ] WebSocket推送稳定

### 6.2 性能要求
- 对话响应首token < 500ms
- 活动日志查询 < 100ms
- WebSocket延迟 < 100ms
- 支持50+并发对话
- 支持100+并发WebSocket

### 6.3 代码质量
- 测试覆盖率 > 80%
- 类型注解完整
- 文档字符串完整
