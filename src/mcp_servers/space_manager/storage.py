"""
M1: 空间管理 MCP Server - 存储层
================================
目前使用内存存储，后续接入数据库。
"""

from typing import Optional
from datetime import datetime


class SpaceStorage:
    """空间数据存储"""

    def __init__(self):
        # 内存存储 - 后续替换为数据库
        self._buildings: dict[str, dict] = {}
        self._floors: dict[str, dict] = {}
        self._zones: dict[str, dict] = {}
        self._points: dict[str, dict] = {}

        # 初始化示例数据
        self._init_sample_data()

    def _init_sample_data(self):
        """初始化示例数据"""
        tenant_id = "tenant_001"

        # 示例楼宇
        building = {
            "id": "building_001",
            "tenant_id": tenant_id,
            "name": "港湾中心A座",
            "code": "HK-A",
            "address": "香港九龙湾宏开道1号",
            "total_floors": 25,
            "total_area": 50000.0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        self._buildings[building["id"]] = building

        # 示例楼层
        for floor_num in range(1, 4):
            floor = {
                "id": f"floor_{floor_num:03d}",
                "building_id": "building_001",
                "tenant_id": tenant_id,
                "floor_number": floor_num,
                "level": floor_num,
                "name": f"{floor_num}F",
                "area": 2000.0,
                "height": 3.5,
                "map_file": None,
                "map_scale": 1.0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            self._floors[floor["id"]] = floor

        # 示例区域
        zones_data = [
            {"id": "zone_001", "floor_id": "floor_001", "name": "1F大堂", "code": "Z001", "zone_type": "lobby", "area": 500.0, "cleaning_duration": 30, "cleanable": True, "clean_priority": 8},
            {"id": "zone_002", "floor_id": "floor_001", "name": "1F走廊A", "code": "Z002", "zone_type": "corridor", "area": 200.0, "cleaning_duration": 15, "cleanable": True, "clean_priority": 5},
            {"id": "zone_003", "floor_id": "floor_002", "name": "2F走廊", "code": "Z003", "zone_type": "corridor", "area": 300.0, "cleaning_duration": 20, "cleanable": True, "clean_priority": 5},
            {"id": "zone_004", "floor_id": "floor_002", "name": "2F洗手间", "code": "Z004", "zone_type": "restroom", "area": 50.0, "cleaning_duration": 15, "cleanable": True, "clean_priority": 9},
        ]
        for zone_data in zones_data:
            zone = {
                **zone_data,
                "building_id": "building_001",
                "tenant_id": tenant_id,
                "clean_frequency": "daily",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            self._zones[zone["id"]] = zone

        # 示例点位
        points_data = [
            {"id": "point_001", "zone_id": "zone_001", "floor_id": "floor_001", "name": "1F充电站A", "code": "P001", "point_type": "charging", "x": 10.0, "y": 5.0},
            {"id": "point_002", "zone_id": "zone_001", "floor_id": "floor_001", "name": "1F入口", "code": "P002", "point_type": "entrance", "x": 0.0, "y": 0.0},
            {"id": "point_003", "zone_id": "zone_002", "floor_id": "floor_001", "name": "1F路径点1", "code": "P003", "point_type": "waypoint", "x": 15.0, "y": 10.0},
            {"id": "point_004", "zone_id": "zone_003", "floor_id": "floor_002", "name": "2F充电站", "code": "P004", "point_type": "charging", "x": 20.0, "y": 8.0},
        ]
        for point_data in points_data:
            point = {
                **point_data,
                "building_id": "building_001",
                "tenant_id": tenant_id,
                "heading": 0.0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            self._points[point["id"]] = point

    # ============================================================
    # Building 操作
    # ============================================================

    async def get_buildings(self, tenant_id: str) -> list[dict]:
        """获取租户的所有楼宇"""
        return [
            b for b in self._buildings.values()
            if b["tenant_id"] == tenant_id
        ]

    async def get_building(self, building_id: str) -> Optional[dict]:
        """获取楼宇详情"""
        return self._buildings.get(building_id)

    async def create_building(self, building: dict) -> dict:
        """创建楼宇"""
        self._buildings[building["id"]] = building
        return building

    # ============================================================
    # Floor 操作
    # ============================================================

    async def get_floors(self, building_id: str) -> list[dict]:
        """获取楼宇的所有楼层"""
        return [
            f for f in self._floors.values()
            if f["building_id"] == building_id
        ]

    async def get_floor(self, floor_id: str) -> Optional[dict]:
        """获取楼层详情"""
        return self._floors.get(floor_id)

    async def create_floor(self, floor: dict) -> dict:
        """创建楼层"""
        self._floors[floor["id"]] = floor
        return floor

    # ============================================================
    # Zone 操作
    # ============================================================

    async def get_zones(
        self,
        floor_id: Optional[str] = None,
        building_id: Optional[str] = None,
        zone_type: Optional[str] = None
    ) -> list[dict]:
        """获取区域列表"""
        zones = list(self._zones.values())

        if floor_id:
            zones = [z for z in zones if z["floor_id"] == floor_id]

        if building_id:
            floor_ids = [f["id"] for f in self._floors.values() if f["building_id"] == building_id]
            zones = [z for z in zones if z["floor_id"] in floor_ids]

        if zone_type:
            zones = [z for z in zones if z["zone_type"] == zone_type]

        return zones

    async def get_zone(self, zone_id: str) -> Optional[dict]:
        """获取区域详情"""
        return self._zones.get(zone_id)

    async def create_zone(self, zone: dict) -> dict:
        """创建区域"""
        self._zones[zone["id"]] = zone
        return zone

    async def update_zone(self, zone_id: str, updates: dict) -> Optional[dict]:
        """更新区域"""
        zone = self._zones.get(zone_id)
        if not zone:
            return None

        # 更新允许的字段
        allowed_fields = [
            "name", "zone_type", "area", "cleanable",
            "clean_priority", "clean_frequency", "cleaning_duration"
        ]
        for field in allowed_fields:
            if field in updates and updates[field] is not None:
                zone[field] = updates[field]

        zone["updated_at"] = datetime.utcnow().isoformat()
        self._zones[zone_id] = zone
        return zone

    # ============================================================
    # Point 操作
    # ============================================================

    async def get_points(
        self,
        zone_id: Optional[str] = None,
        floor_id: Optional[str] = None,
        point_type: Optional[str] = None
    ) -> list[dict]:
        """获取点位列表"""
        points = list(self._points.values())

        if zone_id:
            points = [p for p in points if p["zone_id"] == zone_id]

        if floor_id:
            points = [p for p in points if p["floor_id"] == floor_id]

        if point_type:
            points = [p for p in points if p["point_type"] == point_type]

        return points

    async def get_point(self, point_id: str) -> Optional[dict]:
        """获取点位详情"""
        return self._points.get(point_id)

    async def create_point(self, point: dict) -> dict:
        """创建点位"""
        self._points[point["id"]] = point
        return point
