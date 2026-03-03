"""
Sprint 1 集成测试 — 端到端流水线

测试场景:
1. 决策校验管道端到端 (DecisionValidator full pipeline)
2. 实时事件流端到端 (RealtimeClient → EventDrivenCollector → WebSocket)
3. 联动场景 (机器人事件触发采集 + 决策校验)
"""
import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from realtime.models import RobotEventType, RobotRealtimeEvent
from realtime.realtime_client import RealtimeClient
from realtime.event_driven_collector import EventDrivenCollector
from realtime.websocket_endpoints import MonitoringWebSocketManager

from validation.decision_validator import DecisionValidator
from validation.base_validator import ValidationSeverity


# ============================================================
# 1. 决策校验管道 — 端到端集成测试
# ============================================================

class TestDecisionPipelineIntegration:
    """决策校验管道完整流程"""

    @pytest.fixture
    def validator(self):
        return DecisionValidator()

    @pytest.mark.asyncio
    async def test_valid_decision_passes_all_layers(self, validator):
        """合法决策通过 Schema→Reference→Constraint→Safety 全部层"""
        decision = {
            "action": "schedule",
            "assignments": [
                {
                    "robot_id": "robot-001",
                    "zone_id": "zone-3F-lobby",
                    "task_type": "standard",
                    "priority": 3,
                },
                {
                    "robot_id": "robot-002",
                    "zone_id": "zone-5F-office",
                    "task_type": "standard",
                    "priority": 1,
                },
            ],
        }
        context = {
            "known_robot_ids": ["robot-001", "robot-002", "robot-003"],
            "known_zone_ids": ["zone-3F-lobby", "zone-5F-office"],
            "robot_states": {
                "robot-001": {"battery_level": 80, "status": "idle"},
                "robot-002": {"battery_level": 65, "status": "idle"},
            },
            "closed_zones": [],
            "total_robots_in_building": 10,
        }
        result = await validator.validate(decision, context)
        assert result.valid
        assert len(result.errors) == 0
        assert len(result.validators_executed) >= 4

    @pytest.mark.asyncio
    async def test_invalid_schema_stops_with_errors(self, validator):
        """Schema层失败时产生错误"""
        decision = {
            "action": "fly_to_moon",  # 非法 action
            "assignments": [],
        }
        context = {}
        result = await validator.validate(decision, context)
        assert not result.valid
        assert any(e.validator == "schema" for e in result.errors)

    @pytest.mark.asyncio
    async def test_safety_catches_low_battery(self, validator):
        """Safety层捕获低电量机器人分配"""
        decision = {
            "action": "schedule",
            "assignments": [
                {
                    "robot_id": "robot-001",
                    "zone_id": "zone-3F-lobby",
                    "task_type": "standard",
                    "priority": 3,
                },
            ],
        }
        context = {
            "known_robot_ids": ["robot-001"],
            "known_zone_ids": ["zone-3F-lobby"],
            "robot_states": {
                "robot-001": {"battery_level": 3, "status": "idle"},
            },
            "closed_zones": [],
            "total_robots_in_building": 10,
        }
        result = await validator.validate(decision, context)
        assert not result.valid
        assert any("电量" in e.message or "battery" in e.message.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_safety_catches_duplicate_robot(self, validator):
        """Safety层捕获重复分配同一机器人"""
        decision = {
            "action": "schedule",
            "assignments": [
                {
                    "robot_id": "robot-001",
                    "zone_id": "zone-3F-lobby",
                    "task_type": "standard",
                    "priority": 3,
                },
                {
                    "robot_id": "robot-001",
                    "zone_id": "zone-5F-office",
                    "task_type": "standard",
                    "priority": 3,
                },
            ],
        }
        context = {
            "known_robot_ids": ["robot-001"],
            "known_zone_ids": ["zone-3F-lobby", "zone-5F-office"],
            "robot_states": {
                "robot-001": {"battery_level": 80, "status": "idle"},
            },
            "closed_zones": [],
            "total_robots_in_building": 10,
        }
        result = await validator.validate(decision, context)
        assert not result.valid
        assert any("多个任务" in e.message or "重复" in e.message for e in result.errors)

    @pytest.mark.asyncio
    async def test_safety_catches_error_status_robot(self, validator):
        """Safety层捕获故障状态机器人"""
        decision = {
            "action": "schedule",
            "assignments": [
                {
                    "robot_id": "robot-001",
                    "zone_id": "zone-3F-lobby",
                    "task_type": "standard",
                    "priority": 3,
                },
            ],
        }
        context = {
            "known_robot_ids": ["robot-001"],
            "known_zone_ids": ["zone-3F-lobby"],
            "robot_states": {
                "robot-001": {"battery_level": 80, "status": "error"},
            },
            "closed_zones": [],
            "total_robots_in_building": 10,
        }
        result = await validator.validate(decision, context)
        assert not result.valid
        assert any("错误状态" in e.message or "error" in e.message.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_safety_catches_closed_zone(self, validator):
        """Safety层捕获关闭区域"""
        decision = {
            "action": "schedule",
            "assignments": [
                {
                    "robot_id": "robot-001",
                    "zone_id": "zone-3F-lobby",
                    "task_type": "standard",
                    "priority": 3,
                },
            ],
        }
        context = {
            "known_robot_ids": ["robot-001"],
            "known_zone_ids": ["zone-3F-lobby"],
            "robot_states": {
                "robot-001": {"battery_level": 80, "status": "idle"},
            },
            "closed_zones": ["zone-3F-lobby"],
            "total_robots_in_building": 10,
        }
        result = await validator.validate(decision, context)
        assert not result.valid
        assert any("关闭" in e.message for e in result.errors)

    @pytest.mark.asyncio
    async def test_reference_catches_invalid_robot(self, validator):
        """Reference层捕获不存在的机器人"""
        decision = {
            "action": "schedule",
            "assignments": [
                {
                    "robot_id": "robot-999",
                    "zone_id": "zone-3F-lobby",
                    "task_type": "standard",
                    "priority": 3,
                },
            ],
        }
        context = {
            "known_robot_ids": ["robot-001", "robot-002"],
            "known_zone_ids": ["zone-3F-lobby"],
            "robot_states": {},
            "closed_zones": [],
            "total_robots_in_building": 10,
        }
        result = await validator.validate(decision, context)
        assert not result.valid
        assert any("robot-999" in e.message for e in result.errors)

    @pytest.mark.asyncio
    async def test_pipeline_timing(self, validator):
        """校验管道执行耗时 < 100ms"""
        decision = {
            "action": "schedule",
            "assignments": [
                {
                    "robot_id": "robot-001",
                    "zone_id": "zone-3F-lobby",
                    "task_type": "standard",
                    "priority": 3,
                },
            ],
        }
        context = {
            "known_robot_ids": ["robot-001"],
            "known_zone_ids": ["zone-3F-lobby"],
            "robot_states": {
                "robot-001": {"battery_level": 80, "status": "idle"},
            },
            "closed_zones": [],
            "total_robots_in_building": 10,
        }
        result = await validator.validate(decision, context)
        assert result.validation_duration_ms < 100


# ============================================================
# 2. 实时事件流 — 端到端集成测试
# ============================================================

class TestRealtimeEventFlowIntegration:
    """RealtimeClient → EventDrivenCollector → WebSocket 联动"""

    @pytest.fixture
    def realtime_client(self):
        return RealtimeClient(brand="gaoxian")

    @pytest.fixture
    def collector(self):
        return EventDrivenCollector()

    @pytest.fixture
    def ws_manager(self):
        return MonitoringWebSocketManager()

    @pytest.mark.asyncio
    async def test_event_flows_client_to_collector(self, realtime_client, collector):
        """事件从 RealtimeClient 流到 EventDrivenCollector"""
        await realtime_client.connect("robot-001")
        await realtime_client.subscribe(
            "robot-001",
            [RobotEventType.STATUS_CHANGED, RobotEventType.ERROR_OCCURRED],
            collector.on_robot_event,
        )

        event = RobotRealtimeEvent.create(
            "robot-001",
            RobotEventType.STATUS_CHANGED,
            {"old_status": "idle", "new_status": "working"},
        )
        await realtime_client.emit_event(event)

        assert collector.event_count == 1
        events = collector.get_collected_events(robot_id="robot-001")
        assert len(events) == 1
        assert events[0]["event_type"] == "robot.status.changed"

    @pytest.mark.asyncio
    async def test_error_event_triggers_alert_via_pipeline(self, realtime_client, collector):
        """错误事件通过管道触发告警"""
        alerts = []

        async def on_alert(alert):
            alerts.append(alert)

        collector.register_alert_callback(on_alert)

        await realtime_client.connect("robot-001")
        await realtime_client.subscribe(
            "robot-001",
            [RobotEventType.ERROR_OCCURRED],
            collector.on_robot_event,
        )

        event = RobotRealtimeEvent.create(
            "robot-001",
            RobotEventType.ERROR_OCCURRED,
            {"error_code": "MOTOR_STUCK", "message": "电机堵转"},
        )
        await realtime_client.emit_event(event)

        assert len(alerts) == 1
        assert alerts[0]["type"] == "robot_error"
        assert alerts[0]["error_code"] == "MOTOR_STUCK"

    @pytest.mark.asyncio
    async def test_battery_critical_triggers_alert(self, realtime_client, collector):
        """低电量事件通过管道触发告警"""
        alerts = []

        async def on_alert(alert):
            alerts.append(alert)

        collector.register_alert_callback(on_alert)

        await realtime_client.connect("robot-001")
        await realtime_client.subscribe(
            "robot-001",
            [RobotEventType.BATTERY_CRITICAL],
            collector.on_robot_event,
        )

        event = RobotRealtimeEvent.create(
            "robot-001",
            RobotEventType.BATTERY_CRITICAL,
            {"battery_level": 8, "estimated_remaining_minutes": 10},
        )
        await realtime_client.emit_event(event)

        assert len(alerts) == 1
        assert alerts[0]["type"] == "battery_critical"
        assert alerts[0]["battery_level"] == 8

    @pytest.mark.asyncio
    async def test_event_flows_to_websocket(self, realtime_client, collector, ws_manager):
        """完整链路: RealtimeClient → Collector → WebSocket"""
        ws_manager.register_robot("robot-001", "building-001")
        ws_conn = ws_manager.connect("building-001")

        async def combined_handler(evt):
            await collector.on_robot_event(evt)
            await ws_manager.broadcast_event(evt)

        await realtime_client.connect("robot-001")
        await realtime_client.subscribe(
            "robot-001",
            [RobotEventType.STATUS_CHANGED],
            combined_handler,
        )

        event = RobotRealtimeEvent.create(
            "robot-001",
            RobotEventType.STATUS_CHANGED,
            {"old_status": "idle", "new_status": "cleaning"},
        )
        await realtime_client.emit_event(event)

        assert collector.event_count == 1

        ws_event = await ws_conn.receive_event()
        assert ws_event is not None
        assert ws_event["type"] == "robot_event"
        assert ws_event["data"]["robot_id"] == "robot-001"
        assert ws_event["data"]["payload"]["new_status"] == "cleaning"

    @pytest.mark.asyncio
    async def test_disconnect_reconnect_preserves_events(self, realtime_client, collector):
        """断连重连后缓冲事件被正确投递"""
        await realtime_client.connect("robot-001")
        await realtime_client.subscribe(
            "robot-001",
            [RobotEventType.STATUS_CHANGED, RobotEventType.CONNECTIVITY_RESTORED],
            collector.on_robot_event,
        )

        await realtime_client.simulate_disconnect("robot-001")

        event = RobotRealtimeEvent.create(
            "robot-001",
            RobotEventType.STATUS_CHANGED,
            {"status": "charging"},
        )
        await realtime_client.emit_event(event)

        assert collector.event_count == 0

        await realtime_client.simulate_reconnect("robot-001")

        assert collector.event_count >= 1

    @pytest.mark.asyncio
    async def test_multiple_robots_multiple_collectors(self, realtime_client, ws_manager):
        """多机器人多采集器并发场景"""
        collector_a = EventDrivenCollector()
        collector_b = EventDrivenCollector()

        ws_manager.register_robot("robot-001", "building-001")
        ws_manager.register_robot("robot-002", "building-001")
        ws_conn = ws_manager.connect("building-001")

        await realtime_client.connect("robot-001")
        await realtime_client.connect("robot-002")

        async def handler_a(evt):
            await collector_a.on_robot_event(evt)
            await ws_manager.broadcast_event(evt)

        async def handler_b(evt):
            await collector_b.on_robot_event(evt)
            await ws_manager.broadcast_event(evt)

        await realtime_client.subscribe(
            "robot-001", [RobotEventType.STATUS_CHANGED], handler_a
        )
        await realtime_client.subscribe(
            "robot-002", [RobotEventType.TASK_COMPLETED], handler_b
        )

        e1 = RobotRealtimeEvent.create(
            "robot-001", RobotEventType.STATUS_CHANGED, {"new_status": "working"}
        )
        await realtime_client.emit_event(e1)

        e2 = RobotRealtimeEvent.create(
            "robot-002", RobotEventType.TASK_COMPLETED, {"task_id": "t-001"}
        )
        await realtime_client.emit_event(e2)

        assert collector_a.event_count == 1
        assert collector_b.event_count == 1

        ws_evt1 = await ws_conn.receive_event()
        ws_evt2 = await ws_conn.receive_event()
        assert ws_evt1 is not None
        assert ws_evt2 is not None


# ============================================================
# 3. 联动场景 — 实时事件触发决策校验
# ============================================================

class TestRealtimeDecisionIntegration:
    """实时事件触发决策校验的联动场景"""

    @pytest.mark.asyncio
    async def test_robot_error_triggers_revalidation(self):
        """
        场景: 机器人故障 → 采集告警 → 重新校验当前调度方案
        """
        client = RealtimeClient(brand="gaoxian")
        collector = EventDrivenCollector()
        validator = DecisionValidator()

        error_alerts = []
        revalidation_results = []

        async def on_error_alert(alert):
            error_alerts.append(alert)
            current_decision = {
                "action": "schedule",
                "assignments": [
                    {
                        "robot_id": alert["robot_id"],
                        "zone_id": "zone-3F-lobby",
                        "task_type": "standard",
                        "priority": 3,
                    },
                ],
            }
            context = {
                "known_robot_ids": [alert["robot_id"]],
                "known_zone_ids": ["zone-3F-lobby"],
                "robot_states": {
                    alert["robot_id"]: {"battery_level": 80, "status": "error"},
                },
                "closed_zones": [],
                "total_robots_in_building": 10,
            }
            result = await validator.validate(current_decision, context)
            revalidation_results.append(result)

        collector.register_alert_callback(on_error_alert)

        await client.connect("robot-001")
        await client.subscribe(
            "robot-001",
            [RobotEventType.ERROR_OCCURRED],
            collector.on_robot_event,
        )

        event = RobotRealtimeEvent.create(
            "robot-001",
            RobotEventType.ERROR_OCCURRED,
            {"error_code": "MOTOR_STUCK", "message": "电机堵转"},
        )
        await client.emit_event(event)

        assert len(error_alerts) == 1
        assert len(revalidation_results) == 1
        assert not revalidation_results[0].valid
        assert any(
            "错误状态" in e.message or "error" in e.message.lower()
            for e in revalidation_results[0].errors
        )

        await client.close()

    @pytest.mark.asyncio
    async def test_battery_critical_blocks_new_tasks(self):
        """
        场景: 低电量事件 → 采集告警 → 校验新任务分配被阻止
        """
        client = RealtimeClient(brand="ecovacs")
        collector = EventDrivenCollector()
        validator = DecisionValidator()

        async def on_battery_alert(alert):
            decision = {
                "action": "schedule",
                "assignments": [
                    {
                        "robot_id": alert["robot_id"],
                        "zone_id": "zone-1F-entrance",
                        "task_type": "standard",
                        "priority": 3,
                    },
                ],
            }
            context = {
                "known_robot_ids": [alert["robot_id"]],
                "known_zone_ids": ["zone-1F-entrance"],
                "robot_states": {
                    alert["robot_id"]: {
                        "battery_level": alert["battery_level"],
                        "status": "idle",
                    },
                },
                "closed_zones": [],
                "total_robots_in_building": 10,
            }
            result = await validator.validate(decision, context)
            assert not result.valid, "低电量机器人不应通过校验"

        collector.register_alert_callback(on_battery_alert)

        await client.connect("robot-002")
        await client.subscribe(
            "robot-002",
            [RobotEventType.BATTERY_CRITICAL],
            collector.on_robot_event,
        )

        event = RobotRealtimeEvent.create(
            "robot-002",
            RobotEventType.BATTERY_CRITICAL,
            {"battery_level": 3, "estimated_remaining_minutes": 5},
        )
        await client.emit_event(event)

        await client.close()

    @pytest.mark.asyncio
    async def test_full_pipeline_20_robots(self):
        """
        压力场景: 20台机器人同时事件 → 采集 → 校验
        模拟 Tower C 生产环境规模
        """
        client = RealtimeClient(brand="gaoxian")
        collector = EventDrivenCollector()
        ws_manager = MonitoringWebSocketManager()

        for i in range(20):
            robot_id = f"robot-{i:03d}"
            ws_manager.register_robot(robot_id, "building-tower-c")
            await client.connect(robot_id)

        ws_conn = ws_manager.connect("building-tower-c")

        async def pipeline_handler(evt):
            await collector.on_robot_event(evt)
            await ws_manager.broadcast_event(evt)

        for i in range(20):
            robot_id = f"robot-{i:03d}"
            await client.subscribe(
                robot_id,
                [RobotEventType.STATUS_CHANGED],
                pipeline_handler,
            )

        for i in range(20):
            event = RobotRealtimeEvent.create(
                f"robot-{i:03d}",
                RobotEventType.STATUS_CHANGED,
                {"new_status": "cleaning", "zone": f"zone-{i+1}F"},
            )
            await client.emit_event(event)

        assert collector.event_count == 20

        ws_events = []
        for _ in range(20):
            evt = await ws_conn.receive_event()
            if evt:
                ws_events.append(evt)
        assert len(ws_events) == 20

        await client.close()

    @pytest.mark.asyncio
    async def test_concurrent_validation_after_events(self):
        """
        场景: 多台机器人同时故障 → 批量重校验
        """
        client = RealtimeClient(brand="gaoxian")
        collector = EventDrivenCollector()
        validator = DecisionValidator()

        validation_results = []

        async def on_alert(alert):
            decision = {
                "action": "schedule",
                "assignments": [
                    {
                        "robot_id": alert["robot_id"],
                        "zone_id": "zone-1F",
                        "task_type": "standard",
                        "priority": 3,
                    }
                ],
            }
            context = {
                "known_robot_ids": [alert["robot_id"]],
                "known_zone_ids": ["zone-1F"],
                "robot_states": {
                    alert["robot_id"]: {"battery_level": 80, "status": "error"},
                },
                "closed_zones": [],
                "total_robots_in_building": 20,
            }
            result = await validator.validate(decision, context)
            validation_results.append(result)

        collector.register_alert_callback(on_alert)

        for i in range(5):
            robot_id = f"robot-{i:03d}"
            await client.connect(robot_id)
            await client.subscribe(
                robot_id,
                [RobotEventType.ERROR_OCCURRED],
                collector.on_robot_event,
            )

        for i in range(5):
            event = RobotRealtimeEvent.create(
                f"robot-{i:03d}",
                RobotEventType.ERROR_OCCURRED,
                {"error_code": "SENSOR_FAULT", "message": "传感器异常"},
            )
            await client.emit_event(event)

        assert len(validation_results) == 5
        assert all(not r.valid for r in validation_results)

        await client.close()
