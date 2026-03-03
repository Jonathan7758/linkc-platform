"""
L3 约束校验器 — 治理规则校验 (K2)
"""

from typing import Dict, Any, List, Optional
import operator

from .base_validator import ValidatorType, ValidationError, ValidationSeverity


# 操作符映射（用于json-rules条件评估）
OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
    "contains": lambda a, b: b in a if isinstance(a, (list, str)) else False,
}


class ConstraintValidator:
    """
    L3 约束校验器

    从规则列表评估治理规则，可产生自动修正建议。
    """

    def __init__(self, rules: Optional[List] = None):
        """
        Args:
            rules: GovernanceRule 列表。如不提供，从 context['active_rules'] 读取。
        """
        self._rules = rules or []

    @property
    def validator_type(self) -> ValidatorType:
        return ValidatorType.CONSTRAINT

    def set_rules(self, rules: List) -> None:
        """动态设置规则列表"""
        self._rules = rules

    async def validate(
        self,
        decision: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[ValidationError]:
        """评估所有活跃规则"""
        errors = []
        rules = self._rules or context.get("active_rules", [])

        # 按优先级降序排列
        sorted_rules = sorted(rules, key=lambda r: getattr(r, "priority", 50), reverse=True)

        for rule in sorted_rules:
            if not getattr(rule, "enabled", True):
                continue

            triggered = self._evaluate_condition(rule.condition, decision, context)

            if triggered:
                severity = self._map_action_to_severity(rule.action_type)
                action_config = getattr(rule, "action_config", {})

                errors.append(
                    ValidationError(
                        validator="constraint",
                        field="",
                        message=action_config.get("message", rule.description),
                        severity=severity,
                        rule_id=rule.rule_id,
                        suggested_fix=action_config.get("suggested_fix"),
                    )
                )

        return errors

    async def get_corrections(
        self,
        decision: Dict[str, Any],
        errors: List[ValidationError],
    ) -> Optional[Dict[str, Any]]:
        """基于MODIFY类型的规则生成自动修正"""
        corrections = dict(decision)
        has_corrections = False

        for rule in self._rules:
            if not getattr(rule, "enabled", True):
                continue
            action_type = getattr(rule, "action_type", None)
            if action_type and action_type.value == "modify":
                action_config = getattr(rule, "action_config", {})
                field = action_config.get("field")
                set_to = action_config.get("set_to")
                if field and set_to is not None:
                    corrections[field] = set_to
                    has_corrections = True

        return corrections if has_corrections else None

    def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        decision: Dict[str, Any],
        context: Dict[str, Any],
    ) -> bool:
        """评估json-rules格式条件"""
        if not condition:
            return False

        # 复合条件
        if "and" in condition:
            return all(
                self._evaluate_condition(sub, decision, context)
                for sub in condition["and"]
            )

        if "or" in condition:
            return any(
                self._evaluate_condition(sub, decision, context)
                for sub in condition["or"]
            )

        if "not" in condition:
            return not self._evaluate_condition(condition["not"], decision, context)

        # 原子条件: {"field": "...", "operator": "...", "value": ...}
        field_name = condition.get("field", "")
        op_name = condition.get("operator", "==")
        expected_value = condition.get("value")

        actual_value = self._resolve_field(field_name, decision, context)
        if actual_value is None:
            return False

        op_func = OPERATORS.get(op_name)
        if op_func is None:
            return False

        try:
            return op_func(actual_value, expected_value)
        except (TypeError, ValueError):
            return False

    def _resolve_field(
        self,
        field_path: str,
        decision: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Any:
        """从 decision 或 context 中解析字段值"""
        # 先从 context 中的 robot_states 查找
        robot_states = context.get("robot_states", {})
        for robot_id, state in robot_states.items():
            if field_path in state:
                return state[field_path]

        # 然后从 decision 查找
        parts = field_path.split(".")
        current = decision
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                # 从 context 查找
                current = context
                for p in parts:
                    if isinstance(current, dict) and p in current:
                        current = current[p]
                    else:
                        return None
                return current
        return current

    def _map_action_to_severity(self, action_type) -> ValidationSeverity:
        """将规则动作类型映射为校验严重性"""
        action_value = action_type.value if hasattr(action_type, "value") else str(action_type)
        mapping = {
            "block": ValidationSeverity.CRITICAL,
            "warn": ValidationSeverity.WARNING,
            "modify": ValidationSeverity.WARNING,
            "log": ValidationSeverity.INFO,
            "escalate": ValidationSeverity.ERROR,
        }
        return mapping.get(action_value, ValidationSeverity.WARNING)
