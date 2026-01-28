"""MCP基类单元测试"""

import pytest
from unittest.mock import AsyncMock

from app.mcp_servers.base_mcp_server import (
    BaseMCPServer,
    MCPServerType,
    MCPTool,
    MCPToolCall,
    ToolParameter,
)


class TestToolParameter:
    """ToolParameter测试"""

    def test_create_required_parameter(self):
        """测试创建必填参数"""
        param = ToolParameter(
            name="device_id",
            type="string",
            description="设备ID",
            required=True,
        )
        assert param.name == "device_id"
        assert param.type == "string"
        assert param.required is True

    def test_create_optional_parameter_with_enum(self):
        """测试创建带枚举的可选参数"""
        param = ToolParameter(
            name="status",
            type="string",
            description="设备状态",
            required=False,
            enum=["running", "stopped", "fault"],
        )
        assert param.required is False
        assert param.enum == ["running", "stopped", "fault"]


class TestMCPTool:
    """MCPTool测试"""

    def test_to_openai_format(self):
        """测试转换为OpenAI格式"""
        tool = MCPTool(
            name="get_device_status",
            description="获取设备状态",
            parameters=[
                ToolParameter(
                    name="device_id",
                    type="string",
                    description="设备ID",
                    required=True,
                ),
                ToolParameter(
                    name="include_readings",
                    type="boolean",
                    description="是否包含读数",
                    required=False,
                ),
            ],
            handler=AsyncMock(),
        )

        result = tool.to_openai_format()

        assert result["type"] == "function"
        assert result["function"]["name"] == "get_device_status"
        assert "device_id" in result["function"]["parameters"]["properties"]
        assert "device_id" in result["function"]["parameters"]["required"]
        assert "include_readings" not in result["function"]["parameters"]["required"]


class TestMCPServerType:
    """MCPServerType枚举测试"""

    def test_server_types(self):
        """测试服务器类型枚举"""
        assert MCPServerType.DEVICE.value == "device"
        assert MCPServerType.KNOWLEDGE.value == "knowledge"
        assert MCPServerType.ALARM.value == "alarm"
        assert MCPServerType.ENERGY.value == "energy"


class ConcreteMCPServer(BaseMCPServer):
    """用于测试的具体MCP Server实现"""

    def _register_tools(self) -> None:
        pass


class TestBaseMCPServer:
    """BaseMCPServer测试"""

    def test_create_server(self):
        """测试创建服务器"""
        server = ConcreteMCPServer(MCPServerType.DEVICE)
        assert server.server_type == MCPServerType.DEVICE

    def test_register_tool(self):
        """测试注册工具"""
        server = ConcreteMCPServer(MCPServerType.DEVICE)
        tool = MCPTool(
            name="test_tool",
            description="测试工具",
            parameters=[],
            handler=AsyncMock(),
        )

        server.register_tool(tool)

        assert len(server.get_tools()) == 1
        assert server.get_tools()[0].name == "test_tool"

    def test_get_tools_openai_format(self):
        """测试获取OpenAI格式工具列表"""
        server = ConcreteMCPServer(MCPServerType.DEVICE)
        tool = MCPTool(
            name="test_tool",
            description="测试工具",
            parameters=[
                ToolParameter(
                    name="param1",
                    type="string",
                    description="参数1",
                    required=True,
                )
            ],
            handler=AsyncMock(),
        )
        server.register_tool(tool)

        tools = server.get_tools_openai_format()

        assert len(tools) == 1
        assert tools[0]["function"]["name"] == "test_tool"

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """测试成功调用工具"""
        server = ConcreteMCPServer(MCPServerType.DEVICE)
        handler = AsyncMock(return_value={"status": "ok"})
        tool = MCPTool(
            name="test_tool",
            description="测试工具",
            parameters=[],
            handler=handler,
        )
        server.register_tool(tool)

        result = await server.call_tool(
            MCPToolCall(call_id="123", tool_name="test_tool", arguments={})
        )

        assert result.success is True
        assert result.result == {"status": "ok"}
        assert result.call_id == "123"

    @pytest.mark.asyncio
    async def test_call_tool_not_found(self):
        """测试调用不存在的工具"""
        server = ConcreteMCPServer(MCPServerType.DEVICE)

        result = await server.call_tool(
            MCPToolCall(call_id="123", tool_name="nonexistent", arguments={})
        )

        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_call_tool_missing_required_param(self):
        """测试缺少必填参数"""
        server = ConcreteMCPServer(MCPServerType.DEVICE)
        tool = MCPTool(
            name="test_tool",
            description="测试工具",
            parameters=[
                ToolParameter(
                    name="required_param",
                    type="string",
                    description="必填参数",
                    required=True,
                )
            ],
            handler=AsyncMock(),
        )
        server.register_tool(tool)

        result = await server.call_tool(
            MCPToolCall(call_id="123", tool_name="test_tool", arguments={})
        )

        assert result.success is False
        assert "Missing required parameter" in result.error

    @pytest.mark.asyncio
    async def test_call_tool_invalid_enum(self):
        """测试无效的枚举值"""
        server = ConcreteMCPServer(MCPServerType.DEVICE)
        tool = MCPTool(
            name="test_tool",
            description="测试工具",
            parameters=[
                ToolParameter(
                    name="status",
                    type="string",
                    description="状态",
                    required=True,
                    enum=["a", "b", "c"],
                )
            ],
            handler=AsyncMock(),
        )
        server.register_tool(tool)

        result = await server.call_tool(
            MCPToolCall(
                call_id="123", tool_name="test_tool", arguments={"status": "invalid"}
            )
        )

        assert result.success is False
        assert "must be one of" in result.error

    @pytest.mark.asyncio
    async def test_call_tool_handler_exception(self):
        """测试处理函数异常"""
        server = ConcreteMCPServer(MCPServerType.DEVICE)
        handler = AsyncMock(side_effect=Exception("Something went wrong"))
        tool = MCPTool(
            name="test_tool",
            description="测试工具",
            parameters=[],
            handler=handler,
        )
        server.register_tool(tool)

        result = await server.call_tool(
            MCPToolCall(call_id="123", tool_name="test_tool", arguments={})
        )

        assert result.success is False
        assert "Something went wrong" in result.error
