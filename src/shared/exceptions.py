"""
LinkC Platform - 统一异常处理
============================
定义所有模块共用的异常类型。
"""

from typing import Optional


class LinkCException(Exception):
    """LinkC平台基础异常"""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict] = None
    ):
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details
        }


# ============================================================
# 通用异常
# ============================================================

class NotFoundError(LinkCException):
    """资源未找到"""
    
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} with id {resource_id} not found",
            code="NOT_FOUND",
            details={"resource": resource, "id": resource_id}
        )


class ValidationError(LinkCException):
    """验证失败"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field} if field else {}
        )


class ConflictError(LinkCException):
    """资源冲突"""
    
    def __init__(self, message: str, resource: Optional[str] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            details={"resource": resource} if resource else {}
        )


class UnauthorizedError(LinkCException):
    """未授权"""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            code="UNAUTHORIZED"
        )


class ForbiddenError(LinkCException):
    """禁止访问"""
    
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(
            message=message,
            code="FORBIDDEN"
        )


# ============================================================
# 业务异常
# ============================================================

class RobotBusyError(LinkCException):
    """机器人忙碌"""
    
    def __init__(self, robot_id: str, current_task: Optional[str] = None):
        super().__init__(
            message=f"Robot {robot_id} is currently busy",
            code="ROBOT_BUSY",
            details={"robot_id": robot_id, "current_task": current_task}
        )


class RobotOfflineError(LinkCException):
    """机器人离线"""
    
    def __init__(self, robot_id: str):
        super().__init__(
            message=f"Robot {robot_id} is offline",
            code="ROBOT_OFFLINE",
            details={"robot_id": robot_id}
        )


class TaskAlreadyAssignedError(LinkCException):
    """任务已分配"""
    
    def __init__(self, task_id: str, robot_id: str):
        super().__init__(
            message=f"Task {task_id} is already assigned to robot {robot_id}",
            code="TASK_ALREADY_ASSIGNED",
            details={"task_id": task_id, "robot_id": robot_id}
        )


class InsufficientBatteryError(LinkCException):
    """电量不足"""
    
    def __init__(self, robot_id: str, current_level: int, required_level: int):
        super().__init__(
            message=f"Robot {robot_id} has insufficient battery ({current_level}% < {required_level}%)",
            code="INSUFFICIENT_BATTERY",
            details={
                "robot_id": robot_id,
                "current_level": current_level,
                "required_level": required_level
            }
        )


class MCPConnectionError(LinkCException):
    """MCP连接错误"""
    
    def __init__(self, server_name: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Failed to connect to MCP server {server_name}",
            code="MCP_CONNECTION_ERROR",
            details={"server": server_name}
        )


class ExternalAPIError(LinkCException):
    """外部API错误"""
    
    def __init__(self, api_name: str, status_code: Optional[int] = None, message: Optional[str] = None):
        super().__init__(
            message=message or f"External API {api_name} returned an error",
            code="EXTERNAL_API_ERROR",
            details={"api": api_name, "status_code": status_code}
        )


# ============================================================
# 导出
# ============================================================

__all__ = [
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
