"""报表MCP单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

from app.mcp_servers.report_mcp import ReportMCPServer


class TestReportMCPServer:
    """ReportMCPServer测试"""

    @pytest.fixture
    def mock_db(self):
        """创建mock数据库会话"""
        return MagicMock()

    @pytest.fixture
    def report_mcp(self, mock_db):
        """创建报表MCP实例"""
        return ReportMCPServer(mock_db)

    def test_init(self, report_mcp):
        """测试初始化"""
        assert report_mcp.server_type.value == "report"
        assert len(report_mcp._tools) == 5

    def test_tools_registered(self, report_mcp):
        """测试工具注册"""
        tool_names = list(report_mcp._tools.keys())
        assert "generate_energy_report" in tool_names
        assert "generate_alarm_report" in tool_names
        assert "generate_ticket_report" in tool_names
        assert "generate_operations_report" in tool_names
        assert "get_report_list" in tool_names


class TestGetReportPeriod:
    """_get_report_period测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def report_mcp(self, mock_db):
        return ReportMCPServer(mock_db)

    def test_daily_period(self, report_mcp):
        """测试日报周期"""
        start, end = report_mcp._get_report_period("daily", "2026-01-25")
        assert start.day == 25
        assert (end - start).days == 1

    def test_weekly_period(self, report_mcp):
        """测试周报周期"""
        start, end = report_mcp._get_report_period("weekly", "2026-01-25")
        assert start.weekday() == 0  # 周一
        assert (end - start).days == 7

    def test_monthly_period(self, report_mcp):
        """测试月报周期"""
        start, end = report_mcp._get_report_period("monthly", "2026-01-15")
        assert start.day == 1
        assert end.month == 2


class TestGenerateEnergyReport:
    """generate_energy_report测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def report_mcp(self, mock_db):
        return ReportMCPServer(mock_db)

    @pytest.fixture
    def sample_readings(self):
        """示例能耗数据"""
        reading1 = MagicMock()
        reading1.energy_type = "electricity"
        reading1.value = 100.0
        reading1.building = "A栋"

        reading2 = MagicMock()
        reading2.energy_type = "electricity"
        reading2.value = 80.0
        reading2.building = "B栋"

        reading3 = MagicMock()
        reading3.energy_type = "water"
        reading3.value = 50.0
        reading3.building = "A栋"

        return [reading1, reading2, reading3]

    @pytest.mark.asyncio
    async def test_generate_daily_report(self, report_mcp, mock_db, sample_readings):
        """测试生成日报"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = sample_readings
        mock_result1 = MagicMock()
        mock_result1.scalars.return_value = mock_scalars

        mock_result2 = MagicMock()
        mock_result2.scalar.return_value = 200.0  # 去年同期

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        result = await report_mcp._generate_energy_report({
            "report_type": "daily",
            "date": "2026-01-25"
        })

        assert result["report_type"] == "daily"
        assert result["summary"]["total_consumption"] == 230.0
        assert result["summary"]["reading_count"] == 3
        assert "by_type" in result["breakdown"]
        assert "by_building" in result["breakdown"]

    @pytest.mark.asyncio
    async def test_generate_report_empty(self, report_mcp, mock_db):
        """测试无数据报表"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result1 = MagicMock()
        mock_result1.scalars.return_value = mock_scalars

        mock_result2 = MagicMock()
        mock_result2.scalar.return_value = None

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        result = await report_mcp._generate_energy_report({"report_type": "daily"})

        assert result["summary"]["total_consumption"] == 0
        assert result["summary"]["reading_count"] == 0


class TestGenerateAlarmReport:
    """generate_alarm_report测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def report_mcp(self, mock_db):
        return ReportMCPServer(mock_db)

    @pytest.fixture
    def sample_alarms(self):
        """示例告警数据"""
        alarm1 = MagicMock()
        alarm1.severity = "critical"
        alarm1.status = "resolved"
        alarm1.device_type = "hvac"
        alarm1.created_at = datetime.now(timezone.utc) - timedelta(hours=5)
        alarm1.acknowledged_at = datetime.now(timezone.utc) - timedelta(hours=4)

        alarm2 = MagicMock()
        alarm2.severity = "warning"
        alarm2.status = "acknowledged"
        alarm2.device_type = "lighting"
        alarm2.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        alarm2.acknowledged_at = datetime.now(timezone.utc) - timedelta(hours=1)

        alarm3 = MagicMock()
        alarm3.severity = "warning"
        alarm3.status = "active"
        alarm3.device_type = "hvac"
        alarm3.created_at = datetime.now(timezone.utc) - timedelta(hours=1)
        alarm3.acknowledged_at = None

        return [alarm1, alarm2, alarm3]

    @pytest.mark.asyncio
    async def test_generate_alarm_report(self, report_mcp, mock_db, sample_alarms):
        """测试生成告警报表"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = sample_alarms
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await report_mcp._generate_alarm_report({
            "report_type": "daily",
            "date": "2026-01-25"
        })

        assert result["summary"]["total_alarms"] == 3
        assert result["summary"]["resolved_alarms"] == 1
        assert result["summary"]["acknowledged_alarms"] == 1
        assert "by_severity" in result["breakdown"]
        assert result["breakdown"]["by_severity"]["warning"] == 2


class TestGenerateTicketReport:
    """generate_ticket_report测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def report_mcp(self, mock_db):
        return ReportMCPServer(mock_db)

    @pytest.fixture
    def sample_tickets(self):
        """示例工单数据"""
        ticket1 = MagicMock()
        ticket1.type = "repair"
        ticket1.priority = "high"
        ticket1.status = "completed"
        ticket1.assigned_to = "张工"
        ticket1.due_date = None
        ticket1.started_at = datetime.now(timezone.utc) - timedelta(hours=5)
        ticket1.completed_at = datetime.now(timezone.utc) - timedelta(hours=2)

        ticket2 = MagicMock()
        ticket2.type = "maintenance"
        ticket2.priority = "medium"
        ticket2.status = "in_progress"
        ticket2.assigned_to = "李工"
        ticket2.due_date = datetime.now(timezone.utc) + timedelta(days=1)
        ticket2.started_at = datetime.now(timezone.utc) - timedelta(hours=1)
        ticket2.completed_at = None

        ticket3 = MagicMock()
        ticket3.type = "repair"
        ticket3.priority = "low"
        ticket3.status = "pending"
        ticket3.assigned_to = None
        ticket3.due_date = datetime.now(timezone.utc) - timedelta(hours=1)  # 已逾期
        ticket3.started_at = None
        ticket3.completed_at = None

        return [ticket1, ticket2, ticket3]

    @pytest.mark.asyncio
    async def test_generate_ticket_report(self, report_mcp, mock_db, sample_tickets):
        """测试生成工单报表"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = sample_tickets
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await report_mcp._generate_ticket_report({
            "report_type": "weekly",
            "date": "2026-01-25"
        })

        assert result["summary"]["total_tickets"] == 3
        assert result["summary"]["completed_tickets"] == 1
        assert result["summary"]["in_progress_tickets"] == 1
        assert result["summary"]["overdue_tickets"] == 1
        assert "by_type" in result["breakdown"]
        assert result["breakdown"]["by_type"]["repair"] == 2


class TestGenerateOperationsReport:
    """generate_operations_report测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def report_mcp(self, mock_db):
        return ReportMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_generate_operations_report(self, report_mcp, mock_db):
        """测试生成综合运营报表"""
        # 设置多个查询的mock返回值
        mock_scalars1 = MagicMock()
        mock_scalars1.all.return_value = []
        mock_result1 = MagicMock()
        mock_result1.scalars.return_value = mock_scalars1

        mock_result2 = MagicMock()
        mock_result2.scalar.return_value = None

        mock_scalars3 = MagicMock()
        mock_scalars3.all.return_value = []
        mock_result3 = MagicMock()
        mock_result3.scalars.return_value = mock_scalars3

        mock_scalars4 = MagicMock()
        mock_scalars4.all.return_value = []
        mock_result4 = MagicMock()
        mock_result4.scalars.return_value = mock_scalars4

        mock_db.execute = AsyncMock(side_effect=[
            mock_result1, mock_result2,  # energy report
            mock_result3,  # alarm report
            mock_result4,  # ticket report
        ])

        result = await report_mcp._generate_operations_report({
            "report_type": "daily",
            "date": "2026-01-25"
        })

        assert "key_metrics" in result
        assert "energy" in result["key_metrics"]
        assert "alarms" in result["key_metrics"]
        assert "tickets" in result["key_metrics"]


class TestGetReportList:
    """get_report_list测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def report_mcp(self, mock_db):
        return ReportMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_get_report_list(self, report_mcp):
        """测试获取报表列表"""
        result = await report_mcp._get_report_list({})

        assert "reports" in result
        assert len(result["reports"]) == 4

        report_names = [r["name"] for r in result["reports"]]
        assert "generate_energy_report" in report_names
        assert "generate_alarm_report" in report_names
