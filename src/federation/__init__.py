"""
Federation 集成模块

提供与 ECIS Federation Gateway 的通信能力
"""

from .client import FederationClient
from .events import EventPublisher, EventTypes
from .handlers import EventHandler

__all__ = [
    "FederationClient",
    "EventPublisher",
    "EventTypes",
    "EventHandler"
]
