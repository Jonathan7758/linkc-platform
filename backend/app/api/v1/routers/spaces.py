"""
G1: 空间管理 API (简化版 - 内置数据)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/spaces", tags=["spaces"])

# 内置示例数据
BUILDINGS = {
    "building_001": {
        "id": "building_001", "tenant_id": "tenant_001", "name": "港湾中心A座",
        "address": "香港九龙湾宏开道1号", "total_floors": 25, "total_area": 50000.0
    }
}

FLOORS = {
    "floor_001": {"id": "floor_001", "building_id": "building_001", "floor_number": 1, "name": "1F"},
    "floor_002": {"id": "floor_002", "building_id": "building_001", "floor_number": 2, "name": "2F"},
    "floor_003": {"id": "floor_003", "building_id": "building_001", "floor_number": 3, "name": "3F"},
}

ZONES = {
    "zone_001": {"id": "zone_001", "floor_id": "floor_001", "name": "1F大堂", "zone_type": "lobby", "area": 500.0},
    "zone_002": {"id": "zone_002", "floor_id": "floor_001", "name": "1F走廊A", "zone_type": "corridor", "area": 200.0},
    "zone_003": {"id": "zone_003", "floor_id": "floor_002", "name": "2F走廊", "zone_type": "corridor", "area": 300.0},
    "zone_004": {"id": "zone_004", "floor_id": "floor_002", "name": "2F洗手间", "zone_type": "restroom", "area": 50.0},
}

@router.get("/buildings")
async def list_buildings(tenant_id: str = Query(...)):
    buildings = [b for b in BUILDINGS.values() if b["tenant_id"] == tenant_id]
    return {"success": True, "buildings": buildings, "total": len(buildings)}

@router.get("/buildings/{building_id}")
async def get_building(building_id: str):
    if building_id not in BUILDINGS:
        raise HTTPException(status_code=404, detail="Building not found")
    return {"success": True, "building": BUILDINGS[building_id]}

@router.get("/buildings/{building_id}/floors")
async def list_floors(building_id: str):
    floors = [f for f in FLOORS.values() if f["building_id"] == building_id]
    return {"success": True, "floors": floors, "total": len(floors)}

@router.get("/zones")
async def list_zones(floor_id: Optional[str] = None, building_id: Optional[str] = None, zone_type: Optional[str] = None):
    zones = list(ZONES.values())
    if floor_id:
        zones = [z for z in zones if z["floor_id"] == floor_id]
    if building_id:
        floor_ids = [f["id"] for f in FLOORS.values() if f["building_id"] == building_id]
        zones = [z for z in zones if z["floor_id"] in floor_ids]
    if zone_type:
        zones = [z for z in zones if z["zone_type"] == zone_type]
    return {"success": True, "zones": zones, "total": len(zones)}

@router.get("/zones/{zone_id}")
async def get_zone(zone_id: str):
    if zone_id not in ZONES:
        raise HTTPException(status_code=404, detail="Zone not found")
    return {"success": True, "zone": ZONES[zone_id]}
