"""
ECIS Offline Support Module (P1)

Server-side infrastructure for mobile offline operations including
operation queueing, synchronisation with conflict resolution, and
in-memory caching with TTL expiry.

Usage::

    from offline import (
        OfflineQueueManager,
        CacheManager,
        OfflineOperation,
        SyncResult,
        SyncBatchResult,
        ConflictError,
    )

    queue = OfflineQueueManager()
    cache = CacheManager()

    op_id = await queue.enqueue("user-1", "task_confirm", {"task_id": "t-42"})
    result = await queue.sync_operation(op_id, my_server_handler)
"""

from .offline_queue import (
    CacheManager,
    ConflictError,
    OfflineOperation,
    OfflineQueueManager,
    SyncBatchResult,
    SyncResult,
)

__all__ = [
    "CacheManager",
    "ConflictError",
    "OfflineOperation",
    "OfflineQueueManager",
    "SyncBatchResult",
    "SyncResult",
]
