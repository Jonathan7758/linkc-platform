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
                "error": f"Building {building_id} not found"
            }
        return {
            "success": True,
            "building": building
        }
    
    async def list_floors(self, building_id: str) -> dict:
        """列出楼宇的所有楼层"""
        floors = await self.storage.get_floors(building_id)
        return {
            "success": True,
            "floors": floors,
            "total": len(floors)
        }
    
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
                "error": f"Zone {zone_id} not found"
            }
        return {
            "success": True,
            "zone": zone
        }
