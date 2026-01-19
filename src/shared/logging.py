"""
LinkC Platform - 统一日志系统 (F2)
================================
提供结构化日志、上下文追踪、性能监控。
"""

import sys
import json
import logging
import traceback
from datetime import datetime
from typing import Any, Optional, Dict
from contextvars import ContextVar
from functools import wraps
import time


request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
tenant_id_ctx: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)
user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class JSONFormatter(logging.Formatter):
    """JSON格式日志"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if request_id := request_id_ctx.get():
            log_data["request_id"] = request_id
        if tenant_id := tenant_id_ctx.get():
            log_data["tenant_id"] = tenant_id
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
            }
        return json.dumps(log_data, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """文本格式日志（用于开发环境）"""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
        "RESET": "\033[0m"
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        ctx_parts = []
        if request_id := request_id_ctx.get():
            ctx_parts.append("req=" + request_id[:8])
        if tenant_id := tenant_id_ctx.get():
            ctx_parts.append("tenant=" + tenant_id)
        ctx_str = "[" + " ".join(ctx_parts) + "] " if ctx_parts else ""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = timestamp + " " + color + record.levelname.ljust(8) + reset + " " + record.name + " - " + ctx_str + record.getMessage()
        if record.exc_info:
            msg += "\n" + "".join(traceback.format_exception(*record.exc_info))
        return msg


class LinkCLogger:
    """LinkC平台日志器"""

    def __init__(self, name: str, level: str = "INFO", format_type: str = "json", log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.logger.handlers = []
        formatter = JSONFormatter() if format_type == "json" else TextFormatter()
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(JSONFormatter())
            self.logger.addHandler(file_handler)

    def _log(self, level: int, msg: str, extra_data: Optional[Dict] = None, exc_info=None):
        record = self.logger.makeRecord(self.logger.name, level, "(unknown)", 0, msg, (), exc_info)
        if extra_data:
            record.extra_data = extra_data
        self.logger.handle(record)

    def debug(self, msg: str, **kwargs):
        self._log(logging.DEBUG, msg, kwargs if kwargs else None)

    def info(self, msg: str, **kwargs):
        self._log(logging.INFO, msg, kwargs if kwargs else None)

    def warning(self, msg: str, **kwargs):
        self._log(logging.WARNING, msg, kwargs if kwargs else None)

    def error(self, msg: str, exc_info: bool = False, **kwargs):
        self._log(logging.ERROR, msg, kwargs if kwargs else None, exc_info=sys.exc_info() if exc_info else None)

    def critical(self, msg: str, exc_info: bool = True, **kwargs):
        self._log(logging.CRITICAL, msg, kwargs if kwargs else None, exc_info=sys.exc_info() if exc_info else None)


_loggers: Dict[str, LinkCLogger] = {}


def get_logger(name: str, level: str = "INFO", format_type: str = "text") -> LinkCLogger:
    """获取或创建日志器"""
    if name not in _loggers:
        _loggers[name] = LinkCLogger(name, level, format_type)
    return _loggers[name]


def set_request_context(request_id: Optional[str] = None, tenant_id: Optional[str] = None, user_id: Optional[str] = None):
    """设置请求上下文"""
    if request_id:
        request_id_ctx.set(request_id)
    if tenant_id:
        tenant_id_ctx.set(tenant_id)
    if user_id:
        user_id_ctx.set(user_id)


def clear_request_context():
    """清除请求上下文"""
    request_id_ctx.set(None)
    tenant_id_ctx.set(None)
    user_id_ctx.set(None)


def log_execution_time(logger: Optional[LinkCLogger] = None, level: str = "info"):
    """装饰器：记录函数执行时间"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            _logger = logger or get_logger(func.__module__)
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                getattr(_logger, level)(func.__name__ + " completed", duration_ms=round(elapsed, 2))
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                _logger.error(func.__name__ + " failed: " + str(e), duration_ms=round(elapsed, 2), exc_info=True)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            _logger = logger or get_logger(func.__module__)
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                getattr(_logger, level)(func.__name__ + " completed", duration_ms=round(elapsed, 2))
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                _logger.error(func.__name__ + " failed: " + str(e), duration_ms=round(elapsed, 2), exc_info=True)
                raise

        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


default_logger = get_logger("linkc", "INFO", "text")

__all__ = [
    "LinkCLogger", "get_logger", "set_request_context", "clear_request_context",
    "log_execution_time", "request_id_ctx", "tenant_id_ctx", "user_id_ctx", "default_logger",
]
