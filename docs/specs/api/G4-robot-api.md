# 模块开发规格书：G4 机器人管理API

## 文档信息
| 项目 | 内容 |
|-----|------|
| 模块ID | G4 |
| 模块名称 | 机器人管理API |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | F1数据模型, F4认证授权, M3/M4机器人MCP |

---

## 1. 模块概述

### 1.1 职责描述
机器人管理API提供机器人设备的注册、状态监控、控制指令和历史数据查询的RESTful接口，是前端与机器人交互的统一入口。

### 1.2 在系统中的位置
```
前端应用 (训练工作台/运营控制台)
         │
         ▼
┌─────────────────────────────────────┐
│         G4 机器人管理API            │  ← 本模块
│   /api/v1/robots/*                  │
└─────────────────────────────────────┘
         │
         ├──────────────────┬──────────────────┐
         ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  M3 高仙MCP     │ │  M4 科沃斯MCP   │ │  D3 数据查询    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 1.3 输入/输出概述
| 方向 | 内容 |
|-----|------|
| 输入 | HTTP请求（前端应用） |
| 输出 | JSON响应（机器人数据、控制结果） |
| 依赖 | MCP Servers（机器人控制）、数据服务（历史数据） |

---

## 2. API定义

### 2.1 机器人列表
```yaml
GET /api/v1/robots
描述: 获取机器人列表
权限: robots:read

查询参数:
  - tenant_id: string (required) - 租户ID
  - building_id: string (optional) - 楼宇筛选
  - brand: string (optional) - 品牌筛选 (gaoxian/ecovacs)
  - status: string (optional) - 状态筛选 (idle/working/charging/error/offline)
  - page: integer (default: 1) - 页码
  - page_size: integer (default: 20, max: 100) - 每页数量

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "items": [
        {
          "robot_id": "robot_001",
          "name": "清洁机器人1号",
          "brand": "gaoxian",
          "model": "GX-40",
          "serial_number": "GX40-2024-001",
          "building_id": "building_001",
          "building_name": "A座",
          "current_floor_id": "floor_001",
          "current_floor_name": "1F",
          "status": "idle",
          "battery_level": 85,
          "position": {
            "x": 10.5,
            "y": 20.3,
            "orientation": 45.0
          },
          "current_task_id": null,
          "last_active_at": "2026-01-20T10:30:00Z",
          "created_at": "2025-06-01T00:00:00Z"
        }
      ],
      "total": 15,
      "page": 1,
      "page_size": 20
    }
  }
```

### 2.2 机器人详情
```yaml
GET /api/v1/robots/{robot_id}
描述: 获取单个机器人详情
权限: robots:read

路径参数:
  - robot_id: string (required) - 机器人ID

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "robot_id": "robot_001",
      "name": "清洁机器人1号",
      "brand": "gaoxian",
      "model": "GX-40",
      "serial_number": "GX40-2024-001",
      "firmware_version": "2.3.1",
      "building_id": "building_001",
      "building_name": "A座",
      "current_floor_id": "floor_001",
      "current_floor_name": "1F",
      "status": "idle",
      "battery_level": 85,
      "position": {
        "x": 10.5,
        "y": 20.3,
        "orientation": 45.0
      },
      "capabilities": ["cleaning", "mopping", "mapping"],
      "consumables": {
        "brush": {"remaining_percent": 75, "estimated_hours": 150},
        "filter": {"remaining_percent": 60, "estimated_hours": 120},
        "water_tank": {"remaining_percent": 80, "estimated_hours": 160}
      },
      "current_task": null,
      "statistics": {
        "total_tasks": 156,
        "total_area_cleaned": 45600.5,
        "total_working_hours": 312.5,
        "average_efficiency": 145.8
      },
      "last_active_at": "2026-01-20T10:30:00Z",
      "created_at": "2025-06-01T00:00:00Z",
      "updated_at": "2026-01-20T10:30:00Z"
    }
  }
```

### 2.3 注册机器人
```yaml
POST /api/v1/robots
描述: 注册新机器人
权限: robots:write

请求体:
  {
    "tenant_id": "tenant_001",
    "name": "清洁机器人1号",
    "brand": "gaoxian",
    "model": "GX-40",
    "serial_number": "GX40-2024-001",
    "building_id": "building_001",
    "connection_config": {
      "host": "192.168.1.100",
      "port": 8080,
      "protocol": "ros2"
    }
  }

响应 201:
  {
    "code": 0,
    "message": "Robot registered successfully",
    "data": {
      "robot_id": "robot_001",
      "name": "清洁机器人1号",
      "status": "offline"
    }
  }
```

### 2.4 更新机器人
```yaml
PUT /api/v1/robots/{robot_id}
描述: 更新机器人信息
权限: robots:write

请求体:
  {
    "name": "清洁机器人1号-改名",
    "building_id": "building_002"
  }

响应 200:
  {
    "code": 0,
    "message": "Robot updated successfully",
    "data": {
      "robot_id": "robot_001",
      "name": "清洁机器人1号-改名",
      "building_id": "building_002"
    }
  }
```

### 2.5 删除机器人
```yaml
DELETE /api/v1/robots/{robot_id}
描述: 删除机器人（软删除）
权限: robots:delete

响应 200:
  {
    "code": 0,
    "message": "Robot deleted successfully"
  }
```

### 2.6 实时状态
```yaml
GET /api/v1/robots/{robot_id}/status
描述: 获取机器人实时状态
权限: robots:read

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "robot_id": "robot_001",
      "status": "working",
      "battery_level": 72,
      "position": {
        "x": 15.2,
        "y": 25.8,
        "orientation": 90.0
      },
      "speed": 0.5,
      "cleaning_mode": "standard",
      "current_task_id": "task_001",
      "task_progress": 45.5,
      "errors": [],
      "timestamp": "2026-01-20T10:30:00Z"
    }
  }
```

### 2.7 控制指令
```yaml
POST /api/v1/robots/{robot_id}/control
描述: 发送控制指令
权限: robots:control

请求体:
  {
    "command": "start_task",  # start_task/pause/resume/stop/return_charge/emergency_stop
    "params": {
      "task_id": "task_001"
    }
  }

响应 200:
  {
    "code": 0,
    "message": "Command sent successfully",
    "data": {
      "robot_id": "robot_001",
      "command": "start_task",
      "status": "accepted",
      "execution_id": "exec_001"
    }
  }
```

### 2.8 位置历史
```yaml
GET /api/v1/robots/{robot_id}/positions
描述: 获取位置历史轨迹
权限: robots:read

查询参数:
  - start_time: datetime (required) - 开始时间
  - end_time: datetime (required) - 结束时间
  - interval: integer (default: 5) - 采样间隔秒数

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "robot_id": "robot_001",
      "positions": [
        {
          "timestamp": "2026-01-20T10:00:00Z",
          "x": 10.5,
          "y": 20.3,
          "orientation": 45.0,
          "floor_id": "floor_001"
        },
        {
          "timestamp": "2026-01-20T10:00:05Z",
          "x": 11.0,
          "y": 20.5,
          "orientation": 48.0,
          "floor_id": "floor_001"
        }
      ],
      "total_points": 720
    }
  }
```

### 2.9 状态历史
```yaml
GET /api/v1/robots/{robot_id}/status-history
描述: 获取状态变更历史
权限: robots:read

查询参数:
  - start_time: datetime (required)
  - end_time: datetime (required)
  - limit: integer (default: 100)

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "robot_id": "robot_001",
      "history": [
        {
          "timestamp": "2026-01-20T10:00:00Z",
          "status": "idle",
          "battery_level": 85,
          "event": "task_completed"
        },
        {
          "timestamp": "2026-01-20T09:30:00Z",
          "status": "working",
          "battery_level": 92,
          "event": "task_started"
        }
      ]
    }
  }
```

### 2.10 批量状态查询
```yaml
POST /api/v1/robots/batch-status
描述: 批量获取多个机器人状态
权限: robots:read

请求体:
  {
    "robot_ids": ["robot_001", "robot_002", "robot_003"]
  }

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "robots": [
        {
          "robot_id": "robot_001",
          "status": "idle",
          "battery_level": 85,
          "position": {"x": 10.5, "y": 20.3}
        },
        {
          "robot_id": "robot_002",
          "status": "working",
          "battery_level": 72,
          "position": {"x": 30.2, "y": 15.8}
        }
      ],
      "timestamp": "2026-01-20T10:30:00Z"
    }
  }
```

### 2.11 WebSocket实时推送
```yaml
WebSocket /api/v1/robots/ws
描述: 实时状态推送
权限: robots:read

连接参数:
  - token: string (required) - JWT令牌
  - robot_ids: string (optional) - 逗号分隔的机器人ID列表

客户端消息:
  {
    "type": "subscribe",
    "robot_ids": ["robot_001", "robot_002"]
  }

服务端推送:
  {
    "type": "status_update",
    "robot_id": "robot_001",
    "data": {
      "status": "working",
      "battery_level": 71,
      "position": {"x": 15.5, "y": 26.0},
      "task_progress": 46.2
    },
    "timestamp": "2026-01-20T10:30:05Z"
  }
```

---

## 3. 数据模型

### 3.1 请求/响应模型
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class RobotBrand(str, Enum):
    GAOXIAN = "gaoxian"
    ECOVACS = "ecovacs"

class RobotStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    CHARGING = "charging"
    ERROR = "error"
    OFFLINE = "offline"

class ControlCommand(str, Enum):
    START_TASK = "start_task"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    RETURN_CHARGE = "return_charge"
    EMERGENCY_STOP = "emergency_stop"

class Position(BaseModel):
    x: float
    y: float
    orientation: Optional[float] = None

class ConsumableStatus(BaseModel):
    remaining_percent: int = Field(ge=0, le=100)
    estimated_hours: Optional[int] = None

class RobotListRequest(BaseModel):
    tenant_id: str
    building_id: Optional[str] = None
    brand: Optional[RobotBrand] = None
    status: Optional[RobotStatus] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

class RobotCreateRequest(BaseModel):
    tenant_id: str
    name: str = Field(max_length=100)
    brand: RobotBrand
    model: str = Field(max_length=50)
    serial_number: str = Field(max_length=100)
    building_id: str
    connection_config: dict

class RobotUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    building_id: Optional[str] = None

class ControlRequest(BaseModel):
    command: ControlCommand
    params: Optional[dict] = None

class RobotResponse(BaseModel):
    robot_id: str
    name: str
    brand: RobotBrand
    model: str
    serial_number: str
    building_id: str
    building_name: str
    current_floor_id: Optional[str]
    current_floor_name: Optional[str]
    status: RobotStatus
    battery_level: int
    position: Optional[Position]
    current_task_id: Optional[str]
    last_active_at: Optional[datetime]
    created_at: datetime

class RobotDetailResponse(RobotResponse):
    firmware_version: Optional[str]
    capabilities: List[str]
    consumables: dict[str, ConsumableStatus]
    current_task: Optional[dict]
    statistics: dict
    updated_at: datetime

class RobotStatusResponse(BaseModel):
    robot_id: str
    status: RobotStatus
    battery_level: int
    position: Optional[Position]
    speed: Optional[float]
    cleaning_mode: Optional[str]
    current_task_id: Optional[str]
    task_progress: Optional[float]
    errors: List[str]
    timestamp: datetime

class PositionHistoryResponse(BaseModel):
    robot_id: str
    positions: List[dict]
    total_points: int
```

---

## 4. 实现要求

### 4.1 技术栈
- Python 3.11+
- FastAPI
- Pydantic v2
- asyncio
- WebSocket (fastapi.websockets)

### 4.2 核心实现

#### 路由器结构
```python
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from typing import List

router = APIRouter(prefix="/api/v1/robots", tags=["robots"])

@router.get("", response_model=ApiResponse[PaginatedResponse[RobotResponse]])
async def list_robots(
    tenant_id: str,
    building_id: Optional[str] = None,
    brand: Optional[RobotBrand] = None,
    status: Optional[RobotStatus] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    robot_service: RobotService = Depends(get_robot_service)
):
    """获取机器人列表"""
    pass

@router.get("/{robot_id}", response_model=ApiResponse[RobotDetailResponse])
async def get_robot(
    robot_id: str,
    current_user: User = Depends(get_current_user),
    robot_service: RobotService = Depends(get_robot_service)
):
    """获取机器人详情"""
    pass

@router.post("", response_model=ApiResponse[RobotResponse], status_code=201)
async def create_robot(
    request: RobotCreateRequest,
    current_user: User = Depends(get_current_user),
    robot_service: RobotService = Depends(get_robot_service)
):
    """注册新机器人"""
    pass

@router.post("/{robot_id}/control", response_model=ApiResponse[dict])
async def control_robot(
    robot_id: str,
    request: ControlRequest,
    current_user: User = Depends(get_current_user),
    robot_service: RobotService = Depends(get_robot_service)
):
    """发送控制指令"""
    pass

@router.websocket("/ws")
async def robot_websocket(
    websocket: WebSocket,
    token: str,
    robot_service: RobotService = Depends(get_robot_service)
):
    """WebSocket实时状态推送"""
    pass
```

#### 服务层
```python
class RobotService:
    def __init__(
        self,
        robot_repo: RobotRepository,
        mcp_manager: MCPManager,
        data_service: DataQueryService,
        cache: Redis
    ):
        self.robot_repo = robot_repo
        self.mcp_manager = mcp_manager
        self.data_service = data_service
        self.cache = cache
    
    async def list_robots(
        self,
        tenant_id: str,
        filters: dict,
        pagination: dict
    ) -> PaginatedResponse:
        """获取机器人列表"""
        pass
    
    async def get_robot_detail(self, robot_id: str) -> RobotDetailResponse:
        """获取机器人详情，合并实时状态"""
        pass
    
    async def get_realtime_status(self, robot_id: str) -> RobotStatusResponse:
        """获取实时状态（从MCP Server）"""
        pass
    
    async def send_control_command(
        self,
        robot_id: str,
        command: ControlCommand,
        params: dict
    ) -> dict:
        """发送控制指令到MCP Server"""
        pass
```

### 4.3 MCP调用封装
```python
class MCPManager:
    """MCP Server调用管理器"""
    
    def __init__(self):
        self.mcp_clients: dict[str, MCPClient] = {}
    
    async def get_robot_status(self, robot_id: str, brand: str) -> dict:
        """根据品牌路由到对应MCP"""
        client = self._get_client(brand)
        return await client.call_tool("get_robot_status", {"robot_id": robot_id})
    
    async def send_command(self, robot_id: str, brand: str, command: str, params: dict) -> dict:
        """发送控制指令"""
        client = self._get_client(brand)
        tool_name = self._command_to_tool(command)
        return await client.call_tool(tool_name, {"robot_id": robot_id, **params})
    
    def _get_client(self, brand: str) -> MCPClient:
        if brand == "gaoxian":
            return self.mcp_clients["gaoxian"]
        elif brand == "ecovacs":
            return self.mcp_clients["ecovacs"]
        raise ValueError(f"Unknown brand: {brand}")
```

### 4.4 WebSocket管理
```python
class RobotWebSocketManager:
    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}  # robot_id -> connections
    
    async def connect(self, websocket: WebSocket, robot_ids: List[str]):
        await websocket.accept()
        for robot_id in robot_ids:
            if robot_id not in self.active_connections:
                self.active_connections[robot_id] = set()
            self.active_connections[robot_id].add(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        for connections in self.active_connections.values():
            connections.discard(websocket)
    
    async def broadcast_status(self, robot_id: str, status: dict):
        if robot_id in self.active_connections:
            message = {
                "type": "status_update",
                "robot_id": robot_id,
                "data": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            for connection in self.active_connections[robot_id]:
                await connection.send_json(message)
```

---

## 5. 测试要求

### 5.1 单元测试用例
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_robots(client: AsyncClient, auth_headers: dict):
    """测试获取机器人列表"""
    response = await client.get(
        "/api/v1/robots",
        params={"tenant_id": "tenant_001"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "items" in data["data"]

@pytest.mark.asyncio
async def test_get_robot_detail(client: AsyncClient, auth_headers: dict):
    """测试获取机器人详情"""
    response = await client.get(
        "/api/v1/robots/robot_001",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["robot_id"] == "robot_001"

@pytest.mark.asyncio
async def test_control_robot(client: AsyncClient, auth_headers: dict):
    """测试发送控制指令"""
    response = await client.post(
        "/api/v1/robots/robot_001/control",
        json={"command": "pause", "params": {}},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "accepted"

@pytest.mark.asyncio
async def test_robot_not_found(client: AsyncClient, auth_headers: dict):
    """测试机器人不存在"""
    response = await client.get(
        "/api/v1/robots/nonexistent",
        headers=auth_headers
    )
    assert response.status_code == 404
```

---

## 6. 验收标准

### 6.1 功能验收
- [ ] 机器人CRUD操作正常
- [ ] 实时状态查询正确
- [ ] 控制指令发送成功
- [ ] WebSocket连接稳定
- [ ] 位置历史查询正确
- [ ] 批量查询正常
- [ ] 权限验证生效

### 6.2 性能要求
- 列表查询响应 < 100ms
- 状态查询响应 < 50ms
- 控制指令响应 < 200ms
- WebSocket延迟 < 100ms
- 支持100+并发WebSocket连接

### 6.3 代码质量
- 测试覆盖率 > 80%
- 类型注解完整
- 文档字符串完整
- 无Lint错误
