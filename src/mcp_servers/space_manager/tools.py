"""
M1: 空间管理 MCP Server - Tool 实现
===================================
"""

from typing import Optional
from src.mcp_servers.space_manager.storage import SpaceStorage


class SpaceManagerTools:
    """空间管理 Tool 实现"""

    def __init__(self, storage: SpaceStorage):
        self.storage = storage

    # ============================================================
    # Building Tools
    # ============================================================

    async def list_buildings(self, tenant_id: str) -> dict:
        """列出所有楼宇"""
        buildings = await self.storage.get_buildings(tenant_id)
        return {
            "success": True,
            "buildings": buildings,
            "total": len(buildings)
        }

    async def get_building(self, building_id: str) -> dict:
        """获取楼宇详情"""
        building = await self.storage.get_building(building_id)
        if not building:
            return {
                "success": False,
                "error": f"Building {building_id} not found",
                "error_code": "NOT_FOUND"
            }
        return {
            "success": True,
            "building": building
        }

    # ============================================================
    # Floor Tools
    # ============================================================

    async def list_floors(self, building_id: str) -> dict:
        """列出楼宇的所有楼层"""
        floors = await self.storage.get_floors(building_id)
        return {
            "success": True,
            "floors": floors,
            "total": len(floors)
        }

    async def get_floor(self, floor_id: str) -> dict:
        """获取楼层详情"""
        floor = await self.storage.get_floor(floor_id)
        if not floor:
            return {
                "success": False,
                "error": f"Floor {floor_id} not found",
                "error_code": "NOT_FOUND"
            }
        return {
            "success": True,
            "floor": floor
        }

    # ============================================================
    # Zone Tools
    # ============================================================

    async def list_zones(
        self,
        floor_id: Optional[str] = None,
        building_id: Optional[str] = None,
        zone_type: Optional[str] = None
    ) -> dict:
        """列出区域"""
        zones = await self.storage.get_zones(
            floor_id=floor_id,
            building_id=building_id,
            zone_type=zone_type
        )
        return {
            "success": True,
            "zones": zones,
            "total": len(zones)
        }

    async def get_zone(self, zone_id: str) -> dict:
        """获取区域详情"""
        zone = await self.storage.get_zone(zone_id)
        if not zone:
            return {
                "success": False,
                "error": f"Zone {zone_id} not found",
                "error_code": "NOT_FOUND"
            }
        return {
            "success": True,
            "zone": zone
        }

    async def update_zone(
        self,
        zone_id: str,
        name: Optional[str] = None,
        zone_type: Optional[str] = None,
        cleanable: Optional[bool] = None,
        clean_priority: Optional[int] = None,
        clean_frequency: Optional[str] = None
    ) -> dict:
        """更新区域信息"""
        # 验证 clean_priority 范围
        if clean_priority is not None and (clean_priority < 1 or clean_priority > 10):
            return {
                "success": False,
                "error": "clean_priority must be between 1 and 10",
                "error_code": "VALIDATION_ERROR"
            }

        # 验证 clean_frequency 值
        valid_frequencies = ["hourly", "daily", "weekly"]
        if clean_frequency is not None and clean_frequency not in valid_frequencies:
            return {
                "success": False,
                "error": f"clean_frequency must be one of: {valid_frequencies}",
                "error_code": "VALIDATION_ERROR"
            }

        updates = {
            "name": name,
            "zone_type": zone_type,
            "cleanable": cleanable,
            "clean_priority": clean_priority,
            "clean_frequency": clean_frequency
        }

        zone = await self.storage.update_zone(zone_id, updates)
        if not zone:
            return {
                "success": False,
                "error": f"Zone {zone_id} not found",
                "error_code": "NOT_FOUND"
            }

        return {
            "success": True,
            "zone": zone
        }

    # ============================================================
    # Point Tools
    # ============================================================

    async def list_points(
        self,
        zone_id: Optional[str] = None,
        floor_id: Optional[str] = None,
        point_type: Optional[str] = None
    ) -> dict:
        """列出点位（query_points）"""
        points = await self.storage.get_points(
            zone_id=zone_id,
            floor_id=floor_id,
            point_type=point_type
        )
        return {
            "success": True,
            "points": points,
            "total": len(points)
        }
