"""
G2: 空间管理API - 路由定义
===========================
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Optional

from .models import (
    ZoneType,
    BuildingCreate, BuildingUpdate, BuildingResponse, BuildingDetailResponse, BuildingListResponse,
    FloorCreate, FloorUpdate, FloorResponse, FloorDetailResponse, FloorListResponse,
    FloorMapResponse, FloorMapUploadResponse,
    ZoneCreate, ZoneUpdate, ZoneResponse, ZoneDetailResponse, ZoneListResponse,
    PointCreate, PointResponse, PointListResponse,
    MessageResponse
)
from .service import SpaceService

# 导入认证依赖
import sys
sys.path.insert(0, str(__file__).replace("space/router.py", ""))
try:
    from auth.router import require_permission, get_current_user
    from auth.models import CurrentUser
except ImportError:
    # 测试时的模拟依赖
    from typing import Any
    class CurrentUser:
        id: str = "user-admin"
        tenant_id: str = "tenant_001"

    def get_current_user():
        return CurrentUser()

    def require_permission(perm: str):
        def dep():
            return CurrentUser()
        return dep


# ============================================================
# 路由器和依赖
# ============================================================

router = APIRouter(prefix="/spaces", tags=["空间管理"])

# 全局服务实例
_space_service: Optional[SpaceService] = None


def get_space_service() -> SpaceService:
    """获取空间服务"""
    global _space_service
    if _space_service is None:
        _space_service = SpaceService()
    return _space_service


def set_space_service(service: SpaceService):
    """设置空间服务（测试用）"""
    global _space_service
    _space_service = service


# ============================================================
# 楼宇管理接口
# ============================================================

@router.get("/buildings", response_model=BuildingListResponse)
async def list_buildings(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    current_user: CurrentUser = Depends(require_permission("spaces:read")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    获取楼宇列表

    支持分页和搜索。
    """
    result = await space_service.list_buildings(
        tenant_id=current_user.tenant_id,
        page=page,
        page_size=page_size,
        search=search
    )
    return BuildingListResponse(**result)


@router.post("/buildings", response_model=BuildingResponse, status_code=status.HTTP_201_CREATED)
async def create_building(
    request: BuildingCreate,
    current_user: CurrentUser = Depends(require_permission("spaces:write")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    创建楼宇
    """
    return await space_service.create_building(
        tenant_id=current_user.tenant_id,
        data=request
    )


@router.get("/buildings/{building_id}", response_model=BuildingDetailResponse)
async def get_building(
    building_id: str,
    current_user: CurrentUser = Depends(require_permission("spaces:read")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    获取楼宇详情
    """
    building = await space_service.get_building(building_id, current_user.tenant_id)
    if not building:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="楼宇不存在"
        )
    return building


@router.put("/buildings/{building_id}", response_model=BuildingResponse)
async def update_building(
    building_id: str,
    request: BuildingUpdate,
    current_user: CurrentUser = Depends(require_permission("spaces:write")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    更新楼宇信息
    """
    building = await space_service.update_building(
        building_id=building_id,
        tenant_id=current_user.tenant_id,
        data=request
    )
    if not building:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="楼宇不存在"
        )
    return building


@router.delete("/buildings/{building_id}", response_model=MessageResponse)
async def delete_building(
    building_id: str,
    current_user: CurrentUser = Depends(require_permission("spaces:write")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    删除楼宇
    """
    success = await space_service.delete_building(building_id, current_user.tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="楼宇不存在"
        )
    return MessageResponse(message="楼宇已删除")


# ============================================================
# 楼层管理接口
# ============================================================

@router.get("/floors", response_model=FloorListResponse)
async def list_floors(
    building_id: str,
    page: int = 1,
    page_size: int = 20,
    current_user: CurrentUser = Depends(require_permission("spaces:read")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    获取楼层列表

    需要指定楼宇ID。
    """
    result = await space_service.list_floors(
        tenant_id=current_user.tenant_id,
        building_id=building_id,
        page=page,
        page_size=page_size
    )
    return FloorListResponse(**result)


@router.post("/floors", response_model=FloorResponse, status_code=status.HTTP_201_CREATED)
async def create_floor(
    request: FloorCreate,
    current_user: CurrentUser = Depends(require_permission("spaces:write")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    创建楼层
    """
    floor = await space_service.create_floor(
        tenant_id=current_user.tenant_id,
        data=request
    )
    if not floor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="楼宇不存在"
        )
    return floor


@router.get("/floors/{floor_id}", response_model=FloorDetailResponse)
async def get_floor(
    floor_id: str,
    current_user: CurrentUser = Depends(require_permission("spaces:read")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    获取楼层详情
    """
    floor = await space_service.get_floor(floor_id, current_user.tenant_id)
    if not floor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="楼层不存在"
        )
    return floor


@router.put("/floors/{floor_id}", response_model=FloorResponse)
async def update_floor(
    floor_id: str,
    request: FloorUpdate,
    current_user: CurrentUser = Depends(require_permission("spaces:write")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    更新楼层信息
    """
    floor = await space_service.update_floor(
        floor_id=floor_id,
        tenant_id=current_user.tenant_id,
        data=request
    )
    if not floor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="楼层不存在"
        )
    return floor


@router.delete("/floors/{floor_id}", response_model=MessageResponse)
async def delete_floor(
    floor_id: str,
    current_user: CurrentUser = Depends(require_permission("spaces:write")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    删除楼层
    """
    success = await space_service.delete_floor(floor_id, current_user.tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="楼层不存在"
        )
    return MessageResponse(message="楼层已删除")


@router.get("/floors/{floor_id}/map", response_model=FloorMapResponse)
async def get_floor_map(
    floor_id: str,
    current_user: CurrentUser = Depends(require_permission("spaces:read")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    获取楼层地图
    """
    map_info = await space_service.get_floor_map(floor_id, current_user.tenant_id)
    if not map_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="楼层不存在"
        )
    return map_info


@router.post("/floors/{floor_id}/map", response_model=FloorMapUploadResponse)
async def upload_floor_map(
    floor_id: str,
    map_file: UploadFile = File(...),
    resolution: float = Form(default=0.05),
    origin_x: float = Form(default=0),
    origin_y: float = Form(default=0),
    current_user: CurrentUser = Depends(require_permission("spaces:write")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    上传楼层地图

    支持PGM/PNG格式。
    """
    # 简化实现：直接使用文件名作为URL
    # 生产环境应上传到对象存储
    map_url = f"https://storage.ecis-robot.local/maps/{current_user.tenant_id}/{floor_id}/map.pgm"

    result = await space_service.upload_floor_map(
        floor_id=floor_id,
        tenant_id=current_user.tenant_id,
        map_url=map_url,
        resolution=resolution,
        origin_x=origin_x,
        origin_y=origin_y
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="楼层不存在"
        )
    return FloorMapUploadResponse(**result)


# ============================================================
# 区域管理接口
# ============================================================

@router.get("/zones", response_model=ZoneListResponse)
async def list_zones(
    floor_id: str,
    zone_type: Optional[ZoneType] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: CurrentUser = Depends(require_permission("spaces:read")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    获取区域列表

    需要指定楼层ID。
    """
    result = await space_service.list_zones(
        tenant_id=current_user.tenant_id,
        floor_id=floor_id,
        zone_type=zone_type,
        page=page,
        page_size=page_size
    )
    return ZoneListResponse(**result)


@router.post("/zones", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_zone(
    request: ZoneCreate,
    current_user: CurrentUser = Depends(require_permission("spaces:write")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    创建区域
    """
    zone = await space_service.create_zone(
        tenant_id=current_user.tenant_id,
        data=request
    )
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="楼层不存在"
        )
    return zone


@router.get("/zones/{zone_id}", response_model=ZoneDetailResponse)
async def get_zone(
    zone_id: str,
    current_user: CurrentUser = Depends(require_permission("spaces:read")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    获取区域详情
    """
    zone = await space_service.get_zone(zone_id, current_user.tenant_id)
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="区域不存在"
        )
    return zone


@router.put("/zones/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    zone_id: str,
    request: ZoneUpdate,
    current_user: CurrentUser = Depends(require_permission("spaces:write")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    更新区域信息
    """
    zone = await space_service.update_zone(
        zone_id=zone_id,
        tenant_id=current_user.tenant_id,
        data=request
    )
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="区域不存在"
        )
    return zone


@router.delete("/zones/{zone_id}", response_model=MessageResponse)
async def delete_zone(
    zone_id: str,
    current_user: CurrentUser = Depends(require_permission("spaces:write")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    删除区域
    """
    success = await space_service.delete_zone(zone_id, current_user.tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="区域不存在"
        )
    return MessageResponse(message="区域已删除")


@router.get("/zones/{zone_id}/points", response_model=PointListResponse)
async def list_points(
    zone_id: str,
    current_user: CurrentUser = Depends(require_permission("spaces:read")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    获取区域内的点位列表
    """
    result = await space_service.list_points(zone_id, current_user.tenant_id)
    return PointListResponse(**result)


@router.post("/zones/{zone_id}/points", response_model=PointResponse, status_code=status.HTTP_201_CREATED)
async def create_point(
    zone_id: str,
    request: PointCreate,
    current_user: CurrentUser = Depends(require_permission("spaces:write")),
    space_service: SpaceService = Depends(get_space_service)
):
    """
    添加点位到区域
    """
    point = await space_service.create_point(
        zone_id=zone_id,
        tenant_id=current_user.tenant_id,
        data=request
    )
    if not point:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="区域不存在"
        )
    return point
