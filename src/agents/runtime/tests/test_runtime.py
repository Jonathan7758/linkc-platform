"""
A1: Agent运行时框架 - 单元测试
==============================
"""

import pytest
import asyncio
from datetime import datetime

from src.agents.runtime.base import BaseAgent, AgentConfig, AgentState, AutonomyLevel
from src.agents.runtime.decision import Decision, DecisionResult
from src.agents.runtime.mcp_client import MCPClient, ToolResult
from src.agents.runtime.escalation import EscalationHandler, EscalationLevel, EscalationEvent
from src.agents.runtime.activity import ActivityLogger, AgentActivity
from src.agents.runtime.runtime import AgentRuntime


# ============================================================
# Mock Agent for Testing
# ============================================================

class MockAgent(BaseAgent):
    """测试用 Agent"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.think_count = 0
        self.execute_count = 0
        self.runtime = None
        self.mcp_client = None

    async def think(self, context: dict) -> Decision:
        self.think_count += 1
        decision = Decision(
            decision_type="test_decision",
            description="Test decision for testing"
        )
        decision.add_action("test_action", {"param": "value"})
        decision.confidence = 0.9
        decision.auto_approve = True
        return decision

    async def execute(self, decision: Decision) -> DecisionResult:
        self.execute_count += 1
        result = DecisionResult(success=True, decision=decision)
        result.add_executed_action(decision.actions[0], {"status": "done"})
        return result


# ============================================================
# MCP Client Tests
# ============================================================

class TestMCPClient:
    """MCP 客户端测试"""

    @pytest.fixture
    def client(self):
        return MCPClient()

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, client):
        """测试连接和断开"""
        assert not client.is_connected

        await client.connect()
        assert client.is_connected

        await client.disconnect()
        assert not client.is_connected

    @pytest.mark.asyncio
    async def test_call_tool_not_connected(self, client):
        """测试未连接时调用工具"""
        result = await client.call_tool("test_tool", {})
        assert not result.success
        assert result.error_code == "NOT_CONNECTED"

    @pytest.mark.asyncio
    async def test_get_available_tools(self, client):
        """测试获取可用工具"""
        await client.connect()
        tools = client.get_available_tools()
        assert isinstance(tools, dict)
        await client.disconnect()


# ============================================================
# Escalation Tests
# ============================================================

class TestEscalationHandler:
    """异常升级测试"""

    @pytest.fixture
    def handler(self):
        return EscalationHandler()

    @pytest.mark.asyncio
    async def test_handle_escalation(self, handler):
        """测试处理升级事件"""
        event_id = await handler.handle(
            agent_id="test_agent",
            level=EscalationLevel.WARNING,
            reason="Test warning",
            context={"key": "value"}
        )

        assert event_id is not None
        event = handler.get_event(event_id)
        assert event is not None
        assert event.level == EscalationLevel.WARNING
        assert event.status == "pending"

    @pytest.mark.asyncio
    async def test_acknowledge_escalation(self, handler):
        """测试确认升级事件"""
        event_id = await handler.handle(
            agent_id="test_agent",
            level=EscalationLevel.ERROR,
            reason="Test error",
            context={}
        )

        result = await handler.acknowledge(event_id, "user_001")
        assert result is True

        event = handler.get_event(event_id)
        assert event.status == "acknowledged"
        assert event.acknowledged_by == "user_001"

    @pytest.mark.asyncio
    async def test_resolve_escalation(self, handler):
        """测试解决升级事件"""
        event_id = await handler.handle(
            agent_id="test_agent",
            level=EscalationLevel.ERROR,
            reason="Test error",
            context={}
        )

        result = await handler.resolve(event_id, "user_001", "Fixed the issue")
        assert result is True

        event = handler.get_event(event_id)
        assert event.status == "resolved"
        assert event.resolution == "Fixed the issue"

    @pytest.mark.asyncio
    async def test_list_events(self, handler):
        """测试列出升级事件"""
        await handler.handle("agent_1", EscalationLevel.WARNING, "Warning 1", {})
        await handler.handle("agent_2", EscalationLevel.ERROR, "Error 1", {})
        await handler.handle("agent_1", EscalationLevel.INFO, "Info 1", {})

        events = handler.list_events()
        assert len(events) == 3

        error_events = handler.list_events(level=EscalationLevel.ERROR)
        assert len(error_events) == 1

    def test_get_stats(self, handler):
        """测试获取统计信息"""
        stats = handler.get_stats()
        assert "total" in stats
        assert "pending" in stats
        assert "by_level" in stats


# ============================================================
# Activity Logger Tests
# ============================================================

class TestActivityLogger:
    """活动日志测试"""

    @pytest.fixture
    def logger(self):
        return ActivityLogger(buffer_size=10)

    def test_log_activity(self, logger):
        """测试记录活动"""
        activity = AgentActivity(
            agent_id="test_agent",
            tenant_id="tenant_001",
            activity_type="tool_call",
            tool_name="test_tool"
        )

        logger.log(activity)
        assert len(logger._buffer) == 1
        assert len(logger._all_activities) == 1

    def test_log_tool_call(self, logger):
        """测试记录工具调用"""
        logger.log_tool_call(
            agent_id="test_agent",
            tenant_id="tenant_001",
            tool_name="robot_list_robots",
            arguments={"tenant_id": "tenant_001"},
            success=True,
            result_data={"robots": []}
        )

        assert len(logger._all_activities) == 1
        activity = logger._all_activities[0]
        assert activity.activity_type == "tool_call"
        assert activity.tool_name == "robot_list_robots"

    def test_log_decision(self, logger):
        """测试记录决策"""
        logger.log_decision(
            agent_id="test_agent",
            tenant_id="tenant_001",
            decision_type="task_scheduling",
            reason="Scheduled 3 tasks",
            confidence=0.85
        )

        assert len(logger._all_activities) == 1
        activity = logger._all_activities[0]
        assert activity.activity_type == "decision"
        assert activity.decision_confidence == 0.85

    @pytest.mark.asyncio
    async def test_query_activities(self, logger):
        """测试查询活动"""
        logger.log_tool_call("agent_1", "tenant_001", "tool_1", {}, True)
        logger.log_tool_call("agent_2", "tenant_001", "tool_2", {}, True)
        logger.log_decision("agent_1", "tenant_001", "type_1", "reason", 0.9)

        results = await logger.query(agent_id="agent_1")
        assert len(results) == 2

        results = await logger.query(activity_type="decision")
        assert len(results) == 1

    def test_get_stats(self, logger):
        """测试获取统计"""
        logger.log_tool_call("agent_1", "tenant_001", "tool_1", {}, True)
        logger.log_decision("agent_1", "tenant_001", "type_1", "reason", 0.9)

        stats = logger.get_stats()
        assert stats["total"] == 2
        assert stats["by_type"]["tool_call"] == 1
        assert stats["by_type"]["decision"] == 1


# ============================================================
# Agent Runtime Tests
# ============================================================

class TestAgentRuntime:
    """Agent 运行时测试"""

    @pytest.fixture
    def runtime(self):
        return AgentRuntime()

    @pytest.fixture
    def mock_agent(self):
        config = AgentConfig(
            agent_id="test_agent_001",
            name="Test Agent",
            tenant_id="tenant_001",
            autonomy_level=AutonomyLevel.L2_LIMITED
        )
        return MockAgent(config)

    @pytest.mark.asyncio
    async def test_start_stop(self, runtime):
        """测试启动和停止运行时"""
        await runtime.start()
        assert runtime._running

        await runtime.stop()
        assert not runtime._running

    @pytest.mark.asyncio
    async def test_register_agent(self, runtime, mock_agent):
        """测试注册 Agent"""
        await runtime.start()

        agent_id = runtime.register_agent(mock_agent)
        assert agent_id == "test_agent_001"
        assert agent_id in runtime._agents

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_unregister_agent(self, runtime, mock_agent):
        """测试注销 Agent"""
        await runtime.start()

        runtime.register_agent(mock_agent)
        result = runtime.unregister_agent("test_agent_001")
        assert result is True
        assert "test_agent_001" not in runtime._agents

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_list_agents(self, runtime, mock_agent):
        """测试列出 Agent"""
        await runtime.start()

        runtime.register_agent(mock_agent)
        agents = runtime.list_agents()
        assert len(agents) == 1
        assert agents[0]["agent_id"] == "test_agent_001"

        agents = runtime.list_agents(tenant_id="tenant_001")
        assert len(agents) == 1

        agents = runtime.list_agents(tenant_id="other_tenant")
        assert len(agents) == 0

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_start_stop_agent(self, runtime, mock_agent):
        """测试启动停止 Agent"""
        await runtime.start()

        runtime.register_agent(mock_agent)

        result = await runtime.start_agent("test_agent_001")
        assert result is True
        assert mock_agent.state == AgentState.IDLE

        result = await runtime.stop_agent("test_agent_001")
        assert result is True
        assert mock_agent.state == AgentState.STOPPED

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_run_agent_once(self, runtime, mock_agent):
        """测试运行 Agent 一次"""
        await runtime.start()

        runtime.register_agent(mock_agent)
        await runtime.start_agent("test_agent_001")

        result = await runtime.run_agent_once("test_agent_001", {"key": "value"})

        assert result.success is True
        assert mock_agent.think_count == 1
        assert mock_agent.execute_count == 1

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_escalate(self, runtime, mock_agent):
        """测试异常升级"""
        await runtime.start()

        runtime.register_agent(mock_agent)

        event_id = await runtime.escalate(
            agent_id="test_agent_001",
            level=EscalationLevel.ERROR,
            reason="Test error",
            context={"detail": "something went wrong"}
        )

        assert event_id is not None

        event = runtime.escalation_handler.get_event(event_id)
        assert event is not None
        assert event.level == EscalationLevel.ERROR

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_get_stats(self, runtime, mock_agent):
        """测试获取统计信息"""
        await runtime.start()

        runtime.register_agent(mock_agent)

        stats = runtime.get_stats()

        assert stats["running"] is True
        assert stats["agents"]["total"] == 1
        assert "mcp" in stats
        assert "escalations" in stats
        assert "activities" in stats

        await runtime.stop()


# ============================================================
# Integration Tests
# ============================================================

class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_agent_cycle(self):
        """测试完整的 Agent 执行周期"""
        # 创建运行时
        runtime = AgentRuntime()
        await runtime.start()

        # 创建并注册 Agent
        config = AgentConfig(
            agent_id="integration_test_agent",
            name="Integration Test Agent",
            tenant_id="tenant_001",
            autonomy_level=AutonomyLevel.L2_LIMITED
        )
        agent = MockAgent(config)
        runtime.register_agent(agent)

        # 启动 Agent
        await runtime.start_agent("integration_test_agent")

        # 运行一个周期
        result = await runtime.run_agent_once(
            "integration_test_agent",
            {"test_context": "value"}
        )

        assert result.success is True
        assert agent.think_count == 1
        assert agent.execute_count == 1

        # 检查活动日志
        activities = await runtime.get_activities(agent_id="integration_test_agent")
        # 应该有状态变更记录
        assert any(a.activity_type == "state_change" for a in activities)

        # 触发升级
        event_id = await runtime.escalate(
            agent_id="integration_test_agent",
            level=EscalationLevel.WARNING,
            reason="Integration test warning",
            context={}
        )

        # 检查升级事件
        event = runtime.escalation_handler.get_event(event_id)
        assert event is not None
        assert event.tenant_id == "tenant_001"

        # 停止
        await runtime.stop_agent("integration_test_agent")
        await runtime.stop()

    @pytest.mark.asyncio
    async def test_multiple_agents(self):
        """测试多个 Agent 并行"""
        runtime = AgentRuntime()
        await runtime.start()

        # 创建多个 Agent
        agents = []
        for i in range(3):
            config = AgentConfig(
                agent_id=f"agent_{i}",
                name=f"Agent {i}",
                tenant_id="tenant_001"
            )
            agent = MockAgent(config)
            runtime.register_agent(agent)
            agents.append(agent)

        # 启动所有 Agent
        for i in range(3):
            await runtime.start_agent(f"agent_{i}")

        # 并行运行
        tasks = [
            runtime.run_agent_once(f"agent_{i}", {"index": i})
            for i in range(3)
        ]
        results = await asyncio.gather(*tasks)

        # 验证所有都成功
        assert all(r.success for r in results)
        assert all(a.think_count == 1 for a in agents)

        # 检查统计
        stats = runtime.get_stats()
        assert stats["agents"]["total"] == 3

        await runtime.stop()
