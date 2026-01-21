"""
G2: 空间管理API - 业务逻辑
===========================
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from dataclasses import dataclass, field
import uuid
import logging

from .models import (
    EntityStatus, ZoneType, Priority, CleaningFrequency, PointType,
    BuildingCreate, BuildingUpdate, BuildingInDB, BuildingResponse, BuildingDetailResponse,
    FloorCreate, FloorUpdate, FloorInDB, FloorResponse, FloorDetailResponse, FloorSummary, FloorMapResponse,
    ZoneCreate, ZoneUpdate, ZoneInDB, ZoneResponse, ZoneDetailResponse, ZoneSummary,
    PointCreate, PointUpdate, PointInDB, PointResponse
)

logger = logging.getLogger(__name__)


# ============================================================
# 内存存储（测试用）
# ============================================================

class InMemorySpaceStorage:
    """内存空间存储"""

    def __init__(self):
        self.buildings: Dict[str, BuildingInDB] = {}
        self.floors: Dict[str, FloorInDB] = {}
        self.zones: Dict[str, ZoneInDB] = {}
        self.points: Dict[str, PointInDB] = {}
        self._init_default_data()

    def _init_default_data(self):
        """初始化默认数据"""
        now = datetime.now(timezone.utc)

        # 创建默认楼宇
        building = BuildingInDB(
            id="building-001",
            tenant_id="tenant_001",
            name="新鸿基中心",
            address="香港中环皇后大道中99号",
            total_area_sqm=50000,
            metadata={"property_type": "commercial", "year_built": 2010},
            status=EntityStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        self.buildings["building-001"] = building

        # 创建默认楼层
        floor = FloorInDB(
            id="floor-001",
            building_id="building-001",
            tenant_id="tenant_001",
            name="1F 大堂",
            floor_number=1,
            area_sqm=2000,
            has_map=False,
            metadata={"ceiling_height": 5.5, "floor_type": "marble"},
            status=EntityStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        self.floors["floor-001"] = floor

        # 创建默认区域
        zone = ZoneInDB(
            id="zone-001",
            floor_id="floor-001",
            tenant_id="tenant_001",
            name="大堂A区",
            zone_type=ZoneType.LOBBY,
            area_sqm=500,
            priority=Priority.HIGH,
            cleaning_frequency=CleaningFrequency.DAILY,
            boundary={"type": "polygon", "coordinates": [[0, 0], [10, 0], [10, 10], [0, 10]]},
            metadata={"surface_type": "marble", "has_furniture": True},
            status=EntityStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        self.zones["zone-001"] = zone

        # 创建默认点位
        point = PointInDB(
            id="point-001",
            zone_id="zone-001",
            tenant_id="tenant_001",
            name="入口",
            x=5.0,
            y=0.5,
            point_type=PointType.ENTRANCE,
            metadata={},
            created_at=now,
            updated_at=now
        )
        self.points["point-001"] = point


# ============================================================
# 空间服务
# ============================================================

class SpaceService:
    """空间服务"""

    def __init__(self, storage: Optional[InMemorySpaceStorage] = None):
        self.storage = storage or InMemorySpaceStorage()

    # ==================== 楼宇管理 ====================

    async def list_buildings(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取楼宇列表"""
        buildings = [b for b in self.storage.buildings.values()
                     if b.tenant_id == tenant_id and b.status != EntityStatus.DELETED]

        # 搜索过滤
        if search:
            search_lower = search.lower()
            buildings = [b for b in buildings if search_lower in b.name.lower()]

        # 分页
        total = len(buildings)
        start = (page - 1) * page_size
        buildings = buildings[start:start + page_size]

        return {
            "items": [self._building_to_response(b) for b in buildings],
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def create_building(self, tenant_id: str, data: BuildingCreate) -> BuildingResponse:
        """创建楼宇"""
        now = datetime.now(timezone.utc)
        building_id = f"building_{uuid.uuid4().hex[:8]}"

        building = BuildingInDB(
            id=building_id,
            tenant_id=tenant_id,
            name=data.name,
            address=data.address,
            total_area_sqm=data.total_area_sqm,
            metadata=data.metadata,
            status=EntityStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )

        self.storage.buildings[building_id] = building
        return self._building_to_response(building)

    async def get_building(self, building_id: str, tenant_id: str) -> Optional[BuildingDetailResponse]:
        """获取楼宇详情"""
        building = self.storage.buildings.get(building_id)
        if not building or building.tenant_id != tenant_id or building.status == EntityStatus.DELETED:
            return None

        # 获取楼层列表
        floors = [f for f in self.storage.floors.values()
                  if f.building_id == building_id and f.status != EntityStatus.DELETED]

        floor_summaries = []
        for f in floors:
            zone_count = sum(1 for z in self.storage.zones.values()
                             if z.floor_id == f.id and z.status != EntityStatus.DELETED)
            floor_summaries.append(FloorSummary(
                id=f.id,
                name=f.name,
                floor_number=f.floor_number,
                area_sqm=f.area_sqm,
                zone_count=zone_count
            ))

        # 统计信息
        zone_count = sum(s.zone_count for s in floor_summaries)

        return BuildingDetailResponse(
            id=building.id,
            name=building.name,
            address=building.address,
            total_area_sqm=building.total_area_sqm,
            floor_count=len(floors),
            robot_count=0,  # 需要从机器人服务获取
            status=building.status,
            created_at=building.created_at,
            updated_at=building.updated_at,
            metadata=building.metadata,
            floors=floor_summaries,
            statistics={
                "floor_count": len(floors),
                "zone_count": zone_count,
                "robot_count": 0,
                "today_tasks": 0
            }
        )

    async def update_building(
        self,
        building_id: str,
        tenant_id: str,
        data: BuildingUpdate
    ) -> Optional[BuildingResponse]:
        """更新楼宇"""
        building = self.storage.buildings.get(building_id)
        if not building or building.tenant_id != tenant_id or building.status == EntityStatus.DELETED:
            return None

        if data.name is not None:
            building.name = data.name
        if data.address is not None:
            building.address = data.address
        if data.total_area_sqm is not None:
            building.total_area_sqm = data.total_area_sqm
        if data.metadata is not None:
            building.metadata = data.metadata
        if data.status is not None:
            building.status = data.status

        building.updated_at = datetime.now(timezone.utc)
        return self._building_to_response(building)

    async def delete_building(self, building_id: str, tenant_id: str) -> bool:
        """删除楼宇"""
        building = self.storage.buildings.get(building_id)
        if not building or building.tenant_id != tenant_id:
            return False

        # 软删除
        building.status = EntityStatus.DELETED
        building.updated_at = datetime.now(timezone.utc)
        return True

    # ==================== 楼层管理 ====================

    async def list_floors(
        self,
        tenant_id: str,
        building_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取楼层列表"""
        floors = [f for f in self.storage.floors.values()
                  if f.building_id == building_id and f.tenant_id == tenant_id
                  and f.status != EntityStatus.DELETED]

        # 按楼层号排序
        floors.sort(key=lambda f: f.floor_number)

        # 分页
        total = len(floors)
        start = (page - 1) * page_size
        floors = floors[start:start + page_size]

        return {
            "items": [self._floor_to_response(f) for f in floors],
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def create_floor(self, tenant_id: str, data: FloorCreate) -> Optional[FloorResponse]:
        """创建楼层"""
        # 验证楼宇存在
        building = self.storage.buildings.get(data.building_id)
        if not building or building.tenant_id != tenant_id:
            return None

        now = datetime.now(timezone.utc)
        floor_id = f"floor_{uuid.uuid4().hex[:8]}"

        floor = FloorInDB(
            id=floor_id,
            building_id=data.building_id,
            tenant_id=tenant_id,
            name=data.name,
            floor_number=data.floor_number,
            area_sqm=data.area_sqm,
            has_map=False,
            metadata=data.metadata,
            status=EntityStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )

        self.storage.floors[floor_id] = floor
        return self._floor_to_response(floor)

    async def get_floor(self, floor_id: str, tenant_id: str) -> Optional[FloorDetailResponse]:
        """获取楼层详情"""
        floor = self.storage.floors.get(floor_id)
        if not floor or floor.tenant_id != tenant_id or floor.status == EntityStatus.DELETED:
            return None

        building = self.storage.buildings.get(floor.building_id)

        # 获取区域列表
        zones = [z for z in self.storage.zones.values()
                 if z.floor_id == floor_id and z.status != EntityStatus.DELETED]

        zone_summaries = []
        for z in zones:
            point_count = sum(1 for p in self.storage.points.values() if p.zone_id == z.id)
            zone_summaries.append(ZoneSummary(
                id=z.id,
                name=z.name,
                zone_type=z.zone_type,
                priority=z.priority,
                point_count=point_count
            ))

        return FloorDetailResponse(
            id=floor.id,
            building_id=floor.building_id,
            building_name=building.name if building else None,
            name=floor.name,
            floor_number=floor.floor_number,
            area_sqm=floor.area_sqm,
            zone_count=len(zones),
            has_map=floor.has_map,
            map_url=floor.map_url,
            metadata=floor.metadata,
            zones=zone_summaries,
            status=floor.status,
            created_at=floor.created_at
        )

    async def update_floor(
        self,
        floor_id: str,
        tenant_id: str,
        data: FloorUpdate
    ) -> Optional[FloorResponse]:
        """更新楼层"""
        floor = self.storage.floors.get(floor_id)
        if not floor or floor.tenant_id != tenant_id or floor.status == EntityStatus.DELETED:
            return None

        if data.name is not None:
            floor.name = data.name
        if data.floor_number is not None:
            floor.floor_number = data.floor_number
        if data.area_sqm is not None:
            floor.area_sqm = data.area_sqm
        if data.metadata is not None:
            floor.metadata = data.metadata
        if data.status is not None:
            floor.status = data.status

        floor.updated_at = datetime.now(timezone.utc)
        return self._floor_to_response(floor)

    async def delete_floor(self, floor_id: str, tenant_id: str) -> bool:
        """删除楼层"""
        floor = self.storage.floors.get(floor_id)
        if not floor or floor.tenant_id != tenant_id:
            return False

        floor.status = EntityStatus.DELETED
        floor.updated_at = datetime.now(timezone.utc)
        return True

    async def get_floor_map(self, floor_id: str, tenant_id: str) -> Optional[FloorMapResponse]:
        """获取楼层地图"""
        floor = self.storage.floors.get(floor_id)
        if not floor or floor.tenant_id != tenant_id or floor.status == EntityStatus.DELETED:
            return None

        origin = floor.metadata.get("map_origin", {"x": 0, "y": 0})

        return FloorMapResponse(
            floor_id=floor.id,
            map_type="pgm",
            resolution=floor.metadata.get("map_resolution", 0.05),
            origin=origin,
            map_url=floor.map_url,
            updated_at=floor.updated_at
        )

    async def upload_floor_map(
        self,
        floor_id: str,
        tenant_id: str,
        map_url: str,
        resolution: float = 0.05,
        origin_x: float = 0,
        origin_y: float = 0
    ) -> Optional[Dict[str, Any]]:
        """上传楼层地图"""
        floor = self.storage.floors.get(floor_id)
        if not floor or floor.tenant_id != tenant_id or floor.status == EntityStatus.DELETED:
            return None

        floor.has_map = True
        floor.map_url = map_url
        floor.metadata["map_resolution"] = resolution
        floor.metadata["map_origin"] = {"x": origin_x, "y": origin_y}
        floor.updated_at = datetime.now(timezone.utc)

        return {
            "floor_id": floor_id,
            "map_url": map_url,
            "message": "地图上传成功"
        }

    # ==================== 区域管理 ====================

    async def list_zones(
        self,
        tenant_id: str,
        floor_id: str,
        zone_type: Optional[ZoneType] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取区域列表"""
        zones = [z for z in self.storage.zones.values()
                 if z.floor_id == floor_id and z.tenant_id == tenant_id
                 and z.status != EntityStatus.DELETED]

        if zone_type:
            zones = [z for z in zones if z.zone_type == zone_type]

        # 分页
        total = len(zones)
        start = (page - 1) * page_size
        zones = zones[start:start + page_size]

        return {
            "items": [self._zone_to_response(z) for z in zones],
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def create_zone(self, tenant_id: str, data: ZoneCreate) -> Optional[ZoneResponse]:
        """创建区域"""
        # 验证楼层存在
        floor = self.storage.floors.get(data.floor_id)
        if not floor or floor.tenant_id != tenant_id:
            return None

        now = datetime.now(timezone.utc)
        zone_id = f"zone_{uuid.uuid4().hex[:8]}"

        zone = ZoneInDB(
            id=zone_id,
            floor_id=data.floor_id,
            tenant_id=tenant_id,
            name=data.name,
            zone_type=data.zone_type,
            area_sqm=data.area_sqm,
            priority=data.priority,
            cleaning_frequency=data.cleaning_frequency,
            boundary=data.boundary,
            metadata=data.metadata,
            status=EntityStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )

        self.storage.zones[zone_id] = zone
        return self._zone_to_response(zone)

    async def get_zone(self, zone_id: str, tenant_id: str) -> Optional[ZoneDetailResponse]:
        """获取区域详情"""
        zone = self.storage.zones.get(zone_id)
        if not zone or zone.tenant_id != tenant_id or zone.status == EntityStatus.DELETED:
            return None

        floor = self.storage.floors.get(zone.floor_id)
        building = self.storage.buildings.get(floor.building_id) if floor else None

        # 获取点位列表
        points = [p for p in self.storage.points.values() if p.zone_id == zone_id]
        point_responses = [PointResponse(
            id=p.id,
            zone_id=p.zone_id,
            name=p.name,
            x=p.x,
            y=p.y,
            point_type=p.point_type,
            metadata=p.metadata
        ) for p in points]

        return ZoneDetailResponse(
            id=zone.id,
            floor_id=zone.floor_id,
            floor_name=floor.name if floor else None,
            building_id=building.id if building else None,
            building_name=building.name if building else None,
            name=zone.name,
            zone_type=zone.zone_type,
            area_sqm=zone.area_sqm,
            priority=zone.priority,
            cleaning_frequency=zone.cleaning_frequency,
            point_count=len(points),
            boundary=zone.boundary,
            metadata=zone.metadata,
            points=point_responses,
            last_cleaned_at=zone.last_cleaned_at,
            statistics={
                "total_cleanings": 0,
                "avg_cleaning_time_minutes": 0,
                "coverage_rate": 0
            },
            status=zone.status,
            created_at=zone.created_at
        )

    async def update_zone(
        self,
        zone_id: str,
        tenant_id: str,
        data: ZoneUpdate
    ) -> Optional[ZoneResponse]:
        """更新区域"""
        zone = self.storage.zones.get(zone_id)
        if not zone or zone.tenant_id != tenant_id or zone.status == EntityStatus.DELETED:
            return None

        if data.name is not None:
            zone.name = data.name
        if data.zone_type is not None:
            zone.zone_type = data.zone_type
        if data.area_sqm is not None:
            zone.area_sqm = data.area_sqm
        if data.priority is not None:
            zone.priority = data.priority
        if data.cleaning_frequency is not None:
            zone.cleaning_frequency = data.cleaning_frequency
        if data.boundary is not None:
            zone.boundary = data.boundary
        if data.metadata is not None:
            zone.metadata = data.metadata
        if data.status is not None:
            zone.status = data.status

        zone.updated_at = datetime.now(timezone.utc)
        return self._zone_to_response(zone)

    async def delete_zone(self, zone_id: str, tenant_id: str) -> bool:
        """删除区域"""
        zone = self.storage.zones.get(zone_id)
        if not zone or zone.tenant_id != tenant_id:
            return False

        zone.status = EntityStatus.DELETED
        zone.updated_at = datetime.now(timezone.utc)
        return True

    # ==================== 点位管理 ====================

    async def list_points(self, zone_id: str, tenant_id: str) -> Dict[str, Any]:
        """获取点位列表"""
        # 验证区域存在
        zone = self.storage.zones.get(zone_id)
        if not zone or zone.tenant_id != tenant_id:
            return {"items": [], "total": 0}

        points = [p for p in self.storage.points.values() if p.zone_id == zone_id]

        return {
            "items": [PointResponse(
                id=p.id,
                zone_id=p.zone_id,
                name=p.name,
                x=p.x,
                y=p.y,
                point_type=p.point_type,
                metadata=p.metadata
            ) for p in points],
            "total": len(points)
        }

    async def create_point(
        self,
        zone_id: str,
        tenant_id: str,
        data: PointCreate
    ) -> Optional[PointResponse]:
        """创建点位"""
        # 验证区域存在
        zone = self.storage.zones.get(zone_id)
        if not zone or zone.tenant_id != tenant_id:
            return None

        now = datetime.now(timezone.utc)
        point_id = f"point_{uuid.uuid4().hex[:8]}"

        point = PointInDB(
            id=point_id,
            zone_id=zone_id,
            tenant_id=tenant_id,
            name=data.name,
            x=data.x,
            y=data.y,
            point_type=data.point_type,
            metadata=data.metadata,
            created_at=now,
            updated_at=now
        )

        self.storage.points[point_id] = point
        return PointResponse(
            id=point.id,
            zone_id=point.zone_id,
            name=point.name,
            x=point.x,
            y=point.y,
            point_type=point.point_type,
            metadata=point.metadata
        )

    async def delete_point(self, point_id: str, tenant_id: str) -> bool:
        """删除点位"""
        point = self.storage.points.get(point_id)
        if not point or point.tenant_id != tenant_id:
            return False

        del self.storage.points[point_id]
        return True

    # ==================== 辅助方法 ====================

    def _building_to_response(self, building: BuildingInDB) -> BuildingResponse:
        """转换楼宇为响应"""
        floor_count = sum(1 for f in self.storage.floors.values()
                          if f.building_id == building.id and f.status != EntityStatus.DELETED)
        return BuildingResponse(
            id=building.id,
            name=building.name,
            address=building.address,
            total_area_sqm=building.total_area_sqm,
            floor_count=floor_count,
            robot_count=0,
            status=building.status,
            created_at=building.created_at,
            updated_at=building.updated_at
        )

    def _floor_to_response(self, floor: FloorInDB) -> FloorResponse:
        """转换楼层为响应"""
        zone_count = sum(1 for z in self.storage.zones.values()
                         if z.floor_id == floor.id and z.status != EntityStatus.DELETED)
        return FloorResponse(
            id=floor.id,
            building_id=floor.building_id,
            name=floor.name,
            floor_number=floor.floor_number,
            area_sqm=floor.area_sqm,
            zone_count=zone_count,
            has_map=floor.has_map,
            status=floor.status,
            created_at=floor.created_at
        )

    def _zone_to_response(self, zone: ZoneInDB) -> ZoneResponse:
        """转换区域为响应"""
        point_count = sum(1 for p in self.storage.points.values() if p.zone_id == zone.id)
        return ZoneResponse(
            id=zone.id,
            floor_id=zone.floor_id,
            name=zone.name,
            zone_type=zone.zone_type,
            area_sqm=zone.area_sqm,
            priority=zone.priority,
            cleaning_frequency=zone.cleaning_frequency,
            point_count=point_count,
            status=zone.status,
            created_at=zone.created_at
        )
