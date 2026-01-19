"""
LinkC Platform - 共享模块
========================
提供配置管理、日志系统、异常处理等基础功能。
"""

from .config import settings, get_settings, Settings, Environment, LogLevel
from .logging import get_logger, set_request_context, clear_request_context, log_execution_time, default_logger
from .exceptions import (
    LinkCException,
    NotFoundError,
    ValidationError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
    RobotBusyError,
    RobotOfflineError,
    TaskAlreadyAssignedError,
    InsufficientBatteryError,
    MCPConnectionError,
    ExternalAPIError,
)

__all__ = [
    # Config
    "settings",
    "get_settings",
    "Settings",
    "Environment",
    "LogLevel",
    # Logging
    "get_logger",
    "set_request_context",
    "clear_request_context",
    "log_execution_time",
    "default_logger",
    # Exceptions
    "LinkCException",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "UnauthorizedError",
    "ForbiddenError",
    "RobotBusyError",
    "RobotOfflineError",
    "TaskAlreadyAssignedError",
    "InsufficientBatteryError",
    "MCPConnectionError",
    "ExternalAPIError",
]
