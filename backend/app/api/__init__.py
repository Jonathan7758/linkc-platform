"""API模块"""
from app.api.energy import router as energy_router
from app.api.alarms import router as alarms_router

__all__ = ["energy_router", "alarms_router"]
