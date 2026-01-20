# 模块开发规格书：M4 科沃斯机器人 MCP Server

## 文档信息

| 项目 | 内容 |
|-----|------|
| 模块ID | M4 |
| 模块名称 | 科沃斯机器人 MCP Server |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | F1数据模型、M1空间管理MCP |

---

## 1. 模块概述

### 1.1 职责描述

科沃斯机器人MCP Server负责对接科沃斯商用清洁机器人，提供：
- **设备发现**：自动发现网络中的科沃斯机器人
- **状态监控**：实时获取机器人位置、电量、工作状态
- **任务控制**：派发清洁任务、控制机器人移动
- **地图管理**：获取和管理机器人地图数据
- **协议适配**：将科沃斯协议转换为统一的MCP接口

### 1.2 在系统中的位置

```
┌─────────────────────────────────────────────────────────────┐
│                         Agent层                             │
│  ┌─────────────────┐ ┌─────────────────┐                   │
│  │ 清洁调度Agent    │ │ 数据采集Agent   │                   │
│  └────────┬────────┘ └────────┬────────┘                   │
│           │                   │                             │
│           ▼                   ▼                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   MCP Client                         │   │
│  └─────────────────────────┬───────────────────────────┘   │
└────────────────────────────┼───────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────┐
│                    MCP Server层                             │
│  ┌─────────────────┐ ┌─────────────────┐                   │
│  │ M3 高仙机器人   │ │ 【M4 科沃斯】    │                   │
│  │ MCP Server      │ │  MCP Server     │                   │
│  │                 │ │  ◄── 本模块     │                   │
│  └─────────────────┘ └────────┬────────┘                   │
│                               │                             │
│                               ▼                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               科沃斯商用云平台 / 本地SDK              │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

### 1.3 输入/输出概述

| 类型 | 内容 |
|-----|------|
| **输入** | Agent通过MCP协议发送的机器人控制请求 |
| **输出** | 机器人状态、任务执行结果、地图数据 |
| **依赖** | 科沃斯云平台API / 本地SDK |

### 1.4 与M3(高仙)的差异

| 对比项 | M3 高仙 | M4 科沃斯 |
|-------|--------|----------|
| 通信方式 | ROS2 + MQTT | REST API + WebSocket |
| 地图格式 | 占用栅格图 | 科沃斯私有格式 |
| 任务模式 | 区域清扫 | 房间/区域清扫 |
| 部署方式 | 本地边缘计算 | 云端+本地混合 |

---

## 2. 接口定义

### 2.1 本模块提供的MCP Tools

本模块必须实现以下 **12个Tools**，与M3保持接口一致：

#### Tool 1: ecovacs_list_robots
```python
async def ecovacs_list_robots(
    tenant_id: str,
    building_id: str = None,    # 可选，按楼宇筛选
    status: str = None          # 可选: "online" | "offline" | "working" | "charging"
) -> ToolResult:
    """
    获取科沃斯机器人列表
    
    返回:
        success=True时，data为机器人列表
        
    示例返回:
    {
        "success": true,
        "data": {
            "robots": [
                {
                    "robot_id": "ecovacs_001",
                    "name": "科沃斯-1F-01",
                    "model": "DEEBOT X1 OMNI",
                    "brand": "ecovacs",
                    "status": "idle",
                    "battery_level": 85,
                    "current_zone_id": "zone-uuid",
                    "firmware_version": "2.1.5",
                    "last_seen": "2026-01-20T10:30:00Z"
                }
            ],
            "total": 5,
            "online_count": 4
        }
    }
    """
```

#### Tool 2: ecovacs_get_robot_status
```python
async def ecovacs_get_robot_status(
    robot_id: str
) -> ToolResult:
    """
    获取单个机器人详细状态
    
    返回:
        {
            "robot_id": "ecovacs_001",
            "status": "working",           # idle/working/charging/error/offline
            "battery_level": 75,
            "position": {
                "x": 15.5,
                "y": 8.3,
                "floor_id": "floor-uuid",
                "zone_id": "zone-uuid",
                "map_id": "map-uuid"
            },
            "current_task": {
                "task_id": "task-uuid",
                "type": "spot_clean",
                "progress": 65,
                "started_at": "2026-01-20T10:00:00Z"
            },
            "consumables": {
                "main_brush": 85,
                "side_brush": 70,
                "filter": 60,
                "mop": 90
            },
            "errors": [],
            "last_updated": "2026-01-20T10:35:00Z"
        }
    """
```

#### Tool 3: ecovacs_start_cleaning
```python
async def ecovacs_start_cleaning(
    robot_id: str,
    zone_id: str,               # 目标清洁区域
    clean_mode: str = "auto",   # auto/vacuum/mop/vacuum_mop
    water_level: str = "medium", # low/medium/high
    suction_power: str = "normal" # quiet/normal/max
) -> ToolResult:
    """
    启动清洁任务
    
    业务规则:
    1. 机器人必须在线且空闲
    2. 电量必须>20%
    3. 机器人必须有目标区域的地图
    
    返回:
        {
            "success": true,
            "data": {
                "task_id": "task-uuid",
                "robot_id": "ecovacs_001",
                "zone_id": "zone-uuid",
                "estimated_duration": 45,
                "started_at": "2026-01-20T10:40:00Z"
            }
        }
    """
```

#### Tool 4: ecovacs_stop_cleaning
```python
async def ecovacs_stop_cleaning(
    robot_id: str,
    return_to_dock: bool = True  # 是否返回充电座
) -> ToolResult:
    """
    停止当前清洁任务
    """
```

#### Tool 5: ecovacs_pause_cleaning
```python
async def ecovacs_pause_cleaning(
    robot_id: str
) -> ToolResult:
    """
    暂停当前清洁任务（可恢复）
    """
```

#### Tool 6: ecovacs_resume_cleaning
```python
async def ecovacs_resume_cleaning(
    robot_id: str
) -> ToolResult:
    """
    恢复暂停的清洁任务
    """
```

#### Tool 7: ecovacs_return_to_dock
```python
async def ecovacs_return_to_dock(
    robot_id: str
) -> ToolResult:
    """
    命令机器人返回充电座
    """
```

#### Tool 8: ecovacs_relocate
```python
async def ecovacs_relocate(
    robot_id: str,
    map_id: str = None  # 指定地图重定位
) -> ToolResult:
    """
    触发机器人重定位
    """
```

#### Tool 9: ecovacs_get_map
```python
async def ecovacs_get_map(
    robot_id: str,
    map_id: str = None  # 不指定则返回当前地图
) -> ToolResult:
    """
    获取机器人地图数据
    
    返回:
        {
            "map_id": "map-uuid",
            "robot_id": "ecovacs_001",
            "floor_id": "floor-uuid",
            "created_at": "2026-01-15T08:00:00Z",
            "rooms": [
                {
                    "room_id": "room-1",
                    "name": "大堂",
                    "area": 120.5,
                    "boundaries": [[x1,y1], [x2,y2], ...]
                }
            ],
            "no_go_zones": [...],
            "dock_position": {"x": 1.0, "y": 2.0}
        }
    """
```

#### Tool 10: ecovacs_get_clean_history
```python
async def ecovacs_get_clean_history(
    robot_id: str,
    start_date: str = None,
    end_date: str = None,
    limit: int = 20
) -> ToolResult:
    """
    获取清洁历史记录
    """
```

#### Tool 11: ecovacs_get_consumables
```python
async def ecovacs_get_consumables(
    robot_id: str
) -> ToolResult:
    """
    获取耗材状态
    
    返回:
        {
            "robot_id": "ecovacs_001",
            "consumables": {
                "main_brush": {"remaining": 85, "need_replace": false},
                "side_brush": {"remaining": 70, "need_replace": false},
                "filter": {"remaining": 30, "need_replace": true},
                "mop": {"remaining": 90, "need_replace": false}
            },
            "alerts": ["filter需要更换"]
        }
    """
```

#### Tool 12: ecovacs_set_schedule
```python
async def ecovacs_set_schedule(
    robot_id: str,
    enabled: bool,
    schedules: list = None  # [{"time": "08:00", "days": [1,2,3,4,5], "rooms": ["room-1"]}]
) -> ToolResult:
    """
    设置机器人本地定时任务
    注意：这是机器人端定时，非系统排程
    """
```

---

## 3. 数据模型

### 3.1 核心数据结构

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class EcovacsRobotStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    CHARGING = "charging"
    RETURNING = "returning"
    ERROR = "error"
    OFFLINE = "offline"

class EcovacsCleanMode(str, Enum):
    AUTO = "auto"
    VACUUM = "vacuum"
    MOP = "mop"
    VACUUM_MOP = "vacuum_mop"

class EcovacsPosition(BaseModel):
    x: float
    y: float
    floor_id: Optional[str] = None
    zone_id: Optional[str] = None
    map_id: Optional[str] = None
    angle: Optional[float] = None  # 朝向角度

class EcovacsConsumables(BaseModel):
    main_brush: int      # 剩余寿命百分比
    side_brush: int
    filter: int
    mop: int
    
class EcovacsRobot(BaseModel):
    robot_id: str
    tenant_id: str
    name: str
    model: str
    brand: str = "ecovacs"
    status: EcovacsRobotStatus
    battery_level: int
    position: Optional[EcovacsPosition] = None
    firmware_version: Optional[str] = None
    consumables: Optional[EcovacsConsumables] = None
    last_seen: datetime
    
class EcovacsTask(BaseModel):
    task_id: str
    robot_id: str
    zone_id: str
    clean_mode: EcovacsCleanMode
    status: str  # pending/running/completed/failed/cancelled
    progress: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    area_cleaned: Optional[float] = None  # 平方米
    duration: Optional[int] = None  # 秒
```

### 3.2 状态机定义

```
机器人状态流转：
                    ┌─────────────┐
                    │   OFFLINE   │
                    └──────┬──────┘
                           │ 上线
                           ▼
┌──────────┐        ┌─────────────┐        ┌──────────┐
│ CHARGING │◄──────►│    IDLE     │◄──────►│  ERROR   │
└────┬─────┘        └──────┬──────┘        └──────────┘
     │                     │
     │ 充电完成            │ 开始清洁
     │                     ▼
     │              ┌─────────────┐
     └─────────────►│   WORKING   │
                    └──────┬──────┘
                           │
                           │ 返回充电
                           ▼
                    ┌─────────────┐
                    │  RETURNING  │
                    └─────────────┘
```

---

## 4. 实现要求

### 4.1 技术栈

```
语言: Python 3.11+
框架: mcp-sdk
协议: 科沃斯云API + WebSocket
依赖:
  - httpx (HTTP客户端)
  - websockets (WebSocket通信)
  - pydantic (数据验证)
```

### 4.2 科沃斯API对接

```python
# 科沃斯商用API配置
ECOVACS_CONFIG = {
    "api_base": "https://api.ecovacs.com/v1",  # 商用API地址
    "ws_endpoint": "wss://realtime.ecovacs.com",
    "auth_type": "oauth2",
    "token_refresh_interval": 3600  # 秒
}

# API认证
class EcovacsAuth:
    async def get_access_token(self) -> str:
        """获取访问令牌"""
        pass
    
    async def refresh_token(self) -> str:
        """刷新令牌"""
        pass
```

### 4.3 WebSocket状态订阅

```python
class EcovacsWebSocket:
    """实时状态订阅"""
    
    async def connect(self):
        """建立WebSocket连接"""
        pass
    
    async def subscribe_robot(self, robot_id: str):
        """订阅机器人状态更新"""
        pass
    
    async def on_status_update(self, callback):
        """状态更新回调"""
        pass
```

### 4.4 错误码定义

| 错误码 | 说明 |
|-------|------|
| `ROBOT_OFFLINE` | 机器人离线 |
| `ROBOT_BUSY` | 机器人忙碌中 |
| `LOW_BATTERY` | 电量不足 |
| `NO_MAP` | 缺少地图数据 |
| `INVALID_ZONE` | 无效的清洁区域 |
| `API_ERROR` | 科沃斯API调用失败 |
| `AUTH_FAILED` | 认证失败 |

---

## 5. 详细功能说明

### 5.1 功能点列表

| 功能 | 描述 | 优先级 |
|-----|------|-------|
| 设备列表查询 | 获取租户下所有科沃斯机器人 | P0 |
| 状态实时获取 | 获取机器人详细状态 | P0 |
| 启动/停止清洁 | 控制机器人清洁任务 | P0 |
| 暂停/恢复清洁 | 清洁任务中断控制 | P0 |
| 返回充电座 | 控制机器人回充 | P0 |
| 地图获取 | 获取机器人地图数据 | P1 |
| 清洁历史 | 获取历史清洁记录 | P1 |
| 耗材监控 | 监控耗材状态 | P2 |
| 本地定时设置 | 设置机器人端定时 | P2 |

### 5.2 业务规则

```
1. 启动清洁前必须检查：
   - 机器人在线
   - 电量>20%
   - 状态为idle或charging
   - 目标区域在机器人地图中存在

2. 停止清洁时：
   - 可选择是否返回充电座
   - 记录已清洁面积和时长

3. 耗材告警阈值：
   - 剩余寿命<30%时生成告警

4. 多租户隔离：
   - 机器人绑定到tenant_id
   - 跨租户访问返回NOT_FOUND
```

---

## 6. 测试要求

### 6.1 单元测试用例

```python
class TestEcovacsTools:
    """科沃斯MCP Tools测试"""
    
    async def test_list_robots_success(self):
        """测试获取机器人列表"""
        pass
    
    async def test_start_cleaning_low_battery(self):
        """测试低电量启动清洁应失败"""
        pass
    
    async def test_start_cleaning_offline_robot(self):
        """测试离线机器人启动应失败"""
        pass
    
    async def test_stop_cleaning_return_to_dock(self):
        """测试停止并返回充电座"""
        pass
```

### 6.2 Mock服务

```python
# 开发时使用Mock服务模拟科沃斯API
class EcovacsMockService:
    """科沃斯API Mock服务"""
    
    robots = [
        {
            "robot_id": "mock_001",
            "name": "测试机器人1",
            "status": "idle",
            "battery_level": 85
        }
    ]
    
    async def get_robots(self):
        return self.robots
```

---

## 7. 验收标准

### 7.1 功能验收

- [ ] 能正确获取机器人列表
- [ ] 能获取机器人实时状态
- [ ] 能成功启动清洁任务
- [ ] 能停止/暂停/恢复清洁
- [ ] 能获取地图数据
- [ ] 电量不足时拒绝启动清洁
- [ ] 离线机器人返回正确错误

### 7.2 性能要求

- 状态查询响应时间 < 500ms
- 命令下发响应时间 < 1s
- 支持同时管理50台机器人

### 7.3 代码质量

- 单元测试覆盖率 > 80%
- 所有公开方法有文档字符串
- 遵循项目代码规范

---

## 8. 参考资源

- M3高仙MCP规格书（接口对照）
- 科沃斯商用API文档（需向厂商获取）
- LinkC接口定义文件 `interfaces/mcp_tools.py`
