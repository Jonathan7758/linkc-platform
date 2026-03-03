"""
Tests for A5 DecisionValidator — 四层校验管道
"""
import pytest
import sys
import os

# 添加 src 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from validation.base_validator import (
    ValidatorType, ValidationError, ValidationResult, ValidationSeverity,
)
from validation.schema_validator import SchemaValidator
from validation.reference_validator import ReferenceValidator, DefaultEntityLookup
from validation.safety_validator import SafetyValidator
from validation.constraint_validator import ConstraintValidator
from validation.decision_validator import DecisionValidator


# ============================================================
# Fixtures
# ============================================================

def make_valid_decision():
    return {
        "action": "schedule",
        "assignments": [
            {
                "robot_id": "robot-001",
                "zone_id": "zone-lobby",
                "task_type": "standard",
                "priority": 3,
                "estimated_duration_minutes": 30,
            }
        ],
        "reasoning": "大堂需要日常清洁",
    }


def make_valid_context():
    return {
        "agent_type": "cleaning_scheduler",
        "known_robot_ids": ["robot-001", "robot-002", "robot-003"],
        "known_zone_ids": ["zone-lobby", "zone-corridor", "zone-office"],
        "known_floor_ids": ["floor-1", "floor-2"],
        "robot_states": {
            "robot-001": {"battery_level": 85, "status": "idle"},
            "robot-002": {"battery_level": 60, "status": "idle"},
            "robot-003": {"battery_level": 30, "status": "working"},
        },
        "total_robots_in_building": 10,
        "closed_zones": [],
    }


# ============================================================
# L1 Schema Validator Tests
# ============================================================

class TestSchemaValidator:
    """L1 Schema校验测试"""

    @pytest.fixture
    def validator(self):
        return SchemaValidator()

    @pytest.mark.asyncio
    async def test_valid_decision_passes(self, validator):
        decision = make_valid_decision()
        errors = await validator.validate(decision, {"agent_type": "cleaning_scheduler"})
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_missing_required_field_action(self, validator):
        decision = {"assignments": []}
        errors = await validator.validate(decision, {"agent_type": "cleaning_scheduler"})
        assert len(errors) >= 1
        assert any("action" in e.field or "action" in e.message for e in errors)

    @pytest.mark.asyncio
    async def test_missing_required_field_assignments(self, validator):
        decision = {"action": "schedule"}
        errors = await validator.validate(decision, {"agent_type": "cleaning_scheduler"})
        assert len(errors) >= 1
        critical = [e for e in errors if e.severity == ValidationSeverity.CRITICAL]
        assert len(critical) >= 1

    @pytest.mark.asyncio
    async def test_invalid_action_enum(self, validator):
        decision = {"action": "destroy", "assignments": []}
        errors = await validator.validate(decision, {"agent_type": "cleaning_scheduler"})
        assert len(errors) >= 1
        assert any("action" in e.field or "action" in e.message for e in errors)

    @pytest.mark.asyncio
    async def test_duration_out_of_range(self, validator):
        decision = {
            "action": "schedule",
            "assignments": [
                {
                    "robot_id": "robot-001",
                    "zone_id": "zone-lobby",
                    "task_type": "standard",
                    "estimated_duration_minutes": 9999,
                }
            ],
        }
        errors = await validator.validate(decision, {"agent_type": "cleaning_scheduler"})
        assert any("estimated_duration_minutes" in e.field for e in errors)

    @pytest.mark.asyncio
    async def test_invalid_task_type_enum(self, validator):
        decision = {
            "action": "schedule",
            "assignments": [
                {
                    "robot_id": "robot-001",
                    "zone_id": "zone-lobby",
                    "task_type": "ultra_mega_clean",
                }
            ],
        }
        errors = await validator.validate(decision, {"agent_type": "cleaning_scheduler"})
        assert any("task_type" in e.field for e in errors)

    @pytest.mark.asyncio
    async def test_unknown_agent_type(self, validator):
        decision = make_valid_decision()
        errors = await validator.validate(decision, {"agent_type": "unknown_agent"})
        assert len(errors) >= 1

    @pytest.mark.asyncio
    async def test_missing_item_required_fields(self, validator):
        decision = {
            "action": "schedule",
            "assignments": [{"robot_id": "robot-001"}],  # 缺少 zone_id, task_type
        }
        errors = await validator.validate(decision, {"agent_type": "cleaning_scheduler"})
        assert len(errors) >= 1


# ============================================================
# L2 Reference Validator Tests
# ============================================================

class TestReferenceValidator:
    """L2 引用校验测试"""

    @pytest.fixture
    def validator(self):
        return ReferenceValidator()

    @pytest.mark.asyncio
    async def test_valid_references(self, validator):
        decision = make_valid_decision()
        context = make_valid_context()
        errors = await validator.validate(decision, context)
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_nonexistent_robot(self, validator):
        decision = {
            "assignments": [{"robot_id": "robot-999", "zone_id": "zone-lobby", "task_type": "standard"}]
        }
        context = make_valid_context()
        errors = await validator.validate(decision, context)
        assert len(errors) == 1
        assert errors[0].severity == ValidationSeverity.CRITICAL
        assert "robot-999" in errors[0].message

    @pytest.mark.asyncio
    async def test_nonexistent_zone(self, validator):
        decision = {
            "assignments": [{"robot_id": "robot-001", "zone_id": "zone-xxx", "task_type": "standard"}]
        }
        context = make_valid_context()
        errors = await validator.validate(decision, context)
        assert len(errors) == 1
        assert "zone-xxx" in errors[0].message

    @pytest.mark.asyncio
    async def test_multiple_invalid_references(self, validator):
        decision = {
            "assignments": [
                {"robot_id": "robot-999", "zone_id": "zone-xxx", "task_type": "standard"},
            ]
        }
        context = make_valid_context()
        errors = await validator.validate(decision, context)
        assert len(errors) == 2

    @pytest.mark.asyncio
    async def test_empty_context_passes(self, validator):
        """无已知实体数据时不阻止"""
        decision = make_valid_decision()
        errors = await validator.validate(decision, {})
        assert len(errors) == 0


# ============================================================
# L3 Constraint Validator Tests
# ============================================================

class TestConstraintValidator:
    """L3 约束校验测试"""

    def _make_rule(self, rule_id, rule_type_val, action_type_val, condition, action_config=None, priority=50):
        """创建一个简单的规则对象"""
        class MockRuleType:
            def __init__(self, v): self.value = v
        class MockActionType:
            def __init__(self, v): self.value = v
        class MockRule:
            pass

        rule = MockRule()
        rule.rule_id = rule_id
        rule.rule_name = rule_id
        rule.description = f"Rule {rule_id}"
        rule.rule_type = MockRuleType(rule_type_val)
        rule.action_type = MockActionType(action_type_val)
        rule.condition = condition
        rule.action_config = action_config or {}
        rule.priority = priority
        rule.enabled = True
        rule.scope = MockRuleType("system")
        return rule

    @pytest.mark.asyncio
    async def test_no_rules_passes(self):
        validator = ConstraintValidator(rules=[])
        errors = await validator.validate(make_valid_decision(), make_valid_context())
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_battery_constraint_blocks(self):
        rule = self._make_rule(
            "gr-001", "constraint", "block",
            condition={"field": "battery_level", "operator": "<", "value": 20},
            action_config={"message": "电量不足20%，禁止分配新任务"},
            priority=90,
        )
        validator = ConstraintValidator(rules=[rule])

        context = make_valid_context()
        context["robot_states"]["robot-001"]["battery_level"] = 15

        errors = await validator.validate(make_valid_decision(), context)
        assert len(errors) == 1
        assert errors[0].severity == ValidationSeverity.CRITICAL
        assert errors[0].rule_id == "gr-001"

    @pytest.mark.asyncio
    async def test_preference_rule_warns(self):
        rule = self._make_rule(
            "gr-002", "preference", "warn",
            condition={"field": "battery_level", "operator": "<", "value": 50},
            action_config={"message": "建议选择电量更充足的机器人"},
        )
        validator = ConstraintValidator(rules=[rule])

        context = make_valid_context()
        context["robot_states"]["robot-001"]["battery_level"] = 40

        errors = await validator.validate(make_valid_decision(), context)
        assert len(errors) == 1
        assert errors[0].severity == ValidationSeverity.WARNING

    @pytest.mark.asyncio
    async def test_compound_and_condition(self):
        rule = self._make_rule(
            "gr-003", "constraint", "block",
            condition={
                "and": [
                    {"field": "battery_level", "operator": "<", "value": 20},
                    {"field": "status", "operator": "!=", "value": "charging"},
                ]
            },
            action_config={"message": "低电量且未充电"},
        )
        validator = ConstraintValidator(rules=[rule])

        context = make_valid_context()
        context["robot_states"]["robot-001"]["battery_level"] = 10
        context["robot_states"]["robot-001"]["status"] = "idle"

        errors = await validator.validate(make_valid_decision(), context)
        assert len(errors) == 1

    @pytest.mark.asyncio
    async def test_disabled_rule_skipped(self):
        rule = self._make_rule(
            "gr-004", "constraint", "block",
            condition={"field": "battery_level", "operator": "<", "value": 100},
            action_config={"message": "永远触发"},
        )
        rule.enabled = False
        validator = ConstraintValidator(rules=[rule])

        errors = await validator.validate(make_valid_decision(), make_valid_context())
        assert len(errors) == 0


# ============================================================
# L4 Safety Validator Tests
# ============================================================

class TestSafetyValidator:
    """L4 安全校验测试"""

    @pytest.fixture
    def validator(self):
        return SafetyValidator()

    @pytest.mark.asyncio
    async def test_valid_passes(self, validator):
        errors = await validator.validate(make_valid_decision(), make_valid_context())
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_duplicate_robot_tasks_blocked(self, validator):
        decision = {
            "action": "schedule",
            "assignments": [
                {"robot_id": "robot-001", "zone_id": "zone-lobby", "task_type": "standard"},
                {"robot_id": "robot-001", "zone_id": "zone-corridor", "task_type": "standard"},
            ],
        }
        errors = await validator.validate(decision, make_valid_context())
        assert len(errors) == 1
        assert errors[0].severity == ValidationSeverity.CRITICAL
        assert "robot-001" in errors[0].message

    @pytest.mark.asyncio
    async def test_critical_battery_blocked(self, validator):
        decision = make_valid_decision()
        context = make_valid_context()
        context["robot_states"]["robot-001"]["battery_level"] = 3

        errors = await validator.validate(decision, context)
        assert len(errors) == 1
        assert errors[0].severity == ValidationSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_error_robot_blocked(self, validator):
        decision = make_valid_decision()
        context = make_valid_context()
        context["robot_states"]["robot-001"]["status"] = "error"

        errors = await validator.validate(decision, context)
        assert len(errors) == 1
        assert errors[0].severity == ValidationSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_closed_zone_blocked(self, validator):
        decision = make_valid_decision()
        context = make_valid_context()
        context["closed_zones"] = ["zone-lobby"]

        errors = await validator.validate(decision, context)
        assert len(errors) == 1
        assert "zone-lobby" in errors[0].message

    @pytest.mark.asyncio
    async def test_dispatch_ratio_blocked(self, validator):
        decision = {
            "action": "schedule",
            "assignments": [
                {"robot_id": f"robot-{i:03d}", "zone_id": f"zone-{i}", "task_type": "standard"}
                for i in range(9)
            ],
        }
        context = make_valid_context()
        context["total_robots_in_building"] = 10  # 80% = 8, dispatching 9

        errors = await validator.validate(decision, context)
        assert len(errors) == 1
        assert errors[0].severity == ValidationSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_charger_task_allowed_low_battery(self, validator):
        """充电任务允许低电量"""
        decision = {
            "action": "schedule",
            "assignments": [
                {"robot_id": "robot-001", "zone_id": "zone-charger", "task_type": "return_to_charger"},
            ],
        }
        context = make_valid_context()
        context["robot_states"]["robot-001"]["battery_level"] = 3

        errors = await validator.validate(decision, context)
        assert len(errors) == 0


# ============================================================
# DecisionValidator Pipeline Tests
# ============================================================

class TestDecisionValidatorPipeline:
    """完整校验管道测试"""

    @pytest.fixture
    def validator(self):
        return DecisionValidator()

    @pytest.mark.asyncio
    async def test_full_pipeline_pass(self, validator):
        result = await validator.validate(
            make_valid_decision(), make_valid_context(), "cleaning_scheduler"
        )
        assert result.valid is True
        assert len(result.validators_executed) == 4
        assert result.validators_executed == ["schema", "reference", "constraint", "safety"]
        assert result.validation_duration_ms >= 0

    @pytest.mark.asyncio
    async def test_schema_failure_short_circuits(self, validator):
        """L1 CRITICAL失败后不执行后续校验"""
        decision = {"action": "schedule"}  # 缺少 assignments
        result = await validator.validate(decision, make_valid_context(), "cleaning_scheduler")
        assert result.valid is False
        assert "schema" in result.validators_executed
        # CRITICAL会中断，后续不执行
        assert len(result.validators_executed) == 1

    @pytest.mark.asyncio
    async def test_safety_failure_detected(self, validator):
        """安全红线被检测到"""
        decision = make_valid_decision()
        context = make_valid_context()
        context["robot_states"]["robot-001"]["status"] = "error"

        result = await validator.validate(decision, context, "cleaning_scheduler")
        assert result.valid is False
        assert any("安全红线" in e.message for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_partial(self, validator):
        """部分校验"""
        result = await validator.validate_partial(
            make_valid_decision(),
            [ValidatorType.SCHEMA, ValidatorType.SAFETY],
            make_valid_context(),
            "cleaning_scheduler",
        )
        assert result.valid is True
        assert len(result.validators_executed) == 2
        assert "schema" in result.validators_executed
        assert "safety" in result.validators_executed
        assert "reference" not in result.validators_executed

    @pytest.mark.asyncio
    async def test_warnings_dont_block(self, validator):
        """WARNING不阻止执行"""
        # 通过constraint validator产生warning
        from validation.constraint_validator import ConstraintValidator

        class MockRuleType:
            def __init__(self, v): self.value = v
        class MockActionType:
            def __init__(self, v): self.value = v
        class MockRule:
            pass

        rule = MockRule()
        rule.rule_id = "gr-warn"
        rule.rule_name = "warn-rule"
        rule.description = "Warning rule"
        rule.rule_type = MockRuleType("preference")
        rule.action_type = MockActionType("warn")
        rule.condition = {"field": "battery_level", "operator": "<", "value": 90}
        rule.action_config = {"message": "电量不够充足"}
        rule.priority = 50
        rule.enabled = True
        rule.scope = MockRuleType("system")

        constraint_v = ConstraintValidator(rules=[rule])
        pipeline = DecisionValidator(constraint_validator=constraint_v)

        result = await pipeline.validate(
            make_valid_decision(), make_valid_context(), "cleaning_scheduler"
        )
        assert result.valid is True
        assert len(result.warnings) >= 1

    @pytest.mark.asyncio
    async def test_empty_decision(self, validator):
        """空决策应该失败"""
        result = await validator.validate({}, make_valid_context(), "cleaning_scheduler")
        assert result.valid is False

    @pytest.mark.asyncio
    async def test_multiple_assignments_validated(self, validator):
        """多个任务分配都被校验"""
        decision = {
            "action": "schedule",
            "assignments": [
                {"robot_id": "robot-001", "zone_id": "zone-lobby", "task_type": "standard"},
                {"robot_id": "robot-002", "zone_id": "zone-corridor", "task_type": "deep"},
            ],
        }
        result = await validator.validate(decision, make_valid_context(), "cleaning_scheduler")
        assert result.valid is True
