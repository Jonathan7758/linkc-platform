"""
ECIS P1 Offline Support - Backend Queue & Cache Infrastructure

Server-side module supporting mobile offline operations. Provides:
- OfflineQueueManager: enqueue, sync, conflict-resolution for offline ops
- CacheManager: in-memory cache with TTL expiry for task lists, robot states

Phase 1 implementation uses in-memory storage. Designed for future migration
to persistent backends (Redis, PostgreSQL) without API changes.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class OfflineOperation:
    """A single offline operation queued for server synchronisation."""

    operation_id: str
    user_id: str
    operation_type: str  # task_confirm | task_complete | anomaly_report | feedback
    payload: Dict[str, Any]
    created_at: datetime
    sync_status: str = "pending"  # pending | syncing | synced | conflict | failed
    retry_count: int = 0
    max_retries: int = 5
    server_response: Optional[Dict[str, Any]] = None
    optimistic_version: int = 1
    synced_at: Optional[datetime] = None


@dataclass
class SyncResult:
    """Outcome of synchronising a single operation."""

    operation_id: str
    success: bool
    conflict: bool = False
    error: str = ""
    server_state: Optional[Dict[str, Any]] = None


@dataclass
class SyncBatchResult:
    """Aggregate outcome of synchronising a batch of operations."""

    synced: int = 0
    failed: int = 0
    conflicts: List[OfflineOperation] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

# An async callable that the caller supplies to actually execute the operation
# on the server.  Signature:  async def handler(payload) -> dict
ServerHandler = Callable[[Dict[str, Any]], Coroutine[Any, Any, Dict[str, Any]]]


# ---------------------------------------------------------------------------
# Conflict exception used by server handlers to signal a 409 conflict
# ---------------------------------------------------------------------------


class ConflictError(Exception):
    """Raised by a server handler when a 409 conflict is detected."""

    def __init__(self, server_state: Optional[Dict[str, Any]] = None):
        super().__init__("conflict")
        self.server_state = server_state


# ---------------------------------------------------------------------------
# OfflineQueueManager
# ---------------------------------------------------------------------------


class OfflineQueueManager:
    """In-memory Phase 1 queue manager for offline operations.

    Thread-safe for concurrent asyncio tasks via an internal lock.
    """

    def __init__(self) -> None:
        self._operations: Dict[str, OfflineOperation] = {}
        self._lock = asyncio.Lock()

    # -- enqueue ------------------------------------------------------------

    async def enqueue(
        self,
        user_id: str,
        operation_type: str,
        payload: Dict[str, Any],
        optimistic_version: int = 1,
    ) -> str:
        """Create and store a new offline operation. Returns operation_id."""
        operation_id = str(uuid.uuid4())
        op = OfflineOperation(
            operation_id=operation_id,
            user_id=user_id,
            operation_type=operation_type,
            payload=payload,
            created_at=datetime.now(timezone.utc),
            optimistic_version=optimistic_version,
        )
        async with self._lock:
            self._operations[operation_id] = op
        logger.info(
            "Enqueued operation %s for user %s (type=%s)",
            operation_id,
            user_id,
            operation_type,
        )
        return operation_id

    # -- get_pending_ops ----------------------------------------------------

    async def get_pending_ops(self, user_id: str) -> List[OfflineOperation]:
        """Return all pending or failed operations for *user_id*, ordered by creation time."""
        async with self._lock:
            return sorted(
                [
                    op
                    for op in self._operations.values()
                    if op.user_id == user_id and op.sync_status in ("pending", "failed")
                ],
                key=lambda o: o.created_at,
            )

    # -- sync_operation -----------------------------------------------------

    async def sync_operation(
        self,
        operation_id: str,
        server_handler: ServerHandler,
    ) -> SyncResult:
        """Attempt to synchronise a single operation via *server_handler*.

        *server_handler* is an async callable ``(payload) -> dict``.
        It should raise :class:`ConflictError` (or return a dict containing
        ``{"status": 409, ...}``) to signal an optimistic-locking conflict.
        Any other exception is treated as a transient failure eligible for
        retry.
        """
        async with self._lock:
            op = self._operations.get(operation_id)
            if op is None:
                return SyncResult(operation_id=operation_id, success=False, error="operation_not_found")
            # Snapshot and mark as syncing
            op.sync_status = "syncing"

        try:
            result = await server_handler(op.payload)

            # Check for conflict conveyed via return value
            if isinstance(result, dict) and result.get("status") == 409:
                raise ConflictError(server_state=result)

            # Success path
            async with self._lock:
                op.sync_status = "synced"
                op.synced_at = datetime.now(timezone.utc)
                op.server_response = result
            logger.info("Synced operation %s", operation_id)
            return SyncResult(operation_id=operation_id, success=True, server_state=result)

        except ConflictError as exc:
            async with self._lock:
                op.sync_status = "conflict"
                op.server_response = exc.server_state
            logger.warning("Conflict on operation %s", operation_id)
            return SyncResult(
                operation_id=operation_id,
                success=False,
                conflict=True,
                server_state=exc.server_state,
            )

        except Exception as exc:  # noqa: BLE001 — catch-all for transient errors
            async with self._lock:
                op.retry_count += 1
                if op.retry_count >= op.max_retries:
                    op.sync_status = "failed"
                    logger.error(
                        "Operation %s permanently failed after %d retries: %s",
                        operation_id,
                        op.retry_count,
                        exc,
                    )
                else:
                    op.sync_status = "pending"  # eligible for next sync pass
                    logger.warning(
                        "Operation %s failed (attempt %d/%d): %s",
                        operation_id,
                        op.retry_count,
                        op.max_retries,
                        exc,
                    )
            return SyncResult(
                operation_id=operation_id,
                success=False,
                error=str(exc),
            )

    # -- sync_all -----------------------------------------------------------

    async def sync_all(
        self,
        user_id: str,
        server_handler: ServerHandler,
    ) -> SyncBatchResult:
        """Synchronise every pending/failed operation for *user_id*."""
        pending = await self.get_pending_ops(user_id)
        batch = SyncBatchResult()

        for op in pending:
            result = await self.sync_operation(op.operation_id, server_handler)
            if result.success:
                batch.synced += 1
            elif result.conflict:
                batch.conflicts.append(op)
            else:
                batch.failed += 1

        logger.info(
            "sync_all for user %s: synced=%d failed=%d conflicts=%d",
            user_id,
            batch.synced,
            batch.failed,
            len(batch.conflicts),
        )
        return batch

    # -- get_status ---------------------------------------------------------

    async def get_status(self, user_id: str) -> Dict[str, Any]:
        """Return a summary dict of queue status for *user_id*."""
        async with self._lock:
            user_ops = [op for op in self._operations.values() if op.user_id == user_id]

        pending = sum(1 for o in user_ops if o.sync_status in ("pending", "syncing"))
        failed = sum(1 for o in user_ops if o.sync_status == "failed")
        synced = sum(1 for o in user_ops if o.sync_status == "synced")
        conflicts = sum(1 for o in user_ops if o.sync_status == "conflict")

        synced_times = [o.synced_at for o in user_ops if o.synced_at is not None]
        last_sync_at = max(synced_times) if synced_times else None

        return {
            "pending": pending,
            "failed": failed,
            "synced": synced,
            "conflicts": conflicts,
            "last_sync_at": last_sync_at,
        }

    # -- resolve_conflict ---------------------------------------------------

    async def resolve_conflict(self, operation_id: str, resolution: str) -> bool:
        """Resolve a conflicted operation.

        *resolution* must be one of:
        - ``"accept_server"`` — discard local change, mark as synced with
          the server's state.
        - ``"force_client"`` — reset to pending so the client payload will be
          re-sent on the next sync pass.
        - ``"discard"`` — drop the operation entirely.

        Returns ``True`` if the operation was found and resolved.
        """
        if resolution not in ("accept_server", "force_client", "discard"):
            raise ValueError(f"Invalid resolution: {resolution!r}")

        async with self._lock:
            op = self._operations.get(operation_id)
            if op is None or op.sync_status != "conflict":
                return False

            if resolution == "accept_server":
                op.sync_status = "synced"
                op.synced_at = datetime.now(timezone.utc)
            elif resolution == "force_client":
                op.sync_status = "pending"
                op.retry_count = 0
            elif resolution == "discard":
                del self._operations[operation_id]

        logger.info("Resolved conflict for %s with %s", operation_id, resolution)
        return True

    # -- mark_synced --------------------------------------------------------

    async def mark_synced(
        self,
        operation_id: str,
        server_response: Dict[str, Any],
    ) -> bool:
        """Externally mark an operation as successfully synced.

        Returns ``True`` if the operation exists and was updated.
        """
        async with self._lock:
            op = self._operations.get(operation_id)
            if op is None:
                return False
            op.sync_status = "synced"
            op.synced_at = datetime.now(timezone.utc)
            op.server_response = server_response
        logger.info("Marked operation %s as synced", operation_id)
        return True


# ---------------------------------------------------------------------------
# CacheManager
# ---------------------------------------------------------------------------


@dataclass
class _CacheEntry:
    """Internal wrapper holding cached data with expiry metadata."""

    data: Any
    max_age_seconds: float
    stored_at: float  # time.monotonic()


class CacheManager:
    """In-memory cache with per-key TTL expiry.

    Uses ``time.monotonic()`` for age tracking so that wall-clock adjustments
    do not cause spurious invalidations.
    """

    def __init__(self) -> None:
        self._store: Dict[str, _CacheEntry] = {}
        self._lock = asyncio.Lock()

    # -- core ---------------------------------------------------------------

    async def cache_data(
        self,
        key: str,
        data: Any,
        max_age_seconds: float = 1800,
    ) -> None:
        """Store *data* under *key* with a TTL of *max_age_seconds*."""
        entry = _CacheEntry(
            data=data,
            max_age_seconds=max_age_seconds,
            stored_at=time.monotonic(),
        )
        async with self._lock:
            self._store[key] = entry

    async def get_cached(self, key: str) -> Optional[Any]:
        """Return cached data for *key*, or ``None`` if missing / expired."""
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            age = time.monotonic() - entry.stored_at
            if age > entry.max_age_seconds:
                del self._store[key]
                return None
            return entry.data

    async def invalidate(self, key: str) -> bool:
        """Remove *key* from the cache. Returns ``True`` if it existed."""
        async with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    async def invalidate_all(self) -> int:
        """Remove every entry. Returns the number of entries cleared."""
        async with self._lock:
            count = len(self._store)
            self._store.clear()
            return count

    def get_cache_age(self, key: str) -> float:
        """Return seconds since *key* was last updated, or ``-1`` if absent."""
        entry = self._store.get(key)
        if entry is None:
            return -1.0
        return time.monotonic() - entry.stored_at

    # -- convenience: task lists --------------------------------------------

    async def cache_task_list(self, user_id: str, tasks: List[Any]) -> None:
        """Cache a task list for *user_id* (default 30-min TTL)."""
        key = f"tasks:{user_id}"
        await self.cache_data(key, tasks)

    async def get_cached_task_list(self, user_id: str) -> Optional[List[Any]]:
        """Retrieve the cached task list for *user_id*."""
        key = f"tasks:{user_id}"
        return await self.get_cached(key)

    # -- convenience: robot states ------------------------------------------

    async def cache_robot_states(
        self,
        building_id: str,
        states: List[Any],
    ) -> None:
        """Cache robot states for *building_id* (default 30-min TTL)."""
        key = f"robots:{building_id}"
        await self.cache_data(key, states)

    async def get_cached_robot_states(
        self,
        building_id: str,
    ) -> Optional[List[Any]]:
        """Retrieve the cached robot states for *building_id*."""
        key = f"robots:{building_id}"
        return await self.get_cached(key)
