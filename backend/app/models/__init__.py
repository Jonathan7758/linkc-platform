"""数据模型模块"""

from .base import TimestampMixin
from .device import Device, DeviceReading, DeviceType, SystemType, DeviceStatus
from .alarm import Alarm, AlarmSeverity, AlarmStatus, AlarmCategory
from .energy import EnergyReading, EnergyType
from .knowledge import KnowledgeArticle, KnowledgeCategory
from .ticket import Ticket, TicketType, TicketPriority, TicketStatus
from .conversation import Conversation, ConversationMessage, MessageRole

__all__ = [
    "TimestampMixin",
    "Device",
    "DeviceReading",
    "DeviceType",
    "SystemType",
    "DeviceStatus",
    "Alarm",
    "AlarmSeverity",
    "AlarmStatus",
    "AlarmCategory",
    "EnergyReading",
    "EnergyType",
    "KnowledgeArticle",
    "KnowledgeCategory",
    "Ticket",
    "TicketType",
    "TicketPriority",
    "TicketStatus",
    "Conversation",
    "ConversationMessage",
    "MessageRole",
]
