"""
API v1 路由模块
"""

from app.api.v1.routers.spaces import router as spaces_router
from app.api.v1.routers.tasks import router as tasks_router
from app.api.v1.routers.robots import router as robots_router
from app.api.v1.routers.agents import router as agents_router
from app.api.v1.routers.websocket import router as ws_router

__all__ = ["spaces_router", "tasks_router", "robots_router", "agents_router", "ws_router"]
