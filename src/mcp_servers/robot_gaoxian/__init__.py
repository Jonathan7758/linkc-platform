"""
M3: 高仙机器人 MCP Server
========================
提供高仙品牌机器人控制功能
"""

from .storage import (
    InMemoryRobotStorage,
    Robot,
    RobotStatus,
    RobotStatusSnapshot,
    RobotBrand,
    RobotType,
    CleaningMode,
    CleaningIntensity,
    Location,
    RobotCapability,
    RobotError,
    ErrorSeverity,
)
from .mock_client import MockGaoxianClient
from .tools import RobotTools, ToolResult

__all__ = [
    'InMemoryRobotStorage',
    'Robot',
    'RobotStatus',
    'RobotStatusSnapshot',
    'RobotBrand',
    'RobotType',
    'CleaningMode',
    'CleaningIntensity',
    'Location',
    'RobotCapability',
    'RobotError',
    'ErrorSeverity',
    'MockGaoxianClient',
    'RobotTools',
    'ToolResult',
]
