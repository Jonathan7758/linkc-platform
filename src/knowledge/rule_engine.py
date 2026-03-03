"""
ECIS v6 -- K2 GovernanceRuleEngine (Phase 1: In-Memory)

Governance rule engine for the knowledge layer. Provides:
  - CRUD operations on GovernanceRule
  - Filtered query for active rules (scope, agent_type, building_id, zone_id)
  - Condition compilation (json-rules format with dot-notation field paths)
  - Single and batch rule evaluation against decision + context
  - Tower C seed data loader

Condition format (json-rules compatible):
  Atomic:   {"field": "battery_level", "operator": "<", "value": 20}
  Compound: {"and": [...]}, {"or": [...]}, {"not": <condition>}
  Paths:    "robot_states.robot-001.battery_level" resolved via dot notation
"""

from __future__ import annotations

import logging
import operator
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
)

logger = logging.getLogger(__name__)


# ============================================================
# Data Models
# ============================================================

@dataclass
class GovernanceRule:
    """A single governance rule."""

    rule_id: str
    rule_name: str
    description: str = ""
    rule_type: str = "constraint"       # constraint | preference | policy
    scope: str = "system"               # agent | zone | building | system
    priority: int = 50
    condition: Dict[str, Any] = field(default_factory=dict)
    action_type: str = "warn"           # block | warn | modify | log | escalate
    action_config: Dict[str, Any] = field(default_factory=dict)
    applicable_agent_types: List[str] = field(default_factory=list)
    applicable_building_ids: List[str] = field(default_factory=list)
    applicable_zone_ids: List[str] = field(default_factory=list)
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    enabled: bool = True
    created_by: str = ""
    created_at: Optional[datetime] = None
    parent_rule_id: Optional[str] = None
    trigger_count: int = 0
    block_count: int = 0


@dataclass
class RuleEvalResult:
    """Result of evaluating a single rule against a decision."""

    rule_id: str
    rule_name: str
    triggered: bool
    action_type: str
    message: str = ""
    severity: str = "warning"           # critical | error | warning | info
    suggested_fix: Optional[Dict[str, Any]] = None


# ============================================================
# Operator registry
# ============================================================

_OPERATORS: Dict[str, Callable[..., bool]] = {
    "==":       operator.eq,
    "!=":       operator.ne,
    "<":        operator.lt,
    ">":        operator.gt,
    "<=":       operator.le,
    ">=":       operator.ge,
    "in":       lambda a, b: a in b,
    "not_in":   lambda a, b: a not in b,
    "contains": lambda a, b: b in a if isinstance(a, (list, str, set)) else False,
    "exists":   lambda a, _: a is not None,
}


# ============================================================
# Compiled condition callable
# ============================================================

class CompiledCondition:
    """
    Wraps a json-rules condition dict and compiles it into a callable
    that evaluates against a merged data dictionary.
    """

    def __init__(self, condition: Dict[str, Any]) -> None:
        self._condition = condition
        self._evaluator = self._compile(condition)

    # ----------------------------------------------------------
    # Public
    # ----------------------------------------------------------

    def evaluate(self, data: Dict[str, Any]) -> bool:
        """Evaluate the compiled condition against *data*."""
        try:
            return self._evaluator(data)
        except Exception:
            logger.debug(
                "Condition evaluation error for %s",
                self._condition,
                exc_info=True,
            )
            return False

    # ----------------------------------------------------------
    # Internal compilation
    # ----------------------------------------------------------

    def _compile(
        self, condition: Dict[str, Any],
    ) -> Callable[[Dict[str, Any]], bool]:
        """Recursively compile a condition dict into a callable."""
        if not condition:
            return lambda _data: False

        # --- compound: and ---
        if "and" in condition:
            children = [self._compile(c) for c in condition["and"]]
            return lambda _data, _ch=children: all(fn(_data) for fn in _ch)

        # --- compound: or ---
        if "or" in condition:
            children = [self._compile(c) for c in condition["or"]]
            return lambda _data, _ch=children: any(fn(_data) for fn in _ch)

        # --- compound: not ---
        if "not" in condition:
            child = self._compile(condition["not"])
            return lambda _data, _child=child: not _child(_data)

        # --- atomic condition ---
        field_path: str = condition.get("field", "")
        op_name: str = condition.get("operator", "==")
        expected = condition.get("value")

        op_func = _OPERATORS.get(op_name)
        if op_func is None:
            logger.warning("Unknown operator '%s' in condition", op_name)
            return lambda _data: False

        def _atomic(
            data: Dict[str, Any],
            _fp: str = field_path,
            _op: Callable[..., bool] = op_func,
            _exp: Any = expected,
        ) -> bool:
            actual = _resolve_field_path(_fp, data)
            if actual is None and op_name != "exists":
                return False
            try:
                return _op(actual, _exp)
            except (TypeError, ValueError):
                return False

        return _atomic


# ============================================================
# Field resolution helper
# ============================================================

def _resolve_field_path(path: str, data: Dict[str, Any]) -> Any:
    """
    Resolve a dot-notation field path against a data dict.

    Example: ``"robot_states.robot-001.battery_level"``
    walks ``data["robot_states"]["robot-001"]["battery_level"]``.
    """
    if not path:
        return None

    parts = path.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


# ============================================================
# Action-type to severity mapping
# ============================================================

_ACTION_SEVERITY: Dict[str, str] = {
    "block":    "critical",
    "escalate": "error",
    "warn":     "warning",
    "modify":   "warning",
    "log":      "info",
}


# ============================================================
# GovernanceRuleEngine
# ============================================================

class GovernanceRuleEngine:
    """
    In-memory governance rule engine (Phase 1).

    Stores rules in a dict keyed by ``rule_id``.
    All public methods are async to match the interface contract
    defined in the K2 spec, allowing a seamless swap to a DB-backed
    implementation in Phase 2.
    """

    def __init__(self) -> None:
        self._rules: Dict[str, GovernanceRule] = {}

    # ==========================================================
    # CRUD
    # ==========================================================

    async def create_rule(self, rule: GovernanceRule) -> str:
        """
        Persist a new governance rule.

        Returns:
            The ``rule_id`` of the created rule.

        Raises:
            ValueError: If a rule with the same ``rule_id`` already exists.
        """
        if rule.rule_id in self._rules:
            raise ValueError(
                f"Rule '{rule.rule_id}' already exists. "
                "Use update_rule to modify it."
            )
        if rule.created_at is None:
            rule.created_at = datetime.utcnow()
        self._rules[rule.rule_id] = rule
        logger.info("Created governance rule '%s' (%s)", rule.rule_id, rule.rule_name)
        return rule.rule_id

    async def get_rule(self, rule_id: str) -> Optional[GovernanceRule]:
        """Return a rule by its id, or ``None`` if not found."""
        return self._rules.get(rule_id)

    async def update_rule(
        self, rule_id: str, updates: Dict[str, Any],
    ) -> bool:
        """
        Apply partial updates to an existing rule.

        Returns:
            ``True`` if the rule was found and updated.
        """
        rule = self._rules.get(rule_id)
        if rule is None:
            logger.warning("update_rule: rule '%s' not found", rule_id)
            return False

        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
            else:
                logger.warning(
                    "update_rule: ignoring unknown field '%s' on rule '%s'",
                    key,
                    rule_id,
                )
        logger.info("Updated governance rule '%s'", rule_id)
        return True

    async def disable_rule(self, rule_id: str) -> bool:
        """
        Soft-disable a rule (set ``enabled = False``).

        Returns:
            ``True`` if the rule existed and was disabled.
        """
        rule = self._rules.get(rule_id)
        if rule is None:
            logger.warning("disable_rule: rule '%s' not found", rule_id)
            return False
        rule.enabled = False
        logger.info("Disabled governance rule '%s'", rule_id)
        return True

    # ==========================================================
    # Query
    # ==========================================================

    async def get_active_rules(
        self,
        scope: Optional[str] = None,
        agent_type: Optional[str] = None,
        building_id: Optional[str] = None,
        zone_id: Optional[str] = None,
    ) -> List[GovernanceRule]:
        """
        Return all currently active rules matching the given filters.

        Active means:
          - ``enabled`` is ``True``
          - Current time falls within ``[effective_from, effective_until]``

        Additional filters narrow results by scope and applicability lists.
        Results are sorted by ``priority`` descending (highest first).
        """
        now = datetime.utcnow()
        matched: List[GovernanceRule] = []

        for rule in self._rules.values():
            # -- must be enabled --
            if not rule.enabled:
                continue

            # -- effective period --
            if rule.effective_from is not None and now < rule.effective_from:
                continue
            if rule.effective_until is not None and now > rule.effective_until:
                continue

            # -- scope filter --
            if scope is not None and rule.scope != scope:
                continue

            # -- agent type applicability --
            if agent_type is not None and rule.applicable_agent_types:
                if agent_type not in rule.applicable_agent_types:
                    continue

            # -- building id applicability --
            if building_id is not None and rule.applicable_building_ids:
                if building_id not in rule.applicable_building_ids:
                    continue

            # -- zone id applicability --
            if zone_id is not None and rule.applicable_zone_ids:
                if zone_id not in rule.applicable_zone_ids:
                    continue

            matched.append(rule)

        # Sort by priority descending
        matched.sort(key=lambda r: r.priority, reverse=True)
        return matched

    # ==========================================================
    # Evaluation
    # ==========================================================

    async def evaluate(
        self,
        decision: Dict[str, Any],
        context: Dict[str, Any],
        scope: str = "system",
        agent_type: str = "",
    ) -> List[RuleEvalResult]:
        """
        Evaluate all applicable active rules against *decision* + *context*.

        Returns a list of :class:`RuleEvalResult` for every rule that
        **triggered** (including ``warn``-level results).
        """
        active_rules = await self.get_active_rules(
            scope=None,  # evaluate across all scopes
            agent_type=agent_type or None,
        )
        results: List[RuleEvalResult] = []

        for rule in active_rules:
            result = await self.evaluate_single(rule, decision, context)
            if result.triggered:
                results.append(result)

        return results

    async def evaluate_single(
        self,
        rule: GovernanceRule,
        decision: Dict[str, Any],
        context: Dict[str, Any],
    ) -> RuleEvalResult:
        """
        Evaluate a single rule against the given decision and context.

        The decision dict and context dict are merged (decision keys
        take precedence for top-level conflicts) to form the data
        universe for field resolution.
        """
        # Merge context and decision so field paths can resolve from
        # either source.  Decision fields overlay context fields.
        merged: Dict[str, Any] = {**context, **decision}

        compiled = self.compile_condition(rule.condition)
        triggered = compiled.evaluate(merged)

        severity = _ACTION_SEVERITY.get(rule.action_type, "warning")
        message = ""
        suggested_fix: Optional[Dict[str, Any]] = None

        if triggered:
            message = rule.action_config.get(
                "message",
                rule.description or f"Rule '{rule.rule_name}' triggered",
            )
            # For modify actions, build a suggested_fix from action_config
            if rule.action_type == "modify":
                modify_field = rule.action_config.get("field")
                modify_value = rule.action_config.get("set_to")
                if modify_field is not None:
                    suggested_fix = {"field": modify_field, "set_to": modify_value}

            # Update counters
            rule.trigger_count += 1
            if rule.action_type == "block":
                rule.block_count += 1

            logger.debug(
                "Rule '%s' triggered (action=%s, priority=%d)",
                rule.rule_id,
                rule.action_type,
                rule.priority,
            )

        return RuleEvalResult(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            triggered=triggered,
            action_type=rule.action_type,
            message=message,
            severity=severity,
            suggested_fix=suggested_fix,
        )

    # ==========================================================
    # Condition compilation
    # ==========================================================

    def compile_condition(
        self, condition: Dict[str, Any],
    ) -> CompiledCondition:
        """
        Compile a json-rules condition dict into a reusable
        :class:`CompiledCondition`.

        Supported operators:
          Comparison: ``==``, ``!=``, ``<``, ``>``, ``<=``, ``>=``
          Membership: ``in``, ``not_in``, ``contains``
          Existence:  ``exists``
          Compound:   ``and``, ``or``, ``not``
        """
        return CompiledCondition(condition)

    # ==========================================================
    # Tower C seed data
    # ==========================================================

    async def load_tower_c_seed_rules(self) -> int:
        """
        Load Tower C initial governance rules.

        Returns:
            Number of rules successfully loaded.
        """
        seed_rules: List[GovernanceRule] = [
            # ---- Hard constraints ----
            GovernanceRule(
                rule_id="gr-tc-001",
                rule_name="低电量禁止分配新任务",
                description="机器人电量低于20%时，禁止分配除返回充电桩以外的任务",
                rule_type="constraint",
                scope="system",
                priority=95,
                condition={
                    "and": [
                        {"field": "battery_level", "operator": "<", "value": 20},
                        {"field": "task_type", "operator": "!=", "value": "return_to_charger"},
                    ]
                },
                action_type="block",
                action_config={
                    "message": "机器人电量低于20%，禁止分配新任务，请先返回充电",
                },
            ),
            GovernanceRule(
                rule_id="gr-tc-002",
                rule_name="VIP区域营业前完成清洁",
                description="VIP区域应在9点营业前完成清洁，超时需上报主管",
                rule_type="constraint",
                scope="zone",
                priority=90,
                condition={
                    "and": [
                        {"field": "zone_type", "operator": "==", "value": "vip"},
                        {"field": "current_hour", "operator": ">=", "value": 9},
                        {"field": "task_status", "operator": "!=", "value": "completed"},
                    ]
                },
                action_type="escalate",
                action_config={
                    "escalate_to": "supervisor",
                    "message": "VIP区域9点后仍未完成清洁",
                },
            ),
            GovernanceRule(
                rule_id="gr-tc-003",
                rule_name="错误状态机器人禁止分配",
                description="处于错误状态的机器人不能接受新任务，需人工检查",
                rule_type="constraint",
                scope="system",
                priority=99,
                condition={
                    "field": "robot_status",
                    "operator": "==",
                    "value": "error",
                },
                action_type="block",
                action_config={
                    "message": "机器人处于错误状态，需要人工检查后才能分配任务",
                },
            ),

            # ---- Soft preferences ----
            GovernanceRule(
                rule_id="gr-tc-010",
                rule_name="优先使用电量充足的机器人",
                description="电量低于50%的机器人分配时发出警告",
                rule_type="preference",
                scope="system",
                priority=40,
                condition={
                    "field": "battery_level",
                    "operator": "<",
                    "value": 50,
                },
                action_type="warn",
                action_config={
                    "message": "建议优先选择电量高于50%的机器人",
                },
            ),
            GovernanceRule(
                rule_id="gr-tc-011",
                rule_name="雨天增加大堂清洁频次",
                description="下雨天大堂区域清洁频次乘以1.3倍",
                rule_type="preference",
                scope="zone",
                priority=60,
                condition={
                    "and": [
                        {"field": "environmental_state.weather", "operator": "==", "value": "rainy"},
                        {"field": "zone_type", "operator": "==", "value": "lobby"},
                    ]
                },
                action_type="modify",
                action_config={
                    "field": "cleaning_frequency_multiplier",
                    "set_to": 1.3,
                },
            ),

            # ---- Policy ----
            GovernanceRule(
                rule_id="gr-tc-020",
                rule_name="午休时段降低清洁噪音",
                description="12:00-14:00期间使用静音清洁模式",
                rule_type="policy",
                scope="building",
                priority=50,
                condition={
                    "and": [
                        {"field": "current_hour", "operator": ">=", "value": 12},
                        {"field": "current_hour", "operator": "<", "value": 14},
                    ]
                },
                action_type="modify",
                action_config={
                    "field": "cleaning_mode",
                    "set_to": "quiet",
                },
            ),
        ]

        loaded = 0
        for rule in seed_rules:
            try:
                await self.create_rule(rule)
                loaded += 1
            except ValueError:
                logger.warning(
                    "Seed rule '%s' already exists, skipping", rule.rule_id,
                )

        logger.info("Loaded %d / %d Tower C seed rules", loaded, len(seed_rules))
        return loaded
