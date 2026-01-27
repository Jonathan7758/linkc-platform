"""
API Routes
"""

from .federation import router as federation_router
from .capabilities import router as capabilities_router

__all__ = ["federation_router", "capabilities_router"]
