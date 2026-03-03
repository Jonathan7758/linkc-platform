"""
Tests for A1 实时事件通道 — RealtimeClient + EventDrivenCollector
"""
import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from realtime.models import RobotEventType, RobotRealtimeEvent, ConnectionStatus
from realtime.realtime_client import RealtimeClient
from realtime.event_driven_collector import EventDrivenCollector


# ============================================================
# RealtimeClient Tests
# ============================================================

class TestRealtimeClient:
    """实时客户端测试"""

    @pytest.fixture
    def client(self):
        return RealtimeClient(brand="gaoxian")

    @pytest.mark.asyncio
    async def test_connect_success(self, client):
        result = await client.connect("robot-001")
        assert result is True
        assert "robot-001" in client.connected_robots

    @pytest.mark.asyncio
    async def test_connect_duplicate(self, client):
        await client.connect("robot-001")
        result = await client.connect("robot-001")
        assert result is True  # 幂等

    @pytest.mark.asyncio
    async def test_disconnect(self, client):
        await client.connect("robot-001")
        result = await client.disconnect("robot-001")
        assert result is True
        assert "robot-001" not in client.connected_robots

    @pytest.mark.asyncio
    async def test_disconnect_not_connected(self, client):
        result = await client.disconnect("robot-999")
        assert result is False

    @pytest.mark.asyncio
    async def test_subscribe_and_receive(self, client):
        received_events = []

        async def on_event(evt):
            received_events.append(evt)

        await client.connect("robot-001")
        sub_id = await client.subscribe(
            "robot-001", [RobotEventType.STATUS_CHANGED], on_event
        )
        assert sub_id.startswith("sub-")

        # 发送事件
        event = RobotRealtimeEvent.create(
            "robot-001",
            RobotEventType.STATUS_CHANGED,
            {"old_status": "idle", "new_status": "working"},
        )
        await client.emit_event(event)

        assert len(received_events) == 1
        assert received_events[0].event_type == RobotEventType.STATUS_CHANGED
        assert received_events[0].data["new_status"] == "working"

    @pytest.mark.asyncio
    async def test_subscribe_filters_event_types(self, client):
        received = []

        async def on_event(evt):
            received.append(evt)

        await client.connect("robot-001")
        await client.subscribe(
            "robot-001", [RobotEventType.STATUS_CHANGED], on_event
        )

        # 发送不匹配的事件
        event = RobotRealtimeEvent.create(
            "robot-001", RobotEventType.POSITION_UPDATE, {"x": 1, "y": 2}
        )
        await client.emit_event(event)

        assert len(received) == 0  # 不应收到

    @pytest.mark.asyncio
    async def test_subscribe_not_connected_raises(self, client):
        async def on_event(evt):
            pass

        with pytest.raises(ValueError, match="not connected"):
            await client.subscribe("robot-999", [RobotEventType.STATUS_CHANGED], on_event)

    @pytest.mark.asyncio
    async def test_unsubscribe(self, client):
        received = []

        async def on_event(evt):
            received.append(evt)

        await client.connect("robot-001")
        sub_id = await client.subscribe(
            "robot-001", [RobotEventType.STATUS_CHANGED], on_event
        )
        await client.unsubscribe(sub_id)

        event = RobotRealtimeEvent.create(
            "robot-001", RobotEventType.STATUS_CHANGED, {}
        )
        await client.emit_event(event)

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_connection_status(self, client):
        await client.connect("robot-001")
        status = await client.get_connection_status("robot-001")
        assert status["connected"] is True
        assert status["reconnect_count"] == 0

    @pytest.mark.asyncio
    async def test_connection_status_not_connected(self, client):
        status = await client.get_connection_status("robot-999")
        assert status["connected"] is False

    @pytest.mark.asyncio
    async def test_simulate_disconnect_reconnect(self, client):
        received = []

        async def on_event(evt):
            received.append(evt)

        await client.connect("robot-001")
        await client.subscribe(
            "robot-001",
            [RobotEventType.STATUS_CHANGED, RobotEventType.CONNECTIVITY_RESTORED],
            on_event,
        )

        # 模拟断连
        await client.simulate_disconnect("robot-001")
        assert "robot-001" not in client.connected_robots

        # 断连期间发送事件 → 缓冲
        event = RobotRealtimeEvent.create(
            "robot-001", RobotEventType.STATUS_CHANGED, {"status": "charging"}
        )
        await client.emit_event(event)

        # 此时不应收到事件
        assert len(received) == 0

        # 模拟重连
        await client.simulate_reconnect("robot-001")
        assert "robot-001" in client.connected_robots

        # 重连后应收到缓冲事件 + 重连事件
        assert len(received) >= 1

    @pytest.mark.asyncio
    async def test_multiple_robots(self, client):
        await client.connect("robot-001")
        await client.connect("robot-002")
        assert len(client.connected_robots) == 2

        await client.disconnect("robot-001")
        assert len(client.connected_robots) == 1
        assert "robot-002" in client.connected_robots

    @pytest.mark.asyncio
    async def test_close(self, client):
        await client.connect("robot-001")
        await client.connect("robot-002")
        await client.close()
        assert len(client.connected_robots) == 0

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, client):
        received_a = []
        received_b = []

        async def on_a(evt):
            received_a.append(evt)

        async def on_b(evt):
            received_b.append(evt)

        await client.connect("robot-001")
        await client.subscribe("robot-001", [RobotEventType.STATUS_CHANGED], on_a)
        await client.subscribe("robot-001", [RobotEventType.STATUS_CHANGED], on_b)

        event = RobotRealtimeEvent.create(
            "robot-001", RobotEventType.STATUS_CHANGED, {}
        )
        await client.emit_event(event)

        assert len(received_a) == 1
        assert len(received_b) == 1


# ============================================================
# EventDrivenCollector Tests
# ============================================================

class TestEventDrivenCollector:
    """事件驱动采集器测试"""

    @pytest.fixture
    def collector(self):
        return EventDrivenCollector()

    @pytest.mark.asyncio
    async def test_collect_event(self, collector):
        event = RobotRealtimeEvent.create(
            "robot-001", RobotEventType.STATUS_CHANGED, {"new_status": "working"}
        )
        await collector.on_robot_event(event)

        assert collector.event_count == 1
        events = collector.get_collected_events(robot_id="robot-001")
        assert len(events) == 1
        assert events[0]["event_type"] == "robot.status.changed"

    @pytest.mark.asyncio
    async def test_battery_critical_triggers_alert(self, collector):
        alerts = []

        async def on_alert(alert):
            alerts.append(alert)

        collector.register_alert_callback(on_alert)

        event = RobotRealtimeEvent.create(
            "robot-001",
            RobotEventType.BATTERY_CRITICAL,
            {"battery_level": 12, "estimated_remaining_minutes": 15},
        )
        await collector.on_robot_event(event)

        assert len(alerts) == 1
        assert alerts[0]["type"] == "battery_critical"
        assert alerts[0]["battery_level"] == 12

    @pytest.mark.asyncio
    async def test_error_triggers_alert(self, collector):
        alerts = []

        async def on_alert(alert):
            alerts.append(alert)

        collector.register_alert_callback(on_alert)

        event = RobotRealtimeEvent.create(
            "robot-001",
            RobotEventType.ERROR_OCCURRED,
            {"error_code": "E001", "message": "前方障碍物无法绕行"},
        )
        await collector.on_robot_event(event)

        assert len(alerts) == 1
        assert alerts[0]["type"] == "robot_error"
        assert alerts[0]["error_code"] == "E001"

    @pytest.mark.asyncio
    async def test_threshold_breach(self, collector):
        alerts = []

        async def on_alert(alert):
            alerts.append(alert)

        collector.register_alert_callback(on_alert)

        await collector.on_threshold_breach("temperature", 85.0, "robot-001")

        assert len(alerts) == 1
        assert alerts[0]["type"] == "threshold_breach"
        assert alerts[0]["metric"] == "temperature"
        assert alerts[0]["value"] == 85.0

    @pytest.mark.asyncio
    async def test_custom_handler(self, collector):
        handled = []

        async def custom_handler(event):
            handled.append(event)

        collector.register_handler(RobotEventType.TASK_COMPLETED, custom_handler)

        event = RobotRealtimeEvent.create(
            "robot-001",
            RobotEventType.TASK_COMPLETED,
            {"task_id": "t-001", "duration_minutes": 25},
        )
        await collector.on_robot_event(event)

        assert len(handled) == 1

    @pytest.mark.asyncio
    async def test_filter_events_by_robot(self, collector):
        for i in range(3):
            event = RobotRealtimeEvent.create(
                f"robot-{i:03d}",
                RobotEventType.STATUS_CHANGED,
                {"status": "working"},
            )
            await collector.on_robot_event(event)

        events = collector.get_collected_events(robot_id="robot-001")
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_filter_events_by_type(self, collector):
        e1 = RobotRealtimeEvent.create("robot-001", RobotEventType.STATUS_CHANGED, {})
        e2 = RobotRealtimeEvent.create("robot-001", RobotEventType.BATTERY_UPDATE, {})
        await collector.on_robot_event(e1)
        await collector.on_robot_event(e2)

        events = collector.get_collected_events(event_type="robot.status.changed")
        assert len(events) == 1


# ============================================================
# RobotRealtimeEvent Model Tests
# ============================================================

class TestRobotRealtimeEvent:
    def test_create_event(self):
        event = RobotRealtimeEvent.create(
            "robot-001", RobotEventType.STATUS_CHANGED, {"new_status": "working"}
        )
        assert event.robot_id == "robot-001"
        assert event.event_type == RobotEventType.STATUS_CHANGED
        assert event.event_id.startswith("evt-")
        assert event.data["new_status"] == "working"

    def test_event_type_values(self):
        assert RobotEventType.STATUS_CHANGED.value == "robot.status.changed"
        assert RobotEventType.BATTERY_CRITICAL.value == "robot.battery.critical"
        assert RobotEventType.ERROR_OCCURRED.value == "robot.error.occurred"
        assert RobotEventType.CONNECTIVITY_LOST.value == "robot.connectivity.lost"
