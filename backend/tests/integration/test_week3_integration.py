"""Week 3 集成测试

测试告警、能耗、工单、报表模块的完整流程。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from app.mcp_servers.alarm_mcp import AlarmMCPServer
from app.mcp_servers.energy_mcp import EnergyMCPServer
from app.mcp_servers.ticket_mcp import TicketMCPServer
from app.mcp_servers.report_mcp import ReportMCPServer
from app.agents.alarm_agent import AlarmAgent, AlarmAgentConfig
from app.agents.energy_agent import EnergyAgent, EnergyAgentConfig
from app.agents.base_agent import AgentContext
from app.models.alarm import AlarmStatus


class TestAlarmWorkflow:
    """告警处理完整流程测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def alarm_mcp(self, mock_db):
        return AlarmMCPServer(mock_db)

    @pytest.fixture
    def ticket_mcp(self, mock_db):
        return TicketMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_alarm_to_ticket_flow(self, alarm_mcp, ticket_mcp, mock_db):
        """测试告警触发工单的流程"""
        # 1. 模拟获取告警
        alarm = MagicMock()
        alarm.alarm_id = "ALM-001"
        alarm.title = "空调温度过高"
        alarm.severity = "warning"
        alarm.status = "active"
        alarm.device_id = "DEV-HVAC-001"
        alarm.category = "threshold"
        alarm.description = "3楼空调出风温度超过设定值"
        alarm.trigger_value = 30.5
        alarm.threshold_value = 28.0
        alarm.trigger_parameter = "temperature"
        alarm.triggered_at = datetime.now(timezone.utc)
        alarm.acknowledged_at = None
        alarm.resolved_at = None
        alarm.acknowledged_by = None
        alarm.resolved_by = None
        alarm.resolution_notes = None

        # 模拟设备
        device = MagicMock()
        device.device_id = "DEV-HVAC-001"
        device.name = "3楼空调机组"
        device.device_type = "hvac"
        device.location = "A栋3楼"

        mock_alarm_result = MagicMock()
        mock_alarm_result.scalar_one_or_none.return_value = alarm

        mock_device_result = MagicMock()
        mock_device_result.scalar_one_or_none.return_value = device

        mock_db.execute = AsyncMock(side_effect=[mock_alarm_result, mock_device_result])

        # 获取告警详情
        detail_result = await alarm_mcp._get_alarm_detail({"alarm_id": "ALM-001"})
        # 实际格式：成功时返回告警数据直接包含alarm_id等字段
        assert "alarm_id" in detail_result
        assert detail_result["severity"] == "warning"

        # 2. 根据告警创建工单
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        ticket_result = await ticket_mcp._create_ticket({
            "title": f"处理告警: {alarm.title}",
            "description": alarm.description,
            "type": "repair",
            "priority": "high",
            "device_id": alarm.device_id,
            "alarm_id": alarm.alarm_id,
        })

        assert ticket_result["success"] is True
        assert ticket_result["ticket_id"].startswith("TKT-")

    @pytest.mark.asyncio
    async def test_alarm_acknowledge_and_resolve(self, alarm_mcp, mock_db):
        """测试告警确认和解决流程"""
        # 模拟告警
        alarm = MagicMock()
        alarm.alarm_id = "ALM-002"
        alarm.status = AlarmStatus.ACTIVE.value
        alarm.acknowledged_at = None
        alarm.resolved_at = None
        alarm.acknowledged_by = None
        alarm.resolved_by = None
        alarm.resolution_notes = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = alarm
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        # 1. 确认告警
        ack_result = await alarm_mcp._acknowledge_alarm({
            "alarm_id": "ALM-002",
            "comment": "已知晓，正在处理"
        })
        # 实际格式：成功时返回 {"alarm_id": ..., "status": "acknowledged", "message": ...}
        assert ack_result["status"] == "acknowledged"
        assert "alarm_id" in ack_result

        # 2. 更新状态为已确认
        alarm.status = AlarmStatus.ACKNOWLEDGED.value
        alarm.acknowledged_at = datetime.now(timezone.utc)

        # 3. 解决告警
        resolve_result = await alarm_mcp._resolve_alarm({
            "alarm_id": "ALM-002",
            "resolution": "已更换滤网，温度恢复正常"
        })
        # 实际格式：成功时返回 {"alarm_id": ..., "status": "resolved", "resolution": ...}
        assert resolve_result["status"] == "resolved"


class TestEnergyAnalysisWorkflow:
    """能耗分析完整流程测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def energy_mcp(self, mock_db):
        return EnergyMCPServer(mock_db)

    @pytest.fixture
    def report_mcp(self, mock_db):
        return ReportMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_energy_monitoring_flow(self, energy_mcp, mock_db):
        """测试能耗监控流程"""
        # 模拟能耗数据
        readings = []
        for i in range(10):
            reading = MagicMock()
            reading.meter_id = f"MTR-{i:03d}"
            reading.energy_type = "electricity"
            reading.value = 100.0 + i * 10
            reading.unit = "kWh"
            reading.building = "A栋" if i < 5 else "B栋"
            reading.timestamp = datetime.now(timezone.utc) - timedelta(hours=i)
            readings.append(reading)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = readings
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        # 1. 获取能耗数据
        consumption = await energy_mcp._get_energy_consumption({
            "energy_type": "electricity",
            "hours": 24
        })

        assert consumption["total_readings"] == 10
        assert consumption["total_consumption"] > 0

        # 2. 检测异常
        anomaly = await energy_mcp._get_energy_anomaly({
            "threshold": 1.5,
            "hours": 24
        })

        assert "anomaly_count" in anomaly
        assert "averages" in anomaly

    @pytest.mark.asyncio
    async def test_energy_comparison_flow(self, energy_mcp, mock_db):
        """测试能耗对比流程"""
        # 模拟当前期和对比期数据
        mock_current = MagicMock()
        mock_current.scalar.return_value = 1500.0

        mock_previous = MagicMock()
        mock_previous.scalar.return_value = 1200.0

        mock_db.execute = AsyncMock(side_effect=[mock_current, mock_previous])

        # 获取环比数据
        comparison = await energy_mcp._get_energy_comparison({
            "energy_type": "electricity",
            "compare_type": "mom"
        })

        assert comparison["current_period"]["value"] == 1500.0
        assert comparison["previous_period"]["value"] == 1200.0
        assert comparison["change_rate"] == 25.0
        assert comparison["trend"] == "up"


class TestTicketWorkflow:
    """工单处理完整流程测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def ticket_mcp(self, mock_db):
        return TicketMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_ticket_lifecycle(self, ticket_mcp, mock_db):
        """测试工单全生命周期"""
        # 1. 创建工单
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        create_result = await ticket_mcp._create_ticket({
            "title": "空调维修",
            "description": "A栋3楼空调不制冷",
            "type": "repair",
            "priority": "high",
        })
        assert create_result["success"] is True
        ticket_id = create_result["ticket_id"]

        # 2. 分配工单
        ticket = MagicMock()
        ticket.ticket_id = ticket_id
        ticket.status = "pending"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ticket
        mock_db.execute = AsyncMock(return_value=mock_result)

        assign_result = await ticket_mcp._assign_ticket({
            "ticket_id": ticket_id,
            "assigned_to": "张工"
        })
        assert assign_result["success"] is True

        # 3. 开始处理
        ticket.status = "assigned"
        ticket.started_at = None
        ticket.completed_at = None
        ticket.work_notes = None

        start_result = await ticket_mcp._update_ticket_status({
            "ticket_id": ticket_id,
            "status": "in_progress",
            "work_notes": "开始检修"
        })
        assert start_result["success"] is True

        # 4. 完成工单
        ticket.status = "in_progress"
        ticket.started_at = datetime.now(timezone.utc) - timedelta(hours=2)

        complete_result = await ticket_mcp._update_ticket_status({
            "ticket_id": ticket_id,
            "status": "completed",
            "work_notes": "已更换压缩机，测试正常"
        })
        assert complete_result["success"] is True


class TestReportGeneration:
    """报表生成测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def report_mcp(self, mock_db):
        return ReportMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_daily_report_generation(self, report_mcp, mock_db):
        """测试日报生成"""
        # 模拟能耗数据
        reading = MagicMock()
        reading.energy_type = "electricity"
        reading.value = 100.0
        reading.building = "A栋"

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [reading]
        mock_result1 = MagicMock()
        mock_result1.scalars.return_value = mock_scalars

        mock_result2 = MagicMock()
        mock_result2.scalar.return_value = 90.0  # 去年同期

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        # 生成能耗日报
        report = await report_mcp._generate_energy_report({
            "report_type": "daily",
            "energy_type": "electricity"
        })

        assert report["report_type"] == "daily"
        assert "summary" in report
        assert "breakdown" in report

    @pytest.mark.asyncio
    async def test_operations_report_aggregation(self, report_mcp, mock_db):
        """测试综合运营报表汇总"""
        # 模拟各项数据
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_result.scalar.return_value = 0

        mock_db.execute = AsyncMock(return_value=mock_result)

        # 生成综合报表
        report = await report_mcp._generate_operations_report({
            "report_type": "daily"
        })

        assert "key_metrics" in report
        assert "energy" in report["key_metrics"]
        assert "alarms" in report["key_metrics"]
        assert "tickets" in report["key_metrics"]


class TestAgentMCPIntegration:
    """Agent与MCP集成测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def alarm_agent(self, mock_db):
        config = AlarmAgentConfig(name="test_alarm_agent")
        agent = AlarmAgent(config)
        return agent, mock_db

    @pytest.fixture
    def energy_agent(self, mock_db):
        config = EnergyAgentConfig(name="test_energy_agent")
        agent = EnergyAgent(config)
        return agent, mock_db

    @pytest.mark.asyncio
    async def test_alarm_agent_with_mcp(self, alarm_agent):
        """测试告警Agent调用MCP"""
        agent, mock_db = alarm_agent

        # Mock _execute_tool 方法以模拟MCP调用
        agent._execute_tool = AsyncMock(return_value={
            "success": True,
            "result": {
                "total": 10,
                "stats": {
                    "critical": 2,
                    "warning": 5,
                    "info": 3,
                }
            }
        })

        # 获取告警摘要
        summary = await agent.get_alarm_summary(24)

        assert summary["success"] is True
        assert summary["total_alarms"] == 10

    @pytest.mark.asyncio
    async def test_energy_agent_with_mcp(self, energy_agent):
        """测试能耗Agent调用MCP"""
        agent, mock_db = energy_agent

        # Mock _execute_tool 方法以模拟MCP调用
        agent._execute_tool = AsyncMock(return_value={
            "success": True,
            "result": {
                "ranking": [
                    {"rank": 1, "name": "A栋", "consumption": 1500.0},
                    {"rank": 2, "name": "B栋", "consumption": 1200.0},
                ]
            }
        })

        # 获取建筑对比
        comparison = await agent.get_building_comparison(days=7)

        assert comparison["success"] is True
        assert len(comparison["ranking"]) == 2


class TestCrossModuleWorkflow:
    """跨模块协作流程测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_anomaly_to_alarm_to_ticket(self, mock_db):
        """测试异常->告警->工单的完整流程"""
        energy_mcp = EnergyMCPServer(mock_db)
        alarm_mcp = AlarmMCPServer(mock_db)
        ticket_mcp = TicketMCPServer(mock_db)

        # 1. 检测能耗异常
        anomaly_reading = MagicMock()
        anomaly_reading.meter_id = "MTR-001"
        anomaly_reading.energy_type = "electricity"
        anomaly_reading.value = 500.0  # 异常高值
        anomaly_reading.building = "A栋"
        anomaly_reading.timestamp = datetime.now(timezone.utc)

        normal_reading = MagicMock()
        normal_reading.meter_id = "MTR-002"
        normal_reading.energy_type = "electricity"
        normal_reading.value = 100.0
        normal_reading.building = "A栋"
        normal_reading.timestamp = datetime.now(timezone.utc)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [anomaly_reading, normal_reading]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        anomaly = await energy_mcp._get_energy_anomaly({"threshold": 1.5})
        assert anomaly["anomaly_count"] >= 1

        # 2. 如果有异常，创建维修工单
        if anomaly["anomaly_count"] > 0:
            anomaly_item = anomaly["anomalies"][0]

            mock_db.add = MagicMock()
            mock_db.flush = AsyncMock()

            ticket = await ticket_mcp._create_ticket({
                "title": f"能耗异常: {anomaly_item['meter_id']}",
                "description": f"检测到能耗异常，当前值{anomaly_item['value']}，超过平均值{anomaly_item['ratio']}倍",
                "type": "inspection",
                "priority": "high",
            })

            assert ticket["success"] is True

    @pytest.mark.asyncio
    async def test_report_with_all_modules(self, mock_db):
        """测试包含所有模块数据的综合报表"""
        report_mcp = ReportMCPServer(mock_db)

        # 模拟各模块数据
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_result.scalar.return_value = 0

        mock_db.execute = AsyncMock(return_value=mock_result)

        # 生成综合报表
        report = await report_mcp._generate_operations_report({
            "report_type": "weekly"
        })

        # 验证报表结构完整性
        assert report["report_type"] == "weekly"
        assert "key_metrics" in report
        assert "details" in report
        assert "energy" in report["details"]
        assert "alarms" in report["details"]
        assert "tickets" in report["details"]


class TestErrorHandling:
    """错误处理测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_alarm_not_found_handling(self, mock_db):
        """测试告警不存在的处理"""
        alarm_mcp = AlarmMCPServer(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await alarm_mcp._get_alarm_detail({"alarm_id": "ALM-NOTEXIST"})

        # 实际格式：不存在时返回 {"error": "告警 ALM-NOTEXIST 不存在"}
        assert "error" in result
        assert "不存在" in result["error"]

    @pytest.mark.asyncio
    async def test_ticket_invalid_status_transition(self, mock_db):
        """测试工单无效状态转换"""
        ticket_mcp = TicketMCPServer(mock_db)

        # 模拟已完成的工单
        ticket = MagicMock()
        ticket.ticket_id = "TKT-001"
        ticket.status = "completed"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ticket
        mock_db.execute = AsyncMock(return_value=mock_result)

        # 尝试分配已完成的工单
        result = await ticket_mcp._assign_ticket({
            "ticket_id": "TKT-001",
            "assigned_to": "张工"
        })

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_energy_empty_data_handling(self, mock_db):
        """测试能耗数据为空的处理"""
        energy_mcp = EnergyMCPServer(mock_db)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await energy_mcp._get_energy_consumption({})

        assert result["total_readings"] == 0
        assert result["total_consumption"] == 0
        assert result["average_consumption"] == 0
