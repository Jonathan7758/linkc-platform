"""
G5: Agent交互API 测试
======================
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.agent import (
    router, AgentService,
    ConversationRequest, ResolveItemRequest, FeedbackRequest, AgentControlRequest,
    AgentType, ActivityLevel, PendingItemPriority, PendingItemStatus,
    FeedbackType, AgentControlAction
)


@pytest.fixture
def app():
    """创建测试应用"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def service():
    """创建服务实例"""
    return AgentService()


class TestAgentService:
    """Agent服务测试"""

    @pytest.mark.asyncio
    async def test_chat(self, service):
        """测试对话"""
        request = ConversationRequest(
            tenant_id="tenant_001",
            message="今天有几个清洁任务？"
        )

        result = await service.chat("tenant_001", request)

        assert result.session_id is not None
        assert result.response is not None
        assert result.timestamp is not None

    @pytest.mark.asyncio
    async def test_chat_with_session(self, service):
        """测试带会话的对话"""
        request1 = ConversationRequest(
            tenant_id="tenant_001",
            message="你好"
        )
        result1 = await service.chat("tenant_001", request1)

        request2 = ConversationRequest(
            tenant_id="tenant_001",
            session_id=result1.session_id,
            message="继续聊"
        )
        result2 = await service.chat("tenant_001", request2)

        assert result1.session_id == result2.session_id

    @pytest.mark.asyncio
    async def test_get_activities(self, service):
        """测试获取活动日志"""
        result = await service.get_activities("tenant_001")

        assert len(result.activities) > 0
        assert result.activities[0].activity_id is not None

    @pytest.mark.asyncio
    async def test_get_activities_with_filter(self, service):
        """测试按类型筛选活动"""
        result = await service.get_activities(
            "tenant_001",
            agent_type=AgentType.CLEANING_SCHEDULER
        )

        for activity in result.activities:
            assert activity.agent_type == AgentType.CLEANING_SCHEDULER

    @pytest.mark.asyncio
    async def test_get_activities_with_level_filter(self, service):
        """测试按级别筛选活动"""
        result = await service.get_activities(
            "tenant_001",
            level=ActivityLevel.WARNING
        )

        for activity in result.activities:
            assert activity.level == ActivityLevel.WARNING

    @pytest.mark.asyncio
    async def test_get_activities_pagination(self, service):
        """测试活动分页"""
        result = await service.get_activities("tenant_001", limit=2)

        assert len(result.activities) <= 2

    @pytest.mark.asyncio
    async def test_get_pending_items(self, service):
        """测试获取待处理事项"""
        result = await service.get_pending_items("tenant_001")

        assert result.total > 0
        assert len(result.items) > 0
        assert "high" in result.by_priority or "medium" in result.by_priority

    @pytest.mark.asyncio
    async def test_get_pending_items_with_priority(self, service):
        """测试按优先级筛选"""
        result = await service.get_pending_items(
            "tenant_001",
            priority=PendingItemPriority.HIGH
        )

        for item in result.items:
            assert item.priority == PendingItemPriority.HIGH

    @pytest.mark.asyncio
    async def test_resolve_pending_item(self, service):
        """测试处理待处理事项"""
        request = ResolveItemRequest(
            action="return_charge",
            comment="测试处理"
        )

        result = await service.resolve_pending_item("pending_001", request, "user_001")

        assert result is not None
        assert result.status == "resolved"
        assert result.resolved_by == "user_001"

    @pytest.mark.asyncio
    async def test_resolve_pending_item_not_found(self, service):
        """测试处理不存在的事项"""
        request = ResolveItemRequest(action="ignore")

        result = await service.resolve_pending_item("nonexistent", request, "user_001")
        assert result is None

    @pytest.mark.asyncio
    async def test_submit_feedback(self, service):
        """测试提交反馈"""
        request = FeedbackRequest(
            activity_id="act_001",
            feedback_type=FeedbackType.APPROVAL,
            rating=5,
            comment="决策正确"
        )

        result = await service.submit_feedback(request, "user_001")

        assert result.feedback_id is not None
        assert result.activity_id == "act_001"
        assert result.status == "recorded"

    @pytest.mark.asyncio
    async def test_submit_correction_feedback(self, service):
        """测试提交纠正反馈"""
        request = FeedbackRequest(
            activity_id="act_001",
            feedback_type=FeedbackType.CORRECTION,
            rating=3,
            comment="应该分配给其他机器人",
            correction_data={"suggested_robot_id": "robot_003"}
        )

        result = await service.submit_feedback(request, "user_001")

        assert result.will_affect_future is True

    @pytest.mark.asyncio
    async def test_get_agent_status(self, service):
        """测试获取Agent状态"""
        result = await service.get_agent_status("tenant_001")

        assert len(result.agents) > 0
        for agent in result.agents:
            assert agent.agent_id is not None
            assert agent.health is not None

    @pytest.mark.asyncio
    async def test_control_agent_pause(self, service):
        """测试暂停Agent"""
        request = AgentControlRequest(
            action=AgentControlAction.PAUSE,
            reason="维护"
        )

        result = await service.control_agent("agent_scheduler_001", request, "user_001")

        assert result is not None
        assert result.current_status == "paused"

    @pytest.mark.asyncio
    async def test_control_agent_resume(self, service):
        """测试恢复Agent"""
        # 先暂停
        pause_request = AgentControlRequest(action=AgentControlAction.PAUSE)
        await service.control_agent("agent_scheduler_001", pause_request, "user_001")

        # 再恢复
        resume_request = AgentControlRequest(action=AgentControlAction.RESUME)
        result = await service.control_agent("agent_scheduler_001", resume_request, "user_001")

        assert result.current_status == "running"

    @pytest.mark.asyncio
    async def test_control_agent_not_found(self, service):
        """测试控制不存在的Agent"""
        request = AgentControlRequest(action=AgentControlAction.PAUSE)

        result = await service.control_agent("nonexistent", request, "user_001")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_decisions(self, service):
        """测试获取决策历史"""
        result = await service.get_decisions("tenant_001")

        assert result.total > 0
        assert len(result.decisions) > 0
        assert result.decisions[0].decision_id is not None

    @pytest.mark.asyncio
    async def test_get_decisions_with_filter(self, service):
        """测试按类型筛选决策"""
        result = await service.get_decisions(
            "tenant_001",
            agent_type=AgentType.CLEANING_SCHEDULER
        )

        for decision in result.decisions:
            assert decision.agent_type == AgentType.CLEANING_SCHEDULER


class TestAgentRouter:
    """Agent路由测试"""

    def test_conversation(self, client):
        """测试对话接口"""
        response = client.post("/api/v1/agents/conversation", json={
            "tenant_id": "tenant_001",
            "message": "今天有几个清洁任务？"
        })

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "response" in data

    def test_conversation_with_session(self, client):
        """测试带会话的对话"""
        # 第一次对话
        response1 = client.post("/api/v1/agents/conversation", json={
            "tenant_id": "tenant_001",
            "message": "你好"
        })
        session_id = response1.json()["session_id"]

        # 第二次对话
        response2 = client.post("/api/v1/agents/conversation", json={
            "tenant_id": "tenant_001",
            "session_id": session_id,
            "message": "继续"
        })

        assert response2.json()["session_id"] == session_id

    def test_get_activities(self, client):
        """测试获取活动日志"""
        response = client.get("/api/v1/agents/activities")

        assert response.status_code == 200
        data = response.json()
        assert "activities" in data

    def test_get_activities_with_filter(self, client):
        """测试筛选活动日志"""
        response = client.get(
            "/api/v1/agents/activities",
            params={"agent_type": "cleaning_scheduler", "limit": 10}
        )

        assert response.status_code == 200

    def test_get_pending_items(self, client):
        """测试获取待处理事项"""
        response = client.get("/api/v1/agents/pending-items")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "by_priority" in data

    def test_get_pending_items_with_filter(self, client):
        """测试筛选待处理事项"""
        response = client.get(
            "/api/v1/agents/pending-items",
            params={"priority": "high"}
        )

        assert response.status_code == 200

    def test_resolve_pending_item(self, client):
        """测试处理待处理事项"""
        response = client.post(
            "/api/v1/agents/pending-items/pending_002/resolve",
            json={"action": "extend_time", "comment": "延长30分钟"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"

    def test_resolve_pending_item_not_found(self, client):
        """测试处理不存在的事项"""
        response = client.post(
            "/api/v1/agents/pending-items/nonexistent/resolve",
            json={"action": "ignore"}
        )

        assert response.status_code == 404

    def test_submit_feedback(self, client):
        """测试提交反馈"""
        response = client.post("/api/v1/agents/feedback", json={
            "activity_id": "act_001",
            "feedback_type": "approval",
            "rating": 5,
            "comment": "很好的决策"
        })

        assert response.status_code == 200
        data = response.json()
        assert "feedback_id" in data

    def test_get_agent_status(self, client):
        """测试获取Agent状态"""
        response = client.get("/api/v1/agents/status")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) > 0

    def test_control_agent(self, client):
        """测试控制Agent"""
        response = client.post(
            "/api/v1/agents/agent_conversation_001/control",
            json={"action": "pause", "reason": "测试"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["current_status"] == "paused"

    def test_control_agent_not_found(self, client):
        """测试控制不存在的Agent"""
        response = client.post(
            "/api/v1/agents/nonexistent/control",
            json={"action": "pause"}
        )

        assert response.status_code == 404

    def test_get_decisions(self, client):
        """测试获取决策历史"""
        response = client.get("/api/v1/agents/decisions")

        assert response.status_code == 200
        data = response.json()
        assert "decisions" in data
        assert "total" in data

    def test_get_decisions_with_filter(self, client):
        """测试筛选决策历史"""
        response = client.get(
            "/api/v1/agents/decisions",
            params={"agent_type": "cleaning_scheduler", "limit": 10}
        )

        assert response.status_code == 200


class TestStreamingConversation:
    """流式对话测试"""

    def test_conversation_stream(self, client):
        """测试流式对话"""
        with client.stream(
            "POST",
            "/api/v1/agents/conversation/stream",
            json={"tenant_id": "tenant_001", "message": "测试流式响应"}
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            # 读取一些事件
            events = []
            for line in response.iter_lines():
                if line:
                    events.append(line)
                if len(events) > 5:
                    break

            assert len(events) > 0
