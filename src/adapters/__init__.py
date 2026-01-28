"""
Adapters Module - 设备适配器模块
"""

from .drone import (
    DroneAdapter,
    MockDroneAdapter,
    DroneState,
    DroneStatus,
    DronePosition,
    FlightMode,
    FlightTask,
    FlightResult,
)
from .robot_dog import (
    RobotDogAdapter,
    MockRobotDogAdapter,
    RobotDogState,
    RobotDogStatus,
    RobotDogPosition,
    MovementMode,
    GaitType,
    GroundTask,
    GroundTaskResult,
)

__all__ = [
    # Drone
    "DroneAdapter",
    "MockDroneAdapter",
    "DroneState",
    "DroneStatus",
    "DronePosition",
    "FlightMode",
    "FlightTask",
    "FlightResult",
    # Robot Dog
    "RobotDogAdapter",
    "MockRobotDogAdapter",
    "RobotDogState",
    "RobotDogStatus",
    "RobotDogPosition",
    "MovementMode",
    "GaitType",
    "GroundTask",
    "GroundTaskResult",
]
