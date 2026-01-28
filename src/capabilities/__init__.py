"""
Capabilities Module - 能力定义和注册
"""

from .models import Capability, AgentCapabilityInfo, CapabilityMatch
from .registry import (
    CapabilityRegistry,
    CLEANING_CAPABILITIES,
    DELIVERY_CAPABILITIES,
    PATROL_CAPABILITIES,
)
from .service import CapabilityService
from .drone import (
    DRONE_CAPABILITIES,
    get_drone_capabilities,
    get_drone_capability_ids,
)
from .robot_dog import (
    ROBOT_DOG_CAPABILITIES,
    get_robot_dog_capabilities,
    get_robot_dog_capability_ids,
)

__all__ = [
    # Models
    "Capability",
    "AgentCapabilityInfo",
    "CapabilityMatch",
    # Registry
    "CapabilityRegistry",
    "CLEANING_CAPABILITIES",
    "DELIVERY_CAPABILITIES",
    "PATROL_CAPABILITIES",
    "DRONE_CAPABILITIES",
    "ROBOT_DOG_CAPABILITIES",
    # Service
    "CapabilityService",
    # Helpers
    "get_drone_capabilities",
    "get_drone_capability_ids",
    "get_robot_dog_capabilities",
    "get_robot_dog_capability_ids",
]
