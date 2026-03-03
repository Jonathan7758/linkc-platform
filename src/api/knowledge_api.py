"""
G8 知识管理 API + G9 规则管理 API + Decision Log API

Provides async handler methods that can be mounted on any web framework.
Phase 1 uses in-memory storage via K1/K2/K3 instances.
"""

import logging
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from knowledge.decision_logger import (
    DecisionContext,
    DecisionLogger,
    DecisionOutcome,
    DecisionRecord,
)
from knowledge.rule_engine import (
    GovernanceRule,
    GovernanceRuleEngine,
    RuleEvalResult,
)
from knowledge.scenario_kb import (
    PromptTemplate,
    ScenarioKnowledge,
    ScenarioKnowledgeBase,
    _estimate_tokens,
)

logger = logging.getLogger(__name__)


# ====================================================================
# Serialization helpers
# ====================================================================

def _serialize_value(obj: Any) -> Any:
    """Recursively convert non-JSON-serializable types."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (list, tuple)):
        return [_serialize_value(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _serialize_value(v) for k, v in obj.items()}
    return obj


def _safe_asdict(obj: Any) -> Dict[str, Any]:
    """Convert a dataclass instance to a JSON-safe dict.

    Uses ``dataclasses.asdict`` and then walks the result to convert
    ``datetime`` objects into ISO-8601 strings.
    """
    raw = asdict(obj)
    return _serialize_value(raw)


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Best-effort conversion of a value to a ``datetime`` object.

    Accepts ISO-8601 strings, existing datetime objects, or ``None``.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Handle ISO strings with or without timezone
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            logger.warning("Unable to parse datetime string: %s", value)
            return None
    return None


# ====================================================================
# G8 — Knowledge Management API
# ====================================================================

class KnowledgeManagementAPI:
    """
    G8 知识管理 API

    Wraps :class:`ScenarioKnowledgeBase` (K1) with dict-in / dict-out
    async methods suitable for REST serialization.
    """

    def __init__(self, kb: ScenarioKnowledgeBase) -> None:
        self._kb = kb

    # ----------------------------------------------------------------
    # Serialization helper
    # ----------------------------------------------------------------

    @staticmethod
    def _knowledge_to_dict(k: ScenarioKnowledge) -> Dict[str, Any]:
        """Convert a :class:`ScenarioKnowledge` dataclass to a plain dict
        with all ``datetime`` fields serialized as ISO-8601 strings."""
        return _safe_asdict(k)

    @staticmethod
    def _template_to_dict(t: PromptTemplate) -> Dict[str, Any]:
        """Convert a :class:`PromptTemplate` dataclass to a plain dict."""
        return _safe_asdict(t)

    # ----------------------------------------------------------------
    # 1. Create knowledge
    # ----------------------------------------------------------------

    async def create_knowledge(self, data: dict) -> dict:
        """Create a knowledge entry from a dict.

        Returns ``{"knowledge_id": ..., "status": "created"}`` on success,
        or ``{"error": ...}`` on failure.
        """
        try:
            knowledge = ScenarioKnowledge(
                knowledge_id=data.get("knowledge_id", ""),
                knowledge_type=data.get("knowledge_type", "domain_fact"),
                scenario_category=data.get("scenario_category", ""),
                name=data.get("name", ""),
                description=data.get("description", ""),
                tags=data.get("tags", []),
                applicable_building_types=data.get(
                    "applicable_building_types", ["all"]
                ),
                applicable_zones=data.get("applicable_zones", ["all"]),
                applicable_time_ranges=data.get("applicable_time_ranges", []),
                applicable_conditions=data.get("applicable_conditions", {}),
                content=data.get("content", {}),
                priority=data.get("priority", 50),
                version=data.get("version", "1.0"),
                enabled=data.get("enabled", True),
                effective_from=_parse_datetime(data.get("effective_from")),
                effective_until=_parse_datetime(data.get("effective_until")),
                created_by=data.get("created_by", ""),
            )
            kid = await self._kb.create_knowledge(knowledge)
            logger.info("API create_knowledge: %s", kid)
            return {"knowledge_id": kid, "status": "created"}
        except Exception as exc:
            logger.exception("API create_knowledge failed")
            return {"error": str(exc)}

    # ----------------------------------------------------------------
    # 2. Get knowledge
    # ----------------------------------------------------------------

    async def get_knowledge(self, knowledge_id: str) -> dict:
        """Return a single knowledge entry as a dict, or an error dict."""
        try:
            entry = await self._kb.get_knowledge(knowledge_id)
            if entry is None:
                return {"error": "not_found"}
            return self._knowledge_to_dict(entry)
        except Exception as exc:
            logger.exception("API get_knowledge failed for %s", knowledge_id)
            return {"error": str(exc)}

    # ----------------------------------------------------------------
    # 3. Update knowledge (partial)
    # ----------------------------------------------------------------

    async def update_knowledge(self, knowledge_id: str, data: dict) -> dict:
        """Apply a partial update and return status."""
        try:
            # Pre-process datetime fields if present
            updates = dict(data)
            for dt_field in ("effective_from", "effective_until"):
                if dt_field in updates:
                    updates[dt_field] = _parse_datetime(updates[dt_field])

            ok = await self._kb.update_knowledge(knowledge_id, updates)
            if not ok:
                return {"error": "not_found"}
            return {"status": "updated"}
        except Exception as exc:
            logger.exception("API update_knowledge failed for %s", knowledge_id)
            return {"error": str(exc)}

    # ----------------------------------------------------------------
    # 4. Delete knowledge (soft)
    # ----------------------------------------------------------------

    async def delete_knowledge(self, knowledge_id: str) -> dict:
        """Soft-delete (disable) a knowledge entry."""
        try:
            ok = await self._kb.delete_knowledge(knowledge_id)
            if not ok:
                return {"error": "not_found"}
            return {"status": "deleted"}
        except Exception as exc:
            logger.exception("API delete_knowledge failed for %s", knowledge_id)
            return {"error": str(exc)}

    # ----------------------------------------------------------------
    # 5. List / query knowledge
    # ----------------------------------------------------------------

    async def list_knowledge(self, filters: dict) -> dict:
        """Query knowledge entries matching *filters*.

        Supported filter keys:
          scenario_category, building_type, zone_id, knowledge_types,
          current_time, conditions, max_items
        """
        try:
            items = await self._kb.query_applicable_knowledge(
                scenario_category=filters.get("scenario_category", ""),
                building_type=filters.get("building_type", "all"),
                zone_id=filters.get("zone_id", "all"),
                current_time=filters.get("current_time"),
                conditions=filters.get("conditions"),
                knowledge_types=filters.get("knowledge_types"),
                max_items=filters.get("max_items", 20),
            )
            serialized = [self._knowledge_to_dict(k) for k in items]
            return {"items": serialized, "total": len(serialized)}
        except Exception as exc:
            logger.exception("API list_knowledge failed")
            return {"error": str(exc)}

    # ----------------------------------------------------------------
    # 6. Assemble prompt
    # ----------------------------------------------------------------

    async def assemble_prompt(self, data: dict) -> dict:
        """Assemble a prompt from a template, variables, and knowledge.

        Expected *data* keys:
          template_id, variables (dict), scenario_category, context (dict)
        """
        try:
            template_id: str = data.get("template_id", "")
            variables: Dict[str, str] = data.get("variables", {})
            scenario_category: str = data.get("scenario_category", "")
            context: Dict[str, Any] = data.get("context", {})

            prompt = await self._kb.assemble_prompt(
                template_id=template_id,
                variables=variables,
                scenario_category=scenario_category,
                context=context,
            )
            estimated_tokens = _estimate_tokens(prompt)
            return {"prompt": prompt, "estimated_tokens": estimated_tokens}
        except Exception as exc:
            logger.exception("API assemble_prompt failed")
            return {"error": str(exc)}

    # ----------------------------------------------------------------
    # 7. Create prompt template
    # ----------------------------------------------------------------

    async def create_template(self, data: dict) -> dict:
        """Create a :class:`PromptTemplate` from a dict."""
        try:
            template = PromptTemplate(
                template_id=data.get("template_id", ""),
                agent_type=data.get("agent_type", ""),
                name=data.get("name", ""),
                system_prompt=data.get("system_prompt", ""),
                variables=data.get("variables", []),
                knowledge_slots=data.get("knowledge_slots", []),
                base_tokens_estimate=data.get("base_tokens_estimate", 500),
                max_knowledge_tokens=data.get("max_knowledge_tokens", 2000),
                max_total_tokens=data.get("max_total_tokens", 4000),
                version=data.get("version", "1.0"),
                is_active=data.get("is_active", True),
            )
            tid = await self._kb.create_template(template)
            logger.info("API create_template: %s", tid)
            return {"template_id": tid, "status": "created"}
        except Exception as exc:
            logger.exception("API create_template failed")
            return {"error": str(exc)}

    # ----------------------------------------------------------------
    # 8. Get prompt template
    # ----------------------------------------------------------------

    async def get_template(self, template_id: str) -> dict:
        """Return a prompt template as a dict, or an error dict."""
        try:
            tmpl = await self._kb.get_prompt_template(template_id)
            if tmpl is None:
                return {"error": "not_found"}
            return self._template_to_dict(tmpl)
        except Exception as exc:
            logger.exception("API get_template failed for %s", template_id)
            return {"error": str(exc)}


# ====================================================================
# G9 — Rule Management API
# ====================================================================

class RuleManagementAPI:
    """
    G9 规则管理 API

    Wraps :class:`GovernanceRuleEngine` (K2) with dict-in / dict-out
    async methods suitable for REST serialization.
    """

    def __init__(self, engine: GovernanceRuleEngine) -> None:
        self._engine = engine

    # ----------------------------------------------------------------
    # Serialization helpers
    # ----------------------------------------------------------------

    @staticmethod
    def _rule_to_dict(r: GovernanceRule) -> Dict[str, Any]:
        """Convert a :class:`GovernanceRule` to a JSON-safe dict."""
        return _safe_asdict(r)

    @staticmethod
    def _eval_result_to_dict(r: RuleEvalResult) -> Dict[str, Any]:
        """Convert a :class:`RuleEvalResult` to a plain dict."""
        return _safe_asdict(r)

    # ----------------------------------------------------------------
    # 1. Create rule
    # ----------------------------------------------------------------

    async def create_rule(self, data: dict) -> dict:
        """Create a governance rule from *data*.

        Returns ``{"rule_id": ..., "status": "created"}`` on success.
        """
        try:
            rule = GovernanceRule(
                rule_id=data.get("rule_id", ""),
                rule_name=data.get("rule_name", ""),
                description=data.get("description", ""),
                rule_type=data.get("rule_type", "constraint"),
                scope=data.get("scope", "system"),
                priority=data.get("priority", 50),
                condition=data.get("condition", {}),
                action_type=data.get("action_type", "warn"),
                action_config=data.get("action_config", {}),
                applicable_agent_types=data.get("applicable_agent_types", []),
                applicable_building_ids=data.get("applicable_building_ids", []),
                applicable_zone_ids=data.get("applicable_zone_ids", []),
                effective_from=_parse_datetime(data.get("effective_from")),
                effective_until=_parse_datetime(data.get("effective_until")),
                enabled=data.get("enabled", True),
                created_by=data.get("created_by", ""),
                parent_rule_id=data.get("parent_rule_id"),
            )
            rid = await self._engine.create_rule(rule)
            logger.info("API create_rule: %s", rid)
            return {"rule_id": rid, "status": "created"}
        except Exception as exc:
            logger.exception("API create_rule failed")
            return {"error": str(exc)}

    # ----------------------------------------------------------------
    # 2. Get rule
    # ----------------------------------------------------------------

    async def get_rule(self, rule_id: str) -> dict:
        """Return a single governance rule as a dict, or an error dict."""
        try:
            rule = await self._engine.get_rule(rule_id)
            if rule is None:
                return {"error": "not_found"}
            return self._rule_to_dict(rule)
        except Exception as exc:
            logger.exception("API get_rule failed for %s", rule_id)
            return {"error": str(exc)}

    # ----------------------------------------------------------------
    # 3. Update rule (partial)
    # ----------------------------------------------------------------

    async def update_rule(self, rule_id: str, data: dict) -> dict:
        """Apply a partial update to a governance rule."""
        try:
            updates = dict(data)
            for dt_field in ("effective_from", "effective_until"):
                if dt_field in updates:
                    updates[dt_field] = _parse_datetime(updates[dt_field])

            ok = await self._engine.update_rule(rule_id, updates)
            if not ok:
                return {"error": "not_found"}
            return {"status": "updated"}
        except Exception as exc:
            logger.exception("API update_rule failed for %s", rule_id)
            return {"error": str(exc)}

    # ----------------------------------------------------------------
    # 4. Disable rule (soft)
    # ----------------------------------------------------------------

    async def disable_rule(self, rule_id: str) -> dict:
        """Soft-disable a governance rule."""
        try:
            ok = await self._engine.disable_rule(rule_id)
            if not ok:
                return {"error": "not_found"}
            return {"status": "disabled"}
        except Exception as exc:
            logger.exception("API disable_rule failed for %s", rule_id)
            return {"error": str(exc)}

    # ----------------------------------------------------------------
    # 5. List rules
    # ----------------------------------------------------------------

    async def list_rules(self, filters: dict) -> dict:
        """Query active governance rules matching *filters*.

        Supported filter keys:
          scope, agent_type, building_id, zone_id
        """
        try:
            rules = await self._engine.get_active_rules(
                scope=filters.get("scope"),
                agent_type=filters.get("agent_type"),
                building_id=filters.get("building_id"),
                zone_id=filters.get("zone_id"),
            )
            serialized = [self._rule_to_dict(r) for r in rules]
            return {"items": serialized, "total": len(serialized)}
        except Exception as exc:
            logger.exception("API list_rules failed")
            return {"error": str(exc)}

    # ----------------------------------------------------------------
    # 6. Evaluate rules
    # ----------------------------------------------------------------

    async def evaluate_rules(self, data: dict) -> dict:
        """Evaluate all applicable rules against a decision + context.

        Expected *data* keys:
          decision (dict), context (dict), scope (str, optional),
          agent_type (str, optional)
        """
        try:
            decision: Dict[str, Any] = data.get("decision", {})
            context: Dict[str, Any] = data.get("context", {})
            scope: str = data.get("scope", "system")
            agent_type: str = data.get("agent_type", "")

            results: List[RuleEvalResult] = await self._engine.evaluate(
                decision=decision,
                context=context,
                scope=scope,
                agent_type=agent_type,
            )

            serialized = [self._eval_result_to_dict(r) for r in results]
            block_count = sum(
                1 for r in results if r.action_type == "block"
            )
            warn_count = sum(
                1 for r in results if r.action_type == "warn"
            )

            return {
                "results": serialized,
                "block_count": block_count,
                "warn_count": warn_count,
            }
        except Exception as exc:
            logger.exception("API evaluate_rules failed")
            return {"error": str(exc)}

    # ----------------------------------------------------------------
    # 7. Load seed rules (Tower C)
    # ----------------------------------------------------------------

    async def load_seed_rules(self) -> dict:
        """Load Tower C seed governance rules.

        Returns ``{"loaded": N}`` where N is the number of rules loaded.
        """
        try:
            count = await self._engine.load_tower_c_seed_rules()
            return {"loaded": count}
        except Exception as exc:
            logger.exception("API load_seed_rules failed")
            return {"error": str(exc)}


# ====================================================================
# Decision Log API
# ====================================================================

class DecisionLogAPI:
    """
    Decision Log API

    Wraps :class:`DecisionLogger` (K3) with dict-in / dict-out async
    methods suitable for REST serialization.
    """

    def __init__(self, decision_logger: DecisionLogger) -> None:
        self._logger = decision_logger

    # ----------------------------------------------------------------
    # Serialization helper
    # ----------------------------------------------------------------

    @staticmethod
    def _record_to_dict(r: DecisionRecord) -> Dict[str, Any]:
        """Convert a :class:`DecisionRecord` to a JSON-safe dict."""
        return _safe_asdict(r)

    # ----------------------------------------------------------------
    # 1. Log decision
    # ----------------------------------------------------------------

    async def log_decision(self, data: dict) -> dict:
        """Log a new decision record.

        Expected *data* keys:
          agent_id, agent_type, decision_type, decision (dict),
          context (dict with DecisionContext fields),
          workflow_instance_id (optional), node_id (optional)
        """
        try:
            # Build DecisionContext from nested dict
            ctx_data = data.get("context", {})
            context = DecisionContext(
                trigger_type=ctx_data.get("trigger_type", "scheduled"),
                environmental_state=ctx_data.get("environmental_state", {}),
                available_agents=ctx_data.get("available_agents", []),
                active_constraints=ctx_data.get("active_constraints", []),
                llm_model=ctx_data.get("llm_model", ""),
                llm_input_tokens=ctx_data.get("llm_input_tokens", 0),
                llm_output_tokens=ctx_data.get("llm_output_tokens", 0),
                llm_latency_ms=ctx_data.get("llm_latency_ms", 0),
                validation_passed=ctx_data.get("validation_passed", True),
                validation_errors=ctx_data.get("validation_errors", []),
                knowledge_used=ctx_data.get("knowledge_used", []),
                rules_evaluated=ctx_data.get("rules_evaluated", []),
            )

            # Parse timestamp
            timestamp = _parse_datetime(data.get("timestamp"))
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)

            record = DecisionRecord(
                record_id=data.get("record_id", ""),
                agent_id=data.get("agent_id", ""),
                agent_type=data.get("agent_type", ""),
                decision_type=data.get("decision_type", ""),
                timestamp=timestamp,
                context=context,
                decision=data.get("decision", {}),
                workflow_instance_id=data.get("workflow_instance_id", ""),
                node_id=data.get("node_id", "default"),
            )

            rid = await self._logger.log_decision(record)
            logger.info("API log_decision: %s", rid)
            return {"record_id": rid, "status": "logged"}
        except Exception as exc:
            logger.exception("API log_decision failed")
            return {"error": str(exc)}

    # ----------------------------------------------------------------
    # 2. Update outcome
    # ----------------------------------------------------------------

    async def update_outcome(self, record_id: str, data: dict) -> dict:
        """Back-fill the outcome for a previously logged decision.

        Expected *data* keys (all optional, mirroring DecisionOutcome):
          task_completion_status, actual_duration_minutes, quality_score,
          human_override, override_by, override_reason, override_action,
          outcome_details
        """
        try:
            outcome = DecisionOutcome(
                task_completion_status=data.get(
                    "task_completion_status", "unknown"
                ),
                actual_duration_minutes=data.get(
                    "actual_duration_minutes", 0.0
                ),
                quality_score=data.get("quality_score"),
                human_override=data.get("human_override", False),
                override_by=data.get("override_by", ""),
                override_reason=data.get("override_reason", ""),
                override_action=data.get("override_action", {}),
                outcome_details=data.get("outcome_details", {}),
            )
            ok = await self._logger.update_outcome(record_id, outcome)
            if not ok:
                return {"error": "not_found"}
            return {"status": "updated"}
        except Exception as exc:
            logger.exception(
                "API update_outcome failed for %s", record_id
            )
            return {"error": str(exc)}

    # ----------------------------------------------------------------
    # 3. Query decisions
    # ----------------------------------------------------------------

    async def query_decisions(self, filters: dict) -> dict:
        """Query decision records with optional filters.

        Supported filter keys:
          agent_type, decision_type, start_time (ISO string),
          end_time (ISO string), has_human_override (bool),
          min_quality_score (float), limit (int), offset (int)
        """
        try:
            records = await self._logger.query_decisions(
                agent_type=filters.get("agent_type"),
                decision_type=filters.get("decision_type"),
                start_time=_parse_datetime(filters.get("start_time")),
                end_time=_parse_datetime(filters.get("end_time")),
                has_human_override=filters.get("has_human_override"),
                min_quality_score=filters.get("min_quality_score"),
                limit=filters.get("limit", 100),
                offset=filters.get("offset", 0),
            )
            serialized = [self._record_to_dict(r) for r in records]
            return {"items": serialized, "total": len(serialized)}
        except Exception as exc:
            logger.exception("API query_decisions failed")
            return {"error": str(exc)}

    # ----------------------------------------------------------------
    # 4. Get stats
    # ----------------------------------------------------------------

    async def get_stats(
        self, agent_type: str, time_range_days: int = 7
    ) -> dict:
        """Return aggregate decision statistics for an agent type."""
        try:
            stats = await self._logger.get_decision_stats(
                agent_type=agent_type,
                time_range_days=time_range_days,
            )
            return stats
        except Exception as exc:
            logger.exception("API get_stats failed for %s", agent_type)
            return {"error": str(exc)}


# ====================================================================
# Module exports
# ====================================================================

__all__ = [
    "KnowledgeManagementAPI",
    "RuleManagementAPI",
    "DecisionLogAPI",
]
