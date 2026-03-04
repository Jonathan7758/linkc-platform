"""
Unit tests for P3 NotificationService.

Covers storage, delivery lifecycle, retry logic, expiry cleanup,
stats aggregation, and batch operations.
"""

import os
import sys
from datetime import datetime, timedelta

import pytest

# ---------------------------------------------------------------------------
# Path setup so the import resolves from the project root
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from notifications.notification_service import (
    Notification,
    NotificationService,
    NOTIFICATION_RETRY_CONFIG,
)

# ---------------------------------------------------------------------------
# Mock delivery handlers
# ---------------------------------------------------------------------------


async def success_delivery(notification):
    return True


async def failure_delivery(notification):
    return False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def service():
    """Return a fresh NotificationService for each test."""
    return NotificationService()


# ===========================================================================
# TestStoreNotification (5 tests)
# ===========================================================================


class TestStoreNotification:
    """Tests for store_notification."""

    @pytest.mark.asyncio
    async def test_store_returns_notification_id(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="New Task",
            message="You have a new task",
        )
        assert isinstance(nid, str)
        assert len(nid) > 0

    @pytest.mark.asyncio
    async def test_stored_notification_has_correct_fields(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="robot_error",
            title="Robot Down",
            message="Robot #7 offline",
            priority="high",
            payload={"robot_id": 7},
            channel="email",
        )
        n = await service.get_notification(nid)
        assert n is not None
        assert n.user_id == "user1"
        assert n.notification_type == "robot_error"
        assert n.title == "Robot Down"
        assert n.message == "Robot #7 offline"
        assert n.priority == "high"
        assert n.payload == {"robot_id": 7}
        assert n.channel == "email"
        assert n.delivery_status == "pending"

    @pytest.mark.asyncio
    async def test_auto_generates_created_at(self, service):
        before = datetime.utcnow()
        nid = await service.store_notification(
            user_id="user1",
            notification_type="system_alert",
            title="Alert",
            message="System check",
        )
        after = datetime.utcnow()
        n = await service.get_notification(nid)
        assert n.created_at is not None
        assert before <= n.created_at <= after

    @pytest.mark.asyncio
    async def test_calculates_expires_at_from_ttl_minutes(self, service):
        before = datetime.utcnow()
        nid = await service.store_notification(
            user_id="user1",
            notification_type="system_alert",
            title="Alert",
            message="Expires soon",
            ttl_minutes=60,
        )
        after = datetime.utcnow()
        n = await service.get_notification(nid)
        assert n.expires_at is not None
        # expires_at should be roughly created_at + 60 minutes
        assert before + timedelta(minutes=60) <= n.expires_at <= after + timedelta(
            minutes=60
        )

    @pytest.mark.asyncio
    async def test_default_priority_is_normal(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="task_completed",
            title="Done",
            message="Task completed",
        )
        n = await service.get_notification(nid)
        assert n.priority == "normal"


# ===========================================================================
# TestGetPendingNotifications (4 tests)
# ===========================================================================


class TestGetPendingNotifications:
    """Tests for get_pending_notifications."""

    @pytest.mark.asyncio
    async def test_returns_pending_notifications_for_user(self, service):
        nid1 = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="T1",
            message="m1",
        )
        nid2 = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="T2",
            message="m2",
        )
        pending = await service.get_pending_notifications("user1")
        ids = [n.notification_id for n in pending]
        assert nid1 in ids
        assert nid2 in ids

    @pytest.mark.asyncio
    async def test_excludes_delivered_and_read_notifications(self, service):
        nid_pending = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="Pending",
            message="m",
        )
        nid_delivered = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="Delivered",
            message="m",
        )
        nid_read = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="Read",
            message="m",
        )
        await service.mark_delivered(nid_delivered)
        await service.mark_read(nid_read)

        pending = await service.get_pending_notifications("user1")
        ids = [n.notification_id for n in pending]
        assert nid_pending in ids
        assert nid_delivered not in ids
        assert nid_read not in ids

    @pytest.mark.asyncio
    async def test_sorted_by_priority_then_created_at(self, service):
        # Store in reverse priority order with slight time gaps
        nid_low = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="Low",
            message="m",
            priority="low",
        )
        nid_urgent = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="Urgent",
            message="m",
            priority="urgent",
        )
        nid_normal = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="Normal",
            message="m",
            priority="normal",
        )

        pending = await service.get_pending_notifications("user1")
        priorities = [n.priority for n in pending]
        # urgent should come first, then normal, then low
        assert priorities == ["urgent", "normal", "low"]

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_unknown_user(self, service):
        await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="T",
            message="m",
        )
        pending = await service.get_pending_notifications("unknown_user")
        assert pending == []


# ===========================================================================
# TestMarkDelivered (3 tests)
# ===========================================================================


class TestMarkDelivered:
    """Tests for mark_delivered."""

    @pytest.mark.asyncio
    async def test_sets_delivered_at_and_status(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="T",
            message="m",
        )
        before = datetime.utcnow()
        result = await service.mark_delivered(nid)
        after = datetime.utcnow()

        assert result is True
        n = await service.get_notification(nid)
        assert n.delivery_status == "delivered"
        assert n.delivered_at is not None
        assert before <= n.delivered_at <= after

    @pytest.mark.asyncio
    async def test_returns_false_for_not_found(self, service):
        result = await service.mark_delivered("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_clears_next_retry_at(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="T",
            message="m",
        )
        # Simulate a failure to set next_retry_at
        await service.mark_failed(nid, error="timeout")
        n = await service.get_notification(nid)
        assert n.next_retry_at is not None

        # Now mark delivered - should clear next_retry_at
        await service.mark_delivered(nid)
        n = await service.get_notification(nid)
        assert n.next_retry_at is None


# ===========================================================================
# TestMarkRead (2 tests)
# ===========================================================================


class TestMarkRead:
    """Tests for mark_read."""

    @pytest.mark.asyncio
    async def test_sets_read_at_and_status(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="T",
            message="m",
        )
        before = datetime.utcnow()
        result = await service.mark_read(nid)
        after = datetime.utcnow()

        assert result is True
        n = await service.get_notification(nid)
        assert n.delivery_status == "read"
        assert n.read_at is not None
        assert before <= n.read_at <= after

    @pytest.mark.asyncio
    async def test_returns_false_for_not_found(self, service):
        result = await service.mark_read("nonexistent-id")
        assert result is False


# ===========================================================================
# TestMarkFailed (4 tests)
# ===========================================================================


class TestMarkFailed:
    """Tests for mark_failed."""

    @pytest.mark.asyncio
    async def test_increments_retry_count(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="T",
            message="m",
        )
        n = await service.get_notification(nid)
        assert n.retry_count == 0

        await service.mark_failed(nid, error="timeout")
        n = await service.get_notification(nid)
        assert n.retry_count == 1

        await service.mark_failed(nid, error="timeout again")
        n = await service.get_notification(nid)
        assert n.retry_count == 2

    @pytest.mark.asyncio
    async def test_calculates_next_retry_at_from_delay_schedule(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="T",
            message="m",
            priority="normal",
        )
        delays = NOTIFICATION_RETRY_CONFIG["retry_delays"]

        before = datetime.utcnow()
        await service.mark_failed(nid, error="fail")
        after = datetime.utcnow()

        n = await service.get_notification(nid)
        assert n.next_retry_at is not None
        # First retry uses delays[0] = 10 seconds
        expected_min = before + timedelta(seconds=delays[0])
        expected_max = after + timedelta(seconds=delays[0])
        assert expected_min <= n.next_retry_at <= expected_max

    @pytest.mark.asyncio
    async def test_sets_status_to_failed_when_max_retries_exceeded(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="T",
            message="m",
            priority="normal",
        )
        max_retries = NOTIFICATION_RETRY_CONFIG["max_retries"]

        # Exhaust all retries
        for _ in range(max_retries):
            await service.mark_failed(nid, error="fail")

        n = await service.get_notification(nid)
        assert n.delivery_status == "failed"
        assert n.next_retry_at is None
        assert n.retry_count == max_retries

    @pytest.mark.asyncio
    async def test_urgent_notifications_use_urgent_retry_schedule(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="robot_error",
            title="Urgent",
            message="m",
            priority="urgent",
        )
        urgent_delays = NOTIFICATION_RETRY_CONFIG["urgent_retry_delays"]

        before = datetime.utcnow()
        await service.mark_failed(nid, error="fail")
        after = datetime.utcnow()

        n = await service.get_notification(nid)
        # First urgent retry uses urgent_delays[0] = 5 seconds
        expected_min = before + timedelta(seconds=urgent_delays[0])
        expected_max = after + timedelta(seconds=urgent_delays[0])
        assert expected_min <= n.next_retry_at <= expected_max

        # Urgent max retries is higher
        urgent_max = NOTIFICATION_RETRY_CONFIG["urgent_max_retries"]
        normal_max = NOTIFICATION_RETRY_CONFIG["max_retries"]
        assert urgent_max > normal_max


# ===========================================================================
# TestRetryNotification (3 tests)
# ===========================================================================


class TestRetryNotification:
    """Tests for retry_notification."""

    @pytest.mark.asyncio
    async def test_successful_retry_marks_delivered(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="T",
            message="m",
        )
        result = await service.retry_notification(nid, success_delivery)
        assert result is True

        n = await service.get_notification(nid)
        assert n.delivery_status == "delivered"
        assert n.delivered_at is not None

    @pytest.mark.asyncio
    async def test_failed_retry_marks_failed(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="T",
            message="m",
        )
        result = await service.retry_notification(nid, failure_delivery)
        assert result is False

        n = await service.get_notification(nid)
        assert n.delivery_status == "pending"  # still pending, not max retries yet
        assert n.retry_count == 1

    @pytest.mark.asyncio
    async def test_handler_exception_handled_gracefully(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="T",
            message="m",
        )

        async def exploding_handler(notification):
            raise RuntimeError("Connection refused")

        result = await service.retry_notification(nid, exploding_handler)
        assert result is False

        n = await service.get_notification(nid)
        assert n.retry_count == 1
        # Should not raise -- exception is caught internally


# ===========================================================================
# TestGetRetryCandidates (3 tests)
# ===========================================================================


class TestGetRetryCandidates:
    """Tests for get_retry_candidates."""

    @pytest.mark.asyncio
    async def test_returns_notifications_ready_for_retry(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="T",
            message="m",
        )
        await service.mark_failed(nid, error="fail")

        # Manually set next_retry_at to the past so it is ready
        n = await service.get_notification(nid)
        n.next_retry_at = datetime.utcnow() - timedelta(seconds=1)

        candidates = await service.get_retry_candidates()
        ids = [c.notification_id for c in candidates]
        assert nid in ids

    @pytest.mark.asyncio
    async def test_excludes_not_yet_ready_notifications(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="T",
            message="m",
        )
        await service.mark_failed(nid, error="fail")

        # next_retry_at should already be in the future after mark_failed
        n = await service.get_notification(nid)
        assert n.next_retry_at is not None
        assert n.next_retry_at > datetime.utcnow()

        candidates = await service.get_retry_candidates()
        ids = [c.notification_id for c in candidates]
        assert nid not in ids

    @pytest.mark.asyncio
    async def test_excludes_max_retried_notifications(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="T",
            message="m",
        )
        max_retries = NOTIFICATION_RETRY_CONFIG["max_retries"]

        # Exhaust retries
        for _ in range(max_retries):
            await service.mark_failed(nid, error="fail")

        n = await service.get_notification(nid)
        assert n.delivery_status == "failed"
        assert n.next_retry_at is None

        candidates = await service.get_retry_candidates()
        ids = [c.notification_id for c in candidates]
        assert nid not in ids


# ===========================================================================
# TestCleanupExpired (2 tests)
# ===========================================================================


class TestCleanupExpired:
    """Tests for cleanup_expired."""

    @pytest.mark.asyncio
    async def test_removes_expired_notifications(self, service):
        nid = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="Old",
            message="m",
            ttl_minutes=0,  # expires immediately
        )
        # Force expires_at to the past
        n = await service.get_notification(nid)
        n.expires_at = datetime.utcnow() - timedelta(seconds=1)

        await service.cleanup_expired()
        result = await service.get_notification(nid)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_count_of_removed(self, service):
        # Create 3 expired notifications
        for i in range(3):
            nid = await service.store_notification(
                user_id="user1",
                notification_type="task_assigned",
                title=f"Expired {i}",
                message="m",
            )
            n = await service.get_notification(nid)
            n.expires_at = datetime.utcnow() - timedelta(seconds=1)

        # Create 1 non-expired notification
        await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="Active",
            message="m",
            ttl_minutes=60,
        )

        count = await service.cleanup_expired()
        assert count == 3


# ===========================================================================
# TestGetNotificationStats (2 tests)
# ===========================================================================


class TestGetNotificationStats:
    """Tests for get_notification_stats."""

    @pytest.mark.asyncio
    async def test_returns_correct_counts(self, service):
        # 2 pending, 1 delivered, 1 read
        await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="P1",
            message="m",
        )
        await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="P2",
            message="m",
        )

        nid_d = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="D1",
            message="m",
        )
        await service.mark_delivered(nid_d)

        nid_r = await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="R1",
            message="m",
        )
        await service.mark_read(nid_r)

        stats = await service.get_notification_stats(user_id="user1")
        assert stats["total"] == 4
        assert stats["pending"] == 2
        assert stats["delivered"] == 1
        assert stats["read"] == 1
        assert stats["failed"] == 0

    @pytest.mark.asyncio
    async def test_by_priority_breakdown(self, service):
        await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="Low",
            message="m",
            priority="low",
        )
        await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="Normal",
            message="m",
            priority="normal",
        )
        await service.store_notification(
            user_id="user1",
            notification_type="task_assigned",
            title="High",
            message="m",
            priority="high",
        )
        await service.store_notification(
            user_id="user1",
            notification_type="robot_error",
            title="Urgent1",
            message="m",
            priority="urgent",
        )
        await service.store_notification(
            user_id="user1",
            notification_type="robot_error",
            title="Urgent2",
            message="m",
            priority="urgent",
        )

        stats = await service.get_notification_stats(user_id="user1")
        assert stats["by_priority"]["low"] == 1
        assert stats["by_priority"]["normal"] == 1
        assert stats["by_priority"]["high"] == 1
        assert stats["by_priority"]["urgent"] == 2


# ===========================================================================
# TestBatchStore (2 tests)
# ===========================================================================


class TestBatchStore:
    """Tests for batch_store."""

    @pytest.mark.asyncio
    async def test_stores_multiple_notifications(self, service):
        items = [
            {
                "user_id": "user1",
                "notification_type": "task_assigned",
                "title": "Batch 1",
                "message": "m1",
            },
            {
                "user_id": "user1",
                "notification_type": "task_completed",
                "title": "Batch 2",
                "message": "m2",
                "priority": "high",
            },
            {
                "user_id": "user2",
                "notification_type": "system_alert",
                "title": "Batch 3",
                "message": "m3",
            },
        ]
        ids = await service.batch_store(items)
        assert len(ids) == 3

        for nid in ids:
            n = await service.get_notification(nid)
            assert n is not None

    @pytest.mark.asyncio
    async def test_returns_list_of_ids(self, service):
        items = [
            {
                "user_id": "user1",
                "notification_type": "task_assigned",
                "title": f"N{i}",
                "message": f"msg{i}",
            }
            for i in range(5)
        ]
        ids = await service.batch_store(items)
        assert isinstance(ids, list)
        assert len(ids) == 5
        # All IDs should be unique strings
        assert len(set(ids)) == 5
        for nid in ids:
            assert isinstance(nid, str)
            assert len(nid) > 0
