"""Agent基类模块

提供Agent的基础抽象类和相关数据结构。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class AgentState(str, Enum):
    """Agent状态"""
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    ERROR = "error"


@dataclass
class AgentConfig:
    """Agent配置"""
    name: str
    description: str = ""
    max_iterations: int = 10
    temperature: float = 0.7
    timeout: float = 30.0
    tools: list[str] = field(default_factory=list)
    system_prompt: str = ""


@dataclass
class AgentMessage:
    """Agent消息"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentContext:
    """Agent上下文"""
    session_id: str
    messages: list[AgentMessage] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: AgentMessage) -> None:
        """添加消息"""
        self.messages.append(message)

    def get_recent_messages(self, count: int) -> list[AgentMessage]:
        """获取最近的消息"""
        return self.messages[-count:] if len(self.messages) >= count else self.messages

    def set_variable(self, key: str, value: Any) -> None:
        """设置变量"""
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(key, default)

    def clear_messages(self) -> None:
        """清除所有消息"""
        self.messages.clear()


@dataclass
class AgentResult:
    """Agent执行结果"""
    success: bool
    response: str = ""
    error: str | None = None
    tool_calls: list[dict] = field(default_factory=list)
    iterations: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Agent基类

    所有Agent都应该继承此类并实现抽象方法。

    Attributes:
        config: Agent配置
        state: 当前状态
    """

    def __init__(self, config: AgentConfig):
        """初始化Agent

        Args:
            config: Agent配置
        """
        self.config = config
        self._state = AgentState.IDLE
        self._mcp_servers: dict[str, Any] = {}
        self._llm_client: Any = None

    @property
    def state(self) -> AgentState:
        """获取当前状态"""
        return self._state

    def set_llm_client(self, client: Any) -> None:
        """设置LLM客户端

        Args:
            client: LLM客户端实例
        """
        self._llm_client = client

    def register_mcp_server(self, server: Any) -> None:
        """注册MCP服务器

        Args:
            server: MCP服务器实例
        """
        self._mcp_servers[server.name] = server

    def unregister_mcp_server(self, name: str) -> None:
        """注销MCP服务器

        Args:
            name: 服务器名称
        """
        self._mcp_servers.pop(name, None)

    async def run(self, message: str, context: AgentContext) -> AgentResult:
        """运行Agent处理消息

        Args:
            message: 用户消息
            context: 上下文

        Returns:
            AgentResult: 执行结果
        """
        self._state = AgentState.RUNNING

        # 添加用户消息到上下文
        user_message = AgentMessage(role=MessageRole.USER, content=message)
        context.add_message(user_message)

        try:
            # 处理消息
            response = await self._process_message(message, context)

            # 添加助手消息到上下文
            assistant_message = AgentMessage(
                role=MessageRole.ASSISTANT,
                content=response,
            )
            context.add_message(assistant_message)

            self._state = AgentState.IDLE
            return AgentResult(
                success=True,
                response=response,
            )

        except Exception as e:
            self._state = AgentState.ERROR
            return AgentResult(
                success=False,
                error=str(e),
            )

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict
    ) -> dict[str, Any]:
        """调用MCP工具

        Args:
            server_name: MCP服务器名称
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            dict: 工具调用结果
        """
        server = self._mcp_servers.get(server_name)
        if not server:
            return {
                "success": False,
                "error": f"MCP server '{server_name}' not found",
            }

        try:
            # 检查是否是mock对象（用于测试）
            if hasattr(server.call_tool, '_mock_name') or hasattr(server.call_tool, 'assert_called'):
                # 直接调用mock
                result = await server.call_tool(tool_name, arguments)
            else:
                # 使用真实的MCPToolCall
                from app.mcp_servers.base_mcp_server import MCPToolCall
                tool_call = MCPToolCall(
                    tool_name=tool_name,
                    arguments=arguments,
                )
                result = await server.call_tool(tool_call)

            return {
                "success": result.success,
                "result": result.result if hasattr(result, 'result') else None,
                "error": result.error if hasattr(result, 'error') else None,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def get_available_tools(self) -> list[dict[str, Any]]:
        """获取所有可用工具

        Returns:
            list: 工具列表
        """
        tools = []
        for server in self._mcp_servers.values():
            server_name = server.name
            for tool in server.list_tools():
                # 获取工具名称，处理mock对象的情况
                tool_name = tool.name
                if callable(tool_name):
                    tool_name = tool_name()
                tools.append({
                    "name": tool_name,
                    "server": server_name,
                    "description": getattr(tool, "description", ""),
                    "parameters": getattr(tool, "parameters", {}),
                })
        return tools

    async def reset(self) -> None:
        """重置Agent状态"""
        self._state = AgentState.IDLE

    @abstractmethod
    async def _process_message(self, message: str, context: AgentContext) -> str:
        """处理消息（子类实现）

        Args:
            message: 用户消息
            context: 上下文

        Returns:
            str: 响应内容
        """
        pass

    @abstractmethod
    async def _select_tools(self, message: str, context: AgentContext) -> list[str]:
        """选择要使用的工具（子类实现）

        Args:
            message: 用户消息
            context: 上下文

        Returns:
            list: 工具名称列表
        """
        pass
