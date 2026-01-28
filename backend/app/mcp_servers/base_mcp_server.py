"""MCP Server基类模块"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable


class MCPServerType(str, Enum):
    """MCP Server类型"""

    DEVICE = "device"
    KNOWLEDGE = "knowledge"
    ALARM = "alarm"
    ENERGY = "energy"
    TICKET = "ticket"
    REPORT = "report"


@dataclass
class ToolParameter:
    """工具参数定义"""

    name: str
    type: str  # string, integer, number, boolean, array, object
    description: str
    required: bool = True
    enum: list[str] | None = None
    default: Any = None


@dataclass
class MCPTool:
    """MCP工具定义"""

    name: str
    description: str
    parameters: list[ToolParameter]
    handler: Callable  # 处理函数

    def to_openai_format(self) -> dict:
        """转换为OpenAI Function格式"""
        properties = {}
        required = []

        for param in self.parameters:
            prop: dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


@dataclass
class MCPToolCall:
    """工具调用请求"""

    call_id: str
    tool_name: str
    arguments: dict


@dataclass
class MCPToolResult:
    """工具调用结果"""

    tool_name: str
    call_id: str
    success: bool
    result: Any | None = None
    error: str | None = None


class BaseMCPServer(ABC):
    """MCP Server基类"""

    def __init__(self, server_type: MCPServerType):
        self.server_type = server_type
        self._tools: dict[str, MCPTool] = {}
        self._register_tools()

    def register_tool(self, tool: MCPTool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool

    def get_tools(self) -> list[MCPTool]:
        """获取所有工具"""
        return list(self._tools.values())

    def get_tools_openai_format(self) -> list[dict]:
        """获取OpenAI格式的工具列表"""
        return [tool.to_openai_format() for tool in self._tools.values()]

    async def call_tool(self, tool_call: MCPToolCall) -> MCPToolResult:
        """调用工具"""
        tool = self._tools.get(tool_call.tool_name)

        if not tool:
            return MCPToolResult(
                tool_name=tool_call.tool_name,
                call_id=tool_call.call_id,
                success=False,
                error=f"Tool '{tool_call.tool_name}' not found",
            )

        # 参数验证
        validation_error = self._validate_arguments(tool, tool_call.arguments)
        if validation_error:
            return MCPToolResult(
                tool_name=tool_call.tool_name,
                call_id=tool_call.call_id,
                success=False,
                error=validation_error,
            )

        # 执行工具
        try:
            result = await tool.handler(tool_call.arguments)
            return MCPToolResult(
                tool_name=tool_call.tool_name,
                call_id=tool_call.call_id,
                success=True,
                result=result,
            )
        except Exception as e:
            return MCPToolResult(
                tool_name=tool_call.tool_name,
                call_id=tool_call.call_id,
                success=False,
                error=str(e),
            )

    def _validate_arguments(self, tool: MCPTool, arguments: dict) -> str | None:
        """验证参数，返回错误信息或None"""
        for param in tool.parameters:
            if param.required and param.name not in arguments:
                return f"Missing required parameter: {param.name}"

            if param.name in arguments:
                value = arguments[param.name]
                # 类型检查
                if param.type == "string" and not isinstance(value, str):
                    return f"Parameter '{param.name}' must be string"
                if param.type == "integer" and not isinstance(value, int):
                    return f"Parameter '{param.name}' must be integer"
                if param.type == "number" and not isinstance(value, (int, float)):
                    return f"Parameter '{param.name}' must be number"
                if param.type == "boolean" and not isinstance(value, bool):
                    return f"Parameter '{param.name}' must be boolean"
                # 枚举检查
                if param.enum and value not in param.enum:
                    return f"Parameter '{param.name}' must be one of {param.enum}"

        return None

    @abstractmethod
    def _register_tools(self) -> None:
        """子类实现：注册所有工具"""
        pass
