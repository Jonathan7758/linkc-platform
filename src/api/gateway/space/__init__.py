"""
G2: 空间管理API
===============
提供楼宇、楼层、区域、点位的CRUD管理功能。
"""

from .models import (
    ZoneType, Priority, CleaningFrequency, PointType, EntityStatus,
    BuildingCreate, BuildingUpdate, BuildingResponse, BuildingDetailResponse, BuildingListResponse,
    FloorCreate, FloorUpdate, FloorResponse, FloorDetailResponse, FloorListResponse,
    FloorMapResponse, FloorMapUploadResponse,
    ZoneCreate, ZoneUpdate, ZoneResponse, ZoneDetailResponse, ZoneListResponse,
    PointCreate, PointResponse, PointListResponse,
    MessageResponse
)
from .service import SpaceService, InMemorySpaceStorage
from .router import (
    router,
    get_space_service, set_space_service
)

__all__ = [
    # Enums
    "ZoneType", "Priority", "CleaningFrequency", "PointType", "EntityStatus",
    # Building Models
    "BuildingCreate", "BuildingUpdate", "BuildingResponse", "BuildingDetailResponse", "BuildingListResponse",
    # Floor Models
    "FloorCreate", "FloorUpdate", "FloorResponse", "FloorDetailResponse", "FloorListResponse",
    "FloorMapResponse", "FloorMapUploadResponse",
    # Zone Models
    "ZoneCreate", "ZoneUpdate", "ZoneResponse", "ZoneDetailResponse", "ZoneListResponse",
    # Point Models
    "PointCreate", "PointResponse", "PointListResponse",
    # Common
    "MessageResponse",
    # Service
    "SpaceService", "InMemorySpaceStorage",
    # Router
    "router",
    "get_space_service", "set_space_service",
]
