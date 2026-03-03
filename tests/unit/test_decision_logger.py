"""
Comprehensive unit tests for K3 DecisionLogger module.

Covers: log_decision, update_outcome, query_decisions,
        get_decision_stats, mark_training_candidates.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone

from knowledge.decision_logger import (
    DecisionContext,
    DecisionOutcome,
    DecisionRecord,
    DecisionLogger,
)


# ============================================================
# Helper
# ============================================================

def _make_record(agent_type="cleaning", decision_type="schedule", **kwargs):
    ctx = DecisionContext(
        trigger_type=kwargs.get("trigger_type", "scheduled"),
        validation_passed=kwargs.get("validation_passed", True),
        llm_latency_ms=kwargs.get("llm_latency_ms", 50),
    )
    record = DecisionRecord(
        record_id=kwargs.get("record_id", ""),
        agent_id=kwargs.get("agent_id", "agent-001"),
        agent_type=agent_type,
        decision_type=decision_type,
        timestamp=kwargs.get("timestamp", datetime.now(timezone.utc)),
        context=ctx,
        decision=kwargs.get("decision", {"action": "schedule"}),
    )
    return record


# ============================================================
# Fixtures
# ============================================================

@pytest_asyncio.fixture
async def logger_instance():
    """Fresh DecisionLogger for each test."""
    return DecisionLogger()


@pytest_asyncio.fixture
async def populated_logger():
    """DecisionLogger pre-loaded with several records and outcomes."""
    dl = DecisionLogger()
    now = datetime.now(timezone.utc)

    # Record 1 — cleaning / schedule, high quality, no override
    r1 = _make_record(
        record_id="r-001",
        agent_type="cleaning",
        decision_type="schedule",
        timestamp=now - timedelta(hours=3),
        validation_passed=True,
        llm_latency_ms=40,
    )
    await dl.log_decision(r1)
    await dl.update_outcome(
        "r-001",
        DecisionOutcome(
            task_completion_status="completed",
            quality_score=0.9,
            human_override=False,
        ),
    )

    # Record 2 — cleaning / schedule, low quality, with override
    r2 = _make_record(
        record_id="r-002",
        agent_type="cleaning",
        decision_type="schedule",
        timestamp=now - timedelta(hours=2),
        validation_passed=False,
        llm_latency_ms=80,
    )
    await dl.log_decision(r2)
    await dl.update_outcome(
        "r-002",
        DecisionOutcome(
            task_completion_status="completed",
            quality_score=0.3,
            human_override=True,
            override_reason="wrong area",
        ),
    )

    # Record 3 — hvac / control, medium quality
    r3 = _make_record(
        record_id="r-003",
        agent_type="hvac",
        decision_type="control",
        timestamp=now - timedelta(hours=1),
        validation_passed=True,
        llm_latency_ms=60,
    )
    await dl.log_decision(r3)
    await dl.update_outcome(
        "r-003",
        DecisionOutcome(
            task_completion_status="completed",
            quality_score=0.7,
            human_override=False,
        ),
    )

    # Record 4 — cleaning / inspection, no outcome yet
    r4 = _make_record(
        record_id="r-004",
        agent_type="cleaning",
        decision_type="inspection",
        timestamp=now,
        validation_passed=True,
        llm_latency_ms=30,
    )
    await dl.log_decision(r4)

    return dl


# ============================================================
# TestLogDecision
# ============================================================

class TestLogDecision:
    """Tests for DecisionLogger.log_decision."""

    @pytest.mark.asyncio
    async def test_log_decision_normal(self, logger_instance):
        """Logging a record with an explicit ID stores it successfully."""
        rec = _make_record(record_id="test-1")
        rid = await logger_instance.log_decision(rec)
        assert rid == "test-1"
        assert logger_instance.record_count == 1

    @pytest.mark.asyncio
    async def test_log_decision_auto_generate_id(self, logger_instance):
        """An empty record_id is replaced with an auto-generated one."""
        rec = _make_record(record_id="")
        rid = await logger_instance.log_decision(rec)
        assert rid != ""
        assert rid.startswith("dr-")
        assert len(rid) == 15  # "dr-" + 12 hex chars
        assert rec.record_id == rid

    @pytest.mark.asyncio
    async def test_log_decision_auto_set_timestamp(self, logger_instance):
        """When timestamp is falsy it gets set to now(UTC)."""
        rec = _make_record()
        # Force a falsy timestamp (None would violate type hint but 0 equivalent)
        rec.timestamp = None  # type: ignore[assignment]
        before = datetime.now(timezone.utc)
        await logger_instance.log_decision(rec)
        after = datetime.now(timezone.utc)
        assert rec.timestamp is not None
        assert before <= rec.timestamp <= after

    @pytest.mark.asyncio
    async def test_record_count_increments(self, logger_instance):
        """record_count tracks the number of stored records."""
        assert logger_instance.record_count == 0
        await logger_instance.log_decision(_make_record(record_id="a"))
        assert logger_instance.record_count == 1
        await logger_instance.log_decision(_make_record(record_id="b"))
        assert logger_instance.record_count == 2

    @pytest.mark.asyncio
    async def test_log_decision_returns_record_id(self, logger_instance):
        """Return value matches the stored record_id."""
        rec = _make_record(record_id="explicit-id")
        result = await logger_instance.log_decision(rec)
        assert result == "explicit-id"

    @pytest.mark.asyncio
    async def test_log_decision_overwrites_same_id(self, logger_instance):
        """Logging with a duplicate record_id overwrites the previous entry."""
        rec1 = _make_record(record_id="dup", decision={"v": 1})
        rec2 = _make_record(record_id="dup", decision={"v": 2})
        await logger_instance.log_decision(rec1)
        await logger_instance.log_decision(rec2)
        assert logger_instance.record_count == 1
        results = await logger_instance.query_decisions()
        assert results[0].decision == {"v": 2}


# ============================================================
# TestUpdateOutcome
# ============================================================

class TestUpdateOutcome:
    """Tests for DecisionLogger.update_outcome."""

    @pytest.mark.asyncio
    async def test_update_outcome_normal(self, logger_instance):
        """Updating an existing record attaches the outcome."""
        rec = _make_record(record_id="upd-1")
        await logger_instance.log_decision(rec)
        outcome = DecisionOutcome(
            task_completion_status="completed",
            quality_score=0.85,
            human_override=False,
        )
        result = await logger_instance.update_outcome("upd-1", outcome)
        assert result is True
        records = await logger_instance.query_decisions()
        assert records[0].outcome is not None
        assert records[0].outcome.quality_score == 0.85

    @pytest.mark.asyncio
    async def test_update_outcome_not_found(self, logger_instance):
        """Updating a non-existent record returns False."""
        outcome = DecisionOutcome(task_completion_status="completed")
        result = await logger_instance.update_outcome("no-such-id", outcome)
        assert result is False

    @pytest.mark.asyncio
    async def test_update_outcome_replaces_previous(self, logger_instance):
        """A second update_outcome call overwrites the first outcome."""
        rec = _make_record(record_id="ov-1")
        await logger_instance.log_decision(rec)
        await logger_instance.update_outcome(
            "ov-1", DecisionOutcome(quality_score=0.5)
        )
        await logger_instance.update_outcome(
            "ov-1", DecisionOutcome(quality_score=0.95)
        )
        records = await logger_instance.query_decisions()
        assert records[0].outcome.quality_score == 0.95


# ============================================================
# TestQueryDecisions
# ============================================================

class TestQueryDecisions:
    """Tests for DecisionLogger.query_decisions."""

    @pytest.mark.asyncio
    async def test_query_all(self, populated_logger):
        """Without filters, all records are returned."""
        results = await populated_logger.query_decisions()
        assert len(results) == 4

    @pytest.mark.asyncio
    async def test_query_by_agent_type(self, populated_logger):
        """Filtering by agent_type returns only matching records."""
        results = await populated_logger.query_decisions(agent_type="hvac")
        assert len(results) == 1
        assert results[0].record_id == "r-003"

    @pytest.mark.asyncio
    async def test_query_by_decision_type(self, populated_logger):
        """Filtering by decision_type returns only matching records."""
        results = await populated_logger.query_decisions(decision_type="inspection")
        assert len(results) == 1
        assert results[0].record_id == "r-004"

    @pytest.mark.asyncio
    async def test_query_by_start_time(self, populated_logger):
        """start_time excludes older records."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=90)
        results = await populated_logger.query_decisions(start_time=cutoff)
        # Only r-003 (1h ago) and r-004 (now) should remain
        assert len(results) == 2
        ids = {r.record_id for r in results}
        assert ids == {"r-003", "r-004"}

    @pytest.mark.asyncio
    async def test_query_by_end_time(self, populated_logger):
        """end_time excludes newer records."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=90)
        results = await populated_logger.query_decisions(end_time=cutoff)
        # Only r-001 (3h ago) and r-002 (2h ago) should remain
        assert len(results) == 2
        ids = {r.record_id for r in results}
        assert ids == {"r-001", "r-002"}

    @pytest.mark.asyncio
    async def test_query_has_human_override_true(self, populated_logger):
        """has_human_override=True returns only overridden records."""
        results = await populated_logger.query_decisions(has_human_override=True)
        assert len(results) == 1
        assert results[0].record_id == "r-002"

    @pytest.mark.asyncio
    async def test_query_has_human_override_false(self, populated_logger):
        """has_human_override=False includes records with outcome.human_override=False
        and records without an outcome."""
        results = await populated_logger.query_decisions(has_human_override=False)
        ids = {r.record_id for r in results}
        # r-001 (no override), r-003 (no override), r-004 (no outcome -> not override)
        assert ids == {"r-001", "r-003", "r-004"}

    @pytest.mark.asyncio
    async def test_query_min_quality_score(self, populated_logger):
        """min_quality_score filters out records below the threshold."""
        results = await populated_logger.query_decisions(min_quality_score=0.7)
        assert len(results) == 2
        ids = {r.record_id for r in results}
        assert ids == {"r-001", "r-003"}

    @pytest.mark.asyncio
    async def test_query_pagination_limit(self, populated_logger):
        """limit restricts the number of returned results."""
        results = await populated_logger.query_decisions(limit=2)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_query_pagination_offset(self, populated_logger):
        """offset skips the first N results (sorted desc by timestamp)."""
        all_results = await populated_logger.query_decisions()
        offset_results = await populated_logger.query_decisions(offset=2)
        assert len(offset_results) == 2
        # offset=2 should give the 3rd and 4th items of the desc-sorted list
        assert offset_results[0].record_id == all_results[2].record_id
        assert offset_results[1].record_id == all_results[3].record_id

    @pytest.mark.asyncio
    async def test_query_sorted_descending(self, populated_logger):
        """Results are sorted by timestamp descending (most recent first)."""
        results = await populated_logger.query_decisions()
        timestamps = [r.timestamp for r in results]
        assert timestamps == sorted(timestamps, reverse=True)

    @pytest.mark.asyncio
    async def test_query_combined_filters(self, populated_logger):
        """Multiple filters are combined with AND logic."""
        results = await populated_logger.query_decisions(
            agent_type="cleaning",
            decision_type="schedule",
            has_human_override=False,
        )
        assert len(results) == 1
        assert results[0].record_id == "r-001"


# ============================================================
# TestGetDecisionStats
# ============================================================

class TestGetDecisionStats:
    """Tests for DecisionLogger.get_decision_stats."""

    @pytest.mark.asyncio
    async def test_stats_empty(self, logger_instance):
        """Stats for an agent with no data return zero values."""
        stats = await logger_instance.get_decision_stats("cleaning")
        assert stats["total_decisions"] == 0
        assert stats["validation_pass_rate"] == 0.0
        assert stats["human_override_rate"] == 0.0
        assert stats["avg_quality_score"] == 0.0
        assert stats["avg_llm_latency_ms"] == 0.0
        assert stats["decisions_by_day"] == {}

    @pytest.mark.asyncio
    async def test_stats_with_data(self, populated_logger):
        """Stats for 'cleaning' aggregate correctly across matching records."""
        stats = await populated_logger.get_decision_stats("cleaning")

        # 3 cleaning records: r-001, r-002, r-004
        assert stats["total_decisions"] == 3

        # validation_passed: r-001 True, r-002 False, r-004 True => 2/3
        assert stats["validation_pass_rate"] == pytest.approx(2 / 3)

        # human_override: only r-002 has outcome with override => 1/3
        assert stats["human_override_rate"] == pytest.approx(1 / 3)

        # quality_scores: r-001=0.9, r-002=0.3 (r-004 has no outcome) => avg 0.6
        assert stats["avg_quality_score"] == pytest.approx(0.6)

        # llm_latency_ms: r-001=40, r-002=80, r-004=30 => avg 50
        assert stats["avg_llm_latency_ms"] == pytest.approx(50.0)

    @pytest.mark.asyncio
    async def test_stats_decisions_by_day(self, populated_logger):
        """decisions_by_day groups counts by ISO date string."""
        stats = await populated_logger.get_decision_stats("cleaning")
        by_day = stats["decisions_by_day"]
        total_in_days = sum(by_day.values())
        assert total_in_days == 3

    @pytest.mark.asyncio
    async def test_stats_respects_time_range(self, logger_instance):
        """Records older than time_range_days are excluded from stats."""
        old_ts = datetime.now(timezone.utc) - timedelta(days=10)
        new_ts = datetime.now(timezone.utc) - timedelta(hours=1)

        r_old = _make_record(record_id="old", agent_type="cleaning", timestamp=old_ts)
        r_new = _make_record(record_id="new", agent_type="cleaning", timestamp=new_ts)
        await logger_instance.log_decision(r_old)
        await logger_instance.log_decision(r_new)

        stats_7 = await logger_instance.get_decision_stats("cleaning", time_range_days=7)
        assert stats_7["total_decisions"] == 1

        stats_30 = await logger_instance.get_decision_stats("cleaning", time_range_days=30)
        assert stats_30["total_decisions"] == 2

    @pytest.mark.asyncio
    async def test_stats_zero_latency_excluded(self, logger_instance):
        """Records with llm_latency_ms == 0 are excluded from avg_llm_latency_ms."""
        rec = _make_record(record_id="zero-lat", llm_latency_ms=0)
        await logger_instance.log_decision(rec)
        stats = await logger_instance.get_decision_stats("cleaning")
        assert stats["avg_llm_latency_ms"] == 0.0


# ============================================================
# TestMarkTrainingCandidates
# ============================================================

class TestMarkTrainingCandidates:
    """Tests for DecisionLogger.mark_training_candidates."""

    @pytest.mark.asyncio
    async def test_mark_by_min_quality_score(self, populated_logger):
        """Marks records whose quality_score >= min_quality_score."""
        count = await populated_logger.mark_training_candidates(
            {"min_quality_score": 0.8}
        )
        assert count == 1  # only r-001 (0.9)

    @pytest.mark.asyncio
    async def test_mark_by_max_quality_score(self, populated_logger):
        """Marks records whose quality_score <= max_quality_score."""
        count = await populated_logger.mark_training_candidates(
            {"max_quality_score": 0.5}
        )
        assert count == 1  # only r-002 (0.3)

    @pytest.mark.asyncio
    async def test_mark_by_human_override(self, populated_logger):
        """Marks records whose outcome.human_override matches the flag."""
        count = await populated_logger.mark_training_candidates(
            {"human_override": True}
        )
        assert count == 1  # only r-002

    @pytest.mark.asyncio
    async def test_mark_by_agent_type(self, populated_logger):
        """Marks records filtered by agent_type."""
        count = await populated_logger.mark_training_candidates(
            {"agent_type": "hvac"}
        )
        assert count == 1  # only r-003

    @pytest.mark.asyncio
    async def test_mark_by_decision_type(self, populated_logger):
        """Marks records filtered by decision_type."""
        count = await populated_logger.mark_training_candidates(
            {"decision_type": "control"}
        )
        assert count == 1  # only r-003

    @pytest.mark.asyncio
    async def test_mark_no_outcome_skipped(self, populated_logger):
        """Records without an outcome are never marked."""
        count = await populated_logger.mark_training_candidates(
            {"agent_type": "cleaning", "decision_type": "inspection"}
        )
        # r-004 matches agent_type+decision_type but has no outcome
        assert count == 0

    @pytest.mark.asyncio
    async def test_mark_already_marked_not_recounted(self, populated_logger):
        """Already-marked records are not included in the returned count."""
        first = await populated_logger.mark_training_candidates(
            {"min_quality_score": 0.7}
        )
        assert first == 2  # r-001 (0.9) and r-003 (0.7)
        second = await populated_logger.mark_training_candidates(
            {"min_quality_score": 0.7}
        )
        assert second == 0

    @pytest.mark.asyncio
    async def test_mark_idempotent(self, populated_logger):
        """Calling mark twice with same criteria keeps is_training_candidate True."""
        await populated_logger.mark_training_candidates({"min_quality_score": 0.8})
        await populated_logger.mark_training_candidates({"min_quality_score": 0.8})
        records = await populated_logger.query_decisions()
        r001 = [r for r in records if r.record_id == "r-001"][0]
        assert r001.is_training_candidate is True
