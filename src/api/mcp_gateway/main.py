"""
MCP Server HTTP API - 主入口
=============================
将M1/M2/M3 MCP Servers包装为统一的HTTP API服务

启动方式:
    uvicorn src.api.mcp_gateway.main:app --reload --port 8000
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from src.shared.auth import get_current_user, TokenPayload
from src.shared.config import get_settings

from .routers import space, task, robot

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("MCP Gateway API starting...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    yield
    logger.info("MCP Gateway API shutting down...")


# 创建FastAPI应用
app = FastAPI(
    title="LinkC MCP Gateway API",
    description="物业机器人协同平台 - MCP服务网关",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if hasattr(settings, 'CORS_ORIGINS') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 健康检查
# ============================================================

@app.get("/health", tags=["System"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "mcp-gateway",
        "version": "1.0.0"
    }


@app.get("/ready", tags=["System"])
async def readiness_check():
    """就绪检查"""
    return {
        "status": "ready",
        "services": {
            "space_manager": "ready",
            "task_manager": "ready",
            "robot_gaoxian": "ready"
        }
    }


# ============================================================
# 注册路由
# ============================================================

app.include_router(
    space.router,
    prefix="/api/v1/mcp/space",
    tags=["M1 - Space Manager"]
)

app.include_router(
    task.router,
    prefix="/api/v1/mcp/task",
    tags=["M2 - Task Manager"]
)

app.include_router(
    robot.router,
    prefix="/api/v1/mcp/robot",
    tags=["M3 - Robot Gaoxian"]
)


# ============================================================
# 错误处理
# ============================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "success": False,
        "error": exc.detail,
        "error_code": f"HTTP_{exc.status_code}"
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.exception("Unhandled exception")
    return {
        "success": False,
        "error": "Internal server error",
        "error_code": "INTERNAL_ERROR"
    }
