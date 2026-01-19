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
                "floor_number": floor_num,
                "name": f"{floor_num}F",
                "area": 2000.0,
                "created_at": datetime.utcnow().isoformat()
            }
            self._floors[floor["id"]] = floor
        
        # 示例区域
        zones_data = [
            {"id": "zone_001", "floor_id": "floor_001", "name": "1F大堂", "zone_type": "lobby", "area": 500.0, "cleaning_duration": 30},
            {"id": "zone_002", "floor_id": "floor_001", "name": "1F走廊A", "zone_type": "corridor", "area": 200.0, "cleaning_duration": 15},
            {"id": "zone_003", "floor_id": "floor_002", "name": "2F走廊", "zone_type": "corridor", "area": 300.0, "cleaning_duration": 20},
            {"id": "zone_004", "floor_id": "floor_002", "name": "2F洗手间", "zone_type": "restroom", "area": 50.0, "cleaning_duration": 15},
        ]
        for zone_data in zones_data:
            zone = {
                **zone_data,
                "created_at": datetime.utcnow().isoformat()
            }
            self._zones[zone["id"]] = zone
    
    async def get_buildings(self, tenant_id: str) -> list[dict]:
        """获取租户的所有楼宇"""
        return [
            b for b in self._buildings.values()
            if b["tenant_id"] == tenant_id
        ]
    
    async def get_building(self, building_id: str) -> Optional[dict]:
        """获取楼宇详情"""
        return self._buildings.get(building_id)
    
    async def get_floors(self, building_id: str) -> list[dict]:
        """获取楼宇的所有楼层"""
        return [
            f for f in self._floors.values()
            if f["building_id"] == building_id
        ]
    
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
    
    # ============================================================
    # 写操作 (后续实现)
    # ============================================================
    
    async def create_building(self, building: dict) -> dict:
        """创建楼宇"""
        self._buildings[building["id"]] = building
        return building
    
    async def create_floor(self, floor: dict) -> dict:
        """创建楼层"""
        self._floors[floor["id"]] = floor
        return floor
    
    async def create_zone(self, zone: dict) -> dict:
        """创建区域"""
        self._zones[zone["id"]] = zone
        return zone
