"""
G5: Agent交互API - 服务层
============================
"""

from typing import List, Optional, Dict, Any, AsyncIterator
from datetime import datetime, timezone, timedelta
import logging
import uuid
import json
import asyncio

from .models import (
    AgentType, ActivityLevel, ActivityType,
    PendingItemPriority, PendingItemStatus,
    FeedbackType, AgentControlAction, AgentStatusEnum,
    ConversationRequest, ConversationResponse,
    AgentActivity, ActivitiesResponse,
    PendingItem, PendingItemsResponse, SuggestedAction,
    ResolveItemRequest, ResolveItemResponse,
    FeedbackRequest, FeedbackResponse,
    AgentStatus, AgentHealth, AgentStatistics, AgentStatusListResponse,
    AgentControlRequest, AgentControlResponse,
    DecisionRecord, DecisionsResponse,
    StreamEvent, StreamEventType
)

logger = logging.getLogger(__name__)


class AgentService:
    """Agent交互服务"""

    def __init__(self, conversation_agent=None, scheduler_agent=None):
        """
        初始化服务

        Args:
            conversation_agent: 对话Agent实例
            scheduler_agent: 调度Agent实例
        """
        self.conversation_agent = conversation_agent
        self.scheduler_agent = scheduler_agent

        # 内存存储（测试用）
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._activities: List[Dict[str, Any]] = []
        self._pending_items: Dict[str, Dict[str, Any]] = {}
        self._feedbacks: Dict[str, Dict[str, Any]] = {}
        self._agent_states: Dict[str, Dict[str, Any]] = {}
        self._decisions: List[Dict[str, Any]] = []

        self._init_sample_data()

    def _init_sample_data(self):
        """初始化示例数据"""
        now = datetime.now(timezone.utc)

        # 示例Agent状态
        self._agent_states = {
            "agent_scheduler_001": {
                "agent_id": "agent_scheduler_001",
                "agent_type": AgentType.CLEANING_SCHEDULER.value,
                "status": AgentStatusEnum.RUNNING.value,
                "last_activity_at": now,
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
            "agent_conversation_001": {
                "agent_id": "agent_conversation_001",
                "agent_type": AgentType.CONVERSATION.value,
                "status": AgentStatusEnum.RUNNING.value,
                "last_activity_at": now - timedelta(minutes=2),
                "statistics": {
                    "conversations_today": 12,
                    "avg_response_time": 1.2
                },
                "health": {
                    "status": "healthy",
                    "cpu_usage": 8.2,
                    "memory_usage": 128
                }
            },
            "agent_collector_001": {
                "agent_id": "agent_collector_001",
                "agent_type": AgentType.DATA_COLLECTOR.value,
                "status": AgentStatusEnum.RUNNING.value,
                "last_activity_at": now - timedelta(seconds=30),
                "statistics": {
                    "decisions_today": 0,
                    "escalations_today": 0
                },
                "health": {
                    "status": "healthy",
                    "cpu_usage": 5.0,
                    "memory_usage": 64
                }
            }
        }

        # 示例活动
        self._activities = [
            {
                "activity_id": "act_001",
                "agent_type": AgentType.CLEANING_SCHEDULER.value,
                "agent_id": "agent_scheduler_001",
                "activity_type": ActivityType.DECISION.value,
                "level": ActivityLevel.INFO.value,
                "title": "任务分配决策",
                "description": "将任务task_001分配给robot_001",
                "details": {
                    "task_id": "task_001",
                    "robot_id": "robot_001",
                    "match_score": 0.85,
                    "reasoning": "距离最近且电量充足"
                },
                "requires_attention": False,
                "timestamp": now - timedelta(minutes=5)
            },
            {
                "activity_id": "act_002",
                "agent_type": AgentType.CLEANING_SCHEDULER.value,
                "agent_id": "agent_scheduler_001",
                "activity_type": ActivityType.ESCALATION.value,
                "level": ActivityLevel.WARNING.value,
                "title": "机器人电量异常",
                "description": "robot_002电量骤降，需要人工确认",
                "details": {
                    "robot_id": "robot_002",
                    "battery_drop": 15,
                    "time_window": "5min"
                },
                "requires_attention": True,
                "escalation_id": "esc_001",
                "timestamp": now - timedelta(minutes=10)
            },
            {
                "activity_id": "act_003",
                "agent_type": AgentType.CONVERSATION.value,
                "agent_id": "agent_conversation_001",
                "activity_type": ActivityType.TOOL_CALL.value,
                "level": ActivityLevel.INFO.value,
                "title": "工具调用",
                "description": "调用get_robot_status获取机器人状态",
                "details": {
                    "tool": "get_robot_status",
                    "params": {"robot_id": "robot_001"},
                    "duration_ms": 120
                },
                "requires_attention": False,
                "timestamp": now - timedelta(minutes=2)
            }
        ]

        # 示例待处理事项
        self._pending_items = {
            "pending_001": {
                "item_id": "pending_001",
                "type": "escalation",
                "priority": PendingItemPriority.HIGH.value,
                "status": PendingItemStatus.PENDING.value,
                "title": "机器人电量异常",
                "description": "robot_002电量骤降15%，可能存在硬件问题",
                "agent_type": AgentType.CLEANING_SCHEDULER.value,
                "related_entities": {
                    "robot_id": "robot_002",
                    "task_id": "task_005"
                },
                "suggested_actions": [
                    {"action": "pause_robot", "label": "暂停机器人"},
                    {"action": "return_charge", "label": "返回充电"},
                    {"action": "ignore", "label": "忽略"}
                ],
                "created_at": now - timedelta(minutes=10),
                "expires_at": now + timedelta(hours=1)
            },
            "pending_002": {
                "item_id": "pending_002",
                "type": "confirmation",
                "priority": PendingItemPriority.MEDIUM.value,
                "status": PendingItemStatus.PENDING.value,
                "title": "任务超时预警",
                "description": "task_008执行时间已超过预期30%",
                "agent_type": AgentType.CLEANING_SCHEDULER.value,
                "related_entities": {
                    "task_id": "task_008",
                    "robot_id": "robot_003"
                },
                "suggested_actions": [
                    {"action": "extend_time", "label": "延长时间"},
                    {"action": "cancel_task", "label": "取消任务"},
                    {"action": "ignore", "label": "忽略"}
                ],
                "created_at": now - timedelta(minutes=5),
                "expires_at": now + timedelta(minutes=30)
            }
        }

        # 示例决策记录
        self._decisions = [
            {
                "decision_id": "dec_001",
                "agent_type": AgentType.CLEANING_SCHEDULER.value,
                "decision_type": "task_assignment",
                "timestamp": now - timedelta(minutes=5),
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
                    "comment": None
                }
            }
        ]

    # ========== 对话接口 ==========

    async def chat(
        self,
        tenant_id: str,
        request: ConversationRequest
    ) -> ConversationResponse:
        """处理对话请求"""
        now = datetime.now(timezone.utc)

        # 获取或创建会话
        session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "tenant_id": tenant_id,
                "created_at": now,
                "messages": []
            }

        session = self._sessions[session_id]
        session["messages"].append({
            "role": "user",
            "content": request.message,
            "timestamp": now
        })

        # 如果有对话Agent，调用它
        response_text = ""
        intent = None
        confidence = None
        tools_used = []
        suggestions = []

        if self.conversation_agent:
            try:
                result = await self.conversation_agent.process_message(
                    session_id=session_id,
                    message=request.message,
                    context=request.context
                )
                response_text = result.get("response", "")
                intent = result.get("intent")
                confidence = result.get("confidence")
                tools_used = result.get("tools_used", [])
                suggestions = result.get("suggestions", [])
            except Exception as e:
                logger.error(f"Conversation agent error: {e}")
                response_text = "抱歉，处理您的请求时发生错误。请稍后重试。"
        else:
            # 模拟响应
            response_text = f"收到您的消息：{request.message}。这是一个模拟响应。"
            intent = "general_query"
            confidence = 0.8
            suggestions = ["查看更多详情", "帮助"]

        session["messages"].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now(timezone.utc)
        })

        # 记录活动
        self._add_activity(
            agent_type=AgentType.CONVERSATION,
            agent_id="agent_conversation_001",
            activity_type=ActivityType.TOOL_CALL,
            level=ActivityLevel.INFO,
            title="对话响应",
            description=f"处理用户消息: {request.message[:50]}...",
            details={
                "session_id": session_id,
                "intent": intent,
                "tools_used": tools_used
            }
        )

        return ConversationResponse(
            session_id=session_id,
            response=response_text,
            intent=intent,
            confidence=confidence,
            tools_used=tools_used,
            suggestions=suggestions,
            timestamp=datetime.now(timezone.utc)
        )

    async def chat_stream(
        self,
        tenant_id: str,
        request: ConversationRequest
    ) -> AsyncIterator[str]:
        """流式对话响应"""
        session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"

        # 发送思考状态
        yield self._format_sse_event("thinking", {"status": "analyzing", "step": "processing"})
        await asyncio.sleep(0.1)

        # 模拟生成响应
        response = f"收到您的消息：{request.message}。这是一个流式响应示例。"

        # 逐字发送
        for char in response:
            yield self._format_sse_event("token", {"content": char})
            await asyncio.sleep(0.02)

        # 发送完成事件
        yield self._format_sse_event("complete", {
            "session_id": session_id,
            "total_tokens": len(response)
        })

    def _format_sse_event(self, event_type: str, data: dict) -> str:
        """格式化SSE事件"""
        return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    # ========== 活动日志 ==========

    async def get_activities(
        self,
        tenant_id: str,
        agent_type: Optional[AgentType] = None,
        level: Optional[ActivityLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 50,
        cursor: Optional[str] = None
    ) -> ActivitiesResponse:
        """获取活动日志"""
        # 过滤
        activities = self._activities.copy()

        if agent_type:
            activities = [a for a in activities if a["agent_type"] == agent_type.value]
        if level:
            activities = [a for a in activities if a["level"] == level.value]
        if start_time:
            activities = [a for a in activities if a["timestamp"] >= start_time]
        if end_time:
            activities = [a for a in activities if a["timestamp"] <= end_time]

        # 排序（按时间倒序）
        activities.sort(key=lambda x: x["timestamp"], reverse=True)

        # 分页
        start_idx = 0
        if cursor:
            try:
                start_idx = int(cursor)
            except ValueError:
                start_idx = 0

        page_activities = activities[start_idx:start_idx + limit]
        has_more = len(activities) > start_idx + limit

        # 转换
        items = [self._to_activity(a) for a in page_activities]

        return ActivitiesResponse(
            activities=items,
            next_cursor=str(start_idx + limit) if has_more else None,
            has_more=has_more
        )

    def _to_activity(self, data: Dict) -> AgentActivity:
        """转换为活动对象"""
        return AgentActivity(
            activity_id=data["activity_id"],
            agent_type=AgentType(data["agent_type"]),
            agent_id=data["agent_id"],
            activity_type=ActivityType(data["activity_type"]),
            level=ActivityLevel(data["level"]),
            title=data["title"],
            description=data["description"],
            details=data.get("details", {}),
            requires_attention=data.get("requires_attention", False),
            escalation_id=data.get("escalation_id"),
            timestamp=data["timestamp"]
        )

    def _add_activity(
        self,
        agent_type: AgentType,
        agent_id: str,
        activity_type: ActivityType,
        level: ActivityLevel,
        title: str,
        description: str,
        details: Dict = None,
        requires_attention: bool = False
    ) -> str:
        """添加活动记录"""
        activity_id = f"act_{uuid.uuid4().hex[:8]}"
        self._activities.append({
            "activity_id": activity_id,
            "agent_type": agent_type.value,
            "agent_id": agent_id,
            "activity_type": activity_type.value,
            "level": level.value,
            "title": title,
            "description": description,
            "details": details or {},
            "requires_attention": requires_attention,
            "timestamp": datetime.now(timezone.utc)
        })
        return activity_id

    # ========== 待处理事项 ==========

    async def get_pending_items(
        self,
        tenant_id: str,
        priority: Optional[PendingItemPriority] = None,
        status: Optional[PendingItemStatus] = None,
        limit: int = 20
    ) -> PendingItemsResponse:
        """获取待处理事项"""
        items = list(self._pending_items.values())

        if priority:
            items = [i for i in items if i["priority"] == priority.value]
        if status:
            items = [i for i in items if i["status"] == status.value]

        # 按优先级和时间排序
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        items.sort(key=lambda x: (priority_order.get(x["priority"], 4), x["created_at"]))

        items = items[:limit]

        # 统计
        by_priority = {}
        for p in PendingItemPriority:
            count = len([i for i in self._pending_items.values()
                        if i["priority"] == p.value and i["status"] == PendingItemStatus.PENDING.value])
            by_priority[p.value] = count

        # 转换
        result_items = [self._to_pending_item(i) for i in items]

        return PendingItemsResponse(
            items=result_items,
            total=len(items),
            by_priority=by_priority
        )

    def _to_pending_item(self, data: Dict) -> PendingItem:
        """转换为待处理事项对象"""
        return PendingItem(
            item_id=data["item_id"],
            type=data["type"],
            priority=PendingItemPriority(data["priority"]),
            status=PendingItemStatus(data["status"]),
            title=data["title"],
            description=data["description"],
            agent_type=AgentType(data["agent_type"]),
            related_entities=data.get("related_entities", {}),
            suggested_actions=[
                SuggestedAction(**a) for a in data.get("suggested_actions", [])
            ],
            created_at=data["created_at"],
            expires_at=data.get("expires_at")
        )

    async def resolve_pending_item(
        self,
        item_id: str,
        request: ResolveItemRequest,
        user_id: str
    ) -> Optional[ResolveItemResponse]:
        """处理待处理事项"""
        if item_id not in self._pending_items:
            return None

        item = self._pending_items[item_id]
        now = datetime.now(timezone.utc)

        # 更新状态
        item["status"] = PendingItemStatus.RESOLVED.value
        item["resolved_by"] = user_id
        item["resolved_at"] = now
        item["resolution_action"] = request.action
        item["resolution_comment"] = request.comment

        # 执行相应动作（模拟）
        execution_result = {
            "success": True,
            "action": request.action,
            "message": f"Action {request.action} executed successfully"
        }

        # 记录活动
        self._add_activity(
            agent_type=AgentType(item["agent_type"]),
            agent_id="agent_scheduler_001",
            activity_type=ActivityType.STATE_CHANGE,
            level=ActivityLevel.INFO,
            title="事项已处理",
            description=f"待处理事项 {item_id} 已由用户 {user_id} 处理",
            details={
                "item_id": item_id,
                "action": request.action,
                "comment": request.comment
            }
        )

        return ResolveItemResponse(
            item_id=item_id,
            status="resolved",
            resolved_by=user_id,
            resolved_at=now,
            execution_result=execution_result
        )

    # ========== 反馈 ==========

    async def submit_feedback(
        self,
        request: FeedbackRequest,
        user_id: str
    ) -> FeedbackResponse:
        """提交反馈"""
        feedback_id = f"fb_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        self._feedbacks[feedback_id] = {
            "feedback_id": feedback_id,
            "activity_id": request.activity_id,
            "feedback_type": request.feedback_type.value,
            "rating": request.rating,
            "comment": request.comment,
            "correction_data": request.correction_data,
            "user_id": user_id,
            "created_at": now
        }

        # 记录活动
        self._add_activity(
            agent_type=AgentType.CLEANING_SCHEDULER,
            agent_id="agent_scheduler_001",
            activity_type=ActivityType.STATE_CHANGE,
            level=ActivityLevel.INFO,
            title="收到用户反馈",
            description=f"用户对活动 {request.activity_id} 提交了 {request.feedback_type.value} 反馈",
            details={
                "feedback_id": feedback_id,
                "rating": request.rating
            }
        )

        return FeedbackResponse(
            feedback_id=feedback_id,
            activity_id=request.activity_id,
            status="recorded",
            will_affect_future=request.feedback_type == FeedbackType.CORRECTION
        )

    # ========== Agent状态 ==========

    async def get_agent_status(self, tenant_id: str) -> AgentStatusListResponse:
        """获取所有Agent状态"""
        agents = []
        for data in self._agent_states.values():
            agents.append(AgentStatus(
                agent_id=data["agent_id"],
                agent_type=AgentType(data["agent_type"]),
                status=AgentStatusEnum(data["status"]),
                last_activity_at=data.get("last_activity_at"),
                statistics=AgentStatistics(**data.get("statistics", {})),
                health=AgentHealth(**data.get("health", {"status": "unknown"}))
            ))
        return AgentStatusListResponse(agents=agents)

    async def control_agent(
        self,
        agent_id: str,
        request: AgentControlRequest,
        user_id: str
    ) -> Optional[AgentControlResponse]:
        """控制Agent"""
        if agent_id not in self._agent_states:
            return None

        agent = self._agent_states[agent_id]
        previous_status = agent["status"]

        # 执行控制动作
        if request.action == AgentControlAction.PAUSE:
            agent["status"] = AgentStatusEnum.PAUSED.value
        elif request.action == AgentControlAction.RESUME:
            agent["status"] = AgentStatusEnum.RUNNING.value
        elif request.action == AgentControlAction.START:
            agent["status"] = AgentStatusEnum.RUNNING.value
        elif request.action == AgentControlAction.RESTART:
            agent["status"] = AgentStatusEnum.RUNNING.value

        # 记录活动
        self._add_activity(
            agent_type=AgentType(agent["agent_type"]),
            agent_id=agent_id,
            activity_type=ActivityType.STATE_CHANGE,
            level=ActivityLevel.WARNING,
            title=f"Agent {request.action.value}",
            description=f"Agent {agent_id} 状态变更: {previous_status} -> {agent['status']}",
            details={
                "action": request.action.value,
                "reason": request.reason,
                "action_by": user_id
            }
        )

        return AgentControlResponse(
            agent_id=agent_id,
            previous_status=previous_status,
            current_status=agent["status"],
            action_by=user_id
        )

    # ========== 决策历史 ==========

    async def get_decisions(
        self,
        tenant_id: str,
        agent_type: Optional[AgentType] = None,
        decision_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 50
    ) -> DecisionsResponse:
        """获取决策历史"""
        decisions = self._decisions.copy()

        if agent_type:
            decisions = [d for d in decisions if d["agent_type"] == agent_type.value]
        if decision_type:
            decisions = [d for d in decisions if d["decision_type"] == decision_type]
        if start_time:
            decisions = [d for d in decisions if d["timestamp"] >= start_time]
        if end_time:
            decisions = [d for d in decisions if d["timestamp"] <= end_time]

        # 排序
        decisions.sort(key=lambda x: x["timestamp"], reverse=True)
        total = len(decisions)
        decisions = decisions[:limit]

        # 转换
        items = [
            DecisionRecord(
                decision_id=d["decision_id"],
                agent_type=AgentType(d["agent_type"]),
                decision_type=d["decision_type"],
                timestamp=d["timestamp"],
                input=d["input"],
                output=d["output"],
                reasoning=d.get("reasoning"),
                outcome=d.get("outcome"),
                feedback=d.get("feedback")
            )
            for d in decisions
        ]

        return DecisionsResponse(decisions=items, total=total)
