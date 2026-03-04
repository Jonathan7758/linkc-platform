"""
Unit tests for P1 OfflineQueueManager and CacheManager.

Covers queue lifecycle (enqueue, sync, conflict resolution, batch sync,
status reporting) and cache lifecycle (store/retrieve, TTL expiry,
invalidation, convenience helpers).

Run with:
    pytest test_offline_queue.py -v
"""

import os
import sys
import time
from dataclasses import fields as dc_fields
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Path setup so the offline package is importable from the repo root.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from offline.offline_queue import (
    CacheManager,
    ConflictError,
    OfflineOperation,
    OfflineQueueManager,
    SyncBatchResult,
    SyncResult,
)

# ---------------------------------------------------------------------------
# Verify that the data models are plain dataclasses, NOT Pydantic.
# ---------------------------------------------------------------------------


def test_models_are_dataclasses():
    """OfflineOperation, SyncResult, SyncBatchResult must be dataclasses."""
    for cls in (OfflineOperation, SyncResult, SyncBatchResult):
        assert hasattr(cls, "__dataclass_fields__"), f"{cls.__name__} is not a dataclass"


# ---------------------------------------------------------------------------
# Mock server handlers
# ---------------------------------------------------------------------------


async def success_handler(payload):
    return {"status": 200, "result": "ok"}


async def conflict_handler(payload):
    from offline.offline_queue import ConflictError

    raise ConflictError(server_state={"version": 2})


async def failure_handler(payload):
    raise ConnectionError("Network error")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def queue():
    return OfflineQueueManager()


@pytest_asyncio.fixture
async def cache():
    return CacheManager()


# ===================================================================
# TestOfflineQueueManager
# ===================================================================


class TestOfflineQueueManager:
    """Tests for OfflineQueueManager covering enqueue, sync, conflict
    resolution, batch sync and status reporting."""

    # 1. enqueue creates operation with pending status
    @pytest.mark.asyncio
    async def test_enqueue_creates_pending_operation(self, queue):
        op_id = await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})
        ops = await queue.get_pending_ops("user-1")
        assert len(ops) == 1
        assert ops[0].operation_id == op_id
        assert ops[0].sync_status == "pending"

    # 2. enqueue returns unique operation_id
    @pytest.mark.asyncio
    async def test_enqueue_returns_unique_ids(self, queue):
        id1 = await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})
        id2 = await queue.enqueue("user-1", "task_confirm", {"task_id": "t-2"})
        id3 = await queue.enqueue("user-1", "task_complete", {"task_id": "t-3"})
        assert len({id1, id2, id3}) == 3, "operation IDs must be unique"

    # 3. get_pending_ops returns only the specified user's pending ops
    @pytest.mark.asyncio
    async def test_get_pending_ops_filters_by_user(self, queue):
        await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})
        await queue.enqueue("user-2", "task_confirm", {"task_id": "t-2"})
        await queue.enqueue("user-1", "task_complete", {"task_id": "t-3"})

        ops_u1 = await queue.get_pending_ops("user-1")
        ops_u2 = await queue.get_pending_ops("user-2")

        assert len(ops_u1) == 2
        assert all(op.user_id == "user-1" for op in ops_u1)
        assert len(ops_u2) == 1
        assert ops_u2[0].user_id == "user-2"

    # 4. get_pending_ops excludes synced operations
    @pytest.mark.asyncio
    async def test_get_pending_ops_excludes_synced(self, queue):
        op_id = await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})
        await queue.enqueue("user-1", "task_complete", {"task_id": "t-2"})

        # Sync one operation so its status becomes "synced"
        await queue.sync_operation(op_id, success_handler)

        ops = await queue.get_pending_ops("user-1")
        assert len(ops) == 1
        assert ops[0].sync_status == "pending"

    # 5. sync_operation success marks synced
    @pytest.mark.asyncio
    async def test_sync_operation_success(self, queue):
        op_id = await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})
        result = await queue.sync_operation(op_id, success_handler)

        assert result.success is True
        assert result.conflict is False
        assert result.server_state == {"status": 200, "result": "ok"}

        # Verify the operation is marked synced internally
        status = await queue.get_status("user-1")
        assert status["synced"] == 1
        assert status["pending"] == 0

    # 6. sync_operation conflict marks conflict status
    @pytest.mark.asyncio
    async def test_sync_operation_conflict(self, queue):
        op_id = await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})
        result = await queue.sync_operation(op_id, conflict_handler)

        assert result.success is False
        assert result.conflict is True
        assert result.server_state == {"version": 2}

        status = await queue.get_status("user-1")
        assert status["conflicts"] == 1

    # 7. sync_operation failure increments retry_count
    @pytest.mark.asyncio
    async def test_sync_operation_failure_increments_retry(self, queue):
        op_id = await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})
        result = await queue.sync_operation(op_id, failure_handler)

        assert result.success is False
        assert result.conflict is False
        assert "Network error" in result.error

        # Operation should return to pending (eligible for retry)
        ops = await queue.get_pending_ops("user-1")
        assert len(ops) == 1
        assert ops[0].retry_count == 1

    # 8. sync_operation max retries marks failed
    @pytest.mark.asyncio
    async def test_sync_operation_max_retries_marks_failed(self, queue):
        op_id = await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})

        # The default max_retries is 5; exhaust them all.
        for i in range(5):
            result = await queue.sync_operation(op_id, failure_handler)
            assert result.success is False

        # After max_retries the status should be "failed"
        status = await queue.get_status("user-1")
        assert status["failed"] == 1
        assert status["pending"] == 0

    # 9. sync_all syncs multiple operations
    @pytest.mark.asyncio
    async def test_sync_all_multiple_operations(self, queue):
        await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})
        await queue.enqueue("user-1", "task_complete", {"task_id": "t-2"})
        await queue.enqueue("user-1", "anomaly_report", {"task_id": "t-3"})

        batch = await queue.sync_all("user-1", success_handler)

        assert batch.synced == 3
        assert batch.failed == 0
        assert len(batch.conflicts) == 0

    # 10. sync_all handles mixed success/failure
    @pytest.mark.asyncio
    async def test_sync_all_mixed_success_failure(self, queue):
        await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})
        await queue.enqueue("user-1", "task_complete", {"task_id": "t-2"})
        await queue.enqueue("user-1", "anomaly_report", {"task_id": "t-3"})

        call_count = 0

        async def mixed_handler(payload):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"status": 200, "result": "ok"}
            elif call_count == 2:
                raise ConflictError(server_state={"version": 5})
            else:
                raise ConnectionError("Network error")

        batch = await queue.sync_all("user-1", mixed_handler)

        assert batch.synced == 1
        assert len(batch.conflicts) == 1
        assert batch.failed == 1

    # 11. get_status returns correct counts
    @pytest.mark.asyncio
    async def test_get_status_correct_counts(self, queue):
        # Create three operations with different outcomes
        id1 = await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})
        id2 = await queue.enqueue("user-1", "task_complete", {"task_id": "t-2"})
        await queue.enqueue("user-1", "anomaly_report", {"task_id": "t-3"})

        await queue.sync_operation(id1, success_handler)
        await queue.sync_operation(id2, conflict_handler)

        status = await queue.get_status("user-1")
        assert status["synced"] == 1
        assert status["conflicts"] == 1
        assert status["pending"] == 1
        assert status["failed"] == 0
        assert status["last_sync_at"] is not None

    # 12. resolve_conflict accept_server marks synced
    @pytest.mark.asyncio
    async def test_resolve_conflict_accept_server(self, queue):
        op_id = await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})
        await queue.sync_operation(op_id, conflict_handler)

        resolved = await queue.resolve_conflict(op_id, "accept_server")
        assert resolved is True

        status = await queue.get_status("user-1")
        assert status["synced"] == 1
        assert status["conflicts"] == 0

    # 13. resolve_conflict force_client resets to pending
    @pytest.mark.asyncio
    async def test_resolve_conflict_force_client(self, queue):
        op_id = await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})
        await queue.sync_operation(op_id, conflict_handler)

        resolved = await queue.resolve_conflict(op_id, "force_client")
        assert resolved is True

        ops = await queue.get_pending_ops("user-1")
        assert len(ops) == 1
        assert ops[0].retry_count == 0

    # 14. resolve_conflict discard removes operation
    @pytest.mark.asyncio
    async def test_resolve_conflict_discard(self, queue):
        op_id = await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})
        await queue.sync_operation(op_id, conflict_handler)

        resolved = await queue.resolve_conflict(op_id, "discard")
        assert resolved is True

        # The operation should no longer exist in any status
        status = await queue.get_status("user-1")
        assert status["synced"] == 0
        assert status["pending"] == 0
        assert status["conflicts"] == 0

    # 15. resolve_conflict returns False for non-conflict operation
    @pytest.mark.asyncio
    async def test_resolve_conflict_returns_false_for_non_conflict(self, queue):
        op_id = await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})
        # Operation is still in "pending" status, not "conflict"
        resolved = await queue.resolve_conflict(op_id, "accept_server")
        assert resolved is False

    # 16. mark_synced updates status and response
    @pytest.mark.asyncio
    async def test_mark_synced_updates_status_and_response(self, queue):
        op_id = await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})
        server_resp = {"status": 200, "data": "external sync"}

        result = await queue.mark_synced(op_id, server_resp)
        assert result is True

        status = await queue.get_status("user-1")
        assert status["synced"] == 1
        assert status["pending"] == 0

    # -- bonus tests -------------------------------------------------------

    @pytest.mark.asyncio
    async def test_sync_operation_not_found(self, queue):
        """Syncing a non-existent operation returns a failure result."""
        result = await queue.sync_operation("nonexistent-id", success_handler)
        assert result.success is False
        assert result.error == "operation_not_found"

    @pytest.mark.asyncio
    async def test_mark_synced_nonexistent_returns_false(self, queue):
        """mark_synced on a missing operation returns False."""
        result = await queue.mark_synced("no-such-id", {"status": 200})
        assert result is False

    @pytest.mark.asyncio
    async def test_resolve_conflict_invalid_resolution_raises(self, queue):
        """An invalid resolution string raises ValueError."""
        op_id = await queue.enqueue("user-1", "task_confirm", {"task_id": "t-1"})
        with pytest.raises(ValueError, match="Invalid resolution"):
            await queue.resolve_conflict(op_id, "invalid_strategy")


# ===================================================================
# TestCacheManager
# ===================================================================


class TestCacheManager:
    """Tests for CacheManager covering store/retrieve, TTL expiry,
    invalidation, and convenience helpers."""

    # 1. cache_data and get_cached round-trip
    @pytest.mark.asyncio
    async def test_cache_data_and_get_cached_roundtrip(self, cache):
        await cache.cache_data("key-1", {"foo": "bar"})
        result = await cache.get_cached("key-1")
        assert result == {"foo": "bar"}

    # 2. get_cached returns None for missing key
    @pytest.mark.asyncio
    async def test_get_cached_returns_none_for_missing_key(self, cache):
        result = await cache.get_cached("nonexistent")
        assert result is None

    # 3. get_cached returns None for expired entry
    @pytest.mark.asyncio
    async def test_get_cached_returns_none_for_expired_entry(self, cache):
        await cache.cache_data("expire-me", "value", max_age_seconds=0.01)
        # Wait just beyond the TTL
        await _async_sleep(0.05)
        result = await cache.get_cached("expire-me")
        assert result is None

    # 4. invalidate removes entry
    @pytest.mark.asyncio
    async def test_invalidate_removes_entry(self, cache):
        await cache.cache_data("key-1", "val")
        removed = await cache.invalidate("key-1")
        assert removed is True
        assert await cache.get_cached("key-1") is None

    # 5. invalidate_all clears everything
    @pytest.mark.asyncio
    async def test_invalidate_all_clears_everything(self, cache):
        await cache.cache_data("a", 1)
        await cache.cache_data("b", 2)
        await cache.cache_data("c", 3)
        count = await cache.invalidate_all()
        assert count == 3
        assert await cache.get_cached("a") is None
        assert await cache.get_cached("b") is None
        assert await cache.get_cached("c") is None

    # 6. get_cache_age returns -1 for missing key
    @pytest.mark.asyncio
    async def test_get_cache_age_missing_key(self, cache):
        age = cache.get_cache_age("does-not-exist")
        assert age == -1.0

    # 7. get_cache_age returns positive for cached entry
    @pytest.mark.asyncio
    async def test_get_cache_age_positive_for_cached(self, cache):
        await cache.cache_data("recent", "data")
        age = cache.get_cache_age("recent")
        assert age >= 0.0

    # 8. cache_task_list / get_cached_task_list round-trip
    @pytest.mark.asyncio
    async def test_cache_task_list_roundtrip(self, cache):
        tasks = [{"id": "t-1", "title": "Pick widget"}, {"id": "t-2", "title": "Deliver"}]
        await cache.cache_task_list("user-1", tasks)
        result = await cache.get_cached_task_list("user-1")
        assert result == tasks

    # 9. cache_robot_states / get_cached_robot_states round-trip
    @pytest.mark.asyncio
    async def test_cache_robot_states_roundtrip(self, cache):
        states = [{"robot_id": "r-1", "battery": 85}, {"robot_id": "r-2", "battery": 42}]
        await cache.cache_robot_states("building-A", states)
        result = await cache.get_cached_robot_states("building-A")
        assert result == states

    # 10. cache with custom max_age_seconds keeps data alive
    @pytest.mark.asyncio
    async def test_cache_custom_max_age(self, cache):
        await cache.cache_data("short-lived", "gone-soon", max_age_seconds=0.01)
        await cache.cache_data("long-lived", "still-here", max_age_seconds=60)

        await _async_sleep(0.05)

        assert await cache.get_cached("short-lived") is None
        assert await cache.get_cached("long-lived") == "still-here"

    # -- bonus tests -------------------------------------------------------

    @pytest.mark.asyncio
    async def test_invalidate_nonexistent_returns_false(self, cache):
        """Invalidating a key that was never cached returns False."""
        removed = await cache.invalidate("ghost-key")
        assert removed is False

    @pytest.mark.asyncio
    async def test_cache_task_list_different_users_isolated(self, cache):
        """Task lists for different users are stored independently."""
        await cache.cache_task_list("user-1", [{"id": "t-1"}])
        await cache.cache_task_list("user-2", [{"id": "t-99"}])

        assert await cache.get_cached_task_list("user-1") == [{"id": "t-1"}]
        assert await cache.get_cached_task_list("user-2") == [{"id": "t-99"}]

    @pytest.mark.asyncio
    async def test_get_cached_robot_states_missing(self, cache):
        """Requesting robot states for an un-cached building returns None."""
        result = await cache.get_cached_robot_states("no-building")
        assert result is None


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

import asyncio


async def _async_sleep(seconds: float) -> None:
    """Thin wrapper so sleep calls are explicit."""
    await asyncio.sleep(seconds)
