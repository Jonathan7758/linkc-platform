"""A3: Conversation Agent Tests"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from src.agents.conversation.agent import ConversationAgent
from src.agents.conversation.config import ConversationAgentConfig, ConversationRequest
from src.agents.conversation.tools import MCPToolRegistry
from src.shared.llm.base import LLMClient, LLMConfig, LLMProvider, Message, ToolCall, LLMResponse


class MockLLMClient(LLMClient):
    def __init__(self):
        config = LLMConfig(provider=LLMProvider.CLAUDE, api_key="test-key")
        super().__init__(config)
        self.responses = []
        self.call_count = 0
    
    async def chat(self, messages, tools=None, tool_choice=None):
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            return resp
        return LLMResponse(content="Default response")
    
    async def chat_stream(self, messages, tools=None):
        yield "Stream"


@pytest.fixture
def config():
    return ConversationAgentConfig(agent_id="test-agent", tenant_id="tenant-001", llm_api_key="test")


@pytest.fixture
def mock_llm():
    return MockLLMClient()


@pytest.fixture
def agent(config, mock_llm):
    return ConversationAgent(config, llm_client=mock_llm)


class TestMCPToolRegistry:
    def test_get_robot_tools(self):
        tools = MCPToolRegistry.get_robot_tools()
        assert len(tools) >= 3

    def test_get_task_tools(self):
        tools = MCPToolRegistry.get_task_tools()
        assert len(tools) >= 3

    def test_get_all_tools(self):
        tools = MCPToolRegistry.get_all_tools()
        assert len(tools) >= 7


class TestConversationAgentConfig:
    def test_default_config(self):
        config = ConversationAgentConfig(tenant_id="test", llm_api_key="key")
        assert config.agent_id == "conversation-agent"
        assert config.llm_provider == "volcengine"

    def test_custom_config(self):
        config = ConversationAgentConfig(agent_id="custom", tenant_id="test", llm_api_key="key", max_history_turns=10)
        assert config.agent_id == "custom"
        assert config.max_history_turns == 10


class TestConversationAgent:
    @pytest.mark.asyncio
    async def test_init(self, agent):
        assert agent.agent_id == "test-agent"
        assert len(agent.tools) > 0

    @pytest.mark.asyncio
    async def test_chat_simple(self, agent, mock_llm):
        mock_llm.responses = [LLMResponse(content="Hello!")]
        request = ConversationRequest(session_id="s1", tenant_id="t1", user_id="u1", message="Hi")
        response = await agent.chat(request)
        assert response.message == "Hello!"

    @pytest.mark.asyncio
    async def test_chat_with_tool(self, agent, mock_llm):
        mock_llm.responses = [
            LLMResponse(content=None, tool_calls=[ToolCall(id="c1", name="robot_list_robots", arguments={"tenant_id": "t1"})]),
            LLMResponse(content="Found robots"),
        ]
        mock_mcp = AsyncMock()
        mock_mcp.call_tool = AsyncMock(return_value=MagicMock(success=True, data={"robots": []}))
        agent._mcp_client = mock_mcp
        request = ConversationRequest(session_id="s2", tenant_id="t1", user_id="u1", message="List robots")
        response = await agent.chat(request)
        assert len(response.actions_taken) == 1

    @pytest.mark.asyncio
    async def test_session_history(self, agent, mock_llm):
        mock_llm.responses = [LLMResponse(content="R1"), LLMResponse(content="R2")]
        await agent.chat(ConversationRequest(session_id="s3", tenant_id="t1", user_id="u1", message="M1"))
        await agent.chat(ConversationRequest(session_id="s3", tenant_id="t1", user_id="u1", message="M2"))
        history = await agent.get_history("s3")
        assert len(history) == 4

    @pytest.mark.asyncio
    async def test_clear_session(self, agent, mock_llm):
        mock_llm.responses = [LLMResponse(content="Hi")]
        await agent.chat(ConversationRequest(session_id="s4", tenant_id="t1", user_id="u1", message="Test"))
        result = await agent.clear_session("s4")
        assert result is True
        assert "s4" not in agent.sessions

    @pytest.mark.asyncio
    async def test_no_mcp_client(self, agent, mock_llm):
        mock_llm.responses = [
            LLMResponse(content=None, tool_calls=[ToolCall(id="c1", name="robot_get_status", arguments={"robot_id": "r1"})]),
            LLMResponse(content="Error"),
        ]
        request = ConversationRequest(session_id="s5", tenant_id="t1", user_id="u1", message="Status")
        response = await agent.chat(request)
        assert "error" in str(response.actions_taken[0]["result"])
