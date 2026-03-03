"""
Comprehensive unit tests for the K2 GovernanceRuleEngine module.

Covers CRUD, filtered queries, condition compilation, evaluation,
seed-data loading, and the _resolve_field_path helper.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from datetime import datetime, timedelta

import pytest
import pytest_asyncio

from knowledge.rule_engine import (
    CompiledCondition,
    GovernanceRule,
    GovernanceRuleEngine,
    RuleEvalResult,
    _resolve_field_path,
)


# ================================================================
# Fixtures
# ================================================================


@pytest_asyncio.fixture
async def engine() -> GovernanceRuleEngine:
    """Return a fresh, empty GovernanceRuleEngine."""
    return GovernanceRuleEngine()


def _make_rule(
    rule_id: str = "r-001",
    rule_name: str = "Test Rule",
    **kwargs,
) -> GovernanceRule:
    """Shorthand factory for GovernanceRule with sensible defaults."""
    return GovernanceRule(rule_id=rule_id, rule_name=rule_name, **kwargs)


# ================================================================
# 1. CRUD tests
# ================================================================


class TestCRUD:
    """Tests for create_rule, get_rule, update_rule, disable_rule."""

    @pytest.mark.asyncio
    async def test_create_rule_returns_id(self, engine: GovernanceRuleEngine):
        rule = _make_rule()
        result = await engine.create_rule(rule)
        assert result == "r-001"

    @pytest.mark.asyncio
    async def test_create_rule_sets_created_at(self, engine: GovernanceRuleEngine):
        rule = _make_rule()
        await engine.create_rule(rule)
        assert rule.created_at is not None
        assert isinstance(rule.created_at, datetime)

    @pytest.mark.asyncio
    async def test_create_rule_duplicate_raises(self, engine: GovernanceRuleEngine):
        await engine.create_rule(_make_rule())
        with pytest.raises(ValueError, match="already exists"):
            await engine.create_rule(_make_rule())

    @pytest.mark.asyncio
    async def test_get_rule_found(self, engine: GovernanceRuleEngine):
        await engine.create_rule(_make_rule())
        rule = await engine.get_rule("r-001")
        assert rule is not None
        assert rule.rule_name == "Test Rule"

    @pytest.mark.asyncio
    async def test_get_rule_not_found(self, engine: GovernanceRuleEngine):
        result = await engine.get_rule("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_rule_success(self, engine: GovernanceRuleEngine):
        await engine.create_rule(_make_rule())
        updated = await engine.update_rule("r-001", {"priority": 99})
        assert updated is True
        rule = await engine.get_rule("r-001")
        assert rule.priority == 99

    @pytest.mark.asyncio
    async def test_update_rule_unknown_field_ignored(
        self, engine: GovernanceRuleEngine
    ):
        await engine.create_rule(_make_rule())
        updated = await engine.update_rule("r-001", {"nonexistent_field": 42})
        assert updated is True  # still returns True
        rule = await engine.get_rule("r-001")
        assert not hasattr(rule, "nonexistent_field") or getattr(rule, "nonexistent_field", None) is None

    @pytest.mark.asyncio
    async def test_update_rule_not_found(self, engine: GovernanceRuleEngine):
        result = await engine.update_rule("missing", {"priority": 1})
        assert result is False

    @pytest.mark.asyncio
    async def test_disable_rule_success(self, engine: GovernanceRuleEngine):
        await engine.create_rule(_make_rule())
        disabled = await engine.disable_rule("r-001")
        assert disabled is True
        rule = await engine.get_rule("r-001")
        assert rule.enabled is False

    @pytest.mark.asyncio
    async def test_disable_rule_not_found(self, engine: GovernanceRuleEngine):
        result = await engine.disable_rule("missing")
        assert result is False


# ================================================================
# 2. get_active_rules tests
# ================================================================


class TestGetActiveRules:
    """Tests for filtered active-rule queries."""

    @pytest.mark.asyncio
    async def test_filter_by_scope(self, engine: GovernanceRuleEngine):
        await engine.create_rule(_make_rule("r1", "Rule 1", scope="zone"))
        await engine.create_rule(_make_rule("r2", "Rule 2", scope="system"))
        results = await engine.get_active_rules(scope="zone")
        assert len(results) == 1
        assert results[0].rule_id == "r1"

    @pytest.mark.asyncio
    async def test_filter_by_agent_type(self, engine: GovernanceRuleEngine):
        await engine.create_rule(
            _make_rule("r1", "Rule 1", applicable_agent_types=["cleaner"])
        )
        await engine.create_rule(
            _make_rule("r2", "Rule 2", applicable_agent_types=["delivery"])
        )
        results = await engine.get_active_rules(agent_type="cleaner")
        assert len(results) == 1
        assert results[0].rule_id == "r1"

    @pytest.mark.asyncio
    async def test_filter_agent_type_empty_list_means_all(
        self, engine: GovernanceRuleEngine
    ):
        """Rule with no applicable_agent_types matches any agent_type."""
        await engine.create_rule(_make_rule("r1", "Universal"))
        results = await engine.get_active_rules(agent_type="anything")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_filter_by_building_id(self, engine: GovernanceRuleEngine):
        await engine.create_rule(
            _make_rule("r1", "Rule 1", applicable_building_ids=["bldg-A"])
        )
        await engine.create_rule(
            _make_rule("r2", "Rule 2", applicable_building_ids=["bldg-B"])
        )
        results = await engine.get_active_rules(building_id="bldg-A")
        assert len(results) == 1
        assert results[0].rule_id == "r1"

    @pytest.mark.asyncio
    async def test_filter_by_zone_id(self, engine: GovernanceRuleEngine):
        await engine.create_rule(
            _make_rule("r1", "Rule 1", applicable_zone_ids=["z-100"])
        )
        await engine.create_rule(
            _make_rule("r2", "Rule 2", applicable_zone_ids=["z-200"])
        )
        results = await engine.get_active_rules(zone_id="z-100")
        assert len(results) == 1
        assert results[0].rule_id == "r1"

    @pytest.mark.asyncio
    async def test_disabled_rules_excluded(self, engine: GovernanceRuleEngine):
        await engine.create_rule(_make_rule("r1", "Active"))
        await engine.create_rule(_make_rule("r2", "Disabled", enabled=False))
        results = await engine.get_active_rules()
        assert len(results) == 1
        assert results[0].rule_id == "r1"

    @pytest.mark.asyncio
    async def test_effective_period_future_excluded(
        self, engine: GovernanceRuleEngine
    ):
        future = datetime.utcnow() + timedelta(days=30)
        await engine.create_rule(
            _make_rule("r1", "Future Rule", effective_from=future)
        )
        results = await engine.get_active_rules()
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_effective_period_expired_excluded(
        self, engine: GovernanceRuleEngine
    ):
        past = datetime.utcnow() - timedelta(days=30)
        await engine.create_rule(
            _make_rule("r1", "Expired Rule", effective_until=past)
        )
        results = await engine.get_active_rules()
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_priority_ordering_descending(self, engine: GovernanceRuleEngine):
        await engine.create_rule(_make_rule("r-low", "Low", priority=10))
        await engine.create_rule(_make_rule("r-high", "High", priority=90))
        await engine.create_rule(_make_rule("r-mid", "Mid", priority=50))
        results = await engine.get_active_rules()
        priorities = [r.priority for r in results]
        assert priorities == [90, 50, 10]


# ================================================================
# 3. compile_condition + CompiledCondition.evaluate
# ================================================================


class TestCompiledCondition:
    """Tests for condition compilation and all supported operators."""

    # --- atomic operators ---

    def test_operator_eq(self):
        cc = CompiledCondition({"field": "x", "operator": "==", "value": 5})
        assert cc.evaluate({"x": 5}) is True
        assert cc.evaluate({"x": 6}) is False

    def test_operator_ne(self):
        cc = CompiledCondition({"field": "x", "operator": "!=", "value": 5})
        assert cc.evaluate({"x": 3}) is True
        assert cc.evaluate({"x": 5}) is False

    def test_operator_lt(self):
        cc = CompiledCondition({"field": "x", "operator": "<", "value": 10})
        assert cc.evaluate({"x": 5}) is True
        assert cc.evaluate({"x": 10}) is False

    def test_operator_gt(self):
        cc = CompiledCondition({"field": "x", "operator": ">", "value": 10})
        assert cc.evaluate({"x": 15}) is True
        assert cc.evaluate({"x": 10}) is False

    def test_operator_le(self):
        cc = CompiledCondition({"field": "x", "operator": "<=", "value": 10})
        assert cc.evaluate({"x": 10}) is True
        assert cc.evaluate({"x": 11}) is False

    def test_operator_ge(self):
        cc = CompiledCondition({"field": "x", "operator": ">=", "value": 10})
        assert cc.evaluate({"x": 10}) is True
        assert cc.evaluate({"x": 9}) is False

    def test_operator_in(self):
        cc = CompiledCondition(
            {"field": "status", "operator": "in", "value": ["ok", "warn"]}
        )
        assert cc.evaluate({"status": "ok"}) is True
        assert cc.evaluate({"status": "fail"}) is False

    def test_operator_not_in(self):
        cc = CompiledCondition(
            {"field": "status", "operator": "not_in", "value": ["ok", "warn"]}
        )
        assert cc.evaluate({"status": "fail"}) is True
        assert cc.evaluate({"status": "ok"}) is False

    def test_operator_contains(self):
        cc = CompiledCondition(
            {"field": "tags", "operator": "contains", "value": "vip"}
        )
        assert cc.evaluate({"tags": ["vip", "gold"]}) is True
        assert cc.evaluate({"tags": ["basic"]}) is False

    def test_operator_exists(self):
        cc = CompiledCondition(
            {"field": "sensor", "operator": "exists", "value": None}
        )
        assert cc.evaluate({"sensor": 42}) is True
        assert cc.evaluate({"other": 1}) is False

    # --- compound operators ---

    def test_compound_and(self):
        cc = CompiledCondition(
            {
                "and": [
                    {"field": "a", "operator": ">", "value": 0},
                    {"field": "b", "operator": "<", "value": 10},
                ]
            }
        )
        assert cc.evaluate({"a": 1, "b": 5}) is True
        assert cc.evaluate({"a": 1, "b": 15}) is False

    def test_compound_or(self):
        cc = CompiledCondition(
            {
                "or": [
                    {"field": "a", "operator": "==", "value": 1},
                    {"field": "a", "operator": "==", "value": 2},
                ]
            }
        )
        assert cc.evaluate({"a": 2}) is True
        assert cc.evaluate({"a": 3}) is False

    def test_compound_not(self):
        cc = CompiledCondition(
            {"not": {"field": "active", "operator": "==", "value": True}}
        )
        assert cc.evaluate({"active": False}) is True
        assert cc.evaluate({"active": True}) is False

    def test_nested_compound(self):
        cc = CompiledCondition(
            {
                "and": [
                    {"field": "x", "operator": ">", "value": 0},
                    {
                        "or": [
                            {"field": "y", "operator": "==", "value": "a"},
                            {"field": "y", "operator": "==", "value": "b"},
                        ]
                    },
                ]
            }
        )
        assert cc.evaluate({"x": 1, "y": "a"}) is True
        assert cc.evaluate({"x": 1, "y": "c"}) is False
        assert cc.evaluate({"x": -1, "y": "a"}) is False

    # --- dot-notation field paths ---

    def test_dot_notation_field_path(self):
        cc = CompiledCondition(
            {
                "field": "robot_states.robot-001.battery_level",
                "operator": "<",
                "value": 20,
            }
        )
        data = {"robot_states": {"robot-001": {"battery_level": 15}}}
        assert cc.evaluate(data) is True
        data2 = {"robot_states": {"robot-001": {"battery_level": 80}}}
        assert cc.evaluate(data2) is False

    # --- edge cases ---

    def test_empty_condition_returns_false(self):
        cc = CompiledCondition({})
        assert cc.evaluate({"x": 1}) is False

    def test_unknown_operator_returns_false(self):
        cc = CompiledCondition(
            {"field": "x", "operator": "~~~", "value": 1}
        )
        assert cc.evaluate({"x": 1}) is False

    def test_missing_field_returns_false(self):
        cc = CompiledCondition({"field": "missing", "operator": "==", "value": 1})
        assert cc.evaluate({"other": 1}) is False


# ================================================================
# 4. evaluate_single tests
# ================================================================


class TestEvaluateSingle:
    """Tests for evaluate_single behaviour."""

    @pytest.mark.asyncio
    async def test_triggered_result(self, engine: GovernanceRuleEngine):
        rule = _make_rule(
            condition={"field": "battery_level", "operator": "<", "value": 20},
            action_type="block",
            action_config={"message": "Battery too low"},
        )
        result = await engine.evaluate_single(
            rule, {"battery_level": 10}, {}
        )
        assert result.triggered is True
        assert result.action_type == "block"
        assert result.message == "Battery too low"

    @pytest.mark.asyncio
    async def test_not_triggered_result(self, engine: GovernanceRuleEngine):
        rule = _make_rule(
            condition={"field": "battery_level", "operator": "<", "value": 20},
            action_type="block",
        )
        result = await engine.evaluate_single(
            rule, {"battery_level": 80}, {}
        )
        assert result.triggered is False
        assert result.message == ""

    @pytest.mark.asyncio
    async def test_severity_mapping_block(self, engine: GovernanceRuleEngine):
        rule = _make_rule(
            condition={"field": "x", "operator": "==", "value": 1},
            action_type="block",
        )
        result = await engine.evaluate_single(rule, {"x": 1}, {})
        assert result.severity == "critical"

    @pytest.mark.asyncio
    async def test_severity_mapping_escalate(self, engine: GovernanceRuleEngine):
        rule = _make_rule(
            condition={"field": "x", "operator": "==", "value": 1},
            action_type="escalate",
        )
        result = await engine.evaluate_single(rule, {"x": 1}, {})
        assert result.severity == "error"

    @pytest.mark.asyncio
    async def test_severity_mapping_warn(self, engine: GovernanceRuleEngine):
        rule = _make_rule(
            condition={"field": "x", "operator": "==", "value": 1},
            action_type="warn",
        )
        result = await engine.evaluate_single(rule, {"x": 1}, {})
        assert result.severity == "warning"

    @pytest.mark.asyncio
    async def test_severity_mapping_log(self, engine: GovernanceRuleEngine):
        rule = _make_rule(
            condition={"field": "x", "operator": "==", "value": 1},
            action_type="log",
        )
        result = await engine.evaluate_single(rule, {"x": 1}, {})
        assert result.severity == "info"

    @pytest.mark.asyncio
    async def test_trigger_count_increments(self, engine: GovernanceRuleEngine):
        rule = _make_rule(
            condition={"field": "x", "operator": "==", "value": 1},
            action_type="warn",
        )
        assert rule.trigger_count == 0
        await engine.evaluate_single(rule, {"x": 1}, {})
        assert rule.trigger_count == 1
        await engine.evaluate_single(rule, {"x": 1}, {})
        assert rule.trigger_count == 2

    @pytest.mark.asyncio
    async def test_block_count_increments_for_block_action(
        self, engine: GovernanceRuleEngine
    ):
        rule = _make_rule(
            condition={"field": "x", "operator": "==", "value": 1},
            action_type="block",
        )
        assert rule.block_count == 0
        await engine.evaluate_single(rule, {"x": 1}, {})
        assert rule.block_count == 1

    @pytest.mark.asyncio
    async def test_block_count_not_incremented_for_warn(
        self, engine: GovernanceRuleEngine
    ):
        rule = _make_rule(
            condition={"field": "x", "operator": "==", "value": 1},
            action_type="warn",
        )
        await engine.evaluate_single(rule, {"x": 1}, {})
        assert rule.block_count == 0

    @pytest.mark.asyncio
    async def test_modify_action_generates_suggested_fix(
        self, engine: GovernanceRuleEngine
    ):
        rule = _make_rule(
            condition={"field": "x", "operator": "==", "value": 1},
            action_type="modify",
            action_config={"field": "cleaning_mode", "set_to": "quiet"},
        )
        result = await engine.evaluate_single(rule, {"x": 1}, {})
        assert result.suggested_fix is not None
        assert result.suggested_fix["field"] == "cleaning_mode"
        assert result.suggested_fix["set_to"] == "quiet"

    @pytest.mark.asyncio
    async def test_non_modify_action_no_suggested_fix(
        self, engine: GovernanceRuleEngine
    ):
        rule = _make_rule(
            condition={"field": "x", "operator": "==", "value": 1},
            action_type="warn",
        )
        result = await engine.evaluate_single(rule, {"x": 1}, {})
        assert result.suggested_fix is None

    @pytest.mark.asyncio
    async def test_context_merged_with_decision(self, engine: GovernanceRuleEngine):
        """Decision fields overlay context fields in the merged data."""
        rule = _make_rule(
            condition={"field": "battery_level", "operator": "<", "value": 20},
            action_type="warn",
        )
        # battery_level comes from context; decision has something else
        result = await engine.evaluate_single(
            rule,
            decision={"task_type": "clean"},
            context={"battery_level": 10},
        )
        assert result.triggered is True


# ================================================================
# 5. evaluate (batch) tests
# ================================================================


class TestEvaluateBatch:
    """Tests for the batch evaluate method."""

    @pytest.mark.asyncio
    async def test_returns_only_triggered(self, engine: GovernanceRuleEngine):
        await engine.create_rule(
            _make_rule(
                "r1",
                "Will trigger",
                condition={"field": "x", "operator": "==", "value": 1},
                action_type="warn",
            )
        )
        await engine.create_rule(
            _make_rule(
                "r2",
                "Will not trigger",
                condition={"field": "x", "operator": "==", "value": 999},
                action_type="warn",
            )
        )
        results = await engine.evaluate({"x": 1}, {})
        assert len(results) == 1
        assert results[0].rule_id == "r1"
        assert results[0].triggered is True

    @pytest.mark.asyncio
    async def test_empty_when_nothing_triggers(self, engine: GovernanceRuleEngine):
        await engine.create_rule(
            _make_rule(
                "r1",
                "No match",
                condition={"field": "x", "operator": "==", "value": 999},
                action_type="warn",
            )
        )
        results = await engine.evaluate({"x": 1}, {})
        assert results == []


# ================================================================
# 6. load_tower_c_seed_rules tests
# ================================================================


class TestLoadTowerCSeedRules:
    """Tests for the Tower C seed data loader."""

    @pytest.mark.asyncio
    async def test_loads_six_rules(self, engine: GovernanceRuleEngine):
        count = await engine.load_tower_c_seed_rules()
        assert count == 6

    @pytest.mark.asyncio
    async def test_idempotent_no_error_on_second_call(
        self, engine: GovernanceRuleEngine
    ):
        first = await engine.load_tower_c_seed_rules()
        assert first == 6
        second = await engine.load_tower_c_seed_rules()
        # All six are duplicates so zero new rules loaded, but no exception
        assert second == 0

    @pytest.mark.asyncio
    async def test_seed_rules_are_retrievable(self, engine: GovernanceRuleEngine):
        await engine.load_tower_c_seed_rules()
        rule = await engine.get_rule("gr-tc-001")
        assert rule is not None
        assert rule.action_type == "block"
        assert rule.priority == 95


# ================================================================
# 7. _resolve_field_path tests
# ================================================================


class TestResolveFieldPath:
    """Tests for the _resolve_field_path utility."""

    def test_simple_key(self):
        assert _resolve_field_path("x", {"x": 42}) == 42

    def test_nested_key(self):
        data = {"a": {"b": {"c": 99}}}
        assert _resolve_field_path("a.b.c", data) == 99

    def test_missing_key_returns_none(self):
        assert _resolve_field_path("missing", {"x": 1}) is None

    def test_missing_nested_key_returns_none(self):
        assert _resolve_field_path("a.b.c", {"a": {"b": {}}}) is None

    def test_non_dict_intermediate_returns_none(self):
        assert _resolve_field_path("a.b", {"a": 42}) is None

    def test_empty_path_returns_none(self):
        assert _resolve_field_path("", {"x": 1}) is None
