"""
Tests for K1 ScenarioKnowledgeBase -- scenario knowledge CRUD, query, prompt
assembly, and usage tracking.
"""
import pytest
import sys
import os
from copy import deepcopy
from datetime import datetime, timedelta

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from knowledge.scenario_kb import (
    ScenarioKnowledge,
    ScenarioKnowledgeBase,
    PromptTemplate,
)


# ============================================================
# Fixtures
# ============================================================

def _make_knowledge(**overrides) -> ScenarioKnowledge:
    """Helper to build a ScenarioKnowledge with sensible defaults."""
    defaults = dict(
        knowledge_id="sk-test-001",
        knowledge_type="domain_fact",
        scenario_category="cleaning",
        name="Lobby Cleaning Fact",
        description="Lobby needs daily cleaning.",
        tags=["lobby", "daily"],
        applicable_building_types=["office"],
        applicable_zones=["zone-lobby"],
        applicable_time_ranges=[],
        applicable_conditions={},
        content={"fact": "The lobby floor is marble and requires gentle detergent."},
        priority=80,
        enabled=True,
    )
    defaults.update(overrides)
    return ScenarioKnowledge(**defaults)


def _make_template(**overrides) -> PromptTemplate:
    """Helper to build a PromptTemplate with sensible defaults."""
    defaults = dict(
        template_id="pt-test-001",
        agent_type="cleaning_agent",
        name="Cleaning System Prompt",
        system_prompt="You are a cleaning agent for {{building_name}}.\n\n{{knowledge}}",
        variables=["building_name"],
        knowledge_slots=[
            {
                "slot_name": "knowledge",
                "category": "cleaning",
                "max_items": 5,
            }
        ],
        base_tokens_estimate=200,
        max_knowledge_tokens=2000,
        max_total_tokens=4000,
    )
    defaults.update(overrides)
    return PromptTemplate(**defaults)


@pytest.fixture
def kb() -> ScenarioKnowledgeBase:
    """Return a fresh, empty ScenarioKnowledgeBase."""
    return ScenarioKnowledgeBase()


# ============================================================
# Class: TestCreateKnowledge
# ============================================================

class TestCreateKnowledge:
    """Tests for ScenarioKnowledgeBase.create_knowledge."""

    @pytest.mark.asyncio
    async def test_create_normal(self, kb):
        """Creating knowledge with an explicit ID stores it and returns the ID."""
        sk = _make_knowledge()
        result_id = await kb.create_knowledge(sk)
        assert result_id == "sk-test-001"
        stored = await kb.get_knowledge("sk-test-001")
        assert stored is not None
        assert stored.name == "Lobby Cleaning Fact"

    @pytest.mark.asyncio
    async def test_create_duplicate_id_raises(self, kb):
        """Creating two entries with the same knowledge_id raises ValueError."""
        sk1 = _make_knowledge()
        await kb.create_knowledge(sk1)
        sk2 = _make_knowledge(name="Duplicate")
        with pytest.raises(ValueError, match="already exists"):
            await kb.create_knowledge(sk2)

    @pytest.mark.asyncio
    async def test_auto_generate_id(self, kb):
        """When knowledge_id is empty, an ID is auto-generated with 'sk-' prefix."""
        sk = _make_knowledge(knowledge_id="")
        result_id = await kb.create_knowledge(sk)
        assert result_id.startswith("sk-")
        assert len(result_id) > 3
        stored = await kb.get_knowledge(result_id)
        assert stored is not None

    @pytest.mark.asyncio
    async def test_auto_set_created_at(self, kb):
        """When created_at is None, it is set to a recent datetime automatically."""
        sk = _make_knowledge(created_at=None)
        before = datetime.utcnow()
        await kb.create_knowledge(sk)
        after = datetime.utcnow()
        stored = await kb.get_knowledge("sk-test-001")
        assert stored.created_at is not None
        assert before <= stored.created_at <= after

    @pytest.mark.asyncio
    async def test_explicit_created_at_preserved(self, kb):
        """When created_at is explicitly provided, it is preserved as-is."""
        fixed_dt = datetime(2024, 1, 15, 10, 0, 0)
        sk = _make_knowledge(created_at=fixed_dt)
        await kb.create_knowledge(sk)
        stored = await kb.get_knowledge("sk-test-001")
        assert stored.created_at == fixed_dt


# ============================================================
# Class: TestGetKnowledge
# ============================================================

class TestGetKnowledge:
    """Tests for ScenarioKnowledgeBase.get_knowledge."""

    @pytest.mark.asyncio
    async def test_get_existing(self, kb):
        """Retrieving an existing entry returns a ScenarioKnowledge object."""
        await kb.create_knowledge(_make_knowledge())
        result = await kb.get_knowledge("sk-test-001")
        assert result is not None
        assert result.knowledge_id == "sk-test-001"

    @pytest.mark.asyncio
    async def test_get_not_found(self, kb):
        """Retrieving a non-existent ID returns None."""
        result = await kb.get_knowledge("sk-does-not-exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_deepcopy(self, kb):
        """Returned objects are deep copies; mutating them does not affect storage."""
        await kb.create_knowledge(_make_knowledge())
        copy1 = await kb.get_knowledge("sk-test-001")
        copy1.name = "MUTATED"
        copy2 = await kb.get_knowledge("sk-test-001")
        assert copy2.name == "Lobby Cleaning Fact"


# ============================================================
# Class: TestUpdateKnowledge
# ============================================================

class TestUpdateKnowledge:
    """Tests for ScenarioKnowledgeBase.update_knowledge."""

    @pytest.mark.asyncio
    async def test_update_normal(self, kb):
        """Updating valid fields modifies the stored entry and returns True."""
        await kb.create_knowledge(_make_knowledge())
        ok = await kb.update_knowledge("sk-test-001", {"name": "Updated Name", "priority": 99})
        assert ok is True
        stored = await kb.get_knowledge("sk-test-001")
        assert stored.name == "Updated Name"
        assert stored.priority == 99

    @pytest.mark.asyncio
    async def test_update_immutable_fields_skipped(self, kb):
        """Immutable fields (knowledge_id, created_at, created_by) are silently skipped."""
        fixed_dt = datetime(2024, 1, 1)
        await kb.create_knowledge(_make_knowledge(created_at=fixed_dt, created_by="admin"))
        ok = await kb.update_knowledge(
            "sk-test-001",
            {"knowledge_id": "sk-hacked", "created_at": datetime(2099, 1, 1), "created_by": "hacker"},
        )
        assert ok is True
        stored = await kb.get_knowledge("sk-test-001")
        # Immutable fields must not change
        assert stored.knowledge_id == "sk-test-001"
        assert stored.created_at == fixed_dt
        assert stored.created_by == "admin"

    @pytest.mark.asyncio
    async def test_update_unknown_field(self, kb):
        """Unknown fields are silently skipped (logged as warning), update still returns True."""
        await kb.create_knowledge(_make_knowledge())
        ok = await kb.update_knowledge("sk-test-001", {"nonexistent_field": "value"})
        assert ok is True

    @pytest.mark.asyncio
    async def test_update_not_found(self, kb):
        """Updating a non-existent knowledge returns False."""
        ok = await kb.update_knowledge("sk-ghost", {"name": "Nope"})
        assert ok is False


# ============================================================
# Class: TestDeleteKnowledge
# ============================================================

class TestDeleteKnowledge:
    """Tests for ScenarioKnowledgeBase.delete_knowledge (soft delete)."""

    @pytest.mark.asyncio
    async def test_soft_delete_sets_enabled_false(self, kb):
        """Soft-deleting an entry sets enabled=False but the entry remains retrievable."""
        await kb.create_knowledge(_make_knowledge())
        ok = await kb.delete_knowledge("sk-test-001")
        assert ok is True
        stored = await kb.get_knowledge("sk-test-001")
        assert stored is not None
        assert stored.enabled is False

    @pytest.mark.asyncio
    async def test_delete_not_found(self, kb):
        """Deleting a non-existent knowledge returns False."""
        ok = await kb.delete_knowledge("sk-nonexistent")
        assert ok is False


# ============================================================
# Class: TestTemplates
# ============================================================

class TestTemplates:
    """Tests for create_template and get_prompt_template."""

    @pytest.mark.asyncio
    async def test_create_and_get_template(self, kb):
        """Creating a template stores it; get_prompt_template returns it."""
        tmpl = _make_template()
        tid = await kb.create_template(tmpl)
        assert tid == "pt-test-001"
        retrieved = await kb.get_prompt_template("pt-test-001")
        assert retrieved is not None
        assert retrieved.name == "Cleaning System Prompt"

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, kb):
        """get_prompt_template returns None for unknown template_id."""
        result = await kb.get_prompt_template("pt-unknown")
        assert result is None

    @pytest.mark.asyncio
    async def test_create_template_auto_id(self, kb):
        """When template_id is empty, an ID is auto-generated with 'pt-' prefix."""
        tmpl = _make_template(template_id="")
        tid = await kb.create_template(tmpl)
        assert tid.startswith("pt-")
        assert len(tid) > 3


# ============================================================
# Class: TestQueryApplicableKnowledge
# ============================================================

class TestQueryApplicableKnowledge:
    """Tests for ScenarioKnowledgeBase.query_applicable_knowledge."""

    @pytest.mark.asyncio
    async def test_filter_by_category(self, kb):
        """Only entries matching the queried scenario_category are returned."""
        await kb.create_knowledge(_make_knowledge(knowledge_id="sk-c1", scenario_category="cleaning"))
        await kb.create_knowledge(_make_knowledge(knowledge_id="sk-s1", scenario_category="security"))
        results = await kb.query_applicable_knowledge("cleaning", building_type="office", zone_id="zone-lobby")
        assert len(results) == 1
        assert results[0].knowledge_id == "sk-c1"

    @pytest.mark.asyncio
    async def test_filter_by_building_type(self, kb):
        """Entries are filtered by applicable_building_types match."""
        await kb.create_knowledge(
            _make_knowledge(knowledge_id="sk-off", applicable_building_types=["office"])
        )
        await kb.create_knowledge(
            _make_knowledge(knowledge_id="sk-mall", applicable_building_types=["mall"])
        )
        results = await kb.query_applicable_knowledge("cleaning", building_type="office", zone_id="zone-lobby")
        assert len(results) == 1
        assert results[0].knowledge_id == "sk-off"

    @pytest.mark.asyncio
    async def test_filter_by_building_type_all(self, kb):
        """Entries with applicable_building_types=['all'] match any building_type."""
        await kb.create_knowledge(
            _make_knowledge(knowledge_id="sk-all", applicable_building_types=["all"])
        )
        results = await kb.query_applicable_knowledge("cleaning", building_type="warehouse", zone_id="zone-lobby")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_filter_by_zone_id(self, kb):
        """Entries are filtered by applicable_zones match."""
        await kb.create_knowledge(
            _make_knowledge(knowledge_id="sk-lobby", applicable_zones=["zone-lobby"])
        )
        await kb.create_knowledge(
            _make_knowledge(knowledge_id="sk-restroom", applicable_zones=["zone-restroom"])
        )
        results = await kb.query_applicable_knowledge("cleaning", building_type="office", zone_id="zone-lobby")
        assert len(results) == 1
        assert results[0].knowledge_id == "sk-lobby"

    @pytest.mark.asyncio
    async def test_filter_by_time_range(self, kb):
        """Entries with applicable_time_ranges are filtered by current_time."""
        await kb.create_knowledge(
            _make_knowledge(
                knowledge_id="sk-morning",
                applicable_building_types=["all"],
                applicable_zones=["all"],
                applicable_time_ranges=[{"start": "06:00", "end": "09:00"}],
            )
        )
        results_in = await kb.query_applicable_knowledge(
            "cleaning", current_time="07:30"
        )
        assert len(results_in) == 1
        results_out = await kb.query_applicable_knowledge(
            "cleaning", current_time="12:00"
        )
        assert len(results_out) == 0

    @pytest.mark.asyncio
    async def test_filter_by_conditions(self, kb):
        """Entries with applicable_conditions must match the provided conditions."""
        await kb.create_knowledge(
            _make_knowledge(
                knowledge_id="sk-rainy",
                applicable_building_types=["all"],
                applicable_zones=["all"],
                applicable_conditions={"weather": "rainy"},
            )
        )
        results_match = await kb.query_applicable_knowledge(
            "cleaning", conditions={"weather": "rainy"}
        )
        assert len(results_match) == 1
        results_no_match = await kb.query_applicable_knowledge(
            "cleaning", conditions={"weather": "sunny"}
        )
        assert len(results_no_match) == 0

    @pytest.mark.asyncio
    async def test_knowledge_types_filter(self, kb):
        """The knowledge_types parameter restricts results by knowledge_type."""
        await kb.create_knowledge(
            _make_knowledge(
                knowledge_id="sk-fact",
                knowledge_type="domain_fact",
                applicable_building_types=["all"],
                applicable_zones=["all"],
            )
        )
        await kb.create_knowledge(
            _make_knowledge(
                knowledge_id="sk-rule",
                knowledge_type="scenario_rule",
                applicable_building_types=["all"],
                applicable_zones=["all"],
            )
        )
        results = await kb.query_applicable_knowledge(
            "cleaning", knowledge_types=["scenario_rule"]
        )
        assert len(results) == 1
        assert results[0].knowledge_id == "sk-rule"

    @pytest.mark.asyncio
    async def test_priority_ordering(self, kb):
        """Results are sorted by priority descending."""
        await kb.create_knowledge(
            _make_knowledge(knowledge_id="sk-low", priority=10, applicable_building_types=["all"], applicable_zones=["all"])
        )
        await kb.create_knowledge(
            _make_knowledge(knowledge_id="sk-high", priority=90, applicable_building_types=["all"], applicable_zones=["all"])
        )
        await kb.create_knowledge(
            _make_knowledge(knowledge_id="sk-mid", priority=50, applicable_building_types=["all"], applicable_zones=["all"])
        )
        results = await kb.query_applicable_knowledge("cleaning")
        assert [r.knowledge_id for r in results] == ["sk-high", "sk-mid", "sk-low"]

    @pytest.mark.asyncio
    async def test_max_items(self, kb):
        """Results are truncated to max_items."""
        for i in range(10):
            await kb.create_knowledge(
                _make_knowledge(
                    knowledge_id=f"sk-item-{i}",
                    applicable_building_types=["all"],
                    applicable_zones=["all"],
                )
            )
        results = await kb.query_applicable_knowledge("cleaning", max_items=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_disabled_excluded(self, kb):
        """Disabled entries (enabled=False) are never returned by query."""
        await kb.create_knowledge(
            _make_knowledge(
                knowledge_id="sk-disabled",
                enabled=False,
                applicable_building_types=["all"],
                applicable_zones=["all"],
            )
        )
        results = await kb.query_applicable_knowledge("cleaning")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_effective_period_filtering(self, kb):
        """Entries outside their effective_from / effective_until window are excluded."""
        future_from = datetime.utcnow() + timedelta(days=30)
        await kb.create_knowledge(
            _make_knowledge(
                knowledge_id="sk-future",
                effective_from=future_from,
                applicable_building_types=["all"],
                applicable_zones=["all"],
            )
        )
        past_until = datetime.utcnow() - timedelta(days=30)
        await kb.create_knowledge(
            _make_knowledge(
                knowledge_id="sk-expired",
                effective_until=past_until,
                applicable_building_types=["all"],
                applicable_zones=["all"],
            )
        )
        results = await kb.query_applicable_knowledge("cleaning")
        assert len(results) == 0


# ============================================================
# Class: TestAssemblePrompt
# ============================================================

class TestAssemblePrompt:
    """Tests for ScenarioKnowledgeBase.assemble_prompt."""

    @pytest.mark.asyncio
    async def test_variable_filling(self, kb):
        """Variables like {{building_name}} are replaced in the prompt."""
        await kb.create_template(_make_template(
            knowledge_slots=[],
            system_prompt="Hello {{building_name}}, welcome!",
        ))
        prompt = await kb.assemble_prompt(
            template_id="pt-test-001",
            variables={"building_name": "Tower-A"},
            scenario_category="cleaning",
            context={},
        )
        assert "Hello Tower-A, welcome!" in prompt
        assert "{{building_name}}" not in prompt

    @pytest.mark.asyncio
    async def test_knowledge_slot_injection(self, kb):
        """Knowledge entries matching the slot query are injected into the prompt."""
        await kb.create_knowledge(
            _make_knowledge(
                knowledge_id="sk-inject",
                applicable_building_types=["all"],
                applicable_zones=["all"],
                content={"fact": "Use gentle detergent on marble."},
                priority=80,
            )
        )
        await kb.create_template(_make_template())
        prompt = await kb.assemble_prompt(
            template_id="pt-test-001",
            variables={"building_name": "HQ"},
            scenario_category="cleaning",
            context={},
        )
        assert "gentle detergent" in prompt
        assert "Lobby Cleaning Fact" in prompt

    @pytest.mark.asyncio
    async def test_token_truncation(self, kb):
        """When the assembled prompt exceeds max_total_tokens, it is truncated."""
        # Create a template with a very small max_total_tokens
        long_content = "A" * 10000
        await kb.create_template(_make_template(
            system_prompt=long_content,
            knowledge_slots=[],
            max_total_tokens=100,
        ))
        prompt = await kb.assemble_prompt(
            template_id="pt-test-001",
            variables={},
            scenario_category="cleaning",
            context={},
        )
        # max_total_tokens=100 => max_chars = 100*4 = 400
        assert len(prompt) <= 400

    @pytest.mark.asyncio
    async def test_missing_template_error(self, kb):
        """Assembling with a non-existent template_id raises ValueError."""
        with pytest.raises(ValueError, match="Template not found"):
            await kb.assemble_prompt(
                template_id="pt-nonexistent",
                variables={},
                scenario_category="cleaning",
                context={},
            )

    @pytest.mark.asyncio
    async def test_slot_appended_when_no_placeholder(self, kb):
        """When the slot placeholder is absent from the prompt, knowledge is appended."""
        await kb.create_knowledge(
            _make_knowledge(
                knowledge_id="sk-append",
                applicable_building_types=["all"],
                applicable_zones=["all"],
                content={"fact": "Append this fact."},
            )
        )
        await kb.create_template(_make_template(
            system_prompt="No placeholder here.",
            knowledge_slots=[{"slot_name": "extra_slot", "category": "cleaning", "max_items": 5}],
        ))
        prompt = await kb.assemble_prompt(
            template_id="pt-test-001",
            variables={},
            scenario_category="cleaning",
            context={},
        )
        assert "### extra_slot" in prompt
        assert "Append this fact." in prompt


# ============================================================
# Class: TestRecordUsage
# ============================================================

class TestRecordUsage:
    """Tests for ScenarioKnowledgeBase.record_usage."""

    @pytest.mark.asyncio
    async def test_increment_count(self, kb):
        """Each call to record_usage increments usage_count by 1."""
        await kb.create_knowledge(_make_knowledge())
        await kb.record_usage("sk-test-001")
        await kb.record_usage("sk-test-001")
        stored = await kb.get_knowledge("sk-test-001")
        assert stored.usage_count == 2

    @pytest.mark.asyncio
    async def test_update_avg_outcome_score(self, kb):
        """Outcome scores update avg_outcome_score via incremental mean."""
        await kb.create_knowledge(_make_knowledge())

        # First score: avg becomes 0.8
        await kb.record_usage("sk-test-001", outcome_score=0.8)
        stored = await kb.get_knowledge("sk-test-001")
        assert stored.avg_outcome_score == pytest.approx(0.8)
        assert stored.usage_count == 1

        # Second score: incremental mean = 0.8 + (0.6 - 0.8) / 2 = 0.7
        await kb.record_usage("sk-test-001", outcome_score=0.6)
        stored = await kb.get_knowledge("sk-test-001")
        assert stored.avg_outcome_score == pytest.approx(0.7)
        assert stored.usage_count == 2

        # Third score without outcome: count increments, avg unchanged
        await kb.record_usage("sk-test-001")
        stored = await kb.get_knowledge("sk-test-001")
        assert stored.avg_outcome_score == pytest.approx(0.7)
        assert stored.usage_count == 3

    @pytest.mark.asyncio
    async def test_record_usage_not_found(self, kb):
        """Recording usage for a non-existent knowledge does not raise; it is a no-op."""
        # Should not raise
        await kb.record_usage("sk-nonexistent", outcome_score=0.5)


# ============================================================
# Class: TestInternalHelpers
# ============================================================

class TestInternalHelpers:
    """Tests for internal static helper methods."""

    # --- _matches_list ---

    def test_matches_list_value_in_list(self):
        """Returns True when value is in the applicable list."""
        assert ScenarioKnowledgeBase._matches_list(["office", "mall"], "office") is True

    def test_matches_list_value_not_in_list(self):
        """Returns False when value is not in the applicable list."""
        assert ScenarioKnowledgeBase._matches_list(["office", "mall"], "warehouse") is False

    def test_matches_list_all_in_applicable(self):
        """Returns True when applicable list contains 'all'."""
        assert ScenarioKnowledgeBase._matches_list(["all"], "anything") is True

    def test_matches_list_value_is_all(self):
        """Returns True when value is 'all' (caller does not restrict)."""
        assert ScenarioKnowledgeBase._matches_list(["office"], "all") is True

    # --- _time_in_ranges ---

    def test_time_in_normal_range(self):
        """Returns True when time falls within a normal (non-overnight) range."""
        ranges = [{"start": "08:00", "end": "17:00"}]
        assert ScenarioKnowledgeBase._time_in_ranges("12:00", ranges) is True

    def test_time_outside_normal_range(self):
        """Returns False when time is outside a normal range."""
        ranges = [{"start": "08:00", "end": "17:00"}]
        assert ScenarioKnowledgeBase._time_in_ranges("20:00", ranges) is False

    def test_time_in_overnight_range(self):
        """Returns True for times in an overnight range (e.g., 22:00-06:00)."""
        ranges = [{"start": "22:00", "end": "06:00"}]
        assert ScenarioKnowledgeBase._time_in_ranges("23:30", ranges) is True
        assert ScenarioKnowledgeBase._time_in_ranges("03:00", ranges) is True

    def test_time_outside_overnight_range(self):
        """Returns False for times outside an overnight range."""
        ranges = [{"start": "22:00", "end": "06:00"}]
        assert ScenarioKnowledgeBase._time_in_ranges("12:00", ranges) is False

    def test_time_invalid_format(self):
        """Returns False for an invalid time format without raising."""
        ranges = [{"start": "08:00", "end": "17:00"}]
        assert ScenarioKnowledgeBase._time_in_ranges("invalid", ranges) is False

    # --- _conditions_match ---

    def test_conditions_match_all_satisfied(self):
        """Returns True when all required conditions are met."""
        required = {"weather": "rainy", "occupancy": "high"}
        actual = {"weather": "rainy", "occupancy": "high", "extra": "ignored"}
        assert ScenarioKnowledgeBase._conditions_match(required, actual) is True

    def test_conditions_match_not_satisfied(self):
        """Returns False when a required condition value mismatches."""
        required = {"weather": "rainy"}
        actual = {"weather": "sunny"}
        assert ScenarioKnowledgeBase._conditions_match(required, actual) is False

    def test_conditions_match_missing_key(self):
        """Returns False when a required key is absent from actual conditions."""
        required = {"weather": "rainy"}
        actual = {}
        assert ScenarioKnowledgeBase._conditions_match(required, actual) is False

    # --- _fill_variables ---

    def test_fill_variables_replaces(self):
        """Known variables are replaced; unknown placeholders are preserved."""
        text = "Hello {{name}}, you work in {{department}}."
        result = ScenarioKnowledgeBase._fill_variables(
            text, {"name": "Alice"}
        )
        assert result == "Hello Alice, you work in {{department}}."

    def test_fill_variables_no_placeholders(self):
        """Text without placeholders is returned unchanged."""
        text = "No placeholders here."
        result = ScenarioKnowledgeBase._fill_variables(text, {"name": "Alice"})
        assert result == text
