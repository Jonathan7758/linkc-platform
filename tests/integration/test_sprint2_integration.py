"""
Sprint 2 Integration Tests — Knowledge Layer End-to-End

Tests the full flow: K1 + K2 + K3 + G8/G9 APIs + Seed Data
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from knowledge.scenario_kb import ScenarioKnowledge, ScenarioKnowledgeBase, PromptTemplate
from knowledge.rule_engine import GovernanceRule, GovernanceRuleEngine, RuleEvalResult
from knowledge.decision_logger import (
    DecisionContext, DecisionOutcome, DecisionRecord, DecisionLogger,
)
from knowledge.seed_data import load_tower_c_seed_data
from api.knowledge_api import (
    KnowledgeManagementAPI,
    RuleManagementAPI,
    DecisionLogAPI,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def kb():
    return ScenarioKnowledgeBase()


@pytest.fixture
def engine():
    return GovernanceRuleEngine()


@pytest.fixture
def decision_logger():
    return DecisionLogger()


# ============================================================
# Test 1: Seed Data Loading
# ============================================================

class TestSeedDataLoading:
    """Tower C 种子数据加载测试"""

    @pytest.mark.asyncio
    async def test_load_tower_c_knowledge(self, kb):
        result = await load_tower_c_seed_data(kb)
        assert result["knowledge_loaded"] >= 6
        assert result["templates_loaded"] >= 1

    @pytest.mark.asyncio
    async def test_seed_knowledge_queryable(self, kb):
        await load_tower_c_seed_data(kb)
        items = await kb.query_applicable_knowledge(
            scenario_category="cleaning",
        )
        assert len(items) >= 5

    @pytest.mark.asyncio
    async def test_seed_template_exists(self, kb):
        await load_tower_c_seed_data(kb)
        template = await kb.get_prompt_template("pt-tc-001")
        assert template is not None
        assert template.agent_type == "cleaning_scheduler"

    @pytest.mark.asyncio
    async def test_seed_rules_load(self, engine):
        count = await engine.load_tower_c_seed_rules()
        assert count == 6

    @pytest.mark.asyncio
    async def test_seed_rules_idempotent(self, engine):
        first = await engine.load_tower_c_seed_rules()
        second = await engine.load_tower_c_seed_rules()
        assert first == 6
        assert second == 0


# ============================================================
# Test 2: Knowledge + Rule Engine Integration
# ============================================================

class TestKnowledgeRuleIntegration:
    """K1 + K2 协同工作测试"""

    @pytest.mark.asyncio
    async def test_prompt_assembly_with_seed_data(self, kb):
        """种子数据加载后，Prompt组装应注入领域知识"""
        await load_tower_c_seed_data(kb)

        prompt = await kb.assemble_prompt(
            template_id="pt-tc-001",
            variables={
                "building_name": "Tower C",
                "current_time": "08:00",
                "robot_count": "20",
            },
            scenario_category="cleaning",
            context={"building_type": "office_tower"},
        )
        assert "Tower C" in prompt
        assert "20" in prompt
        assert len(prompt) > 100  # should have knowledge injected

    @pytest.mark.asyncio
    async def test_rule_evaluation_blocks_low_battery(self, engine):
        """低电量机器人应被规则引擎阻止"""
        await engine.load_tower_c_seed_rules()

        results = await engine.evaluate(
            decision={"task_type": "standard", "robot_id": "r-001"},
            context={"battery_level": 15, "robot_status": "idle"},
        )

        block_results = [r for r in results if r.action_type == "block"]
        assert len(block_results) >= 1
        assert any("电量" in r.message for r in block_results)

    @pytest.mark.asyncio
    async def test_rule_evaluation_blocks_error_robot(self, engine):
        """错误状态机器人应被阻止"""
        await engine.load_tower_c_seed_rules()

        results = await engine.evaluate(
            decision={"task_type": "standard"},
            context={"battery_level": 80, "robot_status": "error"},
        )

        block_results = [r for r in results if r.action_type == "block"]
        assert len(block_results) >= 1

    @pytest.mark.asyncio
    async def test_rule_evaluation_warns_moderate_battery(self, engine):
        """中等电量应警告"""
        await engine.load_tower_c_seed_rules()

        results = await engine.evaluate(
            decision={"task_type": "standard"},
            context={"battery_level": 45, "robot_status": "idle"},
        )

        warn_results = [r for r in results if r.action_type == "warn"]
        assert len(warn_results) >= 1

    @pytest.mark.asyncio
    async def test_rule_evaluation_passes_healthy_robot(self, engine):
        """健康机器人不应被阻止"""
        await engine.load_tower_c_seed_rules()

        results = await engine.evaluate(
            decision={"task_type": "standard"},
            context={"battery_level": 85, "robot_status": "idle"},
        )

        block_results = [r for r in results if r.action_type == "block"]
        assert len(block_results) == 0


# ============================================================
# Test 3: Decision Logger Integration
# ============================================================

class TestDecisionLogIntegration:
    """K3 决策日志完整生命周期测试"""

    @pytest.mark.asyncio
    async def test_full_decision_lifecycle(self, decision_logger):
        """Context -> Decision -> Outcome 完整三元组"""
        from datetime import datetime, timezone

        # 1. Log decision
        ctx = DecisionContext(
            trigger_type="scheduled",
            llm_model="claude-3",
            llm_latency_ms=120,
            validation_passed=True,
            knowledge_used=["sk-tc-001", "sk-tc-002"],
            rules_evaluated=["gr-tc-001", "gr-tc-003"],
        )
        record = DecisionRecord(
            record_id="",
            agent_id="cleaning-agent-001",
            agent_type="cleaning_scheduler",
            decision_type="schedule",
            timestamp=datetime.now(timezone.utc),
            context=ctx,
            decision={
                "action": "schedule",
                "assignments": [
                    {"robot_id": "r-001", "zone_id": "zone-3F", "task_type": "standard"},
                ],
            },
        )
        record_id = await decision_logger.log_decision(record)
        assert record_id.startswith("dr-")

        # 2. Verify stored
        records = await decision_logger.query_decisions(agent_type="cleaning_scheduler")
        assert len(records) == 1

        # 3. Update outcome
        outcome = DecisionOutcome(
            task_completion_status="completed",
            actual_duration_minutes=45.0,
            quality_score=0.92,
        )
        ok = await decision_logger.update_outcome(record_id, outcome)
        assert ok is True

        # 4. Verify stats
        stats = await decision_logger.get_decision_stats("cleaning_scheduler")
        assert stats["total_decisions"] == 1
        assert stats["avg_quality_score"] == 0.92
        assert stats["validation_pass_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_mark_training_after_outcomes(self, decision_logger):
        """有outcome的高质量记录可标记为训练候选"""
        from datetime import datetime, timezone

        # Log and fill outcome
        for i in range(5):
            record = DecisionRecord(
                record_id=f"dr-train-{i:03d}",
                agent_id="agent-001",
                agent_type="cleaning_scheduler",
                decision_type="schedule",
                timestamp=datetime.now(timezone.utc),
                context=DecisionContext(validation_passed=True),
                decision={"action": "schedule"},
            )
            await decision_logger.log_decision(record)

            score = 0.6 + (i * 0.1)  # 0.6, 0.7, 0.8, 0.9, 1.0
            outcome = DecisionOutcome(
                task_completion_status="completed",
                quality_score=score,
            )
            await decision_logger.update_outcome(f"dr-train-{i:03d}", outcome)

        # Mark high-quality records
        marked = await decision_logger.mark_training_candidates({
            "min_quality_score": 0.8,
            "agent_type": "cleaning_scheduler",
        })
        assert marked == 3  # scores 0.8, 0.9, 1.0


# ============================================================
# Test 4: G8 Knowledge Management API
# ============================================================

class TestG8KnowledgeAPI:
    """G8 知识管理 API 测试"""

    @pytest.fixture
    def api(self, kb):
        return KnowledgeManagementAPI(kb)

    @pytest.mark.asyncio
    async def test_create_and_get_knowledge(self, api):
        result = await api.create_knowledge({
            "knowledge_id": "sk-test-001",
            "knowledge_type": "domain_fact",
            "scenario_category": "cleaning",
            "name": "Test knowledge",
            "content": {"fact": "test fact"},
        })
        assert result["status"] == "created"
        assert result["knowledge_id"] == "sk-test-001"

        got = await api.get_knowledge("sk-test-001")
        assert got["name"] == "Test knowledge"
        assert got["content"]["fact"] == "test fact"

    @pytest.mark.asyncio
    async def test_get_not_found(self, api):
        result = await api.get_knowledge("nonexistent")
        assert result["error"] == "not_found"

    @pytest.mark.asyncio
    async def test_update_knowledge(self, api):
        await api.create_knowledge({
            "knowledge_id": "sk-upd-001",
            "knowledge_type": "domain_fact",
            "scenario_category": "cleaning",
            "name": "Original",
        })
        result = await api.update_knowledge("sk-upd-001", {"name": "Updated"})
        assert result["status"] == "updated"

        got = await api.get_knowledge("sk-upd-001")
        assert got["name"] == "Updated"

    @pytest.mark.asyncio
    async def test_delete_knowledge(self, api):
        await api.create_knowledge({
            "knowledge_id": "sk-del-001",
            "knowledge_type": "domain_fact",
            "scenario_category": "cleaning",
            "name": "To delete",
        })
        result = await api.delete_knowledge("sk-del-001")
        assert result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_list_knowledge(self, api):
        for i in range(3):
            await api.create_knowledge({
                "knowledge_id": f"sk-list-{i:03d}",
                "knowledge_type": "domain_fact",
                "scenario_category": "cleaning",
                "name": f"Knowledge {i}",
            })
        result = await api.list_knowledge({"scenario_category": "cleaning"})
        assert result["total"] == 3

    @pytest.mark.asyncio
    async def test_create_and_get_template(self, api):
        result = await api.create_template({
            "template_id": "pt-test-001",
            "agent_type": "cleaning_scheduler",
            "name": "Test Template",
            "system_prompt": "You are a {{role}}.",
            "variables": ["role"],
        })
        assert result["status"] == "created"

        got = await api.get_template("pt-test-001")
        assert got["name"] == "Test Template"


# ============================================================
# Test 5: G9 Rule Management API
# ============================================================

class TestG9RuleAPI:
    """G9 规则管理 API 测试"""

    @pytest.fixture
    def api(self, engine):
        return RuleManagementAPI(engine)

    @pytest.mark.asyncio
    async def test_create_and_get_rule(self, api):
        result = await api.create_rule({
            "rule_id": "gr-test-001",
            "rule_name": "Test rule",
            "condition": {"field": "battery_level", "operator": "<", "value": 20},
            "action_type": "block",
        })
        assert result["status"] == "created"

        got = await api.get_rule("gr-test-001")
        assert got["rule_name"] == "Test rule"

    @pytest.mark.asyncio
    async def test_update_rule(self, api):
        await api.create_rule({
            "rule_id": "gr-upd-001",
            "rule_name": "Original",
        })
        result = await api.update_rule("gr-upd-001", {"rule_name": "Updated"})
        assert result["status"] == "updated"

    @pytest.mark.asyncio
    async def test_disable_rule(self, api):
        await api.create_rule({
            "rule_id": "gr-dis-001",
            "rule_name": "To disable",
        })
        result = await api.disable_rule("gr-dis-001")
        assert result["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_list_rules(self, api):
        await api.create_rule({
            "rule_id": "gr-list-001",
            "rule_name": "Rule 1",
            "scope": "system",
        })
        await api.create_rule({
            "rule_id": "gr-list-002",
            "rule_name": "Rule 2",
            "scope": "zone",
        })
        result = await api.list_rules({"scope": "system"})
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_evaluate_rules(self, api):
        await api.create_rule({
            "rule_id": "gr-eval-001",
            "rule_name": "Low battery block",
            "condition": {"field": "battery_level", "operator": "<", "value": 20},
            "action_type": "block",
            "action_config": {"message": "低电量"},
        })
        result = await api.evaluate_rules({
            "decision": {"task_type": "standard"},
            "context": {"battery_level": 15},
        })
        assert result["block_count"] == 1
        assert len(result["results"]) == 1

    @pytest.mark.asyncio
    async def test_load_seed_rules(self, api):
        result = await api.load_seed_rules()
        assert result["loaded"] == 6


# ============================================================
# Test 6: Decision Log API
# ============================================================

class TestDecisionLogAPI:
    """Decision Log API 测试"""

    @pytest.fixture
    def api(self, decision_logger):
        return DecisionLogAPI(decision_logger)

    @pytest.mark.asyncio
    async def test_log_and_query(self, api):
        result = await api.log_decision({
            "agent_id": "agent-001",
            "agent_type": "cleaning_scheduler",
            "decision_type": "schedule",
            "decision": {"action": "schedule"},
            "context": {"trigger_type": "scheduled", "llm_latency_ms": 100},
        })
        assert result["status"] == "logged"
        record_id = result["record_id"]

        query_result = await api.query_decisions({"agent_type": "cleaning_scheduler"})
        assert query_result["total"] == 1

    @pytest.mark.asyncio
    async def test_update_outcome_via_api(self, api):
        result = await api.log_decision({
            "agent_id": "agent-001",
            "agent_type": "cleaning_scheduler",
            "decision_type": "schedule",
            "decision": {"action": "schedule"},
        })
        record_id = result["record_id"]

        outcome_result = await api.update_outcome(record_id, {
            "task_completion_status": "completed",
            "quality_score": 0.95,
            "actual_duration_minutes": 30.0,
        })
        assert outcome_result["status"] == "updated"

    @pytest.mark.asyncio
    async def test_get_stats_via_api(self, api):
        await api.log_decision({
            "agent_id": "agent-001",
            "agent_type": "cleaning_scheduler",
            "decision_type": "schedule",
            "decision": {"action": "schedule"},
            "context": {"llm_latency_ms": 120, "validation_passed": True},
        })
        stats = await api.get_stats("cleaning_scheduler")
        assert stats["total_decisions"] == 1


# ============================================================
# Test 7: Cross-module Integration
# ============================================================

class TestCrossModuleIntegration:
    """跨模块集成测试: K1+K2+K3 完整流程"""

    @pytest.mark.asyncio
    async def test_full_decision_pipeline_with_knowledge(self):
        """完整决策流水线: 加载知识 -> 组装Prompt -> 规则评估 -> 记录日志"""
        # Setup
        kb = ScenarioKnowledgeBase()
        engine = GovernanceRuleEngine()
        dl = DecisionLogger()

        # 1. Load seed data
        await load_tower_c_seed_data(kb)
        await engine.load_tower_c_seed_rules()

        # 2. Query applicable knowledge
        knowledge = await kb.query_applicable_knowledge(
            scenario_category="cleaning",
            building_type="office_tower",
        )
        assert len(knowledge) >= 4

        # 3. Assemble prompt
        prompt = await kb.assemble_prompt(
            template_id="pt-tc-001",
            variables={
                "building_name": "Tower C",
                "current_time": "07:30",
                "robot_count": "20",
            },
            scenario_category="cleaning",
            context={"building_type": "office_tower"},
        )
        assert len(prompt) > 200

        # 4. Simulate agent decision
        decision = {
            "action": "schedule",
            "assignments": [
                {"robot_id": "r-001", "zone_id": "zone-1F-lobby", "task_type": "standard"},
                {"robot_id": "r-002", "zone_id": "zone-3F-dining", "task_type": "deep"},
            ],
        }

        # 5. Evaluate rules
        results = await engine.evaluate(
            decision=decision,
            context={"battery_level": 85, "robot_status": "idle"},
        )
        has_block = any(r.action_type == "block" for r in results)
        assert not has_block  # healthy robot should pass

        # 6. Log decision
        from datetime import datetime, timezone
        knowledge_ids = [k.knowledge_id for k in knowledge[:3]]
        ctx = DecisionContext(
            trigger_type="scheduled",
            llm_model="claude-3",
            llm_latency_ms=150,
            validation_passed=True,
            knowledge_used=knowledge_ids,
            rules_evaluated=["gr-tc-001", "gr-tc-003", "gr-tc-010"],
        )
        record = DecisionRecord(
            record_id="",
            agent_id="cleaning-agent-001",
            agent_type="cleaning_scheduler",
            decision_type="schedule",
            timestamp=datetime.now(timezone.utc),
            context=ctx,
            decision=decision,
        )
        record_id = await dl.log_decision(record)
        assert record_id.startswith("dr-")

        # 7. Fill outcome
        outcome = DecisionOutcome(
            task_completion_status="completed",
            actual_duration_minutes=40.0,
            quality_score=0.88,
        )
        await dl.update_outcome(record_id, outcome)

        # 8. Record knowledge usage
        for kid in knowledge_ids:
            await kb.record_usage(kid, outcome_score=0.88)

        # 9. Verify stats
        stats = await dl.get_decision_stats("cleaning_scheduler")
        assert stats["total_decisions"] == 1
        assert stats["avg_quality_score"] == 0.88

    @pytest.mark.asyncio
    async def test_rule_blocks_prevent_scheduling(self):
        """规则阻止应阻止调度并记录日志"""
        engine = GovernanceRuleEngine()
        dl = DecisionLogger()
        await engine.load_tower_c_seed_rules()

        # Low battery scenario
        results = await engine.evaluate(
            decision={"task_type": "standard"},
            context={"battery_level": 10, "robot_status": "idle"},
        )
        blocks = [r for r in results if r.action_type == "block"]
        assert len(blocks) >= 1

        # Log the blocked decision
        from datetime import datetime, timezone
        ctx = DecisionContext(
            trigger_type="scheduled",
            validation_passed=False,
            validation_errors=[{"rule": blocks[0].rule_id, "message": blocks[0].message}],
            rules_evaluated=[r.rule_id for r in results],
        )
        record = DecisionRecord(
            record_id="",
            agent_id="cleaning-agent-001",
            agent_type="cleaning_scheduler",
            decision_type="schedule",
            timestamp=datetime.now(timezone.utc),
            context=ctx,
            decision={"action": "cancelled", "reason": "rule_blocked"},
        )
        await dl.log_decision(record)

        # Verify blocked decision logged
        records = await dl.query_decisions(agent_type="cleaning_scheduler")
        assert len(records) == 1
        assert records[0].context.validation_passed is False

    @pytest.mark.asyncio
    async def test_api_layer_end_to_end(self):
        """G8+G9+DecisionLog API 端到端测试"""
        kb = ScenarioKnowledgeBase()
        engine = GovernanceRuleEngine()
        dl = DecisionLogger()

        g8 = KnowledgeManagementAPI(kb)
        g9 = RuleManagementAPI(engine)
        log_api = DecisionLogAPI(dl)

        # Load seed via APIs
        await load_tower_c_seed_data(kb)
        seed_result = await g9.load_seed_rules()
        assert seed_result["loaded"] == 6

        # Query knowledge via G8
        knowledge_result = await g8.list_knowledge({"scenario_category": "cleaning"})
        assert knowledge_result["total"] >= 5

        # Evaluate via G9
        eval_result = await g9.evaluate_rules({
            "decision": {"task_type": "standard"},
            "context": {"battery_level": 85, "robot_status": "idle"},
        })
        assert eval_result["block_count"] == 0

        # Log via DecisionLogAPI
        log_result = await log_api.log_decision({
            "agent_id": "agent-001",
            "agent_type": "cleaning_scheduler",
            "decision_type": "schedule",
            "decision": {"action": "schedule"},
            "context": {"llm_latency_ms": 100, "validation_passed": True},
        })
        assert log_result["status"] == "logged"

        # Stats via API
        stats = await log_api.get_stats("cleaning_scheduler")
        assert stats["total_decisions"] == 1
