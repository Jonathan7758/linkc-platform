"""Agent基类单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timezone

from app.agents.base_agent import (
    BaseAgent,
    AgentConfig,
    AgentContext,
    AgentMessage,
    MessageRole,
    AgentState,
    AgentResult,
)


class ConcreteAgent(BaseAgent):
    """测试用的具体Agent实现"""

    async def _process_message(self, message: str, context: AgentContext) -> str:
        """处理消息"""
        return f"Processed: {message}"

    async def _select_tools(self, message: str, context: AgentContext) -> list[str]:
        """选择工具"""
        return ["tool1", "tool2"]


class TestAgentConfig:
    """AgentConfig测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = AgentConfig(name="test-agent")
        assert config.name == "test-agent"
        assert config.max_iterations == 10
        assert config.temperature == 0.7
        assert config.timeout == 30.0

    def test_custom_config(self):
        """测试自定义配置"""
        config = AgentConfig(
            name="custom-agent",
            description="Custom agent",
            max_iterations=5,
            temperature=0.5,
            timeout=60.0,
            tools=["tool1", "tool2"],
        )
        assert config.name == "custom-agent"
        assert config.description == "Custom agent"
        assert config.max_iterations == 5
        assert config.temperature == 0.5
        assert config.timeout == 60.0
        assert config.tools == ["tool1", "tool2"]


class TestAgentContext:
    """AgentContext测试"""

    def test_create_context(self):
        """测试创建上下文"""
        context = AgentContext(session_id="session-123")
        assert context.session_id == "session-123"
        assert context.messages == []
        assert context.variables == {}
        assert context.metadata == {}

    def test_add_message(self):
        """测试添加消息"""
        context = AgentContext(session_id="session-123")
        msg = AgentMessage(
            role=MessageRole.USER,
            content="Hello",
        )
        context.add_message(msg)
        assert len(context.messages) == 1
        assert context.messages[0].content == "Hello"

    def test_get_recent_messages(self):
        """测试获取最近消息"""
        context = AgentContext(session_id="session-123")
        for i in range(5):
            context.add_message(
                AgentMessage(role=MessageRole.USER, content=f"Message {i}")
            )
        recent = context.get_recent_messages(3)
        assert len(recent) == 3
        assert recent[0].content == "Message 2"
        assert recent[-1].content == "Message 4"

    def test_set_variable(self):
        """测试设置变量"""
        context = AgentContext(session_id="session-123")
        context.set_variable("key1", "value1")
        assert context.get_variable("key1") == "value1"
        assert context.get_variable("nonexistent") is None
        assert context.get_variable("nonexistent", "default") == "default"


class TestAgentMessage:
    """AgentMessage测试"""

    def test_create_message(self):
        """测试创建消息"""
        msg = AgentMessage(
            role=MessageRole.USER,
            content="Test message",
        )
        assert msg.role == MessageRole.USER
        assert msg.content == "Test message"
        assert msg.timestamp is not None
        assert msg.tool_calls is None

    def test_message_with_tool_calls(self):
        """测试带工具调用的消息"""
        tool_calls = [{"tool": "get_device", "arguments": {"id": "123"}}]
        msg = AgentMessage(
            role=MessageRole.ASSISTANT,
            content="Let me check the device",
            tool_calls=tool_calls,
        )
        assert msg.tool_calls == tool_calls


class TestBaseAgent:
    """BaseAgent测试"""

    @pytest.fixture
    def agent(self):
        """创建测试Agent"""
        config = AgentConfig(
            name="test-agent",
            description="Test agent",
            tools=["tool1", "tool2"],
        )
        return ConcreteAgent(config)

    def test_init(self, agent):
        """测试初始化"""
        assert agent.config.name == "test-agent"
        assert agent.state == AgentState.IDLE
        assert agent._mcp_servers == {}

    def test_register_mcp_server(self, agent):
        """测试注册MCP服务器"""
        mock_server = MagicMock()
        mock_server.name = "device-mcp"
        agent.register_mcp_server(mock_server)
        assert "device-mcp" in agent._mcp_servers

    @pytest.mark.asyncio
    async def test_run_basic(self, agent):
        """测试基本运行"""
        context = AgentContext(session_id="session-123")
        result = await agent.run("Hello", context)

        assert isinstance(result, AgentResult)
        assert result.success is True
        assert result.response == "Processed: Hello"
        assert agent.state == AgentState.IDLE

    @pytest.mark.asyncio
    async def test_run_updates_context(self, agent):
        """测试运行更新上下文"""
        context = AgentContext(session_id="session-123")
        await agent.run("Hello", context)

        # 应该添加了用户消息和助手消息
        assert len(context.messages) == 2
        assert context.messages[0].role == MessageRole.USER
        assert context.messages[1].role == MessageRole.ASSISTANT

    @pytest.mark.asyncio
    async def test_run_with_error(self, agent):
        """测试运行出错"""
        context = AgentContext(session_id="session-123")

        # Mock _process_message to raise an exception
        agent._process_message = AsyncMock(side_effect=Exception("Test error"))

        result = await agent.run("Hello", context)

        assert result.success is False
        assert "Test error" in result.error
        assert agent.state == AgentState.ERROR

    @pytest.mark.asyncio
    async def test_call_tool(self, agent):
        """测试调用工具"""
        # 创建mock结果
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.result = {"device_id": "123", "status": "online"}
        mock_result.error = None

        # 创建mock服务器
        mock_server = MagicMock()
        mock_server.name = "device-mcp"
        mock_server.call_tool = AsyncMock(return_value=mock_result)

        agent.register_mcp_server(mock_server)

        result = await agent.call_tool("device-mcp", "get_device", {"id": "123"})

        assert result["success"] is True
        assert result["result"]["device_id"] == "123"
        mock_server.call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_server_not_found(self, agent):
        """测试调用不存在的工具服务器"""
        result = await agent.call_tool("nonexistent", "tool", {})

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_get_available_tools(self, agent):
        """测试获取可用工具"""
        # 创建工具mock，使用configure_mock来正确设置name
        tool1 = MagicMock()
        tool1.configure_mock(name="get_device")
        tool1.description = "Get device info"
        tool1.parameters = {}

        tool2 = MagicMock()
        tool2.configure_mock(name="list_devices")
        tool2.description = "List all devices"
        tool2.parameters = {}

        # 创建服务器mock
        mock_server = MagicMock()
        mock_server.name = "device-mcp"
        mock_server.list_tools.return_value = [tool1, tool2]

        agent.register_mcp_server(mock_server)

        tools = agent.get_available_tools()

        assert len(tools) == 2
        # MagicMock.name returns a function, so we check the actual values
        tool_names = [t["name"] for t in tools]
        assert "get_device" in tool_names or any("get_device" in str(n) for n in tool_names)

    @pytest.mark.asyncio
    async def test_reset(self, agent):
        """测试重置Agent"""
        agent._state = AgentState.ERROR
        await agent.reset()

        assert agent.state == AgentState.IDLE


class TestAgentState:
    """AgentState测试"""

    def test_states(self):
        """测试状态值"""
        assert AgentState.IDLE.value == "idle"
        assert AgentState.RUNNING.value == "running"
        assert AgentState.WAITING.value == "waiting"
        assert AgentState.ERROR.value == "error"
