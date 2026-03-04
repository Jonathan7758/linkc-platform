"""
ECIS P3 - Notification Persistence Service

Phase 1: In-memory notification storage with retry logic.
Provides async methods for storing, delivering, retrying, and managing
notifications across multiple channels and priority levels.
"""

import uuid
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retry configuration
# ---------------------------------------------------------------------------

NOTIFICATION_RETRY_CONFIG = {
    "max_retries": 5,
    "retry_delays": [10, 30, 60, 300, 600],  # seconds
    "urgent_max_retries": 10,
    "urgent_retry_delays": [5, 10, 30, 60, 120, 300, 300, 600, 600, 600],
}

# Priority ordering (higher number = higher priority)
_PRIORITY_ORDER: Dict[str, int] = {
    "low": 0,
    "normal": 1,
    "high": 2,
    "urgent": 3,
}

# ---------------------------------------------------------------------------
# Notification dataclass
# ---------------------------------------------------------------------------


@dataclass
class Notification:
    notification_id: str
    user_id: str
    notification_type: str  # task_assigned | task_completed | robot_error | system_alert | approval_request
    title: str
    message: str
    priority: str = "normal"  # low | normal | high | urgent
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    delivery_status: str = "pending"  # pending | delivered | read | failed | expired
    retry_count: int = 0
    next_retry_at: Optional[datetime] = None
    channel: str = "push"  # push | websocket | sms | email
    expires_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Notification Service
# ---------------------------------------------------------------------------


class NotificationService:
    """In-memory notification persistence with retry logic (Phase 1)."""

    def __init__(self) -> None:
        self._notifications: Dict[str, Notification] = {}

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _priority_sort_key(n: Notification) -> tuple:
        """Return a sort key so that *higher* priority comes first,
        then earlier created_at comes first."""
        return (
            -_PRIORITY_ORDER.get(n.priority, 1),
            n.created_at or datetime.min,
        )

    def _max_retries_for(self, notification: Notification) -> int:
        if notification.priority == "urgent":
            return NOTIFICATION_RETRY_CONFIG["urgent_max_retries"]
        return NOTIFICATION_RETRY_CONFIG["max_retries"]

    def _retry_delays_for(self, notification: Notification) -> List[int]:
        if notification.priority == "urgent":
            return NOTIFICATION_RETRY_CONFIG["urgent_retry_delays"]
        return NOTIFICATION_RETRY_CONFIG["retry_delays"]

    # 1. store_notification ---------------------------------------------------

    async def store_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        priority: str = "normal",
        payload: Optional[Dict[str, Any]] = None,
        channel: str = "push",
        ttl_minutes: int = 1440,
    ) -> str:
        """Create and store a notification.  Returns the notification_id."""
        notification_id = str(uuid.uuid4())
        now = datetime.utcnow()

        notification = Notification(
            notification_id=notification_id,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            payload=payload if payload is not None else {},
            created_at=now,
            delivery_status="pending",
            channel=channel,
            expires_at=now + timedelta(minutes=ttl_minutes),
        )

        self._notifications[notification_id] = notification
        logger.debug(
            "Stored notification %s for user %s (type=%s, priority=%s)",
            notification_id,
            user_id,
            notification_type,
            priority,
        )
        return notification_id

    # 2. get_pending_notifications --------------------------------------------

    async def get_pending_notifications(self, user_id: str) -> List[Notification]:
        """Return undelivered notifications for *user_id*, sorted by priority
        (urgent first) then by created_at (oldest first)."""
        pending = [
            n
            for n in self._notifications.values()
            if n.user_id == user_id and n.delivery_status in ("pending", "failed")
        ]
        pending.sort(key=self._priority_sort_key)
        return pending

    # 3. mark_delivered -------------------------------------------------------

    async def mark_delivered(self, notification_id: str) -> bool:
        """Mark a notification as delivered.  Returns False if not found."""
        notification = self._notifications.get(notification_id)
        if notification is None:
            return False

        notification.delivered_at = datetime.utcnow()
        notification.delivery_status = "delivered"
        notification.next_retry_at = None
        logger.debug("Notification %s marked delivered", notification_id)
        return True

    # 4. mark_read ------------------------------------------------------------

    async def mark_read(self, notification_id: str) -> bool:
        """Mark a notification as read.  Returns False if not found."""
        notification = self._notifications.get(notification_id)
        if notification is None:
            return False

        notification.read_at = datetime.utcnow()
        notification.delivery_status = "read"
        notification.next_retry_at = None
        logger.debug("Notification %s marked read", notification_id)
        return True

    # 5. mark_failed ----------------------------------------------------------

    async def mark_failed(self, notification_id: str, error: str = "") -> bool:
        """Record a delivery failure.

        * Increments *retry_count*.
        * Calculates *next_retry_at* from the retry-delay schedule.
        * If max retries exceeded, sets delivery_status to ``"failed"``
          permanently (next_retry_at = None).

        Returns False if the notification was not found.
        """
        notification = self._notifications.get(notification_id)
        if notification is None:
            return False

        notification.retry_count += 1

        max_retries = self._max_retries_for(notification)
        delays = self._retry_delays_for(notification)

        if notification.retry_count >= max_retries:
            notification.delivery_status = "failed"
            notification.next_retry_at = None
            logger.warning(
                "Notification %s permanently failed after %d retries: %s",
                notification_id,
                notification.retry_count,
                error,
            )
        else:
            notification.delivery_status = "pending"
            delay_index = min(notification.retry_count - 1, len(delays) - 1)
            delay_seconds = delays[delay_index]
            notification.next_retry_at = datetime.utcnow() + timedelta(
                seconds=delay_seconds
            )
            logger.debug(
                "Notification %s scheduled for retry #%d in %ds: %s",
                notification_id,
                notification.retry_count,
                delay_seconds,
                error,
            )

        return True

    # 6. get_retry_candidates -------------------------------------------------

    async def get_retry_candidates(self) -> List[Notification]:
        """Return notifications that are due for a retry attempt right now."""
        now = datetime.utcnow()
        candidates: List[Notification] = []

        for n in self._notifications.values():
            if n.next_retry_at is None:
                continue
            max_retries = self._max_retries_for(n)
            if n.retry_count < max_retries and n.next_retry_at <= now:
                candidates.append(n)

        candidates.sort(key=self._priority_sort_key)
        return candidates

    # 7. retry_notification ---------------------------------------------------

    async def retry_notification(
        self,
        notification_id: str,
        delivery_handler: Callable[[Notification], Coroutine[Any, Any, bool]],
    ) -> bool:
        """Attempt to deliver *notification_id* via *delivery_handler*.

        *delivery_handler* is an async callable that receives a
        :class:`Notification` and returns ``True`` on success.

        On success the notification is marked delivered; on failure it is
        passed through :meth:`mark_failed`.
        """
        notification = self._notifications.get(notification_id)
        if notification is None:
            return False

        try:
            success = await delivery_handler(notification)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Delivery handler raised for %s: %s", notification_id, exc
            )
            await self.mark_failed(notification_id, error=str(exc))
            return False

        if success:
            await self.mark_delivered(notification_id)
            return True
        else:
            await self.mark_failed(notification_id, error="handler returned False")
            return False

    # 8. cleanup_expired ------------------------------------------------------

    async def cleanup_expired(self) -> int:
        """Remove expired notifications.  Returns the count of removed items."""
        now = datetime.utcnow()
        expired_ids = [
            nid
            for nid, n in self._notifications.items()
            if n.expires_at is not None and n.expires_at <= now
        ]
        for nid in expired_ids:
            del self._notifications[nid]

        if expired_ids:
            logger.info("Cleaned up %d expired notifications", len(expired_ids))
        return len(expired_ids)

    # 9. get_notification_stats -----------------------------------------------

    async def get_notification_stats(
        self, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Return aggregate statistics, optionally filtered by *user_id*."""
        if user_id is not None:
            pool = [
                n for n in self._notifications.values() if n.user_id == user_id
            ]
        else:
            pool = list(self._notifications.values())

        stats: Dict[str, Any] = {
            "total": len(pool),
            "pending": 0,
            "delivered": 0,
            "read": 0,
            "failed": 0,
            "by_priority": {
                "low": 0,
                "normal": 0,
                "high": 0,
                "urgent": 0,
            },
        }

        for n in pool:
            if n.delivery_status in ("pending",):
                stats["pending"] += 1
            elif n.delivery_status == "delivered":
                stats["delivered"] += 1
            elif n.delivery_status == "read":
                stats["read"] += 1
            elif n.delivery_status == "failed":
                stats["failed"] += 1

            if n.priority in stats["by_priority"]:
                stats["by_priority"][n.priority] += 1

        return stats

    # 10. get_notification ----------------------------------------------------

    async def get_notification(
        self, notification_id: str
    ) -> Optional[Notification]:
        """Return a single notification by ID, or ``None`` if not found."""
        return self._notifications.get(notification_id)

    # 11. batch_store ---------------------------------------------------------

    async def batch_store(self, notifications: List[Dict[str, Any]]) -> List[str]:
        """Store multiple notifications at once.

        Each dict in *notifications* is forwarded as keyword arguments to
        :meth:`store_notification`.  Returns a list of the generated
        notification IDs (in the same order).
        """
        ids: List[str] = []
        for item in notifications:
            nid = await self.store_notification(**item)
            ids.append(nid)
        return ids
