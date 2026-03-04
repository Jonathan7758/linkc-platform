"""
Unit tests for B5 Human-Agent Autonomy Boundaries (human_agent_boundary.py).

Covers AutonomyLevel, TaskAutonomyConfig, HumanAgentBoundary (get_autonomy_level,
check_can_auto_execute, approval workflow), and load_tower_c_defaults.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
import pytest_asyncio

from autonomy.human_agent_boundary import (
    AutoExecuteResult,
    AutonomyLevel,
    HumanAgentBoundary,
    TaskAutonomyConfig,
)


# =====================================================================
# Fixtures
# =====================================================================

@pytest_asyncio.fixture
async def boundary():
    """Return a fresh HumanAgentBoundary with Tower C defaults loaded."""
    b = HumanAgentBoundary()
    await b.load_tower_c_defaults()
    return b


@pytest_asyncio.fixture
async def bare_boundary():
    """Return a fresh HumanAgentBoundary with no configs loaded."""
    return HumanAgentBoundary()


# =====================================================================
# TestAutonomyLevel (5 tests)
# =====================================================================

class TestAutonomyLevel:
    """Tests for the AutonomyLevel class helpers."""

    def test_rank_returns_correct_values(self):
        """rank() returns 0 for FULL_HUMAN through 3 for FULL_AI."""
        assert AutonomyLevel.rank(AutonomyLevel.FULL_HUMAN) == 0
        assert AutonomyLevel.rank(AutonomyLevel.HUMAN_APPROVE) == 1
        assert AutonomyLevel.rank(AutonomyLevel.AI_EXECUTE_NOTIFY) == 2
        assert AutonomyLevel.rank(AutonomyLevel.FULL_AI) == 3

    def test_from_rank_reverse_lookup(self):
        """from_rank() maps numeric ranks back to level strings."""
        assert AutonomyLevel.from_rank(0) == AutonomyLevel.FULL_HUMAN
        assert AutonomyLevel.from_rank(1) == AutonomyLevel.HUMAN_APPROVE
        assert AutonomyLevel.from_rank(2) == AutonomyLevel.AI_EXECUTE_NOTIFY
        assert AutonomyLevel.from_rank(3) == AutonomyLevel.FULL_AI

    def test_cap_limits_level(self):
        """cap() returns the lower of the two levels."""
        # L3 capped at L1 -> L1
        assert AutonomyLevel.cap(AutonomyLevel.FULL_AI, AutonomyLevel.HUMAN_APPROVE) == AutonomyLevel.HUMAN_APPROVE
        # L1 capped at L3 -> L1 (already below cap)
        assert AutonomyLevel.cap(AutonomyLevel.HUMAN_APPROVE, AutonomyLevel.FULL_AI) == AutonomyLevel.HUMAN_APPROVE
        # Same level -> unchanged
        assert AutonomyLevel.cap(AutonomyLevel.AI_EXECUTE_NOTIFY, AutonomyLevel.AI_EXECUTE_NOTIFY) == AutonomyLevel.AI_EXECUTE_NOTIFY

    def test_elevate_raises_level(self):
        """elevate() returns the higher of the two levels."""
        # L0 elevated to L2 -> L2
        assert AutonomyLevel.elevate(AutonomyLevel.FULL_HUMAN, AutonomyLevel.AI_EXECUTE_NOTIFY) == AutonomyLevel.AI_EXECUTE_NOTIFY
        # L3 elevated to L1 -> L3 (already above min)
        assert AutonomyLevel.elevate(AutonomyLevel.FULL_AI, AutonomyLevel.HUMAN_APPROVE) == AutonomyLevel.FULL_AI
        # Same level -> unchanged
        assert AutonomyLevel.elevate(AutonomyLevel.HUMAN_APPROVE, AutonomyLevel.HUMAN_APPROVE) == AutonomyLevel.HUMAN_APPROVE

    def test_all_constants_have_valid_values(self):
        """Every constant in ALL_LEVELS is present in _ORDERING and has rank 0-3."""
        assert len(AutonomyLevel.ALL_LEVELS) == 4
        for level in AutonomyLevel.ALL_LEVELS:
            r = AutonomyLevel.rank(level)
            assert 0 <= r <= 3
            assert AutonomyLevel.from_rank(r) == level


# =====================================================================
# TestTaskAutonomyConfig (3 tests)
# =====================================================================

class TestTaskAutonomyConfig:
    """Tests for the TaskAutonomyConfig dataclass."""

    def test_valid_config_creation(self):
        """A config with a valid autonomy_level is created successfully."""
        cfg = TaskAutonomyConfig(
            task_type="standard_clean",
            autonomy_level=AutonomyLevel.AI_EXECUTE_NOTIFY,
            max_auto_assignments=10,
        )
        assert cfg.task_type == "standard_clean"
        assert cfg.autonomy_level == AutonomyLevel.AI_EXECUTE_NOTIFY
        assert cfg.max_auto_assignments == 10

    def test_invalid_autonomy_level_raises_value_error(self):
        """Creating a config with an unknown autonomy_level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid autonomy_level"):
            TaskAutonomyConfig(
                task_type="bad_task",
                autonomy_level="not_a_real_level",
            )

    def test_default_values(self):
        """Default field values are applied when omitted."""
        cfg = TaskAutonomyConfig(
            task_type="test_task",
            autonomy_level=AutonomyLevel.FULL_HUMAN,
        )
        assert cfg.conditions == {}
        assert cfg.escalation_rules == []
        assert cfg.max_auto_assignments == 5
        assert cfg.require_confirmation_above_priority == 4
        assert cfg.auto_timeout_minutes == 30


# =====================================================================
# TestGetAutonomyLevel (8 tests)
# =====================================================================

class TestGetAutonomyLevel:
    """Tests for HumanAgentBoundary.get_autonomy_level()."""

    @pytest.mark.asyncio
    async def test_returns_base_level_when_no_context_overrides(self, boundary):
        """With neutral context, the base level from config is returned."""
        level = await boundary.get_autonomy_level("standard_clean", {"priority": 1})
        assert level == AutonomyLevel.AI_EXECUTE_NOTIFY

    @pytest.mark.asyncio
    async def test_emergency_context_overrides_to_full_ai(self, boundary):
        """is_emergency=True escalates any task to FULL_AI."""
        level = await boundary.get_autonomy_level(
            "deep_clean", {"is_emergency": True}
        )
        assert level == AutonomyLevel.FULL_AI

    @pytest.mark.asyncio
    async def test_high_priority_caps_at_human_approve(self, boundary):
        """Priority >= threshold caps the level to HUMAN_APPROVE."""
        # standard_clean base is L2, threshold is 4 -> capped to L1
        level = await boundary.get_autonomy_level(
            "standard_clean", {"priority": 5}
        )
        assert level == AutonomyLevel.HUMAN_APPROVE

    @pytest.mark.asyncio
    async def test_human_not_available_elevates_to_l2(self, boundary):
        """human_available=False elevates L0/L1 to L2 so system is not blocked."""
        # deep_clean base is L1
        level = await boundary.get_autonomy_level(
            "deep_clean", {"human_available": False}
        )
        assert level == AutonomyLevel.AI_EXECUTE_NOTIFY

    @pytest.mark.asyncio
    async def test_low_robot_count_for_reassignment_escalates_to_full_ai(self, boundary):
        """robot_count < 3 for 'reassignment' task escalates to FULL_AI."""
        level = await boundary.get_autonomy_level(
            "reassignment", {"robot_count": 2}
        )
        assert level == AutonomyLevel.FULL_AI

    @pytest.mark.asyncio
    async def test_emergency_overrides_priority_cap(self, boundary):
        """Emergency flag takes precedence over the high-priority cap."""
        level = await boundary.get_autonomy_level(
            "standard_clean",
            {"priority": 10, "is_emergency": True},
        )
        assert level == AutonomyLevel.FULL_AI

    @pytest.mark.asyncio
    async def test_unknown_task_type_raises_key_error(self, boundary):
        """An unregistered task_type raises KeyError."""
        with pytest.raises(KeyError, match="No autonomy configuration"):
            await boundary.get_autonomy_level("nonexistent_task", {})

    @pytest.mark.asyncio
    async def test_combined_context_high_priority_and_no_human(self, boundary):
        """High priority caps at L1, then no human elevates L1 to L2."""
        # standard_clean base L2, priority >= 4 caps to L1, then no human -> L2
        level = await boundary.get_autonomy_level(
            "standard_clean",
            {"priority": 5, "human_available": False},
        )
        assert level == AutonomyLevel.AI_EXECUTE_NOTIFY

    @pytest.mark.asyncio
    async def test_special_event_full_human_with_no_human_elevates(self, boundary):
        """special_event base L0, human_available=False elevates to L2."""
        level = await boundary.get_autonomy_level(
            "special_event", {"human_available": False}
        )
        assert level == AutonomyLevel.AI_EXECUTE_NOTIFY


# =====================================================================
# TestCheckCanAutoExecute (5 tests)
# =====================================================================

class TestCheckCanAutoExecute:
    """Tests for HumanAgentBoundary.check_can_auto_execute()."""

    @pytest.mark.asyncio
    async def test_l3_can_auto_execute(self, boundary):
        """FULL_AI (L3) allows auto execution."""
        result = await boundary.check_can_auto_execute(
            "emergency", {"priority": 1}
        )
        assert result.can_execute is True
        assert result.autonomy_level == AutonomyLevel.FULL_AI
        assert "log_decision" in result.required_actions

    @pytest.mark.asyncio
    async def test_l2_can_auto_execute_with_notify(self, boundary):
        """AI_EXECUTE_NOTIFY (L2) allows auto execution with notification."""
        result = await boundary.check_can_auto_execute(
            "standard_clean", {"priority": 1}
        )
        assert result.can_execute is True
        assert result.autonomy_level == AutonomyLevel.AI_EXECUTE_NOTIFY
        assert "notify_supervisor" in result.required_actions
        assert "log_decision" in result.required_actions

    @pytest.mark.asyncio
    async def test_l1_cannot_auto_execute_needs_approval(self, boundary):
        """HUMAN_APPROVE (L1) blocks auto execution and escalates."""
        result = await boundary.check_can_auto_execute(
            "deep_clean", {"priority": 1}
        )
        assert result.can_execute is False
        assert result.autonomy_level == AutonomyLevel.HUMAN_APPROVE
        assert result.escalate_to == "human_supervisor"

    @pytest.mark.asyncio
    async def test_l0_cannot_auto_execute(self, boundary):
        """FULL_HUMAN (L0) blocks auto execution entirely."""
        result = await boundary.check_can_auto_execute(
            "special_event", {"priority": 0}
        )
        assert result.can_execute is False
        assert result.autonomy_level == AutonomyLevel.FULL_HUMAN
        assert result.escalate_to == "human_operator"

    @pytest.mark.asyncio
    async def test_emergency_overrides_to_auto_execute(self, boundary):
        """Emergency context overrides even a base-L1 task to auto-execute."""
        result = await boundary.check_can_auto_execute(
            "deep_clean", {"is_emergency": True}
        )
        assert result.can_execute is True
        assert result.autonomy_level == AutonomyLevel.FULL_AI


# =====================================================================
# TestApprovalWorkflow (6 tests)
# =====================================================================

class TestApprovalWorkflow:
    """Tests for the request / process / pending approval workflow."""

    @pytest.mark.asyncio
    async def test_request_human_approval_creates_request(self, bare_boundary):
        """request_human_approval returns a unique request_id starting with 'apr-'."""
        request_id = await bare_boundary.request_human_approval(
            task_id="task-001",
            task_type="deep_clean",
            decision={"action": "assign_robot", "robot_id": "R5"},
            context={"priority": 3},
        )
        assert request_id.startswith("apr-")
        assert len(request_id) > 4  # has hex suffix

    @pytest.mark.asyncio
    async def test_get_pending_approvals_returns_pending(self, bare_boundary):
        """Pending approvals appear in get_pending_approvals."""
        req_id = await bare_boundary.request_human_approval(
            task_id="task-002",
            task_type="deep_clean",
            decision={"action": "reassign"},
            context={"priority": 2},
        )
        pending = await bare_boundary.get_pending_approvals()
        assert len(pending) == 1
        assert pending[0]["request_id"] == req_id
        assert pending[0]["task_id"] == "task-002"

    @pytest.mark.asyncio
    async def test_process_human_response_approved(self, bare_boundary):
        """Approving a request sets approved=True and status='approved'."""
        req_id = await bare_boundary.request_human_approval(
            task_id="task-003",
            task_type="deep_clean",
            decision={"action": "reassign"},
            context={},
        )
        result = await bare_boundary.process_human_response(req_id, approved=True)
        assert result["approved"] is True
        assert result["status"] == "approved"
        assert result["request_id"] == req_id
        assert result["responded_at"] is not None

    @pytest.mark.asyncio
    async def test_process_human_response_rejected(self, bare_boundary):
        """Rejecting a request sets approved=False and status='rejected'."""
        req_id = await bare_boundary.request_human_approval(
            task_id="task-004",
            task_type="emergency",
            decision={"action": "halt"},
            context={},
        )
        result = await bare_boundary.process_human_response(
            req_id, approved=False, modifications={"reason": "not needed"}
        )
        assert result["approved"] is False
        assert result["status"] == "rejected"
        assert result["modifications"] == {"reason": "not needed"}

    @pytest.mark.asyncio
    async def test_process_already_resolved_raises_error(self, bare_boundary):
        """Processing an already-resolved request raises ValueError."""
        req_id = await bare_boundary.request_human_approval(
            task_id="task-005",
            task_type="deep_clean",
            decision={"action": "assign"},
            context={},
        )
        await bare_boundary.process_human_response(req_id, approved=True)

        with pytest.raises(ValueError, match="already been resolved"):
            await bare_boundary.process_human_response(req_id, approved=False)

    @pytest.mark.asyncio
    async def test_get_pending_approvals_filtered_by_user_id(self, bare_boundary):
        """get_pending_approvals filters by user_id when provided."""
        await bare_boundary.request_human_approval(
            task_id="task-A",
            task_type="deep_clean",
            decision={"action": "a"},
            context={"user_id": "alice"},
        )
        await bare_boundary.request_human_approval(
            task_id="task-B",
            task_type="deep_clean",
            decision={"action": "b"},
            context={"user_id": "bob"},
        )
        await bare_boundary.request_human_approval(
            task_id="task-C",
            task_type="deep_clean",
            decision={"action": "c"},
            context={"user_id": "alice"},
        )

        alice_pending = await bare_boundary.get_pending_approvals(user_id="alice")
        bob_pending = await bare_boundary.get_pending_approvals(user_id="bob")
        all_pending = await bare_boundary.get_pending_approvals()

        assert len(alice_pending) == 2
        assert len(bob_pending) == 1
        assert len(all_pending) == 3
        assert all(p["user_id"] == "alice" for p in alice_pending)
        assert bob_pending[0]["user_id"] == "bob"

    @pytest.mark.asyncio
    async def test_process_unknown_request_raises_key_error(self, bare_boundary):
        """Processing an unknown request_id raises KeyError."""
        with pytest.raises(KeyError, match="No pending approval"):
            await bare_boundary.process_human_response("apr-nonexistent", approved=True)


# =====================================================================
# TestLoadTowerCDefaults (3 tests)
# =====================================================================

class TestLoadTowerCDefaults:
    """Tests for HumanAgentBoundary.load_tower_c_defaults()."""

    @pytest.mark.asyncio
    async def test_loads_five_configs(self, boundary):
        """load_tower_c_defaults registers exactly 5 task types."""
        task_types = boundary.registered_task_types
        assert len(task_types) == 5
        expected = {"standard_clean", "deep_clean", "emergency", "reassignment", "special_event"}
        assert set(task_types) == expected

    @pytest.mark.asyncio
    async def test_standard_clean_is_l2(self, boundary):
        """standard_clean base level is AI_EXECUTE_NOTIFY (L2)."""
        level = await boundary.get_autonomy_level("standard_clean", {"priority": 0})
        assert level == AutonomyLevel.AI_EXECUTE_NOTIFY

    @pytest.mark.asyncio
    async def test_emergency_is_l3(self, boundary):
        """emergency base level is FULL_AI (L3)."""
        level = await boundary.get_autonomy_level("emergency", {"priority": 0})
        assert level == AutonomyLevel.FULL_AI

    @pytest.mark.asyncio
    async def test_load_returns_count(self):
        """load_tower_c_defaults() returns the number of configs loaded."""
        b = HumanAgentBoundary()
        count = await b.load_tower_c_defaults()
        assert count == 5
