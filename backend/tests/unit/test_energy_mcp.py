"""能耗MCP单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

from app.mcp_servers.energy_mcp import EnergyMCPServer


class TestEnergyMCPServer:
    """EnergyMCPServer测试"""

    @pytest.fixture
    def mock_db(self):
        """创建mock数据库会话"""
        return MagicMock()

    @pytest.fixture
    def energy_mcp(self, mock_db):
        """创建能耗MCP实例"""
        return EnergyMCPServer(mock_db)

    def test_init(self, energy_mcp):
        """测试初始化"""
        assert energy_mcp.server_type.value == "energy"
        assert len(energy_mcp._tools) == 5

    def test_tools_registered(self, energy_mcp):
        """测试工具注册"""
        tool_names = list(energy_mcp._tools.keys())
        assert "get_energy_consumption" in tool_names
        assert "get_energy_trend" in tool_names
        assert "get_energy_comparison" in tool_names
        assert "get_energy_ranking" in tool_names
        assert "get_energy_anomaly" in tool_names


class TestGetEnergyConsumption:
    """get_energy_consumption测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def energy_mcp(self, mock_db):
        return EnergyMCPServer(mock_db)

    @pytest.fixture
    def sample_readings(self):
        """示例能耗数据"""
        reading1 = MagicMock()
        reading1.meter_id = "MTR-001"
        reading1.energy_type = "electricity"
        reading1.value = 100.5
        reading1.unit = "kWh"
        reading1.building = "A栋"
        reading1.timestamp = datetime.now(timezone.utc)

        reading2 = MagicMock()
        reading2.meter_id = "MTR-002"
        reading2.energy_type = "electricity"
        reading2.value = 80.3
        reading2.unit = "kWh"
        reading2.building = "B栋"
        reading2.timestamp = datetime.now(timezone.utc) - timedelta(hours=1)

        return [reading1, reading2]

    @pytest.mark.asyncio
    async def test_get_consumption_all(self, energy_mcp, mock_db, sample_readings):
        """测试获取所有能耗"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = sample_readings
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await energy_mcp._get_energy_consumption({})

        assert result["total_readings"] == 2
        assert result["total_consumption"] == 180.8

    @pytest.mark.asyncio
    async def test_get_consumption_with_filter(self, energy_mcp, mock_db, sample_readings):
        """测试带过滤条件"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_readings[0]]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await energy_mcp._get_energy_consumption({
            "energy_type": "electricity",
            "building": "A栋"
        })

        assert result["total_readings"] == 1

    @pytest.mark.asyncio
    async def test_get_consumption_empty(self, energy_mcp, mock_db):
        """测试无数据"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await energy_mcp._get_energy_consumption({})

        assert result["total_readings"] == 0
        assert result["total_consumption"] == 0


class TestGetEnergyTrend:
    """get_energy_trend测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def energy_mcp(self, mock_db):
        return EnergyMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_get_trend_by_day(self, energy_mcp, mock_db):
        """测试按天趋势"""
        reading1 = MagicMock()
        reading1.energy_type = "electricity"
        reading1.value = 100.0
        reading1.timestamp = datetime(2026, 1, 25, 10, 0, tzinfo=timezone.utc)

        reading2 = MagicMock()
        reading2.energy_type = "electricity"
        reading2.value = 120.0
        reading2.timestamp = datetime(2026, 1, 24, 10, 0, tzinfo=timezone.utc)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [reading2, reading1]  # 按时间排序
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await energy_mcp._get_energy_trend({"period": "day"})

        assert result["energy_type"] == "electricity"
        assert result["period"] == "day"
        assert len(result["trend"]) == 2

    @pytest.mark.asyncio
    async def test_get_trend_empty(self, energy_mcp, mock_db):
        """测试无数据趋势"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await energy_mcp._get_energy_trend({})

        assert result["data_points"] == 0


class TestGetEnergyComparison:
    """get_energy_comparison测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def energy_mcp(self, mock_db):
        return EnergyMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_comparison_increase(self, energy_mcp, mock_db):
        """测试能耗增加"""
        mock_current = MagicMock()
        mock_current.scalar.return_value = 1000.0

        mock_previous = MagicMock()
        mock_previous.scalar.return_value = 800.0

        mock_db.execute = AsyncMock(side_effect=[mock_current, mock_previous])

        result = await energy_mcp._get_energy_comparison({"compare_type": "mom"})

        assert result["current_period"]["value"] == 1000.0
        assert result["previous_period"]["value"] == 800.0
        assert result["change_rate"] == 25.0
        assert result["trend"] == "up"

    @pytest.mark.asyncio
    async def test_comparison_decrease(self, energy_mcp, mock_db):
        """测试能耗减少"""
        mock_current = MagicMock()
        mock_current.scalar.return_value = 800.0

        mock_previous = MagicMock()
        mock_previous.scalar.return_value = 1000.0

        mock_db.execute = AsyncMock(side_effect=[mock_current, mock_previous])

        result = await energy_mcp._get_energy_comparison({"compare_type": "wow"})

        assert result["change_rate"] == -20.0
        assert result["trend"] == "down"


class TestGetEnergyRanking:
    """get_energy_ranking测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def energy_mcp(self, mock_db):
        return EnergyMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_ranking_by_building(self, energy_mcp, mock_db):
        """测试按建筑排名"""
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("A栋", 1000.0),
            ("B栋", 800.0),
            ("C栋", 600.0),
        ]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await energy_mcp._get_energy_ranking({"group_by": "building"})

        assert len(result["ranking"]) == 3
        assert result["ranking"][0]["name"] == "A栋"
        assert result["ranking"][0]["rank"] == 1

    @pytest.mark.asyncio
    async def test_ranking_empty(self, energy_mcp, mock_db):
        """测试无数据排名"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await energy_mcp._get_energy_ranking({})

        assert result["ranking"] == []


class TestGetEnergyAnomaly:
    """get_energy_anomaly测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def energy_mcp(self, mock_db):
        return EnergyMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_detect_anomaly(self, energy_mcp, mock_db):
        """测试检测异常"""
        reading1 = MagicMock()
        reading1.meter_id = "MTR-001"
        reading1.energy_type = "electricity"
        reading1.value = 100.0
        reading1.building = "A栋"
        reading1.timestamp = datetime.now(timezone.utc)

        reading2 = MagicMock()
        reading2.meter_id = "MTR-002"
        reading2.energy_type = "electricity"
        reading2.value = 300.0  # 异常值
        reading2.building = "B栋"
        reading2.timestamp = datetime.now(timezone.utc)

        reading3 = MagicMock()
        reading3.meter_id = "MTR-003"
        reading3.energy_type = "electricity"
        reading3.value = 100.0
        reading3.building = "C栋"
        reading3.timestamp = datetime.now(timezone.utc)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [reading1, reading2, reading3]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        # 平均值为166.67，阈值1.5倍为250，reading2的300超过阈值
        result = await energy_mcp._get_energy_anomaly({"threshold": 1.5})

        assert result["total_readings"] == 3
        assert result["anomaly_count"] >= 1

    @pytest.mark.asyncio
    async def test_no_anomaly(self, energy_mcp, mock_db):
        """测试无异常"""
        reading1 = MagicMock()
        reading1.meter_id = "MTR-001"
        reading1.energy_type = "electricity"
        reading1.value = 100.0
        reading1.building = "A栋"
        reading1.timestamp = datetime.now(timezone.utc)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [reading1]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await energy_mcp._get_energy_anomaly({})

        assert result["anomaly_count"] == 0

    @pytest.mark.asyncio
    async def test_no_data(self, energy_mcp, mock_db):
        """测试无数据"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await energy_mcp._get_energy_anomaly({})

        assert result["anomalies"] == []
        assert "无能耗数据" in result["message"]
