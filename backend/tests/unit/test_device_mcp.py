"""设备MCP单元测试"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.mcp_servers.device_mcp import DeviceMCPServer
from app.mcp_servers.base_mcp_server import MCPServerType, MCPToolCall


class TestDeviceMCPServer:
    """DeviceMCPServer测试"""

    def test_server_type(self):
        """测试服务器类型"""
        mock_session = MagicMock()
        server = DeviceMCPServer(mock_session)
        assert server.server_type == MCPServerType.DEVICE

    def test_tools_registered(self):
        """测试工具注册"""
        mock_session = MagicMock()
        server = DeviceMCPServer(mock_session)
        tools = server.get_tools()
        tool_names = [t.name for t in tools]

        assert "get_device_status" in tool_names
        assert "get_device_list" in tool_names
        assert "get_device_readings" in tool_names
        assert "get_device_health" in tool_names
        assert "get_device_stats" in tool_names
        assert "control_device" in tool_names
        assert len(tools) == 6

    def test_get_tools_openai_format(self):
        """测试OpenAI格式输出"""
        mock_session = MagicMock()
        server = DeviceMCPServer(mock_session)
        tools = server.get_tools_openai_format()

        assert len(tools) == 6
        for tool in tools:
            assert tool["type"] == "function"
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]


class TestGetDeviceStatus:
    """get_device_status工具测试"""

    @pytest.mark.asyncio
    async def test_device_found(self):
        """测试设备存在"""
        mock_session = MagicMock()
        mock_device = MagicMock()
        mock_device.device_id = "CH-01"
        mock_device.name = "1#冷水机组"
        mock_device.type = "chiller"
        mock_device.system = "hvac"
        mock_device.status = "running"
        mock_device.health_score = 95
        mock_device.building = "A栋"
        mock_device.floor = "B1"
        mock_device.zone = "机房"
        mock_device.parameters = {"rated_capacity": 850}
        mock_device.updated_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_device
        mock_session.execute = AsyncMock(return_value=mock_result)

        server = DeviceMCPServer(mock_session)
        result = await server.call_tool(
            MCPToolCall(
                call_id="123",
                tool_name="get_device_status",
                arguments={"device_id": "CH-01"},
            )
        )

        assert result.success is True
        assert result.result["device_id"] == "CH-01"
        assert result.result["name"] == "1#冷水机组"
        assert result.result["status"] == "running"

    @pytest.mark.asyncio
    async def test_device_not_found(self):
        """测试设备不存在"""
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        server = DeviceMCPServer(mock_session)
        result = await server.call_tool(
            MCPToolCall(
                call_id="123",
                tool_name="get_device_status",
                arguments={"device_id": "INVALID"},
            )
        )

        assert result.success is False
        assert "not found" in result.error.lower()


class TestGetDeviceList:
    """get_device_list工具测试"""

    @pytest.mark.asyncio
    async def test_get_all_devices(self):
        """测试获取所有设备"""
        mock_session = MagicMock()
        mock_device = MagicMock()
        mock_device.device_id = "CH-01"
        mock_device.name = "1#冷水机组"
        mock_device.type = "chiller"
        mock_device.status = "running"
        mock_device.health_score = 95
        mock_device.building = "A栋"

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_device]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        server = DeviceMCPServer(mock_session)
        result = await server.call_tool(
            MCPToolCall(call_id="123", tool_name="get_device_list", arguments={})
        )

        assert result.success is True
        assert result.result["total"] == 1
        assert len(result.result["devices"]) == 1


class TestControlDevice:
    """control_device工具测试"""

    @pytest.mark.asyncio
    async def test_control_device_simulated(self):
        """测试设备控制（模拟）"""
        mock_session = MagicMock()
        server = DeviceMCPServer(mock_session)

        result = await server.call_tool(
            MCPToolCall(
                call_id="123",
                tool_name="control_device",
                arguments={"device_id": "CH-01", "action": "start"},
            )
        )

        assert result.success is True
        assert result.result["status"] == "simulated"
        assert "模拟" in result.result["message"]
