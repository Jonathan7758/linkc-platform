"""对话Agent单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.agents.base_agent import AgentConfig, AgentContext, AgentState, MessageRole
from app.agents.chat_agent import ChatAgent, ChatAgentConfig


class TestChatAgentConfig:
    """ChatAgentConfig测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = ChatAgentConfig(name="chat-agent")
        assert config.name == "chat-agent"
        assert config.model == "doubao-pro-32k"
        assert config.max_tokens == 2048
        assert config.enable_tools is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = ChatAgentConfig(
            name="custom-chat",
            model="custom-model",
            max_tokens=4096,
            enable_tools=False,
            system_prompt="You are a helpful assistant.",
        )
        assert config.name == "custom-chat"
        assert config.model == "custom-model"
        assert config.max_tokens == 4096
        assert config.enable_tools is False
        assert config.system_prompt == "You are a helpful assistant."


class TestChatAgent:
    """ChatAgent测试"""

    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return ChatAgentConfig(
            name="test-chat-agent",
            system_prompt="你是MEP AI助手，专门帮助用户查询和管理机电设备。",
        )

    @pytest.fixture
    def agent(self, config):
        """创建测试Agent"""
        return ChatAgent(config)

    @pytest.fixture
    def mock_llm_client(self):
        """创建mock LLM客户端"""
        client = MagicMock()
        return client

    def test_init(self, agent):
        """测试初始化"""
        assert agent.config.name == "test-chat-agent"
        assert agent.state == AgentState.IDLE

    @pytest.mark.asyncio
    async def test_process_message_simple(self, agent, mock_llm_client):
        """测试处理简单消息"""
        # Mock LLM响应
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="空调系统目前运行正常。",
                    tool_calls=None,
                )
            )
        ]
        mock_llm_client.chat.completions.create = AsyncMock(return_value=mock_response)
        agent.set_llm_client(mock_llm_client)

        context = AgentContext(session_id="session-123")
        result = await agent.run("空调系统状态如何？", context)

        assert result.success is True
        assert "空调" in result.response or len(result.response) > 0

    @pytest.mark.asyncio
    async def test_process_message_with_tool_call(self, agent, mock_llm_client):
        """测试处理需要工具调用的消息"""
        # 第一次LLM响应 - 请求工具调用
        tool_call = MagicMock()
        tool_call.id = "call_123"
        tool_call.function.name = "get_device_status"
        tool_call.function.arguments = '{"device_id": "AHU-001"}'

        first_response = MagicMock()
        first_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=None,
                    tool_calls=[tool_call],
                )
            )
        ]

        # 第二次LLM响应 - 最终回答
        second_response = MagicMock()
        second_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="设备AHU-001当前状态为在线，运行正常。",
                    tool_calls=None,
                )
            )
        ]

        mock_llm_client.chat.completions.create = AsyncMock(
            side_effect=[first_response, second_response]
        )
        agent.set_llm_client(mock_llm_client)

        # Mock MCP服务器
        mock_mcp = MagicMock()
        mock_mcp.name = "device-mcp"
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.result = {"device_id": "AHU-001", "status": "online"}
        mock_result.error = None
        mock_mcp.call_tool = AsyncMock(return_value=mock_result)
        mock_mcp.list_tools.return_value = []
        agent.register_mcp_server(mock_mcp)

        context = AgentContext(session_id="session-123")
        result = await agent.run("查看设备AHU-001的状态", context)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_build_messages(self, agent):
        """测试构建消息列表"""
        context = AgentContext(session_id="session-123")

        messages = agent._build_messages("你好", context)

        # 应该包含系统提示和用户消息
        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "你好"

    @pytest.mark.asyncio
    async def test_build_messages_with_history(self, agent):
        """测试带历史的消息构建"""
        context = AgentContext(session_id="session-123")

        # 添加历史消息
        from app.agents.base_agent import AgentMessage

        context.add_message(
            AgentMessage(role=MessageRole.USER, content="之前的问题")
        )
        context.add_message(
            AgentMessage(role=MessageRole.ASSISTANT, content="之前的回答")
        )

        messages = agent._build_messages("新问题", context)

        # 应该包含：system + 2 history + 新问题
        # 因为"新问题"不在历史中，所以会被添加
        assert len(messages) >= 4  # system + 2 history + user

    def test_format_tool_result(self, agent):
        """测试格式化工具结果"""
        result = {
            "success": True,
            "result": {"device_id": "AHU-001", "status": "online"},
        }

        formatted = agent._format_tool_result(result)

        assert "device_id" in formatted
        assert "AHU-001" in formatted

    def test_format_tool_result_error(self, agent):
        """测试格式化工具错误结果"""
        result = {
            "success": False,
            "error": "Device not found",
        }

        formatted = agent._format_tool_result(result)

        assert "error" in formatted.lower() or "Error" in formatted

    @pytest.mark.asyncio
    async def test_select_tools(self, agent):
        """测试工具选择"""
        # 注册MCP服务器
        mock_mcp = MagicMock()
        mock_mcp.name = "device-mcp"

        tool1 = MagicMock()
        tool1.configure_mock(name="get_device_status")
        tool2 = MagicMock()
        tool2.configure_mock(name="get_device_list")

        mock_mcp.list_tools.return_value = [tool1, tool2]
        agent.register_mcp_server(mock_mcp)

        context = AgentContext(session_id="session-123")
        tools = await agent._select_tools("查看设备状态", context)

        # 应该返回可用工具
        assert isinstance(tools, list)

    @pytest.mark.asyncio
    async def test_llm_error_handling(self, agent, mock_llm_client):
        """测试LLM错误处理"""
        mock_llm_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        agent.set_llm_client(mock_llm_client)

        context = AgentContext(session_id="session-123")
        result = await agent.run("测试消息", context)

        assert result.success is False
        assert "API Error" in result.error or result.error is not None

    @pytest.mark.asyncio
    async def test_max_iterations(self, agent, mock_llm_client):
        """测试最大迭代次数限制"""
        # 创建一个总是返回工具调用的响应
        tool_call = MagicMock()
        tool_call.id = "call_123"
        tool_call.function.name = "get_device_status"
        tool_call.function.arguments = '{"device_id": "AHU-001"}'

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=None,
                    tool_calls=[tool_call],
                )
            )
        ]
        mock_llm_client.chat.completions.create = AsyncMock(return_value=mock_response)
        agent.set_llm_client(mock_llm_client)

        # Mock MCP服务器
        mock_mcp = MagicMock()
        mock_mcp.name = "device-mcp"
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.result = {}
        mock_result.error = None
        mock_mcp.call_tool = AsyncMock(return_value=mock_result)
        mock_mcp.list_tools.return_value = []
        agent.register_mcp_server(mock_mcp)

        # 设置较小的最大迭代次数
        agent.config.max_iterations = 3

        context = AgentContext(session_id="session-123")
        result = await agent.run("测试", context)

        # 应该在达到最大迭代次数后停止
        assert mock_llm_client.chat.completions.create.call_count <= 4


class TestChatAgentIntegration:
    """ChatAgent集成测试"""

    @pytest.fixture
    def agent_with_mock_mcp(self):
        """创建带Mock MCP服务器的Agent"""
        config = ChatAgentConfig(
            name="integration-agent",
            system_prompt="你是MEP设备助手。",
        )
        agent = ChatAgent(config)

        # 使用Mock MCP服务器
        mock_mcp = MagicMock()
        mock_mcp.name = "device-mcp"

        # 创建工具
        tool1 = MagicMock()
        tool1.name = "get_device_status"
        tool1.description = "获取设备状态"
        tool1.parameters = {"type": "object", "properties": {"device_id": {"type": "string"}}}

        tool2 = MagicMock()
        tool2.name = "get_device_list"
        tool2.description = "获取设备列表"
        tool2.parameters = {"type": "object", "properties": {}}

        mock_mcp.list_tools.return_value = [tool1, tool2]
        mock_mcp.get_tools_openai_format.return_value = [
            {
                "type": "function",
                "function": {
                    "name": "get_device_status",
                    "description": "获取设备状态",
                    "parameters": {"type": "object", "properties": {"device_id": {"type": "string"}}},
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_device_list",
                    "description": "获取设备列表",
                    "parameters": {"type": "object", "properties": {}},
                }
            },
        ]
        agent.register_mcp_server(mock_mcp)

        return agent

    def test_get_tools_for_llm(self, agent_with_mock_mcp):
        """测试获取LLM可用的工具格式"""
        tools = agent_with_mock_mcp.get_tools_for_llm()

        assert isinstance(tools, list)
        assert len(tools) > 0
        # 检查OpenAI工具格式
        for tool in tools:
            assert "type" in tool
            assert tool["type"] == "function"
            assert "function" in tool
