"""
LinkC Platform - FastAPI异常处理集成 (F3)
========================================
将异常统一转换为HTTP响应，提供请求追踪中间件。
"""

import uuid
from typing import Union
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .exceptions import (
    LinkCException,
    NotFoundError,
    ValidationError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
)
from .logging import get_logger, set_request_context, clear_request_context


logger = get_logger("linkc.error_handler")


# 异常到HTTP状态码映射
EXCEPTION_STATUS_MAP = {
    NotFoundError: 404,
    ValidationError: 400,
    ConflictError: 409,
    UnauthorizedError: 401,
    ForbiddenError: 403,
}


def linkc_exception_handler(request: Request, exc: LinkCException) -> JSONResponse:
    """处理LinkC自定义异常"""
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 500)

    logger.error(
        "Request failed",
        error_code=exc.code,
        error_message=exc.message,
        path=str(request.url.path),
        method=request.method,
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        }
    )


def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理未预期的异常"""
    logger.critical(
        "Unhandled exception",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=str(request.url.path),
        method=request.method,
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            }
        }
    )


class RequestContextMiddleware(BaseHTTPMiddleware):
    """请求上下文中间件 - 注入request_id和tenant_id"""

    async def dispatch(self, request: Request, call_next):
        # 生成或获取request_id
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # 获取tenant_id
        tenant_id = request.headers.get("X-Tenant-ID") or request.query_params.get("tenant_id")

        # 设置上下文
        set_request_context(request_id=request_id, tenant_id=tenant_id)

        # 添加request_id到request.state供后续使用
        request.state.request_id = request_id
        request.state.tenant_id = tenant_id

        try:
            response = await call_next(request)
            # 在响应头中返回request_id
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            clear_request_context()


def setup_error_handlers(app: FastAPI) -> None:
    """注册所有错误处理器"""

    # 注册LinkC异常处理器
    app.add_exception_handler(LinkCException, linkc_exception_handler)

    # 注册通用异常处理器
    app.add_exception_handler(Exception, generic_exception_handler)

    # 添加请求上下文中间件
    app.add_middleware(RequestContextMiddleware)

    logger.info("Error handlers registered")


__all__ = [
    "setup_error_handlers",
    "linkc_exception_handler",
    "generic_exception_handler",
    "RequestContextMiddleware",
]
