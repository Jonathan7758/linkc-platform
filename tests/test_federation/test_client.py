"""
Federation Client Tests
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestFederationClient:
    """FederationClient 测试"""

    def test_initial_state(self):
        """初始状态测试"""
        from src.federation.client import FederationClient

        client = FederationClient(
            gateway_url="http://localhost:8100",
            system_id="test-system"
        )

        assert client.is_connected is False
        assert client.system_id == "test-system"
        assert len(client.registered_agents) == 0

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """连接成功测试"""
        from src.federation.client import FederationClient

        client = FederationClient(
            gateway_url="http://localhost:8100",
            system_id="test-system"
        )

        with patch.object(client, "_client") as mock_http:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"token": "test-token"}
            mock_http.post = AsyncMock(return_value=mock_response)

            # Mock the AsyncClient
            with patch("httpx.AsyncClient") as MockClient:
                mock_instance = MagicMock()
                mock_instance.post = AsyncMock(return_value=mock_response)
                MockClient.return_value = mock_instance

                result = await client.connect()
                # Note: This test may need adjustment based on actual implementation

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """断开连接测试"""
        from src.federation.client import FederationClient

        client = FederationClient(
            gateway_url="http://localhost:8100",
            system_id="test-system"
        )

        await client.disconnect()
        assert client.is_connected is False

    def test_config_defaults(self):
        """配置默认值测试"""
        from src.federation.client import FederationClient

        client = FederationClient(
            gateway_url="http://localhost:8100",
            system_id="test-system"
        )

        assert client.config.system_type == "property-service"
        assert client.config.display_name == "ECIS Service Robot"
        assert client.config.reconnect_interval == 30
        assert client.config.heartbeat_interval == 30


class TestFederationEvents:
    """Federation Events 测试"""

    def test_event_types(self):
        """事件类型常量测试"""
        from src.federation.events import EventTypes

        assert EventTypes.TASK_STARTED == "ecis.task.started"
        assert EventTypes.TASK_COMPLETED == "ecis.task.completed"
        assert EventTypes.ROBOT_STATUS_CHANGED == "ecis.robot.status.changed"

    @pytest.mark.asyncio
    async def test_event_publisher_build_event(self):
        """事件构建测试"""
        from src.federation.events import EventPublisher

        mock_client = MagicMock()
        mock_client.is_connected = False

        publisher = EventPublisher(mock_client, "test-system")

        event = publisher._build_event(
            "ecis.task.started",
            {"task_id": "task-123"},
            subject="task-123"
        )

        assert event["type"] == "ecis.task.started"
        assert event["source"] == "ecis://test-system"
        assert event["data"]["task_id"] == "task-123"
        assert event["subject"] == "task-123"
