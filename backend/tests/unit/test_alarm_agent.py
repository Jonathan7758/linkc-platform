"""告警Agent单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.agents.alarm_agent import AlarmAgent, AlarmAgentConfig, ALARM_SYSTEM_PROMPT
from app.agents.base_agent import AgentContext, AgentState, MessageRole


class TestAlarmAgentConfig:
    """AlarmAgentConfig测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = AlarmAgentConfig(name="test_alarm_agent")
        assert config.name == "test_alarm_agent"
        assert config.model == "doubao-pro-32k"
        assert config.max_tokens == 2048
        assert config.enable_tools is True
        assert config.auto_acknowledge is False

    def test_custom_config(self):
        """测试自定义配置"""
        config = AlarmAgentConfig(
            name="custom_agent",
            model="gpt-4",
            auto_acknowledge=True,
            severity_threshold="critical",
        )
        assert config.model == "gpt-4"
        assert config.auto_acknowledge is True
        assert config.severity_threshold == "critical"


class TestAlarmAgentInit:
    """AlarmAgent初始化测试"""

    def test_init_with_default_prompt(self):
        """测试使用默认系统提示"""
        config = AlarmAgentConfig(name="test_agent")
        agent = AlarmAgent(config)

        assert agent.config.system_prompt == ALARM_SYSTEM_PROMPT
        assert agent.state == AgentState.IDLE

    def test_init_with_custom_prompt(self):
        """测试使用自定义系统提示"""
        custom_prompt = "你是自定义的告警助手"
        config = AlarmAgentConfig(name="test_agent", system_prompt=custom_prompt)
        agent = AlarmAgent(config)

        assert agent.config.system_prompt == custom_prompt


class TestAnalyzeIntent:
    """意图分析测试"""

    @pytest.fixture
    def agent(self):
        config = AlarmAgentConfig(name="test_agent")
        return AlarmAgent(config)

    def test_list_alarms_intent(self, agent):
        """测试告警列表意图"""
        assert agent._analyze_intent("显示所有告警") == "list_alarms"
        assert agent._analyze_intent("告警列表") == "list_alarms"
        assert agent._analyze_intent("有哪些告警") == "list_alarms"

    def test_alarm_detail_intent(self, agent):
        """测试告警详情意图"""
        assert agent._analyze_intent("告警详情") == "alarm_detail"
        assert agent._analyze_intent("具体信息") == "alarm_detail"

    def test_acknowledge_intent(self, agent):
        """测试确认告警意图"""
        assert agent._analyze_intent("确认这个告警") == "acknowledge"
        assert agent._analyze_intent("收到告警") == "acknowledge"

    def test_resolve_intent(self, agent):
        """测试解决告警意图"""
        assert agent._analyze_intent("告警已解决") == "resolve"
        assert agent._analyze_intent("已修复问题") == "resolve"

    def test_statistics_intent(self, agent):
        """测试统计意图"""
        assert agent._analyze_intent("告警统计") == "statistics"
        assert agent._analyze_intent("生成报告") == "statistics"

    def test_suggestions_intent(self, agent):
        """测试建议意图"""
        assert agent._analyze_intent("告警怎么处理") == "suggestions"
        assert agent._analyze_intent("给我一些建议") == "suggestions"

    def test_general_intent(self, agent):
        """测试一般意图"""
        assert agent._analyze_intent("你好") == "general"
        assert agent._analyze_intent("随便问问") == "general"


class TestSelectTools:
    """工具选择测试"""

    @pytest.fixture
    def agent(self):
        config = AlarmAgentConfig(name="test_agent")
        return AlarmAgent(config)

    @pytest.mark.asyncio
    async def test_select_tools_for_list(self, agent):
        """测试列表意图的工具选择"""
        context = AgentContext(session_id="test")
        context.set_variable("intent", "list_alarms")

        tools = await agent._select_tools("显示告警", context)

        assert "get_alarm_list" in tools
        assert "get_alarm_stats" in tools

    @pytest.mark.asyncio
    async def test_select_tools_for_detail(self, agent):
        """测试详情意图的工具选择"""
        context = AgentContext(session_id="test")
        context.set_variable("intent", "alarm_detail")

        tools = await agent._select_tools("告警详情", context)

        assert "get_alarm_detail" in tools
        assert "get_alarm_suggestions" in tools


class TestAnalyzeAlarm:
    """analyze_alarm测试"""

    @pytest.fixture
    def agent(self):
        config = AlarmAgentConfig(name="test_agent")
        agent = AlarmAgent(config)

        # Mock MCP server
        mock_server = MagicMock()
        mock_server.name = "alarm"

        mock_tool1 = MagicMock()
        mock_tool1.name = "get_alarm_detail"
        mock_tool2 = MagicMock()
        mock_tool2.name = "get_alarm_suggestions"

        mock_server.list_tools.return_value = [mock_tool1, mock_tool2]
        agent._mcp_servers["alarm"] = mock_server

        return agent

    @pytest.mark.asyncio
    async def test_analyze_alarm_success(self, agent):
        """测试分析告警成功"""
        # Mock call_tool
        alarm_data = {
            "found": True,
            "alarm": {
                "alarm_id": "ALM-001",
                "severity": "warning",
                "device_type": "hvac",
                "status": "active",
                "description": "温度过高",
            }
        }
        suggestions_data = {
            "suggestions": ["检查空调滤网", "检查制冷剂"]
        }

        agent.call_tool = AsyncMock(side_effect=[
            {"success": True, "result": alarm_data},
            {"success": True, "result": suggestions_data},
        ])

        result = await agent.analyze_alarm("ALM-001")

        assert result["success"] is True
        assert result["alarm_id"] == "ALM-001"
        assert result["severity"] == "warning"
        assert result["analysis"]["urgency"] == "较高"
        assert len(result["analysis"]["suggestions"]) == 2

    @pytest.mark.asyncio
    async def test_analyze_alarm_not_found(self, agent):
        """测试告警不存在"""
        agent.call_tool = AsyncMock(return_value={
            "success": True,
            "result": {"found": False}
        })

        result = await agent.analyze_alarm("ALM-NOTEXIST")

        assert result["success"] is False
        assert "不存在" in result["error"]


class TestGetAlarmSummary:
    """get_alarm_summary测试"""

    @pytest.fixture
    def agent(self):
        config = AlarmAgentConfig(name="test_agent")
        agent = AlarmAgent(config)

        mock_server = MagicMock()
        mock_server.name = "alarm"

        mock_tool = MagicMock()
        mock_tool.name = "get_alarm_stats"
        mock_server.list_tools.return_value = [mock_tool]

        agent._mcp_servers["alarm"] = mock_server
        return agent

    @pytest.mark.asyncio
    async def test_get_summary_success(self, agent):
        """测试获取摘要成功"""
        stats_data = {
            "total": 10,
            "stats": {
                "critical": 2,
                "warning": 5,
                "info": 3,
            }
        }
        agent.call_tool = AsyncMock(return_value={
            "success": True,
            "result": stats_data
        })

        result = await agent.get_alarm_summary(24)

        assert result["success"] is True
        assert result["total_alarms"] == 10
        assert "严重告警" in result["summary"]

    @pytest.mark.asyncio
    async def test_get_summary_no_alarms(self, agent):
        """测试无告警的摘要"""
        agent.call_tool = AsyncMock(return_value={
            "success": True,
            "result": {"total": 0, "stats": {}}
        })

        result = await agent.get_alarm_summary(24)

        assert result["success"] is True
        assert "无告警" in result["summary"]


class TestBatchAcknowledge:
    """batch_acknowledge测试"""

    @pytest.fixture
    def agent(self):
        config = AlarmAgentConfig(name="test_agent")
        agent = AlarmAgent(config)

        mock_server = MagicMock()
        mock_server.name = "alarm"

        mock_tool = MagicMock()
        mock_tool.name = "acknowledge_alarm"
        mock_server.list_tools.return_value = [mock_tool]

        agent._mcp_servers["alarm"] = mock_server
        return agent

    @pytest.mark.asyncio
    async def test_batch_acknowledge_all_success(self, agent):
        """测试批量确认全部成功"""
        agent.call_tool = AsyncMock(return_value={
            "success": True,
            "result": {"success": True}
        })

        result = await agent.batch_acknowledge(
            ["ALM-001", "ALM-002", "ALM-003"],
            "张工"
        )

        assert result["success"] is True
        assert result["success_count"] == 3
        assert result["fail_count"] == 0

    @pytest.mark.asyncio
    async def test_batch_acknowledge_partial_fail(self, agent):
        """测试批量确认部分失败"""
        agent.call_tool = AsyncMock(side_effect=[
            {"success": True, "result": {"success": True}},
            {"success": True, "result": {"success": False, "message": "告警不存在"}},
            {"success": True, "result": {"success": True}},
        ])

        result = await agent.batch_acknowledge(
            ["ALM-001", "ALM-002", "ALM-003"],
            "张工"
        )

        assert result["success"] is False
        assert result["success_count"] == 2
        assert result["fail_count"] == 1


class TestAssessUrgency:
    """紧急程度评估测试"""

    @pytest.fixture
    def agent(self):
        config = AlarmAgentConfig(name="test_agent")
        return AlarmAgent(config)

    def test_critical_urgency(self, agent):
        """测试严重级别"""
        alarm = {"severity": "critical"}
        assert agent._assess_urgency(alarm) == "紧急"

    def test_warning_urgency(self, agent):
        """测试警告级别"""
        alarm = {"severity": "warning"}
        assert agent._assess_urgency(alarm) == "较高"

    def test_info_urgency(self, agent):
        """测试信息级别"""
        alarm = {"severity": "info"}
        assert agent._assess_urgency(alarm) == "一般"


class TestAssessImpact:
    """影响评估测试"""

    @pytest.fixture
    def agent(self):
        config = AlarmAgentConfig(name="test_agent")
        return AlarmAgent(config)

    def test_hvac_impact(self, agent):
        """测试空调设备影响"""
        alarm = {"device_type": "hvac"}
        impact = agent._assess_impact(alarm)
        assert "多个区域" in impact

    def test_fire_alarm_impact(self, agent):
        """测试消防设备影响"""
        alarm = {"device_type": "fire_alarm"}
        impact = agent._assess_impact(alarm)
        assert "安全" in impact

    def test_lighting_impact(self, agent):
        """测试照明设备影响"""
        alarm = {"device_type": "lighting"}
        impact = agent._assess_impact(alarm)
        assert "有限" in impact
