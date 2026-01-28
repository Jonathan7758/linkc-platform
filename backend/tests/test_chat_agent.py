"""对话Agent单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.agents.base_agent import AgentConfig, AgentContext, AgentState, MessageRole
from app.agents.chat_agent import ChatAgent, ChatAgentConfig, CHAT_SYSTEM_PROMPT


class TestChatAgentConfig:
    """ChatAgentConfig测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = ChatAgentConfig(name="chat-agent")
        assert config.name == "chat-agent"
        assert config.model == "doubao-pro-32k"
        assert config.max_tokens == 2048
        assert config.enable_tools is True
        assert config.enable_intent_routing is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = ChatAgentConfig(
            name="custom-chat",
            model="custom-model",
            max_tokens=4096,
            enable_tools=False,
            enable_intent_routing=False,
            system_prompt="You are a helpful assistant.",
        )
        assert config.name == "custom-chat"
        assert config.model == "custom-model"
        assert config.max_tokens == 4096
        assert config.enable_tools is False
        assert config.enable_intent_routing is False
        assert config.system_prompt == "You are a helpful assistant."


class TestChatAgentInit:
    """ChatAgent初始化测试"""

    def test_init_with_default_prompt(self):
        """测试使用默认系统提示"""
        config = ChatAgentConfig(name="test_agent")
        agent = ChatAgent(config)
        assert agent.config.system_prompt == CHAT_SYSTEM_PROMPT
        assert agent.state == AgentState.IDLE

    def test_init_with_custom_prompt(self):
        """测试使用自定义系统提示"""
        custom_prompt = "你是自定义助手"
        config = ChatAgentConfig(name="test_agent", system_prompt=custom_prompt)
        agent = ChatAgent(config)
        assert agent.config.system_prompt == custom_prompt


class TestAnalyzeIntent:
    """意图分析测试"""

    @pytest.fixture
    def agent(self):
        config = ChatAgentConfig(name="test_agent")
        return ChatAgent(config)

    def test_alarm_intent(self, agent):
        """测试告警意图"""
        assert agent._analyze_intent("显示所有告警") == "alarm"
        assert agent._analyze_intent("告警列表") == "alarm"
        assert agent._analyze_intent("设备故障处理") == "alarm"

    def test_energy_intent(self, agent):
        """测试能耗意图"""
        assert agent._analyze_intent("今天用电多少") == "energy"
        assert agent._analyze_intent("能耗统计") == "energy"
        assert agent._analyze_intent("用水情况") == "energy"

    def test_ticket_intent(self, agent):
        """测试工单意图"""
        assert agent._analyze_intent("创建维修工单") == "ticket"
        assert agent._analyze_intent("报修申请") == "ticket"
        assert agent._analyze_intent("维护任务") == "ticket"

    def test_report_intent(self, agent):
        """测试报表意图"""
        assert agent._analyze_intent("生成日报") == "report"
        assert agent._analyze_intent("周报统计") == "report"
        assert agent._analyze_intent("汇总分析") == "report"

    def test_general_intent(self, agent):
        """测试一般意图"""
        assert agent._analyze_intent("你好") == "general"
        assert agent._analyze_intent("谢谢") == "general"


class TestMultiMCPRegistration:
    """多MCP服务器注册测试"""

    @pytest.fixture
    def agent(self):
        config = ChatAgentConfig(name="test_agent")
        return ChatAgent(config)

    def test_register_single_mcp(self, agent):
        """测试注册单个MCP服务器"""
        mock_server = MagicMock()
        mock_server.server_type = MagicMock()
        mock_server.server_type.value = "alarm"

        agent.register_mcp_server(mock_server)

        assert "alarm" in agent._mcp_servers
        assert agent._mcp_servers["alarm"] == mock_server

    def test_register_multiple_mcps(self, agent):
        """测试批量注册MCP服务器"""
        servers = []
        for server_type in ["alarm", "energy", "ticket", "report"]:
            mock_server = MagicMock()
            mock_server.server_type = MagicMock()
            mock_server.server_type.value = server_type
            servers.append(mock_server)

        agent.register_mcp_servers(servers)

        assert len(agent._mcp_servers) == 4
        assert "alarm" in agent._mcp_servers
        assert "energy" in agent._mcp_servers
        assert "ticket" in agent._mcp_servers
        assert "report" in agent._mcp_servers

    def test_get_server_info(self, agent):
        """测试获取服务器信息"""
        mock_server = MagicMock()
        mock_server.server_type = MagicMock()
        mock_server.server_type.value = "alarm"
        mock_server.get_tools.return_value = [MagicMock(), MagicMock()]

        agent.register_mcp_server(mock_server)

        info = agent.get_server_info()
        assert "alarm" in info
        assert info["alarm"]["type"] == "alarm"
        assert info["alarm"]["tool_count"] == 2


class TestSelectTools:
    """工具选择测试"""

    @pytest.fixture
    def agent_with_mcps(self):
        config = ChatAgentConfig(name="test_agent")
        agent = ChatAgent(config)

        # 注册多个MCP服务器
        for server_type in ["alarm", "energy", "ticket", "report"]:
            mock_server = MagicMock()
            mock_server.server_type = MagicMock()
            mock_server.server_type.value = server_type

            # 创建工具
            mock_tool = MagicMock()
            mock_tool.name = f"get_{server_type}_data"
            mock_server.get_tools.return_value = [mock_tool]

            agent.register_mcp_server(mock_server)

        return agent

    @pytest.mark.asyncio
    async def test_select_tools_for_alarm(self, agent_with_mcps):
        """测试告警意图的工具选择"""
        context = AgentContext(session_id="test")
        context.set_variable("intent", "alarm")

        tools = await agent_with_mcps._select_tools("告警查询", context)

        assert "get_alarm_data" in tools

    @pytest.mark.asyncio
    async def test_select_tools_for_energy(self, agent_with_mcps):
        """测试能耗意图的工具选择"""
        context = AgentContext(session_id="test")
        context.set_variable("intent", "energy")

        tools = await agent_with_mcps._select_tools("用电查询", context)

        assert "get_energy_data" in tools

    @pytest.mark.asyncio
    async def test_select_all_tools_for_general(self, agent_with_mcps):
        """测试一般意图返回所有工具"""
        context = AgentContext(session_id="test")
        context.set_variable("intent", "general")

        tools = await agent_with_mcps._select_tools("你好", context)

        # 应该返回所有工具
        assert len(tools) == 4


class TestExecuteTool:
    """工具执行测试"""

    @pytest.fixture
    def agent(self):
        config = ChatAgentConfig(name="test_agent")
        return ChatAgent(config)

    @pytest.mark.asyncio
    async def test_execute_tool_found(self, agent):
        """测试执行存在的工具"""
        mock_server = MagicMock()
        mock_server.server_type = MagicMock()
        mock_server.server_type.value = "alarm"

        mock_tool = MagicMock()
        mock_tool.name = "get_alarm_list"
        mock_server.get_tools.return_value = [mock_tool]

        agent.register_mcp_server(mock_server)

        # Mock call_tool
        agent.call_tool = AsyncMock(return_value={
            "success": True,
            "result": {"alarms": []}
        })

        result = await agent._execute_tool("get_alarm_list", {})

        assert result["success"] is True
        agent.call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, agent):
        """测试执行不存在的工具"""
        result = await agent._execute_tool("nonexistent_tool", {})

        assert result["success"] is False
        assert "not found" in result["error"]


class TestGetToolsForLLM:
    """LLM工具格式获取测试"""

    @pytest.fixture
    def agent(self):
        config = ChatAgentConfig(name="test_agent")
        return ChatAgent(config)

    def test_get_tools_openai_format(self, agent):
        """测试获取OpenAI格式工具"""
        mock_server = MagicMock()
        mock_server.server_type = MagicMock()
        mock_server.server_type.value = "alarm"
        mock_server.get_tools_openai_format.return_value = [
            {
                "type": "function",
                "function": {
                    "name": "get_alarm_list",
                    "description": "获取告警列表",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]

        agent.register_mcp_server(mock_server)

        tools = agent.get_tools_for_llm()

        assert len(tools) == 1
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "get_alarm_list"

    def test_get_available_tools(self, agent):
        """测试获取可用工具列表"""
        mock_server = MagicMock()
        mock_server.server_type = MagicMock()
        mock_server.server_type.value = "alarm"

        mock_tool = MagicMock()
        mock_tool.name = "get_alarm_list"
        mock_tool.description = "获取告警列表"
        mock_tool.parameters = []
        mock_server.get_tools.return_value = [mock_tool]

        agent.register_mcp_server(mock_server)

        tools = agent.get_available_tools()

        assert len(tools) == 1
        assert tools[0]["name"] == "get_alarm_list"
        assert tools[0]["server"] == "alarm"


class TestProcessMessage:
    """消息处理测试"""

    @pytest.fixture
    def agent(self):
        config = ChatAgentConfig(name="test_agent")
        return ChatAgent(config)

    @pytest.fixture
    def mock_llm_client(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_process_simple_message(self, agent, mock_llm_client):
        """测试处理简单消息"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="您好，我是运维助手。",
                    tool_calls=None,
                )
            )
        ]
        mock_llm_client.chat.completions.create = AsyncMock(return_value=mock_response)
        agent.set_llm_client(mock_llm_client)

        context = AgentContext(session_id="test")
        result = await agent.run("你好", context)

        assert result.success is True
        assert "您好" in result.response or len(result.response) > 0

    @pytest.mark.asyncio
    async def test_process_with_tool_call(self, agent, mock_llm_client):
        """测试处理需要工具调用的消息"""
        # 第一次响应 - 工具调用
        tool_call = MagicMock()
        tool_call.id = "call_123"
        tool_call.function.name = "get_alarm_list"
        tool_call.function.arguments = '{}'

        first_response = MagicMock()
        first_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=None,
                    tool_calls=[tool_call],
                )
            )
        ]

        # 第二次响应 - 最终回答
        second_response = MagicMock()
        second_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="当前有3个告警。",
                    tool_calls=None,
                )
            )
        ]

        mock_llm_client.chat.completions.create = AsyncMock(
            side_effect=[first_response, second_response]
        )
        agent.set_llm_client(mock_llm_client)

        # Mock MCP服务器
        mock_server = MagicMock()
        mock_server.server_type = MagicMock()
        mock_server.server_type.value = "alarm"

        mock_tool = MagicMock()
        mock_tool.name = "get_alarm_list"
        mock_server.get_tools.return_value = [mock_tool]
        mock_server.get_tools_openai_format.return_value = []

        agent.register_mcp_server(mock_server)
        agent.call_tool = AsyncMock(return_value={
            "success": True,
            "result": {"total": 3, "alarms": []}
        })

        context = AgentContext(session_id="test")
        result = await agent.run("显示告警列表", context)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_no_llm_client(self, agent):
        """测试未配置LLM客户端"""
        context = AgentContext(session_id="test")
        result = await agent.run("你好", context)

        assert "未配置" in result.response


class TestBuildMessages:
    """消息构建测试"""

    @pytest.fixture
    def agent(self):
        config = ChatAgentConfig(name="test_agent")
        return ChatAgent(config)

    def test_build_with_system_prompt(self, agent):
        """测试包含系统提示"""
        context = AgentContext(session_id="test")
        messages = agent._build_messages("你好", context)

        assert messages[0]["role"] == "system"
        assert len(messages[0]["content"]) > 0

    def test_build_with_history(self, agent):
        """测试包含历史消息"""
        from app.agents.base_agent import AgentMessage

        context = AgentContext(session_id="test")
        context.add_message(AgentMessage(role=MessageRole.USER, content="之前的问题"))
        context.add_message(AgentMessage(role=MessageRole.ASSISTANT, content="之前的回答"))

        messages = agent._build_messages("新问题", context)

        # system + 2 history + new message
        assert len(messages) >= 4


class TestFormatToolResult:
    """工具结果格式化测试"""

    @pytest.fixture
    def agent(self):
        config = ChatAgentConfig(name="test_agent")
        return ChatAgent(config)

    def test_format_success_result(self, agent):
        """测试格式化成功结果"""
        result = {
            "success": True,
            "result": {"total": 10, "data": []}
        }
        formatted = agent._format_tool_result(result)

        assert "total" in formatted
        assert "10" in formatted

    def test_format_error_result(self, agent):
        """测试格式化错误结果"""
        result = {
            "success": False,
            "error": "工具执行失败"
        }
        formatted = agent._format_tool_result(result)

        assert "Error" in formatted or "error" in formatted.lower()


class TestChatAgentIntegration:
    """ChatAgent集成测试"""

    @pytest.mark.asyncio
    async def test_full_conversation_flow(self):
        """测试完整对话流程"""
        config = ChatAgentConfig(name="integration_test")
        agent = ChatAgent(config)

        # 注册多个MCP服务器
        for server_type in ["alarm", "energy", "ticket"]:
            mock_server = MagicMock()
            mock_server.server_type = MagicMock()
            mock_server.server_type.value = server_type

            mock_tool = MagicMock()
            mock_tool.name = f"get_{server_type}_data"
            mock_server.get_tools.return_value = [mock_tool]
            mock_server.get_tools_openai_format.return_value = []

            agent.register_mcp_server(mock_server)

        # Mock LLM
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="当前系统运行正常。",
                    tool_calls=None,
                )
            )
        ]
        mock_llm.chat.completions.create = AsyncMock(return_value=mock_response)
        agent.set_llm_client(mock_llm)

        # 执行对话
        context = AgentContext(session_id="test")
        result = await agent.run("系统状态如何？", context)

        assert result.success is True
        assert len(context.messages) == 2  # user + assistant
