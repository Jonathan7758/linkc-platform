"""能耗Agent单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.agents.energy_agent import EnergyAgent, EnergyAgentConfig, ENERGY_SYSTEM_PROMPT
from app.agents.base_agent import AgentContext, AgentState


class TestEnergyAgentConfig:
    """EnergyAgentConfig测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = EnergyAgentConfig(name="test_energy_agent")
        assert config.name == "test_energy_agent"
        assert config.model == "doubao-pro-32k"
        assert config.default_energy_type == "electricity"
        assert config.anomaly_threshold == 1.5

    def test_custom_config(self):
        """测试自定义配置"""
        config = EnergyAgentConfig(
            name="custom_agent",
            model="gpt-4",
            default_energy_type="water",
            anomaly_threshold=2.0,
        )
        assert config.model == "gpt-4"
        assert config.default_energy_type == "water"
        assert config.anomaly_threshold == 2.0


class TestEnergyAgentInit:
    """EnergyAgent初始化测试"""

    def test_init_with_default_prompt(self):
        """测试使用默认系统提示"""
        config = EnergyAgentConfig(name="test_agent")
        agent = EnergyAgent(config)

        assert agent.config.system_prompt == ENERGY_SYSTEM_PROMPT
        assert agent.state == AgentState.IDLE

    def test_init_with_custom_prompt(self):
        """测试使用自定义系统提示"""
        custom_prompt = "你是自定义的能耗助手"
        config = EnergyAgentConfig(name="test_agent", system_prompt=custom_prompt)
        agent = EnergyAgent(config)

        assert agent.config.system_prompt == custom_prompt


class TestAnalyzeIntent:
    """意图分析测试"""

    @pytest.fixture
    def agent(self):
        config = EnergyAgentConfig(name="test_agent")
        return EnergyAgent(config)

    def test_consumption_intent(self, agent):
        """测试能耗查询意图"""
        assert agent._analyze_intent("今天用了多少电") == "consumption"
        assert agent._analyze_intent("能耗消耗情况") == "consumption"

    def test_trend_intent(self, agent):
        """测试趋势意图"""
        assert agent._analyze_intent("能耗趋势") == "trend"
        assert agent._analyze_intent("用电变化") == "trend"

    def test_comparison_intent(self, agent):
        """测试对比意图"""
        assert agent._analyze_intent("同比数据") == "comparison"
        assert agent._analyze_intent("和上周比较") == "comparison"

    def test_ranking_intent(self, agent):
        """测试排名意图"""
        assert agent._analyze_intent("能耗排名") == "ranking"
        assert agent._analyze_intent("哪栋楼用电最多") == "ranking"

    def test_anomaly_intent(self, agent):
        """测试异常意图"""
        assert agent._analyze_intent("能耗异常") == "anomaly"
        assert agent._analyze_intent("用电突增") == "anomaly"

    def test_report_intent(self, agent):
        """测试报告意图"""
        assert agent._analyze_intent("能耗报告") == "report"
        assert agent._analyze_intent("分析报表") == "report"

    def test_general_intent(self, agent):
        """测试一般意图"""
        assert agent._analyze_intent("你好") == "general"


class TestSelectTools:
    """工具选择测试"""

    @pytest.fixture
    def agent(self):
        config = EnergyAgentConfig(name="test_agent")
        return EnergyAgent(config)

    @pytest.mark.asyncio
    async def test_select_tools_for_consumption(self, agent):
        """测试消耗查询的工具选择"""
        context = AgentContext(session_id="test")
        context.set_variable("intent", "consumption")

        tools = await agent._select_tools("用电查询", context)

        assert "get_energy_consumption" in tools

    @pytest.mark.asyncio
    async def test_select_tools_for_trend(self, agent):
        """测试趋势的工具选择"""
        context = AgentContext(session_id="test")
        context.set_variable("intent", "trend")

        tools = await agent._select_tools("能耗趋势", context)

        assert "get_energy_trend" in tools


class TestAnalyzeConsumption:
    """analyze_consumption测试"""

    @pytest.fixture
    def agent(self):
        config = EnergyAgentConfig(name="test_agent")
        agent = EnergyAgent(config)

        mock_server = MagicMock()
        mock_server.name = "energy"

        mock_tool = MagicMock()
        mock_tool.name = "get_energy_consumption"
        mock_server.list_tools.return_value = [mock_tool]

        agent._mcp_servers["energy"] = mock_server
        return agent

    @pytest.mark.asyncio
    async def test_analyze_consumption_success(self, agent):
        """测试分析能耗成功"""
        consumption_data = {
            "total_consumption": 1500.0,
            "average_consumption": 100.0,
            "total_readings": 15,
        }

        agent.call_tool = AsyncMock(return_value={
            "success": True,
            "result": consumption_data
        })

        result = await agent.analyze_consumption(
            energy_type="electricity",
            building="A栋",
            hours=24
        )

        assert result["success"] is True
        assert result["analysis"]["total_consumption"] == 1500.0
        assert "assessment" in result["analysis"]


class TestGetEnergyInsights:
    """get_energy_insights测试"""

    @pytest.fixture
    def agent(self):
        config = EnergyAgentConfig(name="test_agent")
        agent = EnergyAgent(config)

        mock_server = MagicMock()
        mock_server.name = "energy"

        tools = []
        for name in ["get_energy_trend", "get_energy_comparison", "get_energy_anomaly"]:
            mock_tool = MagicMock()
            mock_tool.name = name
            tools.append(mock_tool)

        mock_server.list_tools.return_value = tools
        agent._mcp_servers["energy"] = mock_server
        return agent

    @pytest.mark.asyncio
    async def test_get_insights_success(self, agent):
        """测试获取洞察成功"""
        trend_data = {
            "trend": [
                {"period": "2026-01-20", "value": 100},
                {"period": "2026-01-21", "value": 110},
                {"period": "2026-01-22", "value": 120},
                {"period": "2026-01-23", "value": 130},
            ]
        }

        comparison_data = {
            "change_rate": 15.0,
            "trend": "up",
        }

        anomaly_data = {
            "anomaly_count": 2,
            "anomalies": [{"meter_id": "M1"}, {"meter_id": "M2"}]
        }

        agent.call_tool = AsyncMock(side_effect=[
            {"success": True, "result": trend_data},
            {"success": True, "result": comparison_data},
            {"success": True, "result": anomaly_data},
        ])

        result = await agent.get_energy_insights(building="A栋", days=7)

        assert result["success"] is True
        assert len(result["insights"]) > 0
        assert "suggestions" in result


class TestGetBuildingComparison:
    """get_building_comparison测试"""

    @pytest.fixture
    def agent(self):
        config = EnergyAgentConfig(name="test_agent")
        agent = EnergyAgent(config)

        mock_server = MagicMock()
        mock_server.name = "energy"

        mock_tool = MagicMock()
        mock_tool.name = "get_energy_ranking"
        mock_server.list_tools.return_value = [mock_tool]

        agent._mcp_servers["energy"] = mock_server
        return agent

    @pytest.mark.asyncio
    async def test_building_comparison_success(self, agent):
        """测试建筑对比成功"""
        ranking_data = {
            "ranking": [
                {"rank": 1, "name": "A栋", "consumption": 1500.0},
                {"rank": 2, "name": "B栋", "consumption": 1200.0},
                {"rank": 3, "name": "C栋", "consumption": 800.0},
            ]
        }

        agent.call_tool = AsyncMock(return_value={
            "success": True,
            "result": ranking_data
        })

        result = await agent.get_building_comparison(days=7)

        assert result["success"] is True
        assert len(result["ranking"]) == 3
        assert result["statistics"]["total"] == 3500.0
        assert "high_consumption_buildings" in result


class TestDetectAnomalies:
    """detect_anomalies测试"""

    @pytest.fixture
    def agent(self):
        config = EnergyAgentConfig(name="test_agent", anomaly_threshold=1.5)
        agent = EnergyAgent(config)

        mock_server = MagicMock()
        mock_server.name = "energy"

        mock_tool = MagicMock()
        mock_tool.name = "get_energy_anomaly"
        mock_server.list_tools.return_value = [mock_tool]

        agent._mcp_servers["energy"] = mock_server
        return agent

    @pytest.mark.asyncio
    async def test_detect_anomalies_found(self, agent):
        """测试检测到异常"""
        anomaly_data = {
            "total_readings": 100,
            "anomaly_count": 3,
            "anomalies": [
                {"meter_id": "M1", "ratio": 2.5},
                {"meter_id": "M2", "ratio": 1.8},
                {"meter_id": "M3", "ratio": 1.6},
            ]
        }

        agent.call_tool = AsyncMock(return_value={
            "success": True,
            "result": anomaly_data
        })

        result = await agent.detect_anomalies(hours=24)

        assert result["success"] is True
        assert result["anomaly_count"] == 3
        # 应该按ratio排序
        assert result["anomalies"][0]["ratio"] == 2.5
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_detect_anomalies_none(self, agent):
        """测试无异常"""
        agent.call_tool = AsyncMock(return_value={
            "success": True,
            "result": {
                "total_readings": 100,
                "anomaly_count": 0,
                "anomalies": []
            }
        })

        result = await agent.detect_anomalies(hours=24)

        assert result["success"] is True
        assert result["anomaly_count"] == 0
        assert "未检测到" in result["summary"]


class TestAnalyzeTrend:
    """趋势分析测试"""

    @pytest.fixture
    def agent(self):
        config = EnergyAgentConfig(name="test_agent")
        return EnergyAgent(config)

    def test_upward_trend(self, agent):
        """测试上升趋势"""
        trend_data = {
            "trend": [
                {"period": "1", "value": 100},
                {"period": "2", "value": 110},
                {"period": "3", "value": 150},
                {"period": "4", "value": 180},
            ]
        }
        result = agent._analyze_trend(trend_data)

        assert result is not None
        assert "上升" in result["title"]
        assert result["concern_level"] == "high"

    def test_downward_trend(self, agent):
        """测试下降趋势"""
        trend_data = {
            "trend": [
                {"period": "1", "value": 180},
                {"period": "2", "value": 150},
                {"period": "3", "value": 110},
                {"period": "4", "value": 100},
            ]
        }
        result = agent._analyze_trend(trend_data)

        assert result is not None
        assert "下降" in result["title"]
        assert result["concern_level"] == "low"

    def test_stable_trend(self, agent):
        """测试平稳趋势"""
        trend_data = {
            "trend": [
                {"period": "1", "value": 100},
                {"period": "2", "value": 102},
                {"period": "3", "value": 98},
                {"period": "4", "value": 101},
            ]
        }
        result = agent._analyze_trend(trend_data)

        assert result is not None
        assert "平稳" in result["title"]


class TestGenerateSuggestions:
    """建议生成测试"""

    @pytest.fixture
    def agent(self):
        config = EnergyAgentConfig(name="test_agent")
        return EnergyAgent(config)

    def test_suggestions_for_high_concern(self, agent):
        """测试高关注度的建议"""
        insights = [
            {"type": "trend", "concern_level": "high"},
            {"type": "comparison", "concern_level": "high"},
        ]

        suggestions = agent._generate_suggestions(insights)

        assert len(suggestions) >= 2

    def test_suggestions_for_anomaly(self, agent):
        """测试异常的建议"""
        insights = [
            {"type": "anomaly", "concern_level": "high"},
        ]

        suggestions = agent._generate_suggestions(insights)

        assert any("异常" in s for s in suggestions)

    def test_suggestions_when_normal(self, agent):
        """测试正常情况的建议"""
        insights = []

        suggestions = agent._generate_suggestions(insights)

        assert any("良好" in s or "保持" in s for s in suggestions)


class TestGenerateAnomalySummary:
    """异常摘要生成测试"""

    @pytest.fixture
    def agent(self):
        config = EnergyAgentConfig(name="test_agent")
        return EnergyAgent(config)

    def test_no_anomaly_summary(self, agent):
        """测试无异常摘要"""
        summary = agent._generate_anomaly_summary([])
        assert "未检测到" in summary

    def test_severe_anomaly_summary(self, agent):
        """测试严重异常摘要"""
        anomalies = [
            {"ratio": 3.5},
            {"ratio": 2.0},
        ]
        summary = agent._generate_anomaly_summary(anomalies)
        assert "严重" in summary
        assert "2个" in summary

    def test_moderate_anomaly_summary(self, agent):
        """测试中等异常摘要"""
        anomalies = [
            {"ratio": 2.5},
        ]
        summary = agent._generate_anomaly_summary(anomalies)
        assert "中等" in summary
