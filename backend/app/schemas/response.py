"""统一响应Schema"""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """错误详情"""

    code: str
    message: str
    details: dict[str, Any] | None = None


class APIResponse(BaseModel, Generic[T]):
    """统一API响应"""

    success: bool
    data: T | None = None
    message: str | None = None
    error: ErrorDetail | None = None


class PaginationInfo(BaseModel):
    """分页信息"""

    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""

    success: bool = True
    data: list[T]
    pagination: PaginationInfo


# 错误码常量
class ErrorCodes:
    """错误码定义"""

    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"

    # 设备相关
    DEVICE_NOT_FOUND = "DEVICE_NOT_FOUND"
    DEVICE_OFFLINE = "DEVICE_OFFLINE"
    CONTROL_FAILED = "CONTROL_FAILED"

    # 对话相关
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    LLM_ERROR = "LLM_ERROR"
    TOOL_ERROR = "TOOL_ERROR"


ERROR_MESSAGES = {
    ErrorCodes.INTERNAL_ERROR: "服务器内部错误",
    ErrorCodes.VALIDATION_ERROR: "参数验证失败",
    ErrorCodes.NOT_FOUND: "资源不存在",
    ErrorCodes.UNAUTHORIZED: "未授权",
    ErrorCodes.FORBIDDEN: "禁止访问",
    ErrorCodes.DEVICE_NOT_FOUND: "设备不存在",
    ErrorCodes.DEVICE_OFFLINE: "设备离线",
    ErrorCodes.CONTROL_FAILED: "控制命令执行失败",
    ErrorCodes.SESSION_NOT_FOUND: "会话不存在",
    ErrorCodes.LLM_ERROR: "AI服务异常",
    ErrorCodes.TOOL_ERROR: "工具调用失败",
}


def success_response(data: Any = None, message: str | None = None) -> dict:
    """创建成功响应"""
    return {"success": True, "data": data, "message": message, "error": None}


def error_response(code: str, message: str | None = None, details: dict | None = None) -> dict:
    """创建错误响应"""
    return {
        "success": False,
        "data": None,
        "message": None,
        "error": {
            "code": code,
            "message": message or ERROR_MESSAGES.get(code, "未知错误"),
            "details": details,
        },
    }
