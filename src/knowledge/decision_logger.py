"""
K3 DecisionLogger — 决策日志服务 (Phase 1: In-Memory)

Records the full lifecycle of agent decisions as Context -> Decision -> Outcome
triples.  Phase 1 uses a plain dict store; Phase 2 will swap in TimescaleDB via
the same async interface.

Design constraints:
  - log_decision MUST NOT block the caller (< 100 ms).
  - Outcome is back-filled asynchronously after task completion.
  - Training candidate marking is a Phase 3 placeholder.
"""

import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================
# Data Models
# ============================================================

@dataclass
class DecisionContext:
    """Snapshot of the environment and LLM state at decision time."""

    trigger_type: str = "scheduled"  # scheduled | event_driven | manual
    environmental_state: Dict[str, Any] = field(default_factory=dict)
    available_agents: List[Dict] = field(default_factory=list)
    active_constraints: List[str] = field(default_factory=list)
    llm_model: str = ""
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    llm_latency_ms: int = 0
    validation_passed: bool = True
    validation_errors: List[Dict] = field(default_factory=list)
    knowledge_used: List[str] = field(default_factory=list)
    rules_evaluated: List[str] = field(default_factory=list)


@dataclass
class DecisionOutcome:
    """Result of the decision, filled in after task execution."""

    task_completion_status: str = "unknown"  # completed | failed | cancelled | timeout
    actual_duration_minutes: float = 0.0
    quality_score: Optional[float] = None  # 0.0-1.0
    human_override: bool = False
    override_by: str = ""
    override_reason: str = ""
    override_action: Dict[str, Any] = field(default_factory=dict)
    outcome_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionRecord:
    """Full Context -> Decision -> Outcome triple."""

    record_id: str
    agent_id: str
    agent_type: str
    decision_type: str
    timestamp: datetime
    context: DecisionContext
    decision: Dict[str, Any]
    outcome: Optional[DecisionOutcome] = None
    workflow_instance_id: str = ""
    node_id: str = "default"
    is_training_candidate: bool = False
    reward_signal: Optional[float] = None


# ============================================================
# Helper
# ============================================================

def _generate_record_id() -> str:
    """Generate a unique decision-record id."""
    return f"dr-{uuid.uuid4().hex[:12]}"


# ============================================================
# DecisionLogger (Phase 1 — in-memory)
# ============================================================

class DecisionLogger:
    """
    In-memory decision logger.

    All public methods are async to keep the interface compatible with the
    future TimescaleDB-backed implementation.
    """

    def __init__(self) -> None:
        self._records: Dict[str, DecisionRecord] = {}

    # ----------------------------------------------------------
    # Properties
    # ----------------------------------------------------------

    @property
    def record_count(self) -> int:
        """Return the total number of stored decision records."""
        return len(self._records)

    # ----------------------------------------------------------
    # Core API
    # ----------------------------------------------------------

    async def log_decision(self, record: DecisionRecord) -> str:
        """
        Store a decision record (Context + Decision; Outcome initially None).

        In production this would be dispatched via ``asyncio.create_task`` so
        the caller is never blocked.  The in-memory implementation is already
        fast enough to satisfy the < 100 ms constraint directly.

        Returns:
            The ``record_id`` of the stored record.
        """
        if not record.record_id:
            record.record_id = _generate_record_id()

        if not record.timestamp:
            record.timestamp = datetime.now(timezone.utc)

        self._records[record.record_id] = record
        logger.debug(
            "Logged decision %s  agent=%s  type=%s",
            record.record_id,
            record.agent_type,
            record.decision_type,
        )
        return record.record_id

    async def update_outcome(
        self, record_id: str, outcome: DecisionOutcome
    ) -> bool:
        """
        Back-fill the outcome for a previously logged decision.

        Triggered by downstream events such as ``ecis.task.completed``,
        ``ecis.task.failed``, or ``ecis.task.overridden``.

        Returns:
            ``True`` if the record was found and updated, ``False`` otherwise.
        """
        record = self._records.get(record_id)
        if record is None:
            logger.warning("update_outcome: record_id %s not found", record_id)
            return False

        record.outcome = outcome
        logger.debug(
            "Updated outcome for %s  status=%s  override=%s",
            record_id,
            outcome.task_completion_status,
            outcome.human_override,
        )
        return True

    async def query_decisions(
        self,
        agent_type: Optional[str] = None,
        decision_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        has_human_override: Optional[bool] = None,
        min_quality_score: Optional[float] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DecisionRecord]:
        """
        Query and paginate decision records with optional filters.

        All filter parameters are optional.  When omitted the corresponding
        filter is not applied.
        """
        results: List[DecisionRecord] = []

        for record in self._records.values():
            if agent_type is not None and record.agent_type != agent_type:
                continue
            if decision_type is not None and record.decision_type != decision_type:
                continue
            if start_time is not None and record.timestamp < start_time:
                continue
            if end_time is not None and record.timestamp > end_time:
                continue

            # Outcome-dependent filters
            if has_human_override is not None:
                if record.outcome is None:
                    # No outcome yet — cannot match override filter
                    if has_human_override:
                        continue
                elif record.outcome.human_override != has_human_override:
                    continue

            if min_quality_score is not None:
                if record.outcome is None or record.outcome.quality_score is None:
                    continue
                if record.outcome.quality_score < min_quality_score:
                    continue

            results.append(record)

        # Sort by timestamp descending (most recent first)
        results.sort(key=lambda r: r.timestamp, reverse=True)

        # Paginate
        return results[offset : offset + limit]

    # ----------------------------------------------------------
    # Analytics
    # ----------------------------------------------------------

    async def get_decision_stats(
        self, agent_type: str, time_range_days: int = 7
    ) -> Dict[str, Any]:
        """
        Compute aggregate statistics for a given agent type.

        Returns a dict with keys:
            total_decisions, validation_pass_rate, human_override_rate,
            avg_quality_score, avg_llm_latency_ms, decisions_by_day
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=time_range_days)

        matching: List[DecisionRecord] = [
            r
            for r in self._records.values()
            if r.agent_type == agent_type and r.timestamp >= cutoff
        ]

        total = len(matching)
        if total == 0:
            return {
                "total_decisions": 0,
                "validation_pass_rate": 0.0,
                "human_override_rate": 0.0,
                "avg_quality_score": 0.0,
                "avg_llm_latency_ms": 0.0,
                "decisions_by_day": {},
            }

        validation_passed = sum(
            1 for r in matching if r.context.validation_passed
        )
        override_count = sum(
            1
            for r in matching
            if r.outcome is not None and r.outcome.human_override
        )

        quality_scores = [
            r.outcome.quality_score
            for r in matching
            if r.outcome is not None and r.outcome.quality_score is not None
        ]
        latencies = [
            r.context.llm_latency_ms
            for r in matching
            if r.context.llm_latency_ms > 0
        ]

        # Group by day (ISO date string -> count)
        by_day: Dict[str, int] = defaultdict(int)
        for r in matching:
            day_key = r.timestamp.strftime("%Y-%m-%d")
            by_day[day_key] += 1

        return {
            "total_decisions": total,
            "validation_pass_rate": validation_passed / total,
            "human_override_rate": override_count / total,
            "avg_quality_score": (
                sum(quality_scores) / len(quality_scores)
                if quality_scores
                else 0.0
            ),
            "avg_llm_latency_ms": (
                sum(latencies) / len(latencies) if latencies else 0.0
            ),
            "decisions_by_day": dict(sorted(by_day.items())),
        }

    # ----------------------------------------------------------
    # Phase 3 preparation
    # ----------------------------------------------------------

    async def mark_training_candidates(
        self, criteria: Dict[str, Any]
    ) -> int:
        """
        Mark decision records that match *criteria* as training candidates
        for Phase 3 self-learning.

        Supported criteria keys (all optional, combined with AND):
            min_quality_score  (float): outcome.quality_score >= value
            max_quality_score  (float): outcome.quality_score <= value
            human_override     (bool):  outcome.human_override == value
            agent_type         (str):   record.agent_type == value
            decision_type      (str):   record.decision_type == value

        Typical usage:
            quality_score >= 0.8 AND human_override == False  -> positive sample
            human_override == True                            -> correction sample

        Returns:
            The number of records that were marked.
        """
        min_q = criteria.get("min_quality_score")
        max_q = criteria.get("max_quality_score")
        want_override = criteria.get("human_override")
        want_agent = criteria.get("agent_type")
        want_decision = criteria.get("decision_type")

        marked = 0

        for record in self._records.values():
            # Must have an outcome to be eligible
            if record.outcome is None:
                continue

            if want_agent is not None and record.agent_type != want_agent:
                continue
            if want_decision is not None and record.decision_type != want_decision:
                continue
            if want_override is not None and record.outcome.human_override != want_override:
                continue

            if min_q is not None:
                if record.outcome.quality_score is None:
                    continue
                if record.outcome.quality_score < min_q:
                    continue

            if max_q is not None:
                if record.outcome.quality_score is None:
                    continue
                if record.outcome.quality_score > max_q:
                    continue

            if not record.is_training_candidate:
                record.is_training_candidate = True
                marked += 1

        logger.info(
            "Marked %d records as training candidates  criteria=%s",
            marked,
            criteria,
        )
        return marked


__all__ = [
    "DecisionContext",
    "DecisionOutcome",
    "DecisionRecord",
    "DecisionLogger",
]
