"""
B5 Human-Agent Autonomy Boundaries Module for ECIS.

Manages autonomy levels for human-robot task collaboration in cleaning operations.
Determines which decisions the AI agent can make autonomously versus those
requiring explicit human approval, with context-aware escalation logic.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# AutonomyLevel -- string-constant enum approach
# ---------------------------------------------------------------------------

class AutonomyLevel:
    """
    Autonomy levels for human-AI task collaboration.

    L0 FULL_HUMAN      - Human decides everything; AI provides no autonomous action.
    L1 HUMAN_APPROVE    - AI suggests a course of action; human must approve.
    L2 AI_EXECUTE_NOTIFY - AI executes autonomously and notifies the human.
    L3 FULL_AI          - AI decides and executes with no human involvement.
    """

    FULL_HUMAN = "full_human"                # L0
    HUMAN_APPROVE = "human_approve"          # L1
    AI_EXECUTE_NOTIFY = "ai_execute_notify"  # L2
    FULL_AI = "full_ai"                      # L3

    # Ordered from least to most autonomous -- used for comparisons.
    _ORDERING: Dict[str, int] = {
        FULL_HUMAN: 0,
        HUMAN_APPROVE: 1,
        AI_EXECUTE_NOTIFY: 2,
        FULL_AI: 3,
    }

    ALL_LEVELS: List[str] = [FULL_HUMAN, HUMAN_APPROVE, AI_EXECUTE_NOTIFY, FULL_AI]

    @classmethod
    def rank(cls, level: str) -> int:
        """Return the numeric rank (0-3) for the given autonomy level string."""
        if level not in cls._ORDERING:
            raise ValueError(
                f"Unknown autonomy level '{level}'. "
                f"Valid levels: {list(cls._ORDERING.keys())}"
            )
        return cls._ORDERING[level]

    @classmethod
    def from_rank(cls, rank: int) -> str:
        """Return the autonomy level string for a given numeric rank (0-3)."""
        for level, r in cls._ORDERING.items():
            if r == rank:
                return level
        raise ValueError(f"No autonomy level with rank {rank}. Valid ranks: 0-3")

    @classmethod
    def cap(cls, level: str, max_level: str) -> str:
        """Cap *level* so it does not exceed *max_level*."""
        return level if cls.rank(level) <= cls.rank(max_level) else max_level

    @classmethod
    def elevate(cls, level: str, min_level: str) -> str:
        """Elevate *level* so it is at least *min_level*."""
        return level if cls.rank(level) >= cls.rank(min_level) else min_level


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TaskAutonomyConfig:
    """Configuration that governs autonomy behaviour for a specific task type."""

    task_type: str                  # e.g. standard_clean, deep_clean, emergency, reassignment
    autonomy_level: str             # one of AutonomyLevel values
    conditions: Dict[str, Any] = field(default_factory=dict)
    escalation_rules: List[Dict[str, Any]] = field(default_factory=list)
    max_auto_assignments: int = 5
    require_confirmation_above_priority: int = 4
    auto_timeout_minutes: int = 30

    def __post_init__(self) -> None:
        if self.autonomy_level not in AutonomyLevel._ORDERING:
            raise ValueError(
                f"Invalid autonomy_level '{self.autonomy_level}' for task type "
                f"'{self.task_type}'. Must be one of {AutonomyLevel.ALL_LEVELS}"
            )


@dataclass
class AutoExecuteResult:
    """Result of checking whether the AI agent may auto-execute a task."""

    can_execute: bool
    autonomy_level: str
    reason: str = ""
    required_actions: List[str] = field(default_factory=list)
    escalate_to: Optional[str] = None


# ---------------------------------------------------------------------------
# Internal approval-request record
# ---------------------------------------------------------------------------

@dataclass
class _ApprovalRequest:
    """Internal record for a pending human-approval request."""

    request_id: str
    task_id: str
    task_type: str
    decision: Dict[str, Any]
    context: Dict[str, Any]
    status: str = "pending"           # pending | approved | rejected
    created_at: str = ""
    responded_at: Optional[str] = None
    approved: Optional[bool] = None
    modifications: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# HumanAgentBoundary -- main orchestrator
# ---------------------------------------------------------------------------

class HumanAgentBoundary:
    """
    Manages the boundary between human and AI agent decision-making for
    ECIS cleaning-robot task collaboration.

    Responsibilities
    ----------------
    * Store per-task-type autonomy configurations.
    * Resolve the effective autonomy level given runtime context.
    * Gate auto-execution decisions and track approval workflows.
    * Provide Tower C default configurations out of the box.
    """

    def __init__(self) -> None:
        self._task_configs: Dict[str, TaskAutonomyConfig] = {}
        self._decision_log: List[Dict[str, Any]] = []
        self._pending_approvals: Dict[str, _ApprovalRequest] = {}
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # 1. configure_task_autonomy
    # ------------------------------------------------------------------

    async def configure_task_autonomy(self, config: TaskAutonomyConfig) -> None:
        """Register or update the autonomy configuration for a task type."""
        async with self._lock:
            self._task_configs[config.task_type] = config
            self._log_decision(
                action="configure_task_autonomy",
                task_type=config.task_type,
                details={
                    "autonomy_level": config.autonomy_level,
                    "max_auto_assignments": config.max_auto_assignments,
                    "require_confirmation_above_priority": config.require_confirmation_above_priority,
                    "auto_timeout_minutes": config.auto_timeout_minutes,
                },
            )

    # ------------------------------------------------------------------
    # 2. get_autonomy_level
    # ------------------------------------------------------------------

    async def get_autonomy_level(self, task_type: str, context: Dict[str, Any]) -> str:
        """
        Determine the effective autonomy level for *task_type* given runtime
        *context*.

        Context keys considered
        -----------------------
        priority : int          Task priority (higher = more critical).
        is_emergency : bool     Whether the situation is an emergency.
        robot_count : int       Number of robots currently available.
        human_available : bool  Whether a human supervisor is reachable.
        time_of_day : str       Informational; reserved for future rules.

        Override rules (applied in order)
        ---------------------------------
        1. Emergency override  -- escalate to L3.
        2. High-priority cap   -- cap at L1 when priority >= threshold.
        3. No human available  -- ensure level is at most L2 (never L0/L1
           without a human to fulfil the role).
        4. Low robot count     -- for *reassignment* tasks, escalate to L3
           when fewer than 3 robots are available.
        """
        config = self._task_configs.get(task_type)
        if config is None:
            raise KeyError(
                f"No autonomy configuration registered for task type '{task_type}'. "
                "Call configure_task_autonomy() first or load_tower_c_defaults()."
            )

        level = config.autonomy_level

        # --- 1. Emergency override: escalate to L3 regardless ---------------
        if context.get("is_emergency", False):
            level = AutonomyLevel.FULL_AI

        # --- 2. High-priority cap: cap at L1 --------------------------------
        priority = context.get("priority", 0)
        if priority >= config.require_confirmation_above_priority:
            # Emergency override (rule 1) takes precedence -- only apply the
            # cap when this is NOT an emergency.
            if not context.get("is_emergency", False):
                level = AutonomyLevel.cap(level, AutonomyLevel.HUMAN_APPROVE)

        # --- 3. No human available: ensure at most L2 -----------------------
        if not context.get("human_available", True):
            # If the current level requires a human (L0 or L1) but none is
            # available, elevate to L2 so the system is not blocked.
            if AutonomyLevel.rank(level) <= AutonomyLevel.rank(AutonomyLevel.HUMAN_APPROVE):
                level = AutonomyLevel.AI_EXECUTE_NOTIFY

        # --- 4. Low robot count: emergency auto-reassignment -----------------
        robot_count = context.get("robot_count")
        if robot_count is not None and robot_count < 3 and task_type == "reassignment":
            level = AutonomyLevel.FULL_AI

        self._log_decision(
            action="get_autonomy_level",
            task_type=task_type,
            details={
                "base_level": config.autonomy_level,
                "resolved_level": level,
                "context": context,
            },
        )

        return level

    # ------------------------------------------------------------------
    # 3. check_can_auto_execute
    # ------------------------------------------------------------------

    async def check_can_auto_execute(
        self, task_type: str, context: Dict[str, Any]
    ) -> AutoExecuteResult:
        """
        Check whether the AI agent is permitted to auto-execute a task of
        *task_type* under the supplied *context*.

        Returns an :class:`AutoExecuteResult` describing the verdict.
        """
        level = await self.get_autonomy_level(task_type, context)
        config = self._task_configs[task_type]

        required_actions: List[str] = []
        reason = ""
        escalate_to: Optional[str] = None
        can_execute = False

        if level == AutonomyLevel.FULL_AI:
            can_execute = True
            required_actions.append("log_decision")
            reason = "Full AI autonomy -- executing without human involvement."

        elif level == AutonomyLevel.AI_EXECUTE_NOTIFY:
            can_execute = True
            required_actions.extend(["notify_supervisor", "log_decision"])
            reason = "AI may execute but must notify the human supervisor."

        elif level == AutonomyLevel.HUMAN_APPROVE:
            can_execute = False
            escalate_to = "human_supervisor"
            reason = (
                "Human approval required before execution. "
                f"Auto-execute after {config.auto_timeout_minutes} min timeout "
                "if no response."
            )

        elif level == AutonomyLevel.FULL_HUMAN:
            can_execute = False
            escalate_to = "human_operator"
            reason = "Full human control -- AI must not act autonomously."

        result = AutoExecuteResult(
            can_execute=can_execute,
            autonomy_level=level,
            reason=reason,
            required_actions=required_actions,
            escalate_to=escalate_to,
        )

        self._log_decision(
            action="check_can_auto_execute",
            task_type=task_type,
            details={
                "can_execute": result.can_execute,
                "autonomy_level": result.autonomy_level,
                "reason": result.reason,
                "required_actions": result.required_actions,
                "escalate_to": result.escalate_to,
                "context": context,
            },
        )

        return result

    # ------------------------------------------------------------------
    # 4. request_human_approval
    # ------------------------------------------------------------------

    async def request_human_approval(
        self,
        task_id: str,
        task_type: str,
        decision: Dict[str, Any],
        context: Dict[str, Any],
    ) -> str:
        """
        Create a human-approval request and return its unique *request_id*.

        The request is stored internally until the human responds via
        :meth:`process_human_response`.
        """
        request_id = f"apr-{uuid.uuid4().hex[:12]}"

        request = _ApprovalRequest(
            request_id=request_id,
            task_id=task_id,
            task_type=task_type,
            decision=decision,
            context=context,
            user_id=context.get("user_id"),
        )

        async with self._lock:
            self._pending_approvals[request_id] = request

        self._log_decision(
            action="request_human_approval",
            task_type=task_type,
            details={
                "request_id": request_id,
                "task_id": task_id,
                "decision": decision,
                "context": context,
            },
        )

        return request_id

    # ------------------------------------------------------------------
    # 5. process_human_response
    # ------------------------------------------------------------------

    async def process_human_response(
        self,
        request_id: str,
        approved: bool,
        modifications: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Record the human's response to a pending approval request.

        Returns a dict summarising the outcome:
        ``{"request_id", "task_id", "task_type", "approved", "modifications",
        "status", "responded_at"}``.

        Raises :class:`KeyError` if *request_id* is unknown and
        :class:`ValueError` if the request has already been resolved.
        """
        async with self._lock:
            if request_id not in self._pending_approvals:
                raise KeyError(f"No pending approval found for request_id '{request_id}'.")

            request = self._pending_approvals[request_id]

            if request.status != "pending":
                raise ValueError(
                    f"Approval request '{request_id}' has already been resolved "
                    f"with status '{request.status}'."
                )

            now = datetime.now(timezone.utc).isoformat()
            request.status = "approved" if approved else "rejected"
            request.approved = approved
            request.modifications = modifications
            request.responded_at = now

        result: Dict[str, Any] = {
            "request_id": request_id,
            "task_id": request.task_id,
            "task_type": request.task_type,
            "approved": approved,
            "modifications": modifications,
            "status": request.status,
            "responded_at": now,
        }

        self._log_decision(
            action="process_human_response",
            task_type=request.task_type,
            details=result,
        )

        return result

    # ------------------------------------------------------------------
    # 6. get_pending_approvals
    # ------------------------------------------------------------------

    async def get_pending_approvals(
        self, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Return a list of all pending approval requests.

        If *user_id* is provided, only requests associated with that user are
        returned.
        """
        results: List[Dict[str, Any]] = []
        for req in self._pending_approvals.values():
            if req.status != "pending":
                continue
            if user_id is not None and req.user_id != user_id:
                continue
            results.append({
                "request_id": req.request_id,
                "task_id": req.task_id,
                "task_type": req.task_type,
                "decision": req.decision,
                "context": req.context,
                "created_at": req.created_at,
                "user_id": req.user_id,
            })
        return results

    # ------------------------------------------------------------------
    # 7. load_tower_c_defaults
    # ------------------------------------------------------------------

    async def load_tower_c_defaults(self) -> int:
        """
        Load the default autonomy configurations for Tower C operations.

        Registers five task types:

        * **standard_clean** -- L2 (AI_EXECUTE_NOTIFY)
        * **deep_clean**     -- L1 (HUMAN_APPROVE)
        * **emergency**      -- L3 (FULL_AI) with 5-minute escalation
        * **reassignment**   -- L1 (HUMAN_APPROVE); auto-escalates to L3
          when fewer than 3 robots are available (handled by context rules)
        * **special_event**  -- L0 (FULL_HUMAN)

        Returns the number of configurations loaded.
        """
        defaults: List[TaskAutonomyConfig] = [
            TaskAutonomyConfig(
                task_type="standard_clean",
                autonomy_level=AutonomyLevel.AI_EXECUTE_NOTIFY,
                conditions={"floor_types": ["lobby", "corridor", "restroom"]},
                escalation_rules=[],
                max_auto_assignments=5,
                require_confirmation_above_priority=4,
                auto_timeout_minutes=30,
            ),
            TaskAutonomyConfig(
                task_type="deep_clean",
                autonomy_level=AutonomyLevel.HUMAN_APPROVE,
                conditions={"requires_special_equipment": True},
                escalation_rules=[
                    {
                        "condition": "no_response",
                        "timeout_minutes": 15,
                        "escalate_to": AutonomyLevel.AI_EXECUTE_NOTIFY,
                        "notify": ["facility_manager"],
                    }
                ],
                max_auto_assignments=3,
                require_confirmation_above_priority=3,
                auto_timeout_minutes=15,
            ),
            TaskAutonomyConfig(
                task_type="emergency",
                autonomy_level=AutonomyLevel.FULL_AI,
                conditions={"immediate_response": True},
                escalation_rules=[
                    {
                        "condition": "execution_delay",
                        "timeout_minutes": 5,
                        "escalate_to": "facility_manager",
                        "notify": ["facility_manager", "operations_center"],
                        "action": "alert_all_available_robots",
                    }
                ],
                max_auto_assignments=10,
                require_confirmation_above_priority=5,
                auto_timeout_minutes=5,
            ),
            TaskAutonomyConfig(
                task_type="reassignment",
                autonomy_level=AutonomyLevel.HUMAN_APPROVE,
                conditions={
                    "auto_escalate_when_robots_below": 3,
                    "escalate_level": AutonomyLevel.FULL_AI,
                },
                escalation_rules=[
                    {
                        "condition": "robot_count_low",
                        "threshold": 3,
                        "escalate_to": AutonomyLevel.FULL_AI,
                        "notify": ["supervisor"],
                    }
                ],
                max_auto_assignments=5,
                require_confirmation_above_priority=4,
                auto_timeout_minutes=10,
            ),
            TaskAutonomyConfig(
                task_type="special_event",
                autonomy_level=AutonomyLevel.FULL_HUMAN,
                conditions={"requires_human_coordination": True},
                escalation_rules=[],
                max_auto_assignments=0,
                require_confirmation_above_priority=1,
                auto_timeout_minutes=60,
            ),
        ]

        count = 0
        for cfg in defaults:
            await self.configure_task_autonomy(cfg)
            count += 1

        self._log_decision(
            action="load_tower_c_defaults",
            task_type="*",
            details={"configs_loaded": count},
        )

        return count

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log_decision(
        self,
        action: str,
        task_type: str,
        details: Dict[str, Any],
    ) -> None:
        """Append an entry to the in-memory decision log."""
        self._decision_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "task_type": task_type,
            "details": details,
        })

    # -- Convenience accessors (non-async, read-only) --------------------

    @property
    def decision_log(self) -> List[Dict[str, Any]]:
        """Return a shallow copy of the decision log."""
        return list(self._decision_log)

    @property
    def registered_task_types(self) -> List[str]:
        """Return the list of currently registered task type names."""
        return list(self._task_configs.keys())
