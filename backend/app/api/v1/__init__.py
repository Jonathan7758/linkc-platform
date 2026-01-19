"""
API v1 模块
"""

from fastapi import APIRouter
from app.api.v1.routers.spaces import router as spaces_router
from app.api.v1.routers.tasks import router as tasks_router
from app.api.v1.routers.robots import router as robots_router
from app.api.v1.routers.agents import router as agents_router
from app.api.v1.routers.websocket import router as ws_router

router = APIRouter()

router.include_router(spaces_router)
router.include_router(tasks_router)
router.include_router(robots_router)
router.include_router(agents_router)
router.include_router(ws_router)
