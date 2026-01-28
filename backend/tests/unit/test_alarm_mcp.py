"""告警MCP单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

from app.mcp_servers.alarm_mcp import AlarmMCPServer
from app.models.alarm import AlarmStatus, AlarmSeverity, AlarmCategory


class TestAlarmMCPServer:
    """AlarmMCPServer测试"""

    @pytest.fixture
    def mock_db(self):
        """创建mock数据库会话"""
        return MagicMock()

    @pytest.fixture
    def alarm_mcp(self, mock_db):
        """创建告警MCP实例"""
        return AlarmMCPServer(mock_db)

    def test_init(self, alarm_mcp):
        """测试初始化"""
        assert alarm_mcp.server_type.value == "alarm"
        assert len(alarm_mcp._tools) == 6

    def test_tools_registered(self, alarm_mcp):
        """测试工具注册"""
        tool_names = list(alarm_mcp._tools.keys())
        assert "get_alarm_list" in tool_names
        assert "get_alarm_detail" in tool_names
        assert "get_alarm_stats" in tool_names
        assert "acknowledge_alarm" in tool_names
        assert "resolve_alarm" in tool_names
        assert "get_alarm_suggestions" in tool_names


class TestGetAlarmList:
    """get_alarm_list测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def alarm_mcp(self, mock_db):
        return AlarmMCPServer(mock_db)

    @pytest.fixture
    def sample_alarms(self):
        """示例告警数据"""
        alarm1 = MagicMock()
        alarm1.alarm_id = "ALM-001"
        alarm1.title = "温度过高"
        alarm1.severity = "critical"
        alarm1.status = "active"
        alarm1.device_id = "DEV-001"
        alarm1.triggered_at = datetime.now(timezone.utc)
        alarm1.category = "threshold"

        alarm2 = MagicMock()
        alarm2.alarm_id = "ALM-002"
        alarm2.title = "设备离线"
        alarm2.severity = "major"
        alarm2.status = "acknowledged"
        alarm2.device_id = "DEV-002"
        alarm2.triggered_at = datetime.now(timezone.utc) - timedelta(hours=1)
        alarm2.category = "offline"

        return [alarm1, alarm2]

    @pytest.mark.asyncio
    async def test_get_alarm_list_all(self, alarm_mcp, mock_db, sample_alarms):
        """测试获取所有告警"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = sample_alarms
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await alarm_mcp._get_alarm_list({})

        assert result["total"] == 2
        assert result["period_hours"] == 24
        assert len(result["alarms"]) == 2

    @pytest.mark.asyncio
    async def test_get_alarm_list_with_status_filter(self, alarm_mcp, mock_db, sample_alarms):
        """测试按状态筛选"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_alarms[0]]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await alarm_mcp._get_alarm_list({"status": "active"})

        assert result["total"] == 1
        assert result["alarms"][0]["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_alarm_list_empty(self, alarm_mcp, mock_db):
        """测试无告警"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await alarm_mcp._get_alarm_list({})

        assert result["total"] == 0
        assert result["alarms"] == []


class TestGetAlarmDetail:
    """get_alarm_detail测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def alarm_mcp(self, mock_db):
        return AlarmMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_get_alarm_detail_found(self, alarm_mcp, mock_db):
        """测试获取告警详情"""
        mock_alarm = MagicMock()
        mock_alarm.alarm_id = "ALM-001"
        mock_alarm.title = "温度过高"
        mock_alarm.description = "设备温度超过阈值"
        mock_alarm.severity = "critical"
        mock_alarm.status = "active"
        mock_alarm.category = "threshold"
        mock_alarm.device_id = "DEV-001"
        mock_alarm.trigger_value = 85.5
        mock_alarm.threshold_value = 80.0
        mock_alarm.trigger_parameter = "temperature"
        mock_alarm.triggered_at = datetime.now(timezone.utc)
        mock_alarm.acknowledged_at = None
        mock_alarm.acknowledged_by = None
        mock_alarm.resolved_at = None
        mock_alarm.resolved_by = None
        mock_alarm.resolution_notes = None

        # Mock alarm查询
        mock_alarm_result = MagicMock()
        mock_alarm_result.scalar_one_or_none.return_value = mock_alarm

        # Mock device查询
        mock_device = MagicMock()
        mock_device.device_id = "DEV-001"
        mock_device.name = "空调1号"
        mock_device.device_type = "hvac"
        mock_device.location = "A栋1层"

        mock_device_result = MagicMock()
        mock_device_result.scalar_one_or_none.return_value = mock_device

        mock_db.execute = AsyncMock(side_effect=[mock_alarm_result, mock_device_result])

        result = await alarm_mcp._get_alarm_detail({"alarm_id": "ALM-001"})

        assert result["alarm_id"] == "ALM-001"
        assert result["title"] == "温度过高"
        assert result["severity"] == "critical"
        assert result["device"]["name"] == "空调1号"

    @pytest.mark.asyncio
    async def test_get_alarm_detail_not_found(self, alarm_mcp, mock_db):
        """测试告警不存在"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await alarm_mcp._get_alarm_detail({"alarm_id": "NONEXISTENT"})

        assert "error" in result


class TestGetAlarmStats:
    """get_alarm_stats测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def alarm_mcp(self, mock_db):
        return AlarmMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_get_alarm_stats_by_severity(self, alarm_mcp, mock_db):
        """测试按级别统计"""
        mock_alarm1 = MagicMock()
        mock_alarm1.severity = "critical"
        mock_alarm1.status = "active"

        mock_alarm2 = MagicMock()
        mock_alarm2.severity = "major"
        mock_alarm2.status = "active"

        mock_alarm3 = MagicMock()
        mock_alarm3.severity = "critical"
        mock_alarm3.status = "acknowledged"

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_alarm1, mock_alarm2, mock_alarm3]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await alarm_mcp._get_alarm_stats({"group_by": "severity"})

        assert result["total"] == 3
        assert result["statistics"]["critical"] == 2
        assert result["statistics"]["major"] == 1


class TestAcknowledgeAlarm:
    """acknowledge_alarm测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def alarm_mcp(self, mock_db):
        return AlarmMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_acknowledge_alarm_success(self, alarm_mcp, mock_db):
        """测试确认告警成功"""
        mock_alarm = MagicMock()
        mock_alarm.alarm_id = "ALM-001"
        mock_alarm.status = AlarmStatus.ACTIVE.value

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_alarm
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        result = await alarm_mcp._acknowledge_alarm({
            "alarm_id": "ALM-001",
            "comment": "已通知维修"
        })

        assert result["status"] == "acknowledged"
        assert mock_alarm.status == AlarmStatus.ACKNOWLEDGED.value

    @pytest.mark.asyncio
    async def test_acknowledge_alarm_not_found(self, alarm_mcp, mock_db):
        """测试告警不存在"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await alarm_mcp._acknowledge_alarm({"alarm_id": "NONEXISTENT"})

        assert "error" in result

    @pytest.mark.asyncio
    async def test_acknowledge_alarm_invalid_status(self, alarm_mcp, mock_db):
        """测试状态不允许确认"""
        mock_alarm = MagicMock()
        mock_alarm.alarm_id = "ALM-001"
        mock_alarm.status = AlarmStatus.RESOLVED.value

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_alarm
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await alarm_mcp._acknowledge_alarm({"alarm_id": "ALM-001"})

        assert "error" in result


class TestResolveAlarm:
    """resolve_alarm测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def alarm_mcp(self, mock_db):
        return AlarmMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_resolve_alarm_success(self, alarm_mcp, mock_db):
        """测试解决告警成功"""
        mock_alarm = MagicMock()
        mock_alarm.alarm_id = "ALM-001"
        mock_alarm.status = AlarmStatus.ACKNOWLEDGED.value

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_alarm
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        result = await alarm_mcp._resolve_alarm({
            "alarm_id": "ALM-001",
            "resolution": "已更换传感器",
            "comment": "温度恢复正常"
        })

        assert result["status"] == "resolved"
        assert mock_alarm.status == AlarmStatus.RESOLVED.value

    @pytest.mark.asyncio
    async def test_resolve_alarm_already_resolved(self, alarm_mcp, mock_db):
        """测试告警已解决"""
        mock_alarm = MagicMock()
        mock_alarm.alarm_id = "ALM-001"
        mock_alarm.status = AlarmStatus.RESOLVED.value

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_alarm
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await alarm_mcp._resolve_alarm({
            "alarm_id": "ALM-001",
            "resolution": "测试"
        })

        assert "error" in result


class TestGetAlarmSuggestions:
    """get_alarm_suggestions测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def alarm_mcp(self, mock_db):
        return AlarmMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_get_suggestions_threshold(self, alarm_mcp, mock_db):
        """测试阈值告警建议"""
        mock_alarm = MagicMock()
        mock_alarm.alarm_id = "ALM-001"
        mock_alarm.title = "温度过高"
        mock_alarm.category = "threshold"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_alarm
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await alarm_mcp._get_alarm_suggestions({"alarm_id": "ALM-001"})

        assert result["alarm_id"] == "ALM-001"
        assert len(result["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_get_suggestions_fault(self, alarm_mcp, mock_db):
        """测试故障告警建议"""
        mock_alarm = MagicMock()
        mock_alarm.alarm_id = "ALM-002"
        mock_alarm.title = "设备故障"
        mock_alarm.category = "fault"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_alarm
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await alarm_mcp._get_alarm_suggestions({"alarm_id": "ALM-002"})

        assert len(result["suggestions"]) == 4

    def test_preset_suggestions(self, alarm_mcp):
        """测试预设建议"""
        suggestions = alarm_mcp._get_preset_suggestions("threshold")
        assert len(suggestions) == 4

        suggestions = alarm_mcp._get_preset_suggestions("unknown")
        assert len(suggestions) == 1
