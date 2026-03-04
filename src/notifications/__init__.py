"""
ECIS Notification Persistence Module (P3)

Phase 1 in-memory implementation with retry logic and multi-channel support.
"""

from .notification_service import (
    NOTIFICATION_RETRY_CONFIG,
    Notification,
    NotificationService,
)

__all__ = [
    "Notification",
    "NotificationService",
    "NOTIFICATION_RETRY_CONFIG",
]
