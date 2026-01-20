# G2 空间管理API规格书

## 文档信息

| 属性 | 值 |
|-----|-----|
| 模块ID | G2 |
| 模块名称 | 空间管理API (Space API) |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 规格书 |
| 前置依赖 | G1-认证授权, M1-空间MCP |

---

## 1. 模块概述

### 1.1 职责描述

空间管理API负责提供楼宇、楼层、区域的CRUD操作：
1. **楼宇管理**：创建、查询、更新、删除楼宇
2. **楼层管理**：管理楼层及其空间结构
3. **区域管理**：管理清洁区域和点位
4. **地图管理**：上传和管理楼层地图

### 1.2 API端点总览

| 端点 | 方法 | 描述 |
|-----|------|------|
| `/spaces/buildings` | GET/POST | 楼宇列表/创建 |
| `/spaces/buildings/{id}` | GET/PUT/DELETE | 楼宇详情/更新/删除 |
| `/spaces/floors` | GET/POST | 楼层列表/创建 |
| `/spaces/floors/{id}` | GET/PUT/DELETE | 楼层详情/更新/删除 |
| `/spaces/floors/{id}/map` | GET/POST | 楼层地图 |
| `/spaces/zones` | GET/POST | 区域列表/创建 |
| `/spaces/zones/{id}` | GET/PUT/DELETE | 区域详情/更新/删除 |
| `/spaces/zones/{id}/points` | GET/POST | 区域点位 |

---

## 2. 接口定义

### 2.1 楼宇管理接口

#### GET /spaces/buildings

获取楼宇列表。

**查询参数：**
| 参数 | 类型 | 必填 | 描述 |
|-----|------|-----|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| search | string | 否 | 搜索楼宇名称 |

**响应：**
```json
{
  "items": [
    {
      "id": "building-001",
      "name": "新鸿基中心",
      "address": "香港中环皇后大道中99号",
      "floor_count": 25,
      "total_area_sqm": 50000,
      "robot_count": 12,
      "status": "active",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

**所需权限：** `spaces:read`

#### POST /spaces/buildings

创建楼宇。

**请求体：**
```json
{
  "name": "新鸿基中心",
  "address": "香港中环皇后大道中99号",
  "total_area_sqm": 50000,
  "metadata": {
    "property_type": "commercial",
    "year_built": 2010
  }
}
```

**响应：**
```json
{
  "id": "building-001",
  "name": "新鸿基中心",
  "address": "香港中环皇后大道中99号",
  "total_area_sqm": 50000,
  "status": "active",
  "created_at": "2026-01-20T10:00:00Z"
}
```

**所需权限：** `spaces:write`

#### GET /spaces/buildings/{id}

获取楼宇详情。

**响应：**
```json
{
  "id": "building-001",
  "name": "新鸿基中心",
  "address": "香港中环皇后大道中99号",
  "total_area_sqm": 50000,
  "status": "active",
  "metadata": {
    "property_type": "commercial",
    "year_built": 2010
  },
  "floors": [
    {
      "id": "floor-001",
      "name": "1F",
      "floor_number": 1,
      "area_sqm": 2000,
      "zone_count": 5
    }
  ],
  "statistics": {
    "floor_count": 25,
    "zone_count": 100,
    "robot_count": 12,
    "today_tasks": 45
  },
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-15T00:00:00Z"
}
```

### 2.2 楼层管理接口

#### GET /spaces/floors

获取楼层列表。

**查询参数：**
| 参数 | 类型 | 必填 | 描述 |
|-----|------|-----|------|
| building_id | string | 是 | 楼宇ID |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应：**
```json
{
  "items": [
    {
      "id": "floor-001",
      "building_id": "building-001",
      "name": "1F 大堂",
      "floor_number": 1,
      "area_sqm": 2000,
      "zone_count": 5,
      "has_map": true,
      "status": "active"
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 20
}
```

#### POST /spaces/floors

创建楼层。

**请求体：**
```json
{
  "building_id": "building-001",
  "name": "1F 大堂",
  "floor_number": 1,
  "area_sqm": 2000,
  "metadata": {
    "ceiling_height": 5.5,
    "floor_type": "marble"
  }
}
```

#### GET /spaces/floors/{id}/map

获取楼层地图。

**响应：**
```json
{
  "floor_id": "floor-001",
  "map_type": "pgm",
  "resolution": 0.05,
  "width": 1000,
  "height": 800,
  "origin": {"x": -25.0, "y": -20.0},
  "map_url": "https://storage.linkc.com/maps/floor-001.pgm",
  "thumbnail_url": "https://storage.linkc.com/maps/floor-001-thumb.png",
  "updated_at": "2026-01-10T00:00:00Z"
}
```

#### POST /spaces/floors/{id}/map

上传楼层地图。

**请求体：** `multipart/form-data`
| 字段 | 类型 | 描述 |
|-----|------|------|
| map_file | file | PGM/PNG地图文件 |
| resolution | float | 地图分辨率（米/像素） |
| origin_x | float | 原点X坐标 |
| origin_y | float | 原点Y坐标 |

**响应：**
```json
{
  "floor_id": "floor-001",
  "map_url": "https://storage.linkc.com/maps/floor-001.pgm",
  "message": "地图上传成功"
}
```

**所需权限：** `spaces:write`

### 2.3 区域管理接口

#### GET /spaces/zones

获取区域列表。

**查询参数：**
| 参数 | 类型 | 必填 | 描述 |
|-----|------|-----|------|
| floor_id | string | 是 | 楼层ID |
| zone_type | string | 否 | 区域类型筛选 |
| page | int | 否 | 页码 |

**响应：**
```json
{
  "items": [
    {
      "id": "zone-001",
      "floor_id": "floor-001",
      "name": "大堂A区",
      "zone_type": "lobby",
      "area_sqm": 500,
      "priority": "high",
      "cleaning_frequency": "daily",
      "point_count": 10,
      "status": "active"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

#### POST /spaces/zones

创建区域。

**请求体：**
```json
{
  "floor_id": "floor-001",
  "name": "大堂A区",
  "zone_type": "lobby",
  "area_sqm": 500,
  "priority": "high",
  "cleaning_frequency": "daily",
  "boundary": {
    "type": "polygon",
    "coordinates": [[0,0], [10,0], [10,10], [0,10]]
  },
  "metadata": {
    "surface_type": "marble",
    "has_furniture": true
  }
}
```

#### GET /spaces/zones/{id}

获取区域详情。

**响应：**
```json
{
  "id": "zone-001",
  "floor_id": "floor-001",
  "floor_name": "1F 大堂",
  "building_id": "building-001",
  "building_name": "新鸿基中心",
  "name": "大堂A区",
  "zone_type": "lobby",
  "area_sqm": 500,
  "priority": "high",
  "cleaning_frequency": "daily",
  "boundary": {
    "type": "polygon",
    "coordinates": [[0,0], [10,0], [10,10], [0,10]]
  },
  "points": [
    {
      "id": "point-001",
      "name": "入口",
      "x": 5.0,
      "y": 0.5,
      "point_type": "entrance"
    }
  ],
  "last_cleaned_at": "2026-01-20T08:00:00Z",
  "statistics": {
    "total_cleanings": 150,
    "avg_cleaning_time_minutes": 25,
    "coverage_rate": 0.95
  },
  "status": "active",
  "created_at": "2026-01-01T00:00:00Z"
}
```

#### GET /spaces/zones/{id}/points

获取区域内的点位列表。

**响应：**
```json
{
  "items": [
    {
      "id": "point-001",
      "zone_id": "zone-001",
      "name": "入口",
      "x": 5.0,
      "y": 0.5,
      "point_type": "entrance",
      "metadata": {
        "is_charging_station": false
      }
    },
    {
      "id": "point-002",
      "zone_id": "zone-001",
      "name": "充电桩A",
      "x": 8.0,
      "y": 9.0,
      "point_type": "charging",
      "metadata": {
        "is_charging_station": true,
        "charger_type": "standard"
      }
    }
  ],
  "total": 10
}
```

#### POST /spaces/zones/{id}/points

添加点位到区域。

**请求体：**
```json
{
  "name": "清洁起点",
  "x": 2.5,
  "y": 3.0,
  "point_type": "cleaning_start",
  "metadata": {
    "description": "清洁任务默认起点"
  }
}
```

---

## 3. 数据模型

### 3.1 核心模型

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ZoneType(str, Enum):
    LOBBY = "lobby"
    CORRIDOR = "corridor"
    OFFICE = "office"
    RESTROOM = "restroom"
    ELEVATOR = "elevator"
    PARKING = "parking"
    OUTDOOR = "outdoor"
    OTHER = "other"

class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class CleaningFrequency(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"

class PointType(str, Enum):
    ENTRANCE = "entrance"
    CHARGING = "charging"
    CLEANING_START = "cleaning_start"
    CLEANING_END = "cleaning_end"
    WAYPOINT = "waypoint"
    POI = "poi"

class Building(BaseModel):
    id: str
    tenant_id: str
    name: str
    address: Optional[str]
    total_area_sqm: Optional[float]
    metadata: Dict[str, Any] = {}
    status: str = "active"
    created_at: datetime
    updated_at: datetime

class Floor(BaseModel):
    id: str
    building_id: str
    name: str
    floor_number: int
    area_sqm: Optional[float]
    has_map: bool = False
    map_url: Optional[str]
    metadata: Dict[str, Any] = {}
    status: str = "active"
    created_at: datetime
    updated_at: datetime

class Zone(BaseModel):
    id: str
    floor_id: str
    name: str
    zone_type: ZoneType
    area_sqm: Optional[float]
    priority: Priority = Priority.MEDIUM
    cleaning_frequency: CleaningFrequency = CleaningFrequency.DAILY
    boundary: Optional[Dict[str, Any]]  # GeoJSON
    metadata: Dict[str, Any] = {}
    status: str = "active"
    created_at: datetime
    updated_at: datetime

class Point(BaseModel):
    id: str
    zone_id: str
    name: str
    x: float
    y: float
    point_type: PointType
    metadata: Dict[str, Any] = {}
    created_at: datetime
```

### 3.2 请求/响应模型

```python
class BuildingCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: Optional[str] = Field(max_length=500)
    total_area_sqm: Optional[float] = Field(ge=0)
    metadata: Dict[str, Any] = {}

class BuildingUpdate(BaseModel):
    name: Optional[str] = Field(min_length=1, max_length=200)
    address: Optional[str]
    total_area_sqm: Optional[float]
    metadata: Optional[Dict[str, Any]]
    status: Optional[str]

class FloorCreate(BaseModel):
    building_id: str
    name: str = Field(min_length=1, max_length=100)
    floor_number: int
    area_sqm: Optional[float] = Field(ge=0)
    metadata: Dict[str, Any] = {}

class ZoneCreate(BaseModel):
    floor_id: str
    name: str = Field(min_length=1, max_length=100)
    zone_type: ZoneType
    area_sqm: Optional[float] = Field(ge=0)
    priority: Priority = Priority.MEDIUM
    cleaning_frequency: CleaningFrequency = CleaningFrequency.DAILY
    boundary: Optional[Dict[str, Any]]
    metadata: Dict[str, Any] = {}

class PointCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    x: float
    y: float
    point_type: PointType
    metadata: Dict[str, Any] = {}
```

---

## 4. 实现要求

### 4.1 技术栈

- FastAPI
- SQLAlchemy（ORM）
- MinIO/S3（地图文件存储）

### 4.2 路由实现

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List

router = APIRouter(prefix="/spaces", tags=["空间管理"])

# ============ 楼宇 ============

@router.get("/buildings", response_model=PaginatedResponse[BuildingResponse])
async def list_buildings(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    user: User = Depends(require_permission("spaces:read")),
    db: AsyncSession = Depends(get_db)
):
    """获取楼宇列表"""
    query = select(Building).where(Building.tenant_id == user.tenant_id)
    if search:
        query = query.where(Building.name.ilike(f"%{search}%"))
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    items = await db.scalars(
        query.offset((page - 1) * page_size).limit(page_size)
    )
    
    return PaginatedResponse(
        items=[BuildingResponse.from_orm(b) for b in items],
        total=total,
        page=page,
        page_size=page_size
    )

@router.post("/buildings", response_model=BuildingResponse)
async def create_building(
    request: BuildingCreate,
    user: User = Depends(require_permission("spaces:write")),
    db: AsyncSession = Depends(get_db)
):
    """创建楼宇"""
    building = Building(
        id=generate_id("building"),
        tenant_id=user.tenant_id,
        **request.model_dump()
    )
    db.add(building)
    await db.commit()
    return BuildingResponse.from_orm(building)

# ============ 楼层地图 ============

@router.post("/floors/{floor_id}/map")
async def upload_floor_map(
    floor_id: str,
    map_file: UploadFile = File(...),
    resolution: float = 0.05,
    origin_x: float = 0,
    origin_y: float = 0,
    user: User = Depends(require_permission("spaces:write")),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage)
):
    """上传楼层地图"""
    floor = await get_floor_or_404(db, floor_id, user.tenant_id)
    
    # 上传到对象存储
    map_url = await storage.upload_file(
        bucket="maps",
        key=f"{user.tenant_id}/{floor_id}/map.pgm",
        file=map_file
    )
    
    # 更新楼层记录
    floor.has_map = True
    floor.map_url = map_url
    floor.metadata["map_resolution"] = resolution
    floor.metadata["map_origin"] = {"x": origin_x, "y": origin_y}
    await db.commit()
    
    return {"floor_id": floor_id, "map_url": map_url, "message": "地图上传成功"}
```

---

## 5. 测试要求

### 5.1 单元测试用例

```python
@pytest.mark.asyncio
async def test_create_building():
    """测试创建楼宇"""
    response = await client.post("/spaces/buildings", json={
        "name": "测试楼宇",
        "address": "测试地址"
    }, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试楼宇"
    assert "id" in data

@pytest.mark.asyncio
async def test_create_zone_with_boundary():
    """测试创建带边界的区域"""
    response = await client.post("/spaces/zones", json={
        "floor_id": "floor-001",
        "name": "测试区域",
        "zone_type": "lobby",
        "boundary": {
            "type": "polygon",
            "coordinates": [[0,0], [10,0], [10,10], [0,10]]
        }
    }, headers=auth_headers)
    
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_upload_map():
    """测试上传地图"""
    with open("test_map.pgm", "rb") as f:
        response = await client.post(
            "/spaces/floors/floor-001/map",
            files={"map_file": f},
            data={"resolution": 0.05},
            headers=auth_headers
        )
    
    assert response.status_code == 200
```

---

## 6. 验收标准

### 6.1 功能验收

- [ ] 楼宇CRUD操作正常
- [ ] 楼层CRUD操作正常
- [ ] 区域CRUD操作正常
- [ ] 地图上传和获取正常
- [ ] 点位管理正常
- [ ] 租户隔离正确

### 6.2 性能要求

| 指标 | 要求 |
|-----|------|
| 列表查询响应时间 | < 200ms |
| 详情查询响应时间 | < 100ms |
| 地图上传（10MB） | < 5s |

---

*文档版本：1.0*
*更新日期：2026年1月*
