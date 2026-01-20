# M1: 空间管理 MCP Server 规格书

## 文档信息

| 属性 | 值 |
|-----|-----|
| 模块ID | M1 |
| 模块名称 | 空间管理 MCP Server |
| 版本 | 1.0 |
| 日期 | 2026-01 |
| 状态 | 规格完成 |
| 前置依赖 | F1-数据模型, F2-共享工具, F3-配置管理 |

---

## 1. 模块概述

### 1.1 职责描述

空间管理 MCP Server 负责管理物业空间的层级结构数据，包括楼宇(Building)、楼层(Floor)、区域(Zone)和关键点(Point)。为其他模块和Agent提供空间查询、导航计算和区域管理能力。

### 1.2 核心功能

| 功能 | 描述 | 优先级 |
|-----|------|-------|
| 空间层级管理 | 楼宇→楼层→区域→点的CRUD操作 | P0 |
| 空间查询 | 按条件查询空间实体 | P0 |
| 层级导航 | 获取空间的父级/子级关系 | P0 |
| 地图数据管理 | 管理楼层平面图和导航地图 | P1 |
| 覆盖率计算 | 计算区域清洁覆盖率 | P1 |
| 路径规划支持 | 提供点间距离和路径查询 | P2 |

### 1.3 设计原则

1. **层级一致性**: 严格维护空间层级关系的完整性
2. **查询高效**: 支持多维度高效查询
3. **地图兼容**: 支持多种地图格式和坐标系
4. **扩展友好**: 支持自定义空间属性扩展

---

## 2. 数据模型

### 2.1 核心实体

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class SpaceType(str, Enum):
    """空间类型"""
    BUILDING = "building"
    FLOOR = "floor"
    ZONE = "zone"
    POINT = "point"

class ZoneCategory(str, Enum):
    """区域分类"""
    LOBBY = "lobby"           # 大堂
    CORRIDOR = "corridor"     # 走廊
    OFFICE = "office"         # 办公室
    MEETING = "meeting"       # 会议室
    RESTROOM = "restroom"     # 洗手间
    ELEVATOR = "elevator"     # 电梯厅
    STAIRWAY = "stairway"     # 楼梯间
    PARKING = "parking"       # 停车场
    COMMON = "common"         # 公共区域
    RESTRICTED = "restricted" # 限制区域
    OTHER = "other"           # 其他

class PointType(str, Enum):
    """点位类型"""
    CHARGING = "charging"     # 充电站
    WAYPOINT = "waypoint"     # 路径点
    ENTRANCE = "entrance"     # 入口
    EXIT = "exit"             # 出口
    LANDMARK = "landmark"     # 地标
    OBSTACLE = "obstacle"     # 障碍物

class Coordinate(BaseModel):
    """坐标"""
    x: float = Field(..., description="X坐标(米)")
    y: float = Field(..., description="Y坐标(米)")
    z: Optional[float] = Field(None, description="Z坐标(米)，用于多层")

class BoundingBox(BaseModel):
    """边界框"""
    min_x: float
    min_y: float
    max_x: float
    max_y: float

class Polygon(BaseModel):
    """多边形区域"""
    vertices: List[Coordinate] = Field(..., description="顶点列表，顺时针排列")
    
    def area(self) -> float:
        """计算面积(平方米)"""
        # Shoelace formula
        n = len(self.vertices)
        if n < 3:
            return 0.0
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += self.vertices[i].x * self.vertices[j].y
            area -= self.vertices[j].x * self.vertices[i].y
        return abs(area) / 2.0

# ============ 楼宇 Building ============

class BuildingBase(BaseModel):
    """楼宇基础信息"""
    name: str = Field(..., description="楼宇名称")
    code: str = Field(..., description="楼宇编码")
    address: Optional[str] = Field(None, description="地址")
    total_floors: int = Field(..., ge=1, description="总楼层数")
    total_area: Optional[float] = Field(None, ge=0, description="总面积(平方米)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展属性")

class BuildingCreate(BuildingBase):
    """创建楼宇"""
    pass

class BuildingUpdate(BaseModel):
    """更新楼宇"""
    name: Optional[str] = None
    address: Optional[str] = None
    total_floors: Optional[int] = None
    total_area: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class Building(BuildingBase):
    """楼宇实体"""
    id: str = Field(..., description="楼宇ID")
    tenant_id: str = Field(..., description="租户ID")
    created_at: datetime
    updated_at: datetime
    floor_count: int = Field(0, description="已录入楼层数")
    
    class Config:
        from_attributes = True

# ============ 楼层 Floor ============

class FloorBase(BaseModel):
    """楼层基础信息"""
    name: str = Field(..., description="楼层名称，如'1F', 'B1'")
    level: int = Field(..., description="楼层序号，地下为负数")
    area: Optional[float] = Field(None, ge=0, description="楼层面积(平方米)")
    height: Optional[float] = Field(None, ge=0, description="层高(米)")
    map_file: Optional[str] = Field(None, description="地图文件路径")
    map_scale: Optional[float] = Field(1.0, description="地图比例(像素/米)")
    map_origin: Optional[Coordinate] = Field(None, description="地图原点坐标")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FloorCreate(FloorBase):
    """创建楼层"""
    building_id: str = Field(..., description="所属楼宇ID")

class FloorUpdate(BaseModel):
    """更新楼层"""
    name: Optional[str] = None
    area: Optional[float] = None
    height: Optional[float] = None
    map_file: Optional[str] = None
    map_scale: Optional[float] = None
    map_origin: Optional[Coordinate] = None
    metadata: Optional[Dict[str, Any]] = None

class Floor(FloorBase):
    """楼层实体"""
    id: str = Field(..., description="楼层ID")
    building_id: str = Field(..., description="所属楼宇ID")
    tenant_id: str = Field(..., description="租户ID")
    created_at: datetime
    updated_at: datetime
    zone_count: int = Field(0, description="区域数量")
    
    class Config:
        from_attributes = True

# ============ 区域 Zone ============

class ZoneBase(BaseModel):
    """区域基础信息"""
    name: str = Field(..., description="区域名称")
    code: str = Field(..., description="区域编码")
    category: ZoneCategory = Field(..., description="区域分类")
    boundary: Polygon = Field(..., description="区域边界")
    cleanable: bool = Field(True, description="是否可清洁")
    clean_priority: int = Field(5, ge=1, le=10, description="清洁优先级1-10")
    clean_frequency: str = Field("daily", description="清洁频率: hourly/daily/weekly")
    estimated_clean_time: Optional[int] = Field(None, description="预计清洁时间(分钟)")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ZoneCreate(ZoneBase):
    """创建区域"""
    floor_id: str = Field(..., description="所属楼层ID")

class ZoneUpdate(BaseModel):
    """更新区域"""
    name: Optional[str] = None
    category: Optional[ZoneCategory] = None
    boundary: Optional[Polygon] = None
    cleanable: Optional[bool] = None
    clean_priority: Optional[int] = None
    clean_frequency: Optional[str] = None
    estimated_clean_time: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class Zone(ZoneBase):
    """区域实体"""
    id: str = Field(..., description="区域ID")
    floor_id: str = Field(..., description="所属楼层ID")
    building_id: str = Field(..., description="所属楼宇ID")
    tenant_id: str = Field(..., description="租户ID")
    area: float = Field(..., description="面积(平方米)")
    created_at: datetime
    updated_at: datetime
    point_count: int = Field(0, description="点位数量")
    
    class Config:
        from_attributes = True

# ============ 点位 Point ============

class PointBase(BaseModel):
    """点位基础信息"""
    name: str = Field(..., description="点位名称")
    code: str = Field(..., description="点位编码")
    point_type: PointType = Field(..., description="点位类型")
    position: Coordinate = Field(..., description="点位坐标")
    heading: Optional[float] = Field(None, ge=0, lt=360, description="朝向角度")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PointCreate(PointBase):
    """创建点位"""
    zone_id: str = Field(..., description="所属区域ID")

class PointUpdate(BaseModel):
    """更新点位"""
    name: Optional[str] = None
    point_type: Optional[PointType] = None
    position: Optional[Coordinate] = None
    heading: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class Point(PointBase):
    """点位实体"""
    id: str = Field(..., description="点位ID")
    zone_id: str = Field(..., description="所属区域ID")
    floor_id: str = Field(..., description="所属楼层ID")
    building_id: str = Field(..., description="所属楼宇ID")
    tenant_id: str = Field(..., description="租户ID")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### 2.2 查询模型

```python
class SpaceQuery(BaseModel):
    """空间查询参数"""
    building_id: Optional[str] = None
    floor_id: Optional[str] = None
    zone_id: Optional[str] = None
    category: Optional[ZoneCategory] = None
    cleanable: Optional[bool] = None
    keyword: Optional[str] = Field(None, description="名称/编码关键字")
    bbox: Optional[BoundingBox] = Field(None, description="范围查询")
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class SpaceHierarchy(BaseModel):
    """空间层级结构"""
    building: Building
    floors: List[Floor]
    zones_by_floor: Dict[str, List[Zone]]  # floor_id -> zones
    points_by_zone: Dict[str, List[Point]]  # zone_id -> points

class CoverageInfo(BaseModel):
    """覆盖率信息"""
    zone_id: str
    zone_name: str
    total_area: float
    cleaned_area: float
    coverage_rate: float  # 0.0 - 1.0
    last_cleaned_at: Optional[datetime] = None
```

---

## 3. MCP Tools 定义

### 3.1 Tool 清单

| Tool名称 | 功能 | 输入 | 输出 |
|---------|------|------|------|
| list_buildings | 获取楼宇列表 | 查询参数 | 楼宇列表 |
| get_building | 获取楼宇详情 | building_id | 楼宇信息 |
| create_building | 创建楼宇 | 楼宇数据 | 新楼宇 |
| update_building | 更新楼宇 | building_id, 更新数据 | 更新后楼宇 |
| delete_building | 删除楼宇 | building_id | 删除结果 |
| list_floors | 获取楼层列表 | building_id, 查询参数 | 楼层列表 |
| get_floor | 获取楼层详情 | floor_id | 楼层信息 |
| create_floor | 创建楼层 | 楼层数据 | 新楼层 |
| update_floor | 更新楼层 | floor_id, 更新数据 | 更新后楼层 |
| delete_floor | 删除楼层 | floor_id | 删除结果 |
| list_zones | 获取区域列表 | floor_id, 查询参数 | 区域列表 |
| get_zone | 获取区域详情 | zone_id | 区域信息 |
| create_zone | 创建区域 | 区域数据 | 新区域 |
| update_zone | 更新区域 | zone_id, 更新数据 | 更新后区域 |
| delete_zone | 删除区域 | zone_id | 删除结果 |
| list_points | 获取点位列表 | zone_id, 查询参数 | 点位列表 |
| get_point | 获取点位详情 | point_id | 点位信息 |
| create_point | 创建点位 | 点位数据 | 新点位 |
| update_point | 更新点位 | point_id, 更新数据 | 更新后点位 |
| delete_point | 删除点位 | point_id | 删除结果 |
| get_space_hierarchy | 获取空间层级结构 | building_id | 完整层级 |
| find_nearest_point | 查找最近点位 | 坐标, 点位类型 | 最近点位 |
| calculate_distance | 计算两点距离 | 起点, 终点 | 距离信息 |
| get_zone_coverage | 获取区域覆盖率 | zone_id, 时间范围 | 覆盖率 |

### 3.2 Tool 实现

```python
from mcp.server import Server
from mcp.types import Tool, TextContent
import json

app = Server("space-manager")

# ============ 楼宇 Tools ============

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_buildings",
            description="获取楼宇列表",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "名称关键字"},
                    "limit": {"type": "integer", "default": 100},
                    "offset": {"type": "integer", "default": 0}
                }
            }
        ),
        Tool(
            name="get_building",
            description="获取楼宇详情",
            inputSchema={
                "type": "object",
                "properties": {
                    "building_id": {"type": "string", "description": "楼宇ID"}
                },
                "required": ["building_id"]
            }
        ),
        Tool(
            name="create_building",
            description="创建新楼宇",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "楼宇名称"},
                    "code": {"type": "string", "description": "楼宇编码"},
                    "address": {"type": "string", "description": "地址"},
                    "total_floors": {"type": "integer", "description": "总楼层数"},
                    "total_area": {"type": "number", "description": "总面积"}
                },
                "required": ["name", "code", "total_floors"]
            }
        ),
        Tool(
            name="update_building",
            description="更新楼宇信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "building_id": {"type": "string"},
                    "name": {"type": "string"},
                    "address": {"type": "string"},
                    "total_floors": {"type": "integer"},
                    "total_area": {"type": "number"}
                },
                "required": ["building_id"]
            }
        ),
        Tool(
            name="delete_building",
            description="删除楼宇",
            inputSchema={
                "type": "object",
                "properties": {
                    "building_id": {"type": "string"}
                },
                "required": ["building_id"]
            }
        ),
        
        # ============ 楼层 Tools ============
        Tool(
            name="list_floors",
            description="获取楼宇的楼层列表",
            inputSchema={
                "type": "object",
                "properties": {
                    "building_id": {"type": "string", "description": "楼宇ID"},
                    "limit": {"type": "integer", "default": 100},
                    "offset": {"type": "integer", "default": 0}
                },
                "required": ["building_id"]
            }
        ),
        Tool(
            name="get_floor",
            description="获取楼层详情",
            inputSchema={
                "type": "object",
                "properties": {
                    "floor_id": {"type": "string"}
                },
                "required": ["floor_id"]
            }
        ),
        Tool(
            name="create_floor",
            description="创建新楼层",
            inputSchema={
                "type": "object",
                "properties": {
                    "building_id": {"type": "string"},
                    "name": {"type": "string", "description": "楼层名称如'1F'"},
                    "level": {"type": "integer", "description": "楼层序号"},
                    "area": {"type": "number"},
                    "height": {"type": "number"}
                },
                "required": ["building_id", "name", "level"]
            }
        ),
        Tool(
            name="update_floor",
            description="更新楼层信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "floor_id": {"type": "string"},
                    "name": {"type": "string"},
                    "area": {"type": "number"},
                    "height": {"type": "number"},
                    "map_file": {"type": "string"},
                    "map_scale": {"type": "number"}
                },
                "required": ["floor_id"]
            }
        ),
        Tool(
            name="delete_floor",
            description="删除楼层",
            inputSchema={
                "type": "object",
                "properties": {
                    "floor_id": {"type": "string"}
                },
                "required": ["floor_id"]
            }
        ),
        
        # ============ 区域 Tools ============
        Tool(
            name="list_zones",
            description="获取楼层的区域列表",
            inputSchema={
                "type": "object",
                "properties": {
                    "floor_id": {"type": "string"},
                    "category": {"type": "string", "description": "区域分类"},
                    "cleanable": {"type": "boolean"},
                    "limit": {"type": "integer", "default": 100},
                    "offset": {"type": "integer", "default": 0}
                },
                "required": ["floor_id"]
            }
        ),
        Tool(
            name="get_zone",
            description="获取区域详情",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string"}
                },
                "required": ["zone_id"]
            }
        ),
        Tool(
            name="create_zone",
            description="创建新区域",
            inputSchema={
                "type": "object",
                "properties": {
                    "floor_id": {"type": "string"},
                    "name": {"type": "string"},
                    "code": {"type": "string"},
                    "category": {"type": "string"},
                    "boundary": {
                        "type": "object",
                        "properties": {
                            "vertices": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "x": {"type": "number"},
                                        "y": {"type": "number"}
                                    }
                                }
                            }
                        }
                    },
                    "cleanable": {"type": "boolean", "default": True},
                    "clean_priority": {"type": "integer", "default": 5}
                },
                "required": ["floor_id", "name", "code", "category", "boundary"]
            }
        ),
        Tool(
            name="update_zone",
            description="更新区域信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string"},
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "cleanable": {"type": "boolean"},
                    "clean_priority": {"type": "integer"},
                    "clean_frequency": {"type": "string"}
                },
                "required": ["zone_id"]
            }
        ),
        Tool(
            name="delete_zone",
            description="删除区域",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string"}
                },
                "required": ["zone_id"]
            }
        ),
        
        # ============ 点位 Tools ============
        Tool(
            name="list_points",
            description="获取区域的点位列表",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string"},
                    "point_type": {"type": "string"},
                    "limit": {"type": "integer", "default": 100}
                },
                "required": ["zone_id"]
            }
        ),
        Tool(
            name="get_point",
            description="获取点位详情",
            inputSchema={
                "type": "object",
                "properties": {
                    "point_id": {"type": "string"}
                },
                "required": ["point_id"]
            }
        ),
        Tool(
            name="create_point",
            description="创建新点位",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string"},
                    "name": {"type": "string"},
                    "code": {"type": "string"},
                    "point_type": {"type": "string"},
                    "position": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"}
                        }
                    },
                    "heading": {"type": "number"}
                },
                "required": ["zone_id", "name", "code", "point_type", "position"]
            }
        ),
        Tool(
            name="update_point",
            description="更新点位信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "point_id": {"type": "string"},
                    "name": {"type": "string"},
                    "point_type": {"type": "string"},
                    "position": {"type": "object"},
                    "heading": {"type": "number"}
                },
                "required": ["point_id"]
            }
        ),
        Tool(
            name="delete_point",
            description="删除点位",
            inputSchema={
                "type": "object",
                "properties": {
                    "point_id": {"type": "string"}
                },
                "required": ["point_id"]
            }
        ),
        
        # ============ 高级查询 Tools ============
        Tool(
            name="get_space_hierarchy",
            description="获取楼宇完整空间层级结构",
            inputSchema={
                "type": "object",
                "properties": {
                    "building_id": {"type": "string"}
                },
                "required": ["building_id"]
            }
        ),
        Tool(
            name="find_nearest_point",
            description="查找最近的指定类型点位",
            inputSchema={
                "type": "object",
                "properties": {
                    "floor_id": {"type": "string"},
                    "position": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"}
                        }
                    },
                    "point_type": {"type": "string", "description": "点位类型如charging"},
                    "max_distance": {"type": "number", "description": "最大搜索距离(米)"}
                },
                "required": ["floor_id", "position", "point_type"]
            }
        ),
        Tool(
            name="calculate_distance",
            description="计算两点之间的距离",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_point": {
                        "type": "object",
                        "properties": {"x": {"type": "number"}, "y": {"type": "number"}}
                    },
                    "to_point": {
                        "type": "object",
                        "properties": {"x": {"type": "number"}, "y": {"type": "number"}}
                    }
                },
                "required": ["from_point", "to_point"]
            }
        ),
        Tool(
            name="get_zone_coverage",
            description="获取区域清洁覆盖率",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string"},
                    "start_time": {"type": "string", "description": "ISO时间"},
                    "end_time": {"type": "string", "description": "ISO时间"}
                },
                "required": ["zone_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Tool调用路由"""
    
    handlers = {
        "list_buildings": handle_list_buildings,
        "get_building": handle_get_building,
        "create_building": handle_create_building,
        "update_building": handle_update_building,
        "delete_building": handle_delete_building,
        "list_floors": handle_list_floors,
        "get_floor": handle_get_floor,
        "create_floor": handle_create_floor,
        "update_floor": handle_update_floor,
        "delete_floor": handle_delete_floor,
        "list_zones": handle_list_zones,
        "get_zone": handle_get_zone,
        "create_zone": handle_create_zone,
        "update_zone": handle_update_zone,
        "delete_zone": handle_delete_zone,
        "list_points": handle_list_points,
        "get_point": handle_get_point,
        "create_point": handle_create_point,
        "update_point": handle_update_point,
        "delete_point": handle_delete_point,
        "get_space_hierarchy": handle_get_space_hierarchy,
        "find_nearest_point": handle_find_nearest_point,
        "calculate_distance": handle_calculate_distance,
        "get_zone_coverage": handle_get_zone_coverage,
    }
    
    handler = handlers.get(name)
    if not handler:
        return [TextContent(type="text", text=json.dumps({
            "error": f"Unknown tool: {name}"
        }))]
    
    try:
        result = await handler(arguments)
        return [TextContent(type="text", text=json.dumps(result, default=str))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({
            "error": str(e),
            "error_type": type(e).__name__
        }))]
```

### 3.3 Handler 实现示例

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any
import math

# 数据库服务注入（实际实现中通过依赖注入）
db_service = None  # type: DatabaseService

async def handle_list_buildings(args: dict) -> Dict[str, Any]:
    """获取楼宇列表"""
    keyword = args.get("keyword")
    limit = args.get("limit", 100)
    offset = args.get("offset", 0)
    
    async with db_service.session() as session:
        query = select(BuildingModel)
        
        if keyword:
            query = query.where(
                BuildingModel.name.ilike(f"%{keyword}%") |
                BuildingModel.code.ilike(f"%{keyword}%")
            )
        
        query = query.offset(offset).limit(limit)
        result = await session.execute(query)
        buildings = result.scalars().all()
        
        # 获取总数
        count_query = select(func.count(BuildingModel.id))
        if keyword:
            count_query = count_query.where(
                BuildingModel.name.ilike(f"%{keyword}%") |
                BuildingModel.code.ilike(f"%{keyword}%")
            )
        total = await session.scalar(count_query)
        
        return {
            "buildings": [b.to_dict() for b in buildings],
            "total": total,
            "limit": limit,
            "offset": offset
        }


async def handle_get_building(args: dict) -> Dict[str, Any]:
    """获取楼宇详情"""
    building_id = args["building_id"]
    
    async with db_service.session() as session:
        building = await session.get(BuildingModel, building_id)
        if not building:
            raise ValueError(f"Building not found: {building_id}")
        
        # 获取楼层数量
        floor_count = await session.scalar(
            select(func.count(FloorModel.id))
            .where(FloorModel.building_id == building_id)
        )
        
        result = building.to_dict()
        result["floor_count"] = floor_count
        return result


async def handle_create_building(args: dict) -> Dict[str, Any]:
    """创建楼宇"""
    building_data = BuildingCreate(**args)
    
    async with db_service.session() as session:
        building = BuildingModel(
            id=generate_id(),
            tenant_id=get_current_tenant_id(),
            **building_data.model_dump()
        )
        session.add(building)
        await session.commit()
        await session.refresh(building)
        
        return building.to_dict()


async def handle_get_space_hierarchy(args: dict) -> Dict[str, Any]:
    """获取完整空间层级结构"""
    building_id = args["building_id"]
    
    async with db_service.session() as session:
        # 获取楼宇
        building = await session.get(BuildingModel, building_id)
        if not building:
            raise ValueError(f"Building not found: {building_id}")
        
        # 获取所有楼层
        floors_result = await session.execute(
            select(FloorModel)
            .where(FloorModel.building_id == building_id)
            .order_by(FloorModel.level)
        )
        floors = floors_result.scalars().all()
        
        # 获取所有区域
        zones_result = await session.execute(
            select(ZoneModel)
            .where(ZoneModel.building_id == building_id)
        )
        zones = zones_result.scalars().all()
        
        # 获取所有点位
        points_result = await session.execute(
            select(PointModel)
            .where(PointModel.building_id == building_id)
        )
        points = points_result.scalars().all()
        
        # 组织层级结构
        zones_by_floor = {}
        for zone in zones:
            if zone.floor_id not in zones_by_floor:
                zones_by_floor[zone.floor_id] = []
            zones_by_floor[zone.floor_id].append(zone.to_dict())
        
        points_by_zone = {}
        for point in points:
            if point.zone_id not in points_by_zone:
                points_by_zone[point.zone_id] = []
            points_by_zone[point.zone_id].append(point.to_dict())
        
        return {
            "building": building.to_dict(),
            "floors": [f.to_dict() for f in floors],
            "zones_by_floor": zones_by_floor,
            "points_by_zone": points_by_zone
        }


async def handle_find_nearest_point(args: dict) -> Dict[str, Any]:
    """查找最近的指定类型点位"""
    floor_id = args["floor_id"]
    position = args["position"]
    point_type = args["point_type"]
    max_distance = args.get("max_distance", 100.0)  # 默认100米
    
    async with db_service.session() as session:
        # 获取该楼层所有指定类型的点位
        points_result = await session.execute(
            select(PointModel)
            .where(PointModel.floor_id == floor_id)
            .where(PointModel.point_type == point_type)
        )
        points = points_result.scalars().all()
        
        if not points:
            return {"nearest": None, "distance": None, "message": "No points found"}
        
        # 计算距离找最近的
        nearest = None
        min_distance = float('inf')
        
        for point in points:
            dx = point.position_x - position["x"]
            dy = point.position_y - position["y"]
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                nearest = point
        
        if nearest is None:
            return {
                "nearest": None, 
                "distance": None, 
                "message": f"No points within {max_distance}m"
            }
        
        return {
            "nearest": nearest.to_dict(),
            "distance": round(min_distance, 2)
        }


async def handle_calculate_distance(args: dict) -> Dict[str, Any]:
    """计算两点距离"""
    from_point = args["from_point"]
    to_point = args["to_point"]
    
    dx = to_point["x"] - from_point["x"]
    dy = to_point["y"] - from_point["y"]
    distance = math.sqrt(dx*dx + dy*dy)
    
    return {
        "distance": round(distance, 2),
        "unit": "meters",
        "from": from_point,
        "to": to_point
    }


async def handle_get_zone_coverage(args: dict) -> Dict[str, Any]:
    """获取区域覆盖率"""
    zone_id = args["zone_id"]
    start_time = args.get("start_time")
    end_time = args.get("end_time")
    
    async with db_service.session() as session:
        # 获取区域信息
        zone = await session.get(ZoneModel, zone_id)
        if not zone:
            raise ValueError(f"Zone not found: {zone_id}")
        
        # 从数据层查询清洁覆盖数据
        # 这里简化处理，实际需要调用D3数据查询服务
        coverage_data = await data_query_service.get_coverage(
            zone_id=zone_id,
            start_time=start_time,
            end_time=end_time
        )
        
        return {
            "zone_id": zone_id,
            "zone_name": zone.name,
            "total_area": zone.area,
            "cleaned_area": coverage_data.get("cleaned_area", 0),
            "coverage_rate": coverage_data.get("coverage_rate", 0),
            "last_cleaned_at": coverage_data.get("last_cleaned_at")
        }
```

---

## 4. 错误处理

### 4.1 错误类型

```python
class SpaceError(Exception):
    """空间管理基础异常"""
    pass

class BuildingNotFoundError(SpaceError):
    """楼宇不存在"""
    def __init__(self, building_id: str):
        super().__init__(f"Building not found: {building_id}")
        self.building_id = building_id

class FloorNotFoundError(SpaceError):
    """楼层不存在"""
    def __init__(self, floor_id: str):
        super().__init__(f"Floor not found: {floor_id}")
        self.floor_id = floor_id

class ZoneNotFoundError(SpaceError):
    """区域不存在"""
    def __init__(self, zone_id: str):
        super().__init__(f"Zone not found: {zone_id}")
        self.zone_id = zone_id

class PointNotFoundError(SpaceError):
    """点位不存在"""
    def __init__(self, point_id: str):
        super().__init__(f"Point not found: {point_id}")
        self.point_id = point_id

class InvalidBoundaryError(SpaceError):
    """无效的区域边界"""
    def __init__(self, message: str):
        super().__init__(f"Invalid boundary: {message}")

class HierarchyViolationError(SpaceError):
    """层级关系违规"""
    def __init__(self, message: str):
        super().__init__(f"Hierarchy violation: {message}")

class DuplicateCodeError(SpaceError):
    """编码重复"""
    def __init__(self, code: str, entity_type: str):
        super().__init__(f"Duplicate {entity_type} code: {code}")
        self.code = code
        self.entity_type = entity_type
```

### 4.2 错误响应格式

```python
class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    error_type: str
    details: Optional[Dict[str, Any]] = None
    
# 示例错误响应
{
    "error": "Building not found: bld_123",
    "error_type": "BuildingNotFoundError",
    "details": {
        "building_id": "bld_123"
    }
}
```

---

## 5. 测试要求

### 5.1 单元测试

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_db_service():
    """Mock数据库服务"""
    service = AsyncMock()
    return service

@pytest.mark.asyncio
async def test_list_buildings(mock_db_service):
    """测试获取楼宇列表"""
    # 准备测试数据
    mock_buildings = [
        {"id": "bld_1", "name": "A栋", "code": "A"},
        {"id": "bld_2", "name": "B栋", "code": "B"}
    ]
    mock_db_service.list_buildings.return_value = mock_buildings
    
    # 执行测试
    result = await handle_list_buildings({"limit": 10})
    
    # 验证结果
    assert len(result["buildings"]) == 2
    assert result["buildings"][0]["name"] == "A栋"

@pytest.mark.asyncio
async def test_get_building_not_found(mock_db_service):
    """测试获取不存在的楼宇"""
    mock_db_service.get_building.return_value = None
    
    with pytest.raises(BuildingNotFoundError):
        await handle_get_building({"building_id": "not_exist"})

@pytest.mark.asyncio
async def test_create_zone_invalid_boundary():
    """测试创建无效边界的区域"""
    invalid_args = {
        "floor_id": "floor_1",
        "name": "测试区域",
        "code": "TEST",
        "category": "office",
        "boundary": {"vertices": [{"x": 0, "y": 0}]}  # 只有一个点
    }
    
    with pytest.raises(InvalidBoundaryError):
        await handle_create_zone(invalid_args)

@pytest.mark.asyncio
async def test_find_nearest_point():
    """测试查找最近点位"""
    result = await handle_find_nearest_point({
        "floor_id": "floor_1",
        "position": {"x": 10, "y": 10},
        "point_type": "charging",
        "max_distance": 50
    })
    
    assert result["nearest"] is not None or result["message"] is not None

@pytest.mark.asyncio
async def test_calculate_distance():
    """测试距离计算"""
    result = await handle_calculate_distance({
        "from_point": {"x": 0, "y": 0},
        "to_point": {"x": 3, "y": 4}
    })
    
    assert result["distance"] == 5.0
    assert result["unit"] == "meters"
```

### 5.2 集成测试

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_space_hierarchy():
    """测试完整空间层级操作"""
    # 1. 创建楼宇
    building = await handle_create_building({
        "name": "测试楼宇",
        "code": "TEST",
        "total_floors": 3
    })
    building_id = building["id"]
    
    # 2. 创建楼层
    floor = await handle_create_floor({
        "building_id": building_id,
        "name": "1F",
        "level": 1,
        "area": 1000
    })
    floor_id = floor["id"]
    
    # 3. 创建区域
    zone = await handle_create_zone({
        "floor_id": floor_id,
        "name": "大堂",
        "code": "LOBBY",
        "category": "lobby",
        "boundary": {
            "vertices": [
                {"x": 0, "y": 0},
                {"x": 20, "y": 0},
                {"x": 20, "y": 15},
                {"x": 0, "y": 15}
            ]
        }
    })
    zone_id = zone["id"]
    
    # 4. 创建点位
    point = await handle_create_point({
        "zone_id": zone_id,
        "name": "充电站1",
        "code": "CHG1",
        "point_type": "charging",
        "position": {"x": 5, "y": 5}
    })
    
    # 5. 获取层级结构
    hierarchy = await handle_get_space_hierarchy({
        "building_id": building_id
    })
    
    assert hierarchy["building"]["id"] == building_id
    assert len(hierarchy["floors"]) == 1
    assert floor_id in hierarchy["zones_by_floor"]
    assert zone_id in hierarchy["points_by_zone"]
    
    # 6. 清理测试数据
    await handle_delete_building({"building_id": building_id})
```

---

## 6. 性能要求

| 指标 | 要求 | 说明 |
|-----|------|------|
| 查询响应时间 | < 100ms | 单条记录查询 |
| 列表响应时间 | < 500ms | 100条记录以内 |
| 层级结构查询 | < 1s | 完整楼宇层级 |
| 最近点查询 | < 200ms | 单楼层范围内 |
| 并发支持 | 100 QPS | 读操作 |

---

## 7. 文件结构

```
src/mcp_servers/space_manager/
├── __init__.py
├── server.py              # MCP Server入口
├── tools.py               # Tool定义
├── handlers/
│   ├── __init__.py
│   ├── building.py        # 楼宇处理器
│   ├── floor.py           # 楼层处理器
│   ├── zone.py            # 区域处理器
│   ├── point.py           # 点位处理器
│   └── query.py           # 高级查询处理器
├── models/
│   ├── __init__.py
│   └── db_models.py       # 数据库模型
├── services/
│   ├── __init__.py
│   ├── database.py        # 数据库服务
│   └── geometry.py        # 几何计算服务
├── exceptions.py          # 异常定义
└── tests/
    ├── __init__.py
    ├── test_tools.py      # Tool测试
    ├── test_handlers.py   # Handler测试
    └── test_integration.py # 集成测试
```

---

## 8. 验收标准

### 8.1 功能验收

- [ ] 楼宇CRUD操作正常
- [ ] 楼层CRUD操作正常
- [ ] 区域CRUD操作正常，面积自动计算
- [ ] 点位CRUD操作正常
- [ ] 空间层级结构查询正确
- [ ] 最近点位查找功能正常
- [ ] 距离计算准确
- [ ] 覆盖率查询功能正常
- [ ] 层级关系完整性校验
- [ ] 编码唯一性校验

### 8.2 非功能验收

- [ ] 所有Tool响应时间符合性能要求
- [ ] 错误处理完善，返回清晰错误信息
- [ ] 日志记录完整
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过

---

## 9. 依赖说明

### 9.1 外部依赖

```python
# requirements.txt
mcp>=0.9.0
pydantic>=2.0
sqlalchemy[asyncio]>=2.0
asyncpg>=0.29.0
```

### 9.2 内部依赖

| 依赖模块 | 用途 |
|---------|------|
| F1-数据模型 | 基础数据结构 |
| F2-共享工具 | ID生成、日志等 |
| F3-配置管理 | 数据库配置 |
| D2-数据存储 | 数据持久化 |

---

*文档版本: 1.0*
*创建日期: 2026-01*
*状态: 规格完成*
