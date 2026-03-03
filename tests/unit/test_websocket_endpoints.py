"""
Tests for G4 WebSocket/SSE — MonitoringWebSocketManager
"""
import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from realtime.models import RobotEventType, RobotRealtimeEvent
from realtime.websocket_endpoints import (
    WebSocketConnection,
    MonitoringWebSocketManager,
)


class TestWebSocketConnection:
    """WebSocket 连接状态管理测试"""

    def test_create_connection(self):
        conn = WebSocketConnection("ws-001", "building-001")
        assert conn.connection_id == "ws-001"
        assert conn.building_id == "building-001"
        assert not conn.is_closed
        assert len(conn.subscribed_event_types) == 0

    @pytest.mark.asyncio
    async def test_send_event_no_filter(self):
        conn = WebSocketConnection("ws-001", "building-001")
        event_data = {
            "type": "robot_event",
            "event_type": "robot.status.changed",
            "data": {"robot_id": "r-001"},
        }
        result = await conn.send_event(event_data)
        assert result is True

        received = await conn.receive_event()
        assert received["event_type"] == "robot.status.changed"

    @pytest.mark.asyncio
    async def test_send_event_filtered_pass(self):
        conn = WebSocketConnection("ws-001", "building-001")
        conn.subscribed_event_types = {"robot.status.changed"}

        event_data = {"event_type": "robot.status.changed", "data": {}}
        result = await conn.send_event(event_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_send_event_filtered_reject(self):
        conn = WebSocketConnection("ws-001", "building-001")
        conn.subscribed_event_types = {"robot.status.changed"}

        event_data = {"event_type": "robot.battery.update", "data": {}}
        result = await conn.send_event(event_data)
        assert result is False

    @pytest.mark.asyncio
    async def test_send_to_closed_connection(self):
        conn = WebSocketConnection("ws-001", "building-001")
        conn.close()
        result = await conn.send_event({"event_type": "test", "data": {}})
        assert result is False

    def test_handle_subscribe_message(self):
        conn = WebSocketConnection("ws-001", "building-001")
        conn.handle_client_message({
            "type": "subscribe",
            "event_types": ["robot.status.changed", "robot.error.occurred"],
        })
        assert "robot.status.changed" in conn.subscribed_event_types
        assert "robot.error.occurred" in conn.subscribed_event_types

    def test_handle_unsubscribe_message(self):
        conn = WebSocketConnection("ws-001", "building-001")
        conn.subscribed_event_types = {
            "robot.status.changed",
            "robot.error.occurred",
        }
        conn.handle_client_message({
            "type": "unsubscribe",
            "event_types": ["robot.status.changed"],
        })
        assert "robot.status.changed" not in conn.subscribed_event_types
        assert "robot.error.occurred" in conn.subscribed_event_types

    def test_handle_ping_message(self):
        conn = WebSocketConnection("ws-001", "building-001")
        conn.handle_client_message({"type": "ping"})
        # should not raise


class TestMonitoringWebSocketManager:
    """WebSocket 管理器测试"""

    @pytest.fixture
    def manager(self):
        return MonitoringWebSocketManager()

    def test_connect_creates_connection(self, manager):
        conn = manager.connect("building-001")
        assert conn is not None
        assert conn.building_id == "building-001"
        assert manager.get_connection_count("building-001") == 1

    def test_connect_multiple_clients(self, manager):
        conn1 = manager.connect("building-001")
        conn2 = manager.connect("building-001")
        assert conn1.connection_id != conn2.connection_id
        assert manager.get_connection_count("building-001") == 2

    def test_connect_different_buildings(self, manager):
        manager.connect("building-001")
        manager.connect("building-002")
        assert manager.get_connection_count() == 2
        assert manager.get_connection_count("building-001") == 1
        assert manager.get_connection_count("building-002") == 1

    def test_disconnect(self, manager):
        conn = manager.connect("building-001")
        manager.disconnect(conn)
        assert manager.get_connection_count("building-001") == 0
        assert conn.is_closed

    @pytest.mark.asyncio
    async def test_broadcast_to_building(self, manager):
        manager.register_robot("robot-001", "building-001")
        conn1 = manager.connect("building-001")
        conn2 = manager.connect("building-002")

        event = RobotRealtimeEvent.create(
            "robot-001",
            RobotEventType.STATUS_CHANGED,
            {"old_status": "idle", "new_status": "working"},
        )
        sent = await manager.broadcast_event(event)
        assert sent == 1  # 只发到 building-001

        received = await conn1.receive_event()
        assert received["type"] == "robot_event"
        assert received["data"]["robot_id"] == "robot-001"
        assert received["data"]["event_type"] == "robot.status.changed"
        assert received["data"]["payload"]["new_status"] == "working"

    @pytest.mark.asyncio
    async def test_broadcast_unregistered_robot_goes_to_all(self, manager):
        conn1 = manager.connect("building-001")
        conn2 = manager.connect("building-002")

        event = RobotRealtimeEvent.create(
            "robot-unknown", RobotEventType.ERROR_OCCURRED, {"error_code": "E999"}
        )
        sent = await manager.broadcast_event(event)
        assert sent == 2  # 广播到所有

    @pytest.mark.asyncio
    async def test_broadcast_respects_client_filters(self, manager):
        manager.register_robot("robot-001", "building-001")

        conn = manager.connect("building-001")
        conn.handle_client_message({
            "type": "subscribe",
            "event_types": ["robot.error.occurred"],
        })

        # 发送 status_changed 事件 — 应被过滤
        event1 = RobotRealtimeEvent.create(
            "robot-001", RobotEventType.STATUS_CHANGED, {}
        )
        sent = await manager.broadcast_event(event1)
        assert sent == 0

        # 发送 error 事件 — 应通过
        event2 = RobotRealtimeEvent.create(
            "robot-001", RobotEventType.ERROR_OCCURRED, {"error_code": "E001"}
        )
        sent = await manager.broadcast_event(event2)
        assert sent == 1

    @pytest.mark.asyncio
    async def test_broadcast_to_building_direct(self, manager):
        conn = manager.connect("building-001")
        event_data = {
            "type": "system_alert",
            "event_type": "",
            "message": "maintenance scheduled",
        }
        sent = await manager.broadcast_to_building("building-001", event_data)
        assert sent == 1

    def test_get_all_connections(self, manager):
        manager.connect("building-001")
        manager.connect("building-001")
        manager.connect("building-002")

        all_conns = manager.get_all_connections()
        assert len(all_conns) == 3

        b1_conns = manager.get_all_connections("building-001")
        assert len(b1_conns) == 2

    def test_register_robot(self, manager):
        manager.register_robot("robot-001", "building-001")
        manager.register_robot("robot-002", "building-001")
        manager.register_robot("robot-003", "building-002")
        assert manager._robot_building_map["robot-001"] == "building-001"
        assert manager._robot_building_map["robot-003"] == "building-002"
