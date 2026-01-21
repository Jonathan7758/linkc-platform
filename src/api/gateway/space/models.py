"""
G2: 空间管理API - 数据模型
===========================
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# 枚举类型
# ============================================================

class ZoneType(str, Enum):
    """区域类型"""
    LOBBY = "lobby"
    CORRIDOR = "corridor"
    OFFICE = "office"
    RESTROOM = "restroom"
    ELEVATOR = "elevator"
    PARKING = "parking"
    OUTDOOR = "outdoor"
    OTHER = "other"


class Priority(str, Enum):
    """优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CleaningFrequency(str, Enum):
    """清洁频率"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class PointType(str, Enum):
    """点位类型"""
    ENTRANCE = "entrance"
    CHARGING = "charging"
    CLEANING_START = "cleaning_start"
    CLEANING_END = "cleaning_end"
    WAYPOINT = "waypoint"
    POI = "poi"


class EntityStatus(str, Enum):
    """实体状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


# ============================================================
# 楼宇模型
# ============================================================

class BuildingBase(BaseModel):
    """楼宇基础模型"""
    name: str = Field(min_length=1, max_length=200)
    address: Optional[str] = Field(default=None, max_length=500)
    total_area_sqm: Optional[float] = Field(default=None, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BuildingCreate(BuildingBase):
    """创建楼宇请求"""
    pass


class BuildingUpdate(BaseModel):
    """更新楼宇请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    address: Optional[str] = None
    total_area_sqm: Optional[float] = Field(default=None, ge=0)
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[EntityStatus] = None


class BuildingInDB(BuildingBase):
    """数据库中的楼宇"""
    id: str
    tenant_id: str
    status: EntityStatus = EntityStatus.ACTIVE
    created_at: datetime
    updated_at: datetime


class BuildingResponse(BaseModel):
    """楼宇响应"""
    id: str
    name: str
    address: Optional[str] = None
    total_area_sqm: Optional[float] = None
    floor_count: int = 0
    robot_count: int = 0
    status: EntityStatus
    created_at: datetime
    updated_at: Optional[datetime] = None


class BuildingDetailResponse(BuildingResponse):
    """楼宇详情响应"""
    metadata: Dict[str, Any] = {}
    floors: List["FloorSummary"] = []
    statistics: Dict[str, Any] = {}


class BuildingListResponse(BaseModel):
    """楼宇列表响应"""
    items: List[BuildingResponse]
    total: int
    page: int
    page_size: int


# ============================================================
# 楼层模型
# ============================================================

class FloorBase(BaseModel):
    """楼层基础模型"""
    name: str = Field(min_length=1, max_length=100)
    floor_number: int
    area_sqm: Optional[float] = Field(default=None, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FloorCreate(FloorBase):
    """创建楼层请求"""
    building_id: str


class FloorUpdate(BaseModel):
    """更新楼层请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    floor_number: Optional[int] = None
    area_sqm: Optional[float] = Field(default=None, ge=0)
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[EntityStatus] = None


class FloorInDB(FloorBase):
    """数据库中的楼层"""
    id: str
    building_id: str
    tenant_id: str
    has_map: bool = False
    map_url: Optional[str] = None
    status: EntityStatus = EntityStatus.ACTIVE
    created_at: datetime
    updated_at: datetime


class FloorSummary(BaseModel):
    """楼层摘要"""
    id: str
    name: str
    floor_number: int
    area_sqm: Optional[float] = None
    zone_count: int = 0


class FloorResponse(BaseModel):
    """楼层响应"""
    id: str
    building_id: str
    name: str
    floor_number: int
    area_sqm: Optional[float] = None
    zone_count: int = 0
    has_map: bool = False
    status: EntityStatus
    created_at: datetime


class FloorDetailResponse(FloorResponse):
    """楼层详情响应"""
    building_name: Optional[str] = None
    map_url: Optional[str] = None
    metadata: Dict[str, Any] = {}
    zones: List["ZoneSummary"] = []


class FloorListResponse(BaseModel):
    """楼层列表响应"""
    items: List[FloorResponse]
    total: int
    page: int
    page_size: int


class FloorMapResponse(BaseModel):
    """楼层地图响应"""
    floor_id: str
    map_type: str = "pgm"
    resolution: float = 0.05
    width: Optional[int] = None
    height: Optional[int] = None
    origin: Optional[Dict[str, float]] = None
    map_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    updated_at: Optional[datetime] = None


class FloorMapUploadResponse(BaseModel):
    """地图上传响应"""
    floor_id: str
    map_url: str
    message: str


# ============================================================
# 区域模型
# ============================================================

class ZoneBase(BaseModel):
    """区域基础模型"""
    name: str = Field(min_length=1, max_length=100)
    zone_type: ZoneType
    area_sqm: Optional[float] = Field(default=None, ge=0)
    priority: Priority = Priority.MEDIUM
    cleaning_frequency: CleaningFrequency = CleaningFrequency.DAILY
    boundary: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ZoneCreate(ZoneBase):
    """创建区域请求"""
    floor_id: str


class ZoneUpdate(BaseModel):
    """更新区域请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    zone_type: Optional[ZoneType] = None
    area_sqm: Optional[float] = Field(default=None, ge=0)
    priority: Optional[Priority] = None
    cleaning_frequency: Optional[CleaningFrequency] = None
    boundary: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[EntityStatus] = None


class ZoneInDB(ZoneBase):
    """数据库中的区域"""
    id: str
    floor_id: str
    tenant_id: str
    status: EntityStatus = EntityStatus.ACTIVE
    last_cleaned_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ZoneSummary(BaseModel):
    """区域摘要"""
    id: str
    name: str
    zone_type: ZoneType
    priority: Priority
    point_count: int = 0


class ZoneResponse(BaseModel):
    """区域响应"""
    id: str
    floor_id: str
    name: str
    zone_type: ZoneType
    area_sqm: Optional[float] = None
    priority: Priority
    cleaning_frequency: CleaningFrequency
    point_count: int = 0
    status: EntityStatus
    created_at: datetime


class ZoneDetailResponse(ZoneResponse):
    """区域详情响应"""
    floor_name: Optional[str] = None
    building_id: Optional[str] = None
    building_name: Optional[str] = None
    boundary: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}
    points: List["PointResponse"] = []
    last_cleaned_at: Optional[datetime] = None
    statistics: Dict[str, Any] = {}


class ZoneListResponse(BaseModel):
    """区域列表响应"""
    items: List[ZoneResponse]
    total: int
    page: int
    page_size: int


# ============================================================
# 点位模型
# ============================================================

class PointBase(BaseModel):
    """点位基础模型"""
    name: str = Field(min_length=1, max_length=100)
    x: float
    y: float
    point_type: PointType
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PointCreate(PointBase):
    """创建点位请求"""
    pass


class PointUpdate(BaseModel):
    """更新点位请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    x: Optional[float] = None
    y: Optional[float] = None
    point_type: Optional[PointType] = None
    metadata: Optional[Dict[str, Any]] = None


class PointInDB(PointBase):
    """数据库中的点位"""
    id: str
    zone_id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime


class PointResponse(BaseModel):
    """点位响应"""
    id: str
    zone_id: str
    name: str
    x: float
    y: float
    point_type: PointType
    metadata: Dict[str, Any] = {}


class PointListResponse(BaseModel):
    """点位列表响应"""
    items: List[PointResponse]
    total: int


# ============================================================
# 通用响应
# ============================================================

class MessageResponse(BaseModel):
    """消息响应"""
    message: str


# 更新前向引用
BuildingDetailResponse.model_rebuild()
FloorDetailResponse.model_rebuild()
ZoneDetailResponse.model_rebuild()
