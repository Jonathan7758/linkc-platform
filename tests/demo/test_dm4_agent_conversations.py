"""
DM4: Agent对话增强单元测试

测试范围:
- 预设场景处理
- 推理过程生成
- 确认操作流程
- 学习反馈记录
"""

import pytest
import pytest_asyncio
from datetime import datetime

from src.demo.agent_conversations import (
    AgentConversationService,
    ConversationScenario,
    AgentResponse,
    ReasoningStep,
    ConversationMessage
)


class TestReasoningStep:
    """测试推理步骤"""

    def test_reasoning_step_init(self):
        """测试推理步骤初始化"""
        step = ReasoningStep(
            step=1,
            action="parse_intent",
            description="解析用户意图",
            result="创建任务",
            duration_ms=45
        )

        assert step.step == 1
        assert step.action == "parse_intent"
        assert step.description == "解析用户意图"
        assert step.result == "创建任务"
        assert step.duration_ms == 45


class TestAgentResponse:
    """测试Agent响应"""

    def test_response_init(self):
        """测试响应初始化"""
        steps = [
            ReasoningStep(step=1, action="parse", description="解析", duration_ms=30)
        ]

        response = AgentResponse(
            message="测试消息",
            reasoning_steps=steps,
            suggestions=["建议1", "建议2"],
            requires_confirmation=True
        )

        assert response.message == "测试消息"
        assert len(response.reasoning_steps) == 1
        assert len(response.suggestions) == 2
        assert response.requires_confirmation is True

    def test_response_to_dict(self):
        """测试响应转字典"""
        steps = [
            ReasoningStep(step=1, action="parse", description="解析", result="完成", duration_ms=30)
        ]

        response = AgentResponse(
            message="测试消息",
            reasoning_steps=steps,
            metadata={"key": "value"}
        )

        d = response.to_dict()

        assert d["message"] == "测试消息"
        assert len(d["reasoning_steps"]) == 1
        assert d["reasoning_steps"][0]["step"] == 1
        assert d["metadata"]["key"] == "value"


class TestConversationMessage:
    """测试对话消息"""

    def test_message_init(self):
        """测试消息初始化"""
        msg = ConversationMessage(
            role="user",
            content="你好"
        )

        assert msg.role == "user"
        assert msg.content == "你好"
        assert msg.reasoning is None

    def test_message_to_dict(self):
        """测试消息转字典"""
        msg = ConversationMessage(
            role="agent",
            content="你好，有什么可以帮您？"
        )

        d = msg.to_dict()

        assert d["role"] == "agent"
        assert d["content"] == "你好，有什么可以帮您？"
        assert "timestamp" in d


class TestAgentConversationService:
    """测试Agent对话服务"""

    @pytest_asyncio.fixture
    async def service(self):
        """创建测试用服务实例"""
        # 重置单例
        AgentConversationService._instance = None
        svc = AgentConversationService()
        yield svc
        # 清理
        AgentConversationService._instance = None

    def test_get_preset_scenarios(self, service):
        """测试获取预设场景"""
        scenarios = service.get_preset_scenarios()

        assert len(scenarios) == 5

        scenario_ids = [s["id"] for s in scenarios]
        assert "task_scheduling" in scenario_ids
        assert "status_query" in scenario_ids
        assert "problem_diagnosis" in scenario_ids
        assert "data_analysis" in scenario_ids
        assert "batch_operation" in scenario_ids

        # 验证场景包含示例输入
        for scenario in scenarios:
            assert "sample_inputs" in scenario
            assert len(scenario["sample_inputs"]) > 0

    @pytest.mark.asyncio
    async def test_process_message_task_scheduling(self, service):
        """测试任务调度场景"""
        response = await service.process_message(
            session_id="test_session_1",
            user_message="安排明天早上8点大堂深度清洁",
            scenario=ConversationScenario.TASK_SCHEDULING
        )

        assert isinstance(response, AgentResponse)
        assert "大堂" in response.message or "清洁" in response.message
        assert len(response.reasoning_steps) > 0
        assert response.requires_confirmation is True

        # 验证推理步骤
        actions = [s.action for s in response.reasoning_steps]
        assert "parse_intent" in actions

    @pytest.mark.asyncio
    async def test_process_message_status_query(self, service):
        """测试状态查询场景"""
        response = await service.process_message(
            session_id="test_session_2",
            user_message="现在有哪些机器人空闲",
            scenario=ConversationScenario.STATUS_QUERY
        )

        assert isinstance(response, AgentResponse)
        assert "空闲" in response.message or "机器人" in response.message
        assert len(response.reasoning_steps) > 0

    @pytest.mark.asyncio
    async def test_process_message_problem_diagnosis(self, service):
        """测试问题诊断场景"""
        response = await service.process_message(
            session_id="test_session_3",
            user_message="28楼的机器人怎么停了",
            scenario=ConversationScenario.PROBLEM_DIAGNOSIS
        )

        assert isinstance(response, AgentResponse)
        assert len(response.reasoning_steps) > 0
        assert response.requires_confirmation is True

        # 验证包含诊断步骤
        actions = [s.action for s in response.reasoning_steps]
        assert "diagnose" in actions or "analyze_logs" in actions

    @pytest.mark.asyncio
    async def test_process_message_data_analysis(self, service):
        """测试数据分析场景"""
        response = await service.process_message(
            session_id="test_session_4",
            user_message="这周的清洁效率怎么样",
            scenario=ConversationScenario.DATA_ANALYSIS
        )

        assert isinstance(response, AgentResponse)
        assert "效率" in response.message or "分析" in response.message
        assert len(response.reasoning_steps) > 0

        # 验证包含分析步骤
        actions = [s.action for s in response.reasoning_steps]
        assert "trend_analysis" in actions or "calculate_metrics" in actions

    @pytest.mark.asyncio
    async def test_process_message_batch_operation(self, service):
        """测试批量操作场景"""
        response = await service.process_message(
            session_id="test_session_5",
            user_message="把所有电量低于30%的机器人召回充电",
            scenario=ConversationScenario.BATCH_OPERATION
        )

        assert isinstance(response, AgentResponse)
        assert len(response.reasoning_steps) > 0
        assert response.requires_confirmation is True
        assert len(response.actions) > 0

    @pytest.mark.asyncio
    async def test_scenario_detection(self, service):
        """测试场景自动检测"""
        # 任务调度
        response1 = await service.process_message(
            session_id="test_detect_1",
            user_message="帮我安排一个清洁任务"
        )
        assert "metadata" in response1.to_dict()

        # 状态查询
        response2 = await service.process_message(
            session_id="test_detect_2",
            user_message="机器人现在在哪里"
        )
        assert response2 is not None

        # 问题诊断
        response3 = await service.process_message(
            session_id="test_detect_3",
            user_message="机器人怎么了"
        )
        assert response3 is not None

    @pytest.mark.asyncio
    async def test_confirm_action_approved(self, service):
        """测试确认操作 - 批准"""
        # 先发送一条需要确认的消息
        await service.process_message(
            session_id="test_confirm_1",
            user_message="安排大堂清洁",
            scenario=ConversationScenario.TASK_SCHEDULING
        )

        # 确认操作
        result = await service.confirm_action(
            session_id="test_confirm_1",
            confirmed=True
        )

        assert result["confirmed"] is True
        assert result["status"] == "executed"

    @pytest.mark.asyncio
    async def test_confirm_action_rejected_with_feedback(self, service):
        """测试确认操作 - 拒绝并反馈"""
        # 先发送一条需要确认的消息
        await service.process_message(
            session_id="test_confirm_2",
            user_message="安排大堂清洁",
            scenario=ConversationScenario.TASK_SCHEDULING
        )

        # 拒绝并提供反馈
        result = await service.confirm_action(
            session_id="test_confirm_2",
            confirmed=False,
            feedback="我想选择机器人B-01而不是A-01"
        )

        assert result["confirmed"] is False
        assert result["status"] == "cancelled"
        assert result.get("learning_recorded") is True

    @pytest.mark.asyncio
    async def test_record_learning(self, service):
        """测试记录学习"""
        result = await service.record_learning(
            session_id="test_learning_1",
            feedback="这个区域应该优先选择带拖地功能的机器人"
        )

        assert result["success"] is True
        assert "learning_id" in result

        # 验证学习记录已保存
        records = service.get_learning_records()
        assert len(records) > 0

        last_record = records[-1]
        assert "拖地功能" in last_record["feedback"]

    @pytest.mark.asyncio
    async def test_run_demo_conversation(self, service):
        """测试运行演示对话"""
        result = await service.run_demo_conversation(
            ConversationScenario.TASK_SCHEDULING
        )

        assert "session_id" in result
        assert result["scenario"] == "task_scheduling"
        assert "user_input" in result
        assert "response" in result
        assert "conversation" in result

        # 验证对话包含用户消息和Agent响应
        assert len(result["conversation"]) >= 2

    @pytest.mark.asyncio
    async def test_get_conversation_history(self, service):
        """测试获取会话历史"""
        session_id = "test_history_1"

        # 发送几条消息
        await service.process_message(session_id, "你好")
        await service.process_message(session_id, "机器人状态如何")

        # 获取历史
        history = service.get_conversation(session_id)

        assert len(history) >= 4  # 2条用户消息 + 2条Agent回复

        # 验证消息格式
        for msg in history:
            assert "role" in msg
            assert "content" in msg
            assert "timestamp" in msg

    @pytest.mark.asyncio
    async def test_clear_conversation(self, service):
        """测试清除会话"""
        session_id = "test_clear_1"

        # 发送消息
        await service.process_message(session_id, "测试消息")

        # 验证会话存在
        history = service.get_conversation(session_id)
        assert len(history) > 0

        # 清除会话
        success = service.clear_conversation(session_id)
        assert success is True

        # 验证会话已清除
        history = service.get_conversation(session_id)
        assert len(history) == 0

    @pytest.mark.asyncio
    async def test_fallback_response(self, service):
        """测试默认响应"""
        response = await service.process_message(
            session_id="test_fallback",
            user_message="今天天气怎么样"  # 不相关的问题
        )

        # 应该返回帮助信息
        assert "抱歉" in response.message or "可以尝试" in response.message or "任务" in response.message

    @pytest.mark.asyncio
    async def test_reasoning_steps_have_duration(self, service):
        """测试推理步骤包含耗时"""
        response = await service.process_message(
            session_id="test_duration",
            user_message="安排清洁任务",
            scenario=ConversationScenario.TASK_SCHEDULING
        )

        for step in response.reasoning_steps:
            assert step.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_multiple_sessions(self, service):
        """测试多会话隔离"""
        # 会话1
        await service.process_message("session_a", "查询状态")

        # 会话2
        await service.process_message("session_b", "安排任务")

        # 验证会话隔离
        history_a = service.get_conversation("session_a")
        history_b = service.get_conversation("session_b")

        assert len(history_a) == 2
        assert len(history_b) == 2

        # 内容不同
        assert history_a[0]["content"] != history_b[0]["content"]


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
