"""对话Agent模块

提供基于LLM的对话Agent实现，支持多MCP服务器调用。
"""
import json
from dataclasses import dataclass, field
from typing import Any

from app.agents.base_agent import (
    BaseAgent,
    AgentConfig,
    AgentContext,
    AgentMessage,
    AgentResult,
    AgentState,
    MessageRole,
)


CHAT_SYSTEM_PROMPT = """你是一个专业的建筑设备运维助手。你可以帮助用户：

1. 查询和处理设备告警
2. 分析能耗数据，发现异常
3. 管理维修工单
4. 生成运营报表

请用中文回答，保持专业、简洁的风格。根据用户的问题选择合适的工具来获取信息。
"""


@dataclass
class ChatAgentConfig(AgentConfig):
    """对话Agent配置"""
    model: str = "doubao-pro-32k"
    max_tokens: int = 2048
    enable_tools: bool = True
    tool_choice: str = "auto"  # auto, none, required
    enable_intent_routing: bool = True  # 启用意图路由


class ChatAgent(BaseAgent):
    """对话Agent

    基于LLM的对话Agent，支持：
    - 多轮对话
    - 多MCP服务器工具调用
    - 意图识别和路由
    - 上下文管理
    """

    def __init__(self, config: ChatAgentConfig):
        """初始化对话Agent

        Args:
            config: Agent配置
        """
        if not config.system_prompt:
            config.system_prompt = CHAT_SYSTEM_PROMPT
        super().__init__(config)
        self.config: ChatAgentConfig = config

    def register_mcp_servers(self, servers: list[Any]) -> None:
        """批量注册MCP服务器

        Args:
            servers: MCP服务器列表
        """
        for server in servers:
            self.register_mcp_server(server)

    def register_mcp_server(self, server: Any) -> None:
        """注册MCP服务器

        Args:
            server: MCP服务器实例
        """
        # 使用server_type作为名称
        name = server.server_type.value if hasattr(server, 'server_type') else str(server)
        self._mcp_servers[name] = server

    async def _process_message(self, message: str, context: AgentContext) -> str:
        """处理消息

        Args:
            message: 用户消息
            context: 上下文

        Returns:
            str: 响应内容
        """
        if not self._llm_client:
            return "LLM客户端未配置"

        # 分析意图
        if self.config.enable_intent_routing:
            intent = self._analyze_intent(message)
            context.set_variable("intent", intent)

        iterations = 0
        max_iterations = self.config.max_iterations
        messages = self._build_messages(message, context)
        tool_results_messages = []

        while iterations < max_iterations:
            iterations += 1

            # 构建请求参数
            request_params = {
                "model": self.config.model,
                "messages": messages + tool_results_messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            }

            # 添加工具
            if self.config.enable_tools:
                tools = self.get_tools_for_llm()
                if tools:
                    request_params["tools"] = tools
                    request_params["tool_choice"] = self.config.tool_choice

            # 调用LLM
            response = await self._llm_client.chat.completions.create(**request_params)

            assistant_message = response.choices[0].message

            # 检查是否有工具调用
            if assistant_message.tool_calls:
                # 添加助手消息
                tool_results_messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]
                })

                # 执行工具调用
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                    # 查找并调用工具
                    tool_result = await self._execute_tool(tool_name, arguments)

                    # 添加工具结果
                    tool_results_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": self._format_tool_result(tool_result),
                    })
            else:
                # 没有工具调用，返回内容
                return assistant_message.content or ""

        # 达到最大迭代次数
        return "抱歉，处理请求时遇到了问题。请稍后重试。"

    def _analyze_intent(self, message: str) -> str:
        """分析消息意图

        Args:
            message: 用户消息

        Returns:
            str: 意图类型
        """
        message_lower = message.lower()

        # 告警相关
        if any(kw in message_lower for kw in [
            "告警", "警报", "报警", "异常告警", "设备故障",
            "确认告警", "处理告警", "告警列表", "告警统计"
        ]):
            return "alarm"

        # 能耗相关
        if any(kw in message_lower for kw in [
            "能耗", "用电", "用水", "用气", "耗能",
            "电费", "水费", "能源", "消耗", "度数"
        ]):
            return "energy"

        # 工单相关
        if any(kw in message_lower for kw in [
            "工单", "维修", "报修", "派单", "接单",
            "维护", "保养", "检修", "任务"
        ]):
            return "ticket"

        # 报表相关
        if any(kw in message_lower for kw in [
            "报表", "报告", "统计", "汇总", "分析",
            "日报", "周报", "月报"
        ]):
            return "report"

        return "general"

    async def _select_tools(self, message: str, context: AgentContext) -> list[str]:
        """选择要使用的工具

        Args:
            message: 用户消息
            context: 上下文

        Returns:
            list: 工具名称列表
        """
        intent = context.get_variable("intent", "general")

        # 根据意图选择MCP服务器
        if intent == "alarm" and "alarm" in self._mcp_servers:
            return self._get_tools_from_server("alarm")
        elif intent == "energy" and "energy" in self._mcp_servers:
            return self._get_tools_from_server("energy")
        elif intent == "ticket" and "ticket" in self._mcp_servers:
            return self._get_tools_from_server("ticket")
        elif intent == "report" and "report" in self._mcp_servers:
            return self._get_tools_from_server("report")

        # 返回所有工具
        return self._get_all_tool_names()

    def _get_tools_from_server(self, server_name: str) -> list[str]:
        """获取指定服务器的工具名称列表"""
        server = self._mcp_servers.get(server_name)
        if not server:
            return []

        tools = server.get_tools() if hasattr(server, 'get_tools') else []
        return [tool.name for tool in tools]

    def _get_all_tool_names(self) -> list[str]:
        """获取所有工具名称"""
        tool_names = []
        for server in self._mcp_servers.values():
            if hasattr(server, 'get_tools'):
                tools = server.get_tools()
                tool_names.extend([tool.name for tool in tools])
        return tool_names

    def _build_messages(
        self, message: str, context: AgentContext, include_current: bool = True
    ) -> list[dict[str, Any]]:
        """构建LLM消息列表

        Args:
            message: 当前用户消息
            context: 上下文
            include_current: 是否包含当前消息（在run中已添加到context）

        Returns:
            list: 消息列表
        """
        messages = []

        # 添加系统提示
        if self.config.system_prompt:
            messages.append({
                "role": "system",
                "content": self.config.system_prompt,
            })

        # 添加历史消息
        # 注意：在run方法中，当前用户消息已经被添加到context.messages中
        # 所以我们需要包含所有历史消息
        history_messages = context.messages if context.messages else []

        for msg in history_messages:
            messages.append({
                "role": msg.role.value,
                "content": msg.content,
            })

        # 如果历史中没有当前消息（直接调用_build_messages时），添加它
        if not history_messages or history_messages[-1].content != message:
            messages.append({
                "role": "user",
                "content": message,
            })

        return messages

    async def _execute_tool(
        self, tool_name: str, arguments: dict
    ) -> dict[str, Any]:
        """执行工具调用

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            dict: 工具执行结果
        """
        # 查找包含该工具的MCP服务器
        for server_name, server in self._mcp_servers.items():
            # 使用正确的API: get_tools()
            if hasattr(server, 'get_tools'):
                tools = server.get_tools()
                tool_names = [tool.name for tool in tools]

                if tool_name in tool_names:
                    return await self.call_tool(server_name, tool_name, arguments)
            # 兼容mock对象
            elif hasattr(server, '_tools'):
                if tool_name in server._tools:
                    return await self.call_tool(server_name, tool_name, arguments)

        return {
            "success": False,
            "error": f"Tool '{tool_name}' not found in any MCP server",
        }

    def _format_tool_result(self, result: dict[str, Any]) -> str:
        """格式化工具结果

        Args:
            result: 工具结果

        Returns:
            str: 格式化后的结果
        """
        if result.get("success"):
            return json.dumps(result.get("result", {}), ensure_ascii=False, indent=2)
        else:
            return f"Error: {result.get('error', 'Unknown error')}"

    def get_tools_for_llm(self) -> list[dict[str, Any]]:
        """获取LLM可用的工具格式

        Returns:
            list: OpenAI格式的工具列表
        """
        tools = []
        for server in self._mcp_servers.values():
            # 使用MCP服务器的OpenAI格式工具
            if hasattr(server, "get_tools_openai_format"):
                tools.extend(server.get_tools_openai_format())
            elif hasattr(server, "get_tools"):
                # 手动转换
                for tool in server.get_tools():
                    tools.append(tool.to_openai_format())
        return tools

    def get_available_tools(self) -> list[dict[str, Any]]:
        """获取所有可用工具

        Returns:
            list: 工具列表
        """
        tools = []
        for server_name, server in self._mcp_servers.items():
            if hasattr(server, 'get_tools'):
                for tool in server.get_tools():
                    tools.append({
                        "name": tool.name,
                        "server": server_name,
                        "description": tool.description,
                        "parameters": [
                            {
                                "name": p.name,
                                "type": p.type,
                                "description": p.description,
                                "required": p.required,
                            }
                            for p in tool.parameters
                        ],
                    })
        return tools

    def get_server_info(self) -> dict[str, Any]:
        """获取已注册的MCP服务器信息

        Returns:
            dict: 服务器信息
        """
        info = {}
        for name, server in self._mcp_servers.items():
            tool_count = 0
            if hasattr(server, 'get_tools'):
                tool_count = len(server.get_tools())
            info[name] = {
                "type": server.server_type.value if hasattr(server, 'server_type') else "unknown",
                "tool_count": tool_count,
            }
        return info
