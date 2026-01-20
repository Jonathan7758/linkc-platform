# 模块开发规格书：M3 高仙机器人 MCP Server

## 文档信息

| 项目 | 内容 |
|-----|------|
| 模块ID | M3 |
| 模块名称 | 高仙机器人 MCP Server |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | F1数据模型、M1空间管理MCP |

---

## 1. 模块概述

### 1.1 职责描述

高仙机器人MCP Server负责与高仙(Gaussian)品牌商用清洁机器人通信，包括：
- **状态查询**：获取机器人实时状态（位置、电量、工作状态）
- **任务控制**：发送清洁任务、暂停、恢复、取消
- **导航控制**：指挥机器人移动到指定位置
- **设备管理**：获取机器人列表、配置信息
- **故障处理**：接收故障报告、触发告警

### 1.2 高仙机器人技术背景

```
高仙机器人通信方式：
├── 云端API：RESTful API（主要方式）
├── 本地SDK：ROS2接口（边缘部署时使用）
└── MQTT：实时状态推送

MVP阶段策略：
├── 优先实现云端API对接
├── 使用Mock模拟器进行开发测试
└── 预留本地SDK接口
```

### 1.3 在系统中的位置

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
│  │  M1 空间管理    │ │  M2 任务管理    │                   │
│  └─────────────────┘ └─────────────────┘                   │
│  ┌─────────────────┐ ┌─────────────────┐                   │
│  │【M3 高仙机器人】 │ │  M4 科沃斯      │                   │
│  │  MCP Server     │ │  MCP Server     │                   │
│  │  ◄── 本模块     │ │                 │                   │
│  └────────┬────────┘ └─────────────────┘                   │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                高仙机器人云平台/本地设备              │   │
│  │              (Gaussian Cloud API / ROS2)             │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

### 1.4 输入/输出概述

| 类型 | 内容 |
|-----|------|
| **输入** | Agent通过MCP协议发送的机器人控制请求 |
| **输出** | 机器人状态、任务执行结果、故障信息 |
| **外部依赖** | 高仙云平台API / 本地ROS2接口 |

---

## 2. 接口定义

### 2.1 本模块提供的MCP Tools

本模块必须实现以下 **12个Tools**：

#### 设备管理类

##### Tool 1: robot_list_robots
```python
async def robot_list_robots(
    tenant_id: str,
    building_id: str = None,      # 可选，按楼宇筛选
    status: str = None,           # 可选，按状态筛选
    robot_type: str = None        # 可选，按类型筛选 "cleaning" | "security" | "delivery"
) -> ToolResult:
    """
    获取机器人列表
    
    返回:
        success=True时，data为机器人列表 List[Robot]
        
    示例返回:
    {
        "success": true,
        "data": {
            "robots": [
                {
                    "robot_id": "uuid",
                    "name": "清洁机器人-01",
                    "brand": "gaoxian",
                    "model": "GS-50",
                    "robot_type": "cleaning",
                    "status": "idle",
                    "battery_level": 85,
                    "current_location": {"x": 10.5, "y": 20.3, "floor_id": "uuid"},
                    "capabilities": ["vacuum", "mop", "auto_charge"]
                }
            ],
            "total": 5
        }
    }
    """
```

##### Tool 2: robot_get_robot
```python
async def robot_get_robot(
    robot_id: str
) -> ToolResult:
    """
    获取单个机器人详情
    
    返回:
        success=True时，data为机器人详细信息，包含配置和能力
    """
```

##### Tool 3: robot_get_status
```python
async def robot_get_status(
    robot_id: str
) -> ToolResult:
    """
    获取机器人实时状态
    
    返回:
        success=True时，data为状态快照 RobotStatusSnapshot
        
    示例返回:
    {
        "success": true,
        "data": {
            "robot_id": "uuid",
            "status": "working",
            "battery_level": 72,
            "current_location": {"x": 15.2, "y": 30.1, "floor_id": "uuid"},
            "current_task_id": "uuid",
            "speed": 0.5,
            "cleaning_mode": "vacuum",
            "water_level": 65,
            "dustbin_level": 40,
            "error_code": null,
            "timestamp": "2026-01-19T10:30:00Z"
        }
    }
    """
```

##### Tool 4: robot_batch_get_status
```python
async def robot_batch_get_status(
    robot_ids: List[str]
) -> ToolResult:
    """
    批量获取机器人状态
    
    参数:
        robot_ids: 机器人ID列表（最多20个）
        
    返回:
        success=True时，data为状态列表 List[RobotStatusSnapshot]
    """
```

#### 任务控制类

##### Tool 5: robot_start_task
```python
async def robot_start_task(
    robot_id: str,
    zone_id: str,
    task_type: str,               # "vacuum" | "mop" | "vacuum_mop"
    cleaning_mode: str = "standard",  # "eco" | "standard" | "deep"
    task_id: str = None           # 关联的任务ID（来自M2）
) -> ToolResult:
    """
    启动清洁任务
    
    业务规则:
    - 机器人必须处于idle或charging状态
    - 电量低于20%时拒绝启动（建议充电）
    - 区域必须在机器人可达范围内
    
    返回:
        success=True时，data包含任务启动确认和预计完成时间
        
    示例返回:
    {
        "success": true,
        "data": {
            "robot_task_id": "gaoxian-task-12345",
            "robot_id": "uuid",
            "zone_id": "uuid",
            "status": "started",
            "estimated_duration": 45,
            "started_at": "2026-01-19T10:30:00Z"
        }
    }
    """
```

##### Tool 6: robot_pause_task
```python
async def robot_pause_task(
    robot_id: str,
    reason: str = None
) -> ToolResult:
    """
    暂停当前任务
    
    业务规则:
    - 只有working状态的机器人可以暂停
    - 暂停后机器人进入paused状态
    
    返回:
        success=True时，data包含暂停确认
    """
```

##### Tool 7: robot_resume_task
```python
async def robot_resume_task(
    robot_id: str
) -> ToolResult:
    """
    恢复暂停的任务
    
    业务规则:
    - 只有paused状态的机器人可以恢复
    
    返回:
        success=True时，data包含恢复确认
    """
```

##### Tool 8: robot_cancel_task
```python
async def robot_cancel_task(
    robot_id: str,
    reason: str = None
) -> ToolResult:
    """
    取消当前任务
    
    业务规则:
    - working或paused状态的机器人可以取消
    - 取消后机器人进入idle状态
    - 记录取消原因和取消时的进度
    
    返回:
        success=True时，data包含取消确认和任务完成进度
    """
```

#### 导航控制类

##### Tool 9: robot_go_to_location
```python
async def robot_go_to_location(
    robot_id: str,
    target_location: dict,        # {"x": float, "y": float, "floor_id": str}
    reason: str = None            # 移动原因（便于日志追踪）
) -> ToolResult:
    """
    指挥机器人移动到指定位置
    
    业务规则:
    - 机器人必须处于idle状态
    - 目标位置必须在机器人可达范围内
    - 跨楼层移动需要特殊处理（电梯）
    
    返回:
        success=True时，data包含导航确认和预计到达时间
    """
```

##### Tool 10: robot_go_to_charge
```python
async def robot_go_to_charge(
    robot_id: str,
    force: bool = False           # 强制返回（即使正在工作）
) -> ToolResult:
    """
    指挥机器人返回充电桩
    
    业务规则:
    - 默认只有idle状态可返回充电
    - force=True时会先取消当前任务
    
    返回:
        success=True时，data包含返回确认
    """
```

#### 故障处理类

##### Tool 11: robot_get_errors
```python
async def robot_get_errors(
    robot_id: str = None,         # 为空则查询所有机器人
    tenant_id: str = None,
    severity: str = None,         # "warning" | "error" | "critical"
    resolved: bool = False,       # 是否只查询未解决的
    limit: int = 50
) -> ToolResult:
    """
    获取机器人错误/故障列表
    
    返回:
        success=True时，data为错误列表
        
    示例返回:
    {
        "success": true,
        "data": {
            "errors": [
                {
                    "error_id": "uuid",
                    "robot_id": "uuid",
                    "robot_name": "清洁机器人-01",
                    "error_code": "E101",
                    "error_type": "sensor_fault",
                    "severity": "warning",
                    "message": "左侧避障传感器异常",
                    "occurred_at": "2026-01-19T10:25:00Z",
                    "resolved": false,
                    "location": {"x": 15.2, "y": 30.1}
                }
            ],
            "total": 3
        }
    }
    """
```

##### Tool 12: robot_clear_error
```python
async def robot_clear_error(
    robot_id: str,
    error_id: str = None,         # 为空则清除所有可清除的错误
    force: bool = False
) -> ToolResult:
    """
    清除机器人错误状态
    
    业务规则:
    - 只能清除severity为warning的错误
    - error和critical级别需要人工介入
    - force=True可强制清除（需要确认）
    
    返回:
        success=True时，data包含清除结果
    """
```

### 2.2 本模块依赖的接口

```python
# 高仙云平台API（外部依赖）
# MVP阶段使用Mock实现

class GaoxianCloudClient:
    """高仙云平台API客户端"""
    
    async def get_robots(self, org_id: str) -> List[dict]:
        """获取组织下的机器人列表"""
        pass
    
    async def get_robot_status(self, robot_sn: str) -> dict:
        """获取机器人状态"""
        pass
    
    async def send_task(self, robot_sn: str, task: dict) -> dict:
        """发送任务到机器人"""
        pass
    
    async def control_robot(self, robot_sn: str, command: str, params: dict) -> dict:
        """发送控制命令"""
        pass

# 数据模型依赖
from interfaces.data_models import (
    Robot,
    RobotStatus,
    RobotStatusSnapshot,
    RobotBrand,
    RobotType,
    RobotCapability,
    Location
)
```

---

## 3. 数据模型

### 3.1 核心数据结构

```python
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class RobotBrand(str, Enum):
    """机器人品牌"""
    GAOXIAN = "gaoxian"      # 高仙
    ECOVACS = "ecovacs"      # 科沃斯
    PUDU = "pudu"            # 普渡
    OTHER = "other"

class RobotType(str, Enum):
    """机器人类型"""
    CLEANING = "cleaning"     # 清洁
    SECURITY = "security"     # 安保
    DELIVERY = "delivery"     # 配送
    DISINFECTION = "disinfection"  # 消毒

class RobotStatus(str, Enum):
    """机器人状态"""
    OFFLINE = "offline"       # 离线
    IDLE = "idle"             # 空闲
    WORKING = "working"       # 工作中
    PAUSED = "paused"         # 暂停
    CHARGING = "charging"     # 充电中
    ERROR = "error"           # 故障
    MAINTENANCE = "maintenance"  # 维护中

class CleaningMode(str, Enum):
    """清洁模式"""
    VACUUM = "vacuum"         # 吸尘
    MOP = "mop"               # 拖地
    VACUUM_MOP = "vacuum_mop" # 吸拖一体

class CleaningIntensity(str, Enum):
    """清洁强度"""
    ECO = "eco"               # 节能
    STANDARD = "standard"     # 标准
    DEEP = "deep"             # 深度

class Location(BaseModel):
    """位置信息"""
    x: float
    y: float
    floor_id: Optional[UUID] = None
    heading: Optional[float] = None  # 朝向角度

class RobotCapability(BaseModel):
    """机器人能力"""
    can_vacuum: bool = True
    can_mop: bool = True
    can_auto_charge: bool = True
    can_elevator: bool = False       # 能否乘电梯
    max_area: float = 500            # 最大清洁面积(m²)
    max_runtime: int = 180           # 最大续航(分钟)

class Robot(BaseModel):
    """机器人基础信息"""
    robot_id: UUID
    tenant_id: UUID
    
    # 设备信息
    name: str
    brand: RobotBrand
    model: str                        # 型号，如 "GS-50"
    serial_number: str                # 序列号
    robot_type: RobotType
    
    # 分配信息
    building_id: Optional[UUID] = None
    floor_ids: List[UUID] = []        # 可服务的楼层
    home_location: Optional[Location] = None  # 充电桩位置
    
    # 能力配置
    capabilities: RobotCapability
    
    # 状态
    status: RobotStatus = RobotStatus.OFFLINE
    
    # 元信息
    registered_at: datetime
    last_seen_at: Optional[datetime] = None

class RobotStatusSnapshot(BaseModel):
    """机器人状态快照"""
    robot_id: UUID
    status: RobotStatus
    
    # 位置信息
    current_location: Optional[Location] = None
    
    # 电量和耗材
    battery_level: int = Field(..., ge=0, le=100)
    water_level: Optional[int] = Field(None, ge=0, le=100)
    dustbin_level: Optional[int] = Field(None, ge=0, le=100)
    
    # 当前任务
    current_task_id: Optional[UUID] = None
    current_zone_id: Optional[UUID] = None
    task_progress: Optional[float] = None  # 0-100
    
    # 运动状态
    speed: Optional[float] = None          # m/s
    cleaning_mode: Optional[CleaningMode] = None
    cleaning_intensity: Optional[CleaningIntensity] = None
    
    # 错误信息
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    # 时间戳
    timestamp: datetime

class RobotError(BaseModel):
    """机器人错误"""
    error_id: UUID
    robot_id: UUID
    robot_name: Optional[str] = None
    
    error_code: str                   # 厂商错误码
    error_type: str                   # 分类：sensor_fault, motor_fault, navigation_error, etc.
    severity: str                     # warning, error, critical
    message: str
    
    location: Optional[Location] = None
    occurred_at: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
```

### 3.2 高仙特有数据映射

```python
# 高仙API状态码到系统状态的映射
GAOXIAN_STATUS_MAP = {
    0: RobotStatus.OFFLINE,
    1: RobotStatus.IDLE,
    2: RobotStatus.WORKING,
    3: RobotStatus.PAUSED,
    4: RobotStatus.CHARGING,
    5: RobotStatus.ERROR,
    6: RobotStatus.MAINTENANCE,
}

# 高仙错误码分类
GAOXIAN_ERROR_SEVERITY = {
    "E1xx": "warning",    # 传感器警告
    "E2xx": "error",      # 运动控制错误
    "E3xx": "critical",   # 系统级故障
    "E4xx": "warning",    # 清洁模块警告
    "E5xx": "error",      # 导航错误
}
```

---

## 4. 实现要求

### 4.1 技术栈约束

| 项目 | 要求 |
|-----|------|
| Python版本 | 3.11+ |
| MCP SDK | mcp >= 1.0.0 |
| HTTP客户端 | httpx (异步) |
| 数据验证 | Pydantic v2 |
| 异步框架 | asyncio |

### 4.2 代码规范

```python
# 文件头模板
"""
M3: 高仙机器人 MCP Server - [文件描述]

职责: [简要说明]
外部依赖: 高仙云平台API
"""

# 外部API调用必须有超时和重试
async def call_gaoxian_api(self, endpoint: str, params: dict) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(3):
            try:
                response = await client.get(f"{self.base_url}/{endpoint}", params=params)
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                if attempt == 2:
                    raise
                await asyncio.sleep(1)

# 状态变更必须记录日志
logger.info(f"Robot {robot_id} status changed: {old_status} → {new_status}")
```

### 4.3 错误码定义

| 错误码 | 说明 |
|-------|------|
| `INVALID_PARAM` | 参数无效 |
| `NOT_FOUND` | 机器人不存在 |
| `INVALID_STATE` | 机器人状态不允许此操作 |
| `LOW_BATTERY` | 电量过低 |
| `ROBOT_BUSY` | 机器人正忙 |
| `ROBOT_OFFLINE` | 机器人离线 |
| `ROBOT_ERROR` | 机器人故障状态 |
| `API_ERROR` | 高仙API调用失败 |
| `TIMEOUT` | 操作超时 |

### 4.4 Mock模式

```python
# MVP阶段必须支持Mock模式
# 通过环境变量控制

import os

USE_MOCK = os.getenv("GAOXIAN_USE_MOCK", "true").lower() == "true"

if USE_MOCK:
    from .mock_client import MockGaoxianClient as GaoxianClient
else:
    from .gaoxian_client import GaoxianClient
```

---

## 5. 详细功能说明

### 5.1 功能点列表

| 功能 | 描述 | 优先级 |
|-----|------|-------|
| 机器人列表查询 | 获取租户下所有高仙机器人 | P0 |
| 状态实时查询 | 获取机器人当前状态 | P0 |
| 批量状态查询 | 批量获取多个机器人状态 | P0 |
| 启动清洁任务 | 发送清洁任务到机器人 | P0 |
| 任务暂停/恢复 | 控制任务执行 | P0 |
| 任务取消 | 取消正在执行的任务 | P0 |
| 导航控制 | 指挥机器人移动 | P1 |
| 返回充电 | 指挥机器人充电 | P0 |
| 故障查询 | 获取故障列表 | P0 |
| 故障清除 | 清除可恢复的故障 | P1 |
| Mock模拟器 | 开发测试用模拟器 | P0 |

### 5.2 业务规则

#### 任务启动规则
```
1. 机器人状态必须为 idle 或 charging
2. 电量 >= 20%（低于20%建议充电）
3. 没有未清除的 error/critical 级别故障
4. 目标区域在机器人服务范围内
```

#### 状态流转规则
```
允许的状态转换：

offline ──► idle（机器人上线）
idle ──► working（开始任务）
idle ──► charging（返回充电）
working ──► paused（暂停任务）
working ──► idle（任务完成/取消）
working ──► error（发生故障）
paused ──► working（恢复任务）
paused ──► idle（取消任务）
charging ──► idle（充电完成）
error ──► idle（故障清除）
```

#### 电量管理规则
```
电量阈值：
├── >= 80%: 满电，可执行任何任务
├── 50-79%: 正常，可执行任务
├── 20-49%: 低电量，完成当前任务后建议充电
├── 10-19%: 极低，应立即返回充电
└── < 10%: 紧急，强制返回充电
```

### 5.3 边界条件处理

| 场景 | 处理方式 |
|-----|---------|
| 机器人离线 | 返回ROBOT_OFFLINE错误 |
| 机器人正忙 | 返回ROBOT_BUSY错误 |
| 电量过低 | 返回LOW_BATTERY错误，建议充电 |
| API超时 | 重试3次，最终返回TIMEOUT错误 |
| 无效目标位置 | 返回INVALID_PARAM错误 |

---

## 6. 测试要求

### 6.1 单元测试用例

```python
# tests/test_robot_tools.py

import pytest
from uuid import uuid4

class TestRobotStatusTools:
    """状态查询测试"""
    
    async def test_get_status_success(self):
        """测试正常获取状态"""
        result = await tools.handle("robot_get_status", {
            "robot_id": str(uuid4())
        })
        assert result.success
        assert "battery_level" in result.data
    
    async def test_get_status_robot_not_found(self):
        """测试机器人不存在"""
        result = await tools.handle("robot_get_status", {
            "robot_id": str(uuid4())
        })
        assert not result.success
        assert result.error_code == "NOT_FOUND"

class TestTaskControlTools:
    """任务控制测试"""
    
    async def test_start_task_success(self):
        """测试正常启动任务"""
        pass
    
    async def test_start_task_low_battery(self):
        """测试低电量拒绝启动"""
        pass
    
    async def test_start_task_robot_busy(self):
        """测试机器人正忙"""
        pass
    
    async def test_pause_resume_cancel_flow(self):
        """测试暂停/恢复/取消流程"""
        pass

class TestErrorHandling:
    """故障处理测试"""
    
    async def test_get_errors(self):
        """测试获取故障列表"""
        pass
    
    async def test_clear_warning_error(self):
        """测试清除警告级别故障"""
        pass
    
    async def test_cannot_clear_critical_error(self):
        """测试无法清除严重故障"""
        pass
```

### 6.2 Mock模拟器测试场景

```python
class TestMockSimulator:
    """Mock模拟器测试"""
    
    async def test_simulate_task_progress(self):
        """测试任务进度模拟"""
        # 启动任务后，状态应逐渐更新
        pass
    
    async def test_simulate_battery_drain(self):
        """测试电量消耗模拟"""
        pass
    
    async def test_simulate_random_error(self):
        """测试随机故障模拟"""
        pass
```

---

## 7. 示例代码

### 7.1 MCP Server主入口 (server.py)

```python
"""
M3: 高仙机器人 MCP Server
"""
import asyncio
import json
import os
from mcp.server import Server
from mcp.types import Tool, TextContent

from .tools import RobotTools
from .mock_client import MockGaoxianClient
from .storage import InMemoryRobotStorage

# 创建MCP Server实例
app = Server("gaoxian-robot")

# 选择客户端实现
USE_MOCK = os.getenv("GAOXIAN_USE_MOCK", "true").lower() == "true"
if USE_MOCK:
    client = MockGaoxianClient()
else:
    from .gaoxian_client import GaoxianClient
    client = GaoxianClient(
        base_url=os.getenv("GAOXIAN_API_URL"),
        api_key=os.getenv("GAOXIAN_API_KEY")
    )

storage = InMemoryRobotStorage()
tools = RobotTools(client, storage)

# Tool定义列表
GAOXIAN_ROBOT_TOOLS = [
    {
        "name": "robot_list_robots",
        "description": "获取机器人列表",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "format": "uuid"},
                "building_id": {"type": "string", "format": "uuid"},
                "status": {"type": "string"},
                "robot_type": {"type": "string"}
            },
            "required": ["tenant_id"]
        }
    },
    {
        "name": "robot_get_robot",
        "description": "获取单个机器人详情",
        "inputSchema": {
            "type": "object",
            "properties": {
                "robot_id": {"type": "string", "format": "uuid"}
            },
            "required": ["robot_id"]
        }
    },
    {
        "name": "robot_get_status",
        "description": "获取机器人实时状态",
        "inputSchema": {
            "type": "object",
            "properties": {
                "robot_id": {"type": "string", "format": "uuid"}
            },
            "required": ["robot_id"]
        }
    },
    {
        "name": "robot_batch_get_status",
        "description": "批量获取机器人状态",
        "inputSchema": {
            "type": "object",
            "properties": {
                "robot_ids": {
                    "type": "array",
                    "items": {"type": "string", "format": "uuid"},
                    "maxItems": 20
                }
            },
            "required": ["robot_ids"]
        }
    },
    {
        "name": "robot_start_task",
        "description": "启动清洁任务",
        "inputSchema": {
            "type": "object",
            "properties": {
                "robot_id": {"type": "string", "format": "uuid"},
                "zone_id": {"type": "string", "format": "uuid"},
                "task_type": {"type": "string", "enum": ["vacuum", "mop", "vacuum_mop"]},
                "cleaning_mode": {"type": "string", "enum": ["eco", "standard", "deep"]},
                "task_id": {"type": "string", "format": "uuid"}
            },
            "required": ["robot_id", "zone_id", "task_type"]
        }
    },
    {
        "name": "robot_pause_task",
        "description": "暂停当前任务",
        "inputSchema": {
            "type": "object",
            "properties": {
                "robot_id": {"type": "string", "format": "uuid"},
                "reason": {"type": "string"}
            },
            "required": ["robot_id"]
        }
    },
    {
        "name": "robot_resume_task",
        "description": "恢复暂停的任务",
        "inputSchema": {
            "type": "object",
            "properties": {
                "robot_id": {"type": "string", "format": "uuid"}
            },
            "required": ["robot_id"]
        }
    },
    {
        "name": "robot_cancel_task",
        "description": "取消当前任务",
        "inputSchema": {
            "type": "object",
            "properties": {
                "robot_id": {"type": "string", "format": "uuid"},
                "reason": {"type": "string"}
            },
            "required": ["robot_id"]
        }
    },
    {
        "name": "robot_go_to_location",
        "description": "指挥机器人移动到指定位置",
        "inputSchema": {
            "type": "object",
            "properties": {
                "robot_id": {"type": "string", "format": "uuid"},
                "target_location": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number"},
                        "y": {"type": "number"},
                        "floor_id": {"type": "string", "format": "uuid"}
                    },
                    "required": ["x", "y"]
                },
                "reason": {"type": "string"}
            },
            "required": ["robot_id", "target_location"]
        }
    },
    {
        "name": "robot_go_to_charge",
        "description": "指挥机器人返回充电桩",
        "inputSchema": {
            "type": "object",
            "properties": {
                "robot_id": {"type": "string", "format": "uuid"},
                "force": {"type": "boolean", "default": False}
            },
            "required": ["robot_id"]
        }
    },
    {
        "name": "robot_get_errors",
        "description": "获取机器人错误/故障列表",
        "inputSchema": {
            "type": "object",
            "properties": {
                "robot_id": {"type": "string", "format": "uuid"},
                "tenant_id": {"type": "string", "format": "uuid"},
                "severity": {"type": "string", "enum": ["warning", "error", "critical"]},
                "resolved": {"type": "boolean"},
                "limit": {"type": "integer", "default": 50}
            }
        }
    },
    {
        "name": "robot_clear_error",
        "description": "清除机器人错误状态",
        "inputSchema": {
            "type": "object",
            "properties": {
                "robot_id": {"type": "string", "format": "uuid"},
                "error_id": {"type": "string", "format": "uuid"},
                "force": {"type": "boolean", "default": False}
            },
            "required": ["robot_id"]
        }
    }
]


@app.list_tools()
async def list_tools() -> list[Tool]:
    """返回支持的Tools列表"""
    return [Tool(**t) for t in GAOXIAN_ROBOT_TOOLS]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理Tool调用"""
    result = await tools.handle(name, arguments)
    return [TextContent(type="text", text=json.dumps(result.model_dump()))]


async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())
```

### 7.2 Tool实现示例 (tools.py 片段)

```python
"""
高仙机器人Tool实现
"""
from typing import Dict, Any, List
from uuid import uuid4
from datetime import datetime
import logging

from interfaces.data_models import (
    Robot, RobotStatus, RobotStatusSnapshot, Location
)
from interfaces.mcp_tools import ToolResult

logger = logging.getLogger(__name__)

# 电量阈值
BATTERY_LOW_THRESHOLD = 20
BATTERY_CRITICAL_THRESHOLD = 10


class RobotTools:
    def __init__(self, client, storage):
        self.client = client  # 高仙API客户端或Mock
        self.storage = storage
    
    async def handle(self, name: str, arguments: dict) -> ToolResult:
        """路由Tool调用"""
        handlers = {
            "robot_list_robots": self._list_robots,
            "robot_get_robot": self._get_robot,
            "robot_get_status": self._get_status,
            "robot_batch_get_status": self._batch_get_status,
            "robot_start_task": self._start_task,
            "robot_pause_task": self._pause_task,
            "robot_resume_task": self._resume_task,
            "robot_cancel_task": self._cancel_task,
            "robot_go_to_location": self._go_to_location,
            "robot_go_to_charge": self._go_to_charge,
            "robot_get_errors": self._get_errors,
            "robot_clear_error": self._clear_error,
        }
        
        handler = handlers.get(name)
        if not handler:
            return ToolResult(success=False, error=f"Unknown tool: {name}", error_code="NOT_FOUND")
        
        try:
            return await handler(arguments)
        except Exception as e:
            logger.exception(f"Error handling {name}")
            return ToolResult(success=False, error=str(e), error_code="INTERNAL_ERROR")
    
    async def _get_status(self, args: Dict[str, Any]) -> ToolResult:
        """获取机器人实时状态"""
        robot_id = args.get("robot_id")
        if not robot_id:
            return ToolResult(
                success=False,
                error="robot_id is required",
                error_code="INVALID_PARAM"
            )
        
        robot = await self.storage.get_robot(robot_id)
        if not robot:
            return ToolResult(
                success=False,
                error="Robot not found",
                error_code="NOT_FOUND"
            )
        
        # 从高仙API获取实时状态
        try:
            status_data = await self.client.get_robot_status(robot.serial_number)
            snapshot = self._map_gaoxian_status(robot_id, status_data)
            return ToolResult(success=True, data=snapshot.model_dump())
        except Exception as e:
            logger.error(f"Failed to get status for robot {robot_id}: {e}")
            return ToolResult(
                success=False,
                error="Failed to get robot status",
                error_code="API_ERROR"
            )
    
    async def _start_task(self, args: Dict[str, Any]) -> ToolResult:
        """启动清洁任务"""
        robot_id = args.get("robot_id")
        zone_id = args.get("zone_id")
        task_type = args.get("task_type")
        
        if not all([robot_id, zone_id, task_type]):
            return ToolResult(
                success=False,
                error="robot_id, zone_id, task_type are required",
                error_code="INVALID_PARAM"
            )
        
        robot = await self.storage.get_robot(robot_id)
        if not robot:
            return ToolResult(success=False, error="Robot not found", error_code="NOT_FOUND")
        
        # 检查机器人状态
        status = await self.client.get_robot_status(robot.serial_number)
        current_status = self._map_status_code(status.get("status_code"))
        
        if current_status == RobotStatus.OFFLINE:
            return ToolResult(
                success=False,
                error="Robot is offline",
                error_code="ROBOT_OFFLINE"
            )
        
        if current_status not in [RobotStatus.IDLE, RobotStatus.CHARGING]:
            return ToolResult(
                success=False,
                error=f"Robot is {current_status.value}, cannot start task",
                error_code="ROBOT_BUSY"
            )
        
        # 检查电量
        battery_level = status.get("battery_level", 0)
        if battery_level < BATTERY_LOW_THRESHOLD:
            return ToolResult(
                success=False,
                error=f"Battery too low ({battery_level}%), please charge first",
                error_code="LOW_BATTERY"
            )
        
        # 检查是否有未清除的严重故障
        errors = await self.storage.get_robot_errors(robot_id, resolved=False)
        critical_errors = [e for e in errors if e.severity in ["error", "critical"]]
        if critical_errors:
            return ToolResult(
                success=False,
                error=f"Robot has unresolved errors: {critical_errors[0].error_code}",
                error_code="ROBOT_ERROR"
            )
        
        # 发送任务到高仙API
        try:
            task_result = await self.client.send_task(
                robot.serial_number,
                {
                    "type": task_type,
                    "zone_id": zone_id,
                    "mode": args.get("cleaning_mode", "standard")
                }
            )
            
            logger.info(f"Task started: robot={robot_id}, zone={zone_id}, type={task_type}")
            
            return ToolResult(
                success=True,
                data={
                    "robot_task_id": task_result.get("task_id"),
                    "robot_id": robot_id,
                    "zone_id": zone_id,
                    "status": "started",
                    "estimated_duration": task_result.get("estimated_duration", 30),
                    "started_at": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to start task: {e}")
            return ToolResult(
                success=False,
                error="Failed to start task on robot",
                error_code="API_ERROR"
            )
    
    async def _go_to_charge(self, args: Dict[str, Any]) -> ToolResult:
        """指挥机器人返回充电桩"""
        robot_id = args.get("robot_id")
        force = args.get("force", False)
        
        if not robot_id:
            return ToolResult(
                success=False,
                error="robot_id is required",
                error_code="INVALID_PARAM"
            )
        
        robot = await self.storage.get_robot(robot_id)
        if not robot:
            return ToolResult(success=False, error="Robot not found", error_code="NOT_FOUND")
        
        status = await self.client.get_robot_status(robot.serial_number)
        current_status = self._map_status_code(status.get("status_code"))
        
        # 如果正在工作且不是强制返回
        if current_status == RobotStatus.WORKING and not force:
            return ToolResult(
                success=False,
                error="Robot is working. Use force=true to cancel current task and return to charge",
                error_code="ROBOT_BUSY"
            )
        
        # 如果强制返回，先取消当前任务
        if current_status == RobotStatus.WORKING and force:
            await self.client.control_robot(robot.serial_number, "cancel_task", {})
            logger.info(f"Force cancelled task for robot {robot_id}")
        
        # 发送返回充电命令
        try:
            await self.client.control_robot(robot.serial_number, "go_to_charge", {})
            logger.info(f"Robot {robot_id} returning to charge")
            
            return ToolResult(
                success=True,
                data={
                    "robot_id": robot_id,
                    "status": "returning_to_charge",
                    "home_location": robot.home_location.model_dump() if robot.home_location else None
                }
            )
        except Exception as e:
            logger.error(f"Failed to send charge command: {e}")
            return ToolResult(
                success=False,
                error="Failed to send return to charge command",
                error_code="API_ERROR"
            )
    
    def _map_status_code(self, code: int) -> RobotStatus:
        """映射高仙状态码到系统状态"""
        status_map = {
            0: RobotStatus.OFFLINE,
            1: RobotStatus.IDLE,
            2: RobotStatus.WORKING,
            3: RobotStatus.PAUSED,
            4: RobotStatus.CHARGING,
            5: RobotStatus.ERROR,
            6: RobotStatus.MAINTENANCE,
        }
        return status_map.get(code, RobotStatus.OFFLINE)
    
    def _map_gaoxian_status(self, robot_id: str, data: dict) -> RobotStatusSnapshot:
        """映射高仙API返回到状态快照"""
        return RobotStatusSnapshot(
            robot_id=robot_id,
            status=self._map_status_code(data.get("status_code", 0)),
            battery_level=data.get("battery_level", 0),
            water_level=data.get("water_level"),
            dustbin_level=data.get("dustbin_level"),
            current_location=Location(
                x=data.get("position", {}).get("x", 0),
                y=data.get("position", {}).get("y", 0),
                floor_id=data.get("floor_id")
            ) if data.get("position") else None,
            current_task_id=data.get("current_task_id"),
            task_progress=data.get("task_progress"),
            speed=data.get("speed"),
            error_code=data.get("error_code"),
            error_message=data.get("error_message"),
            timestamp=datetime.utcnow()
        )
```

### 7.3 Mock客户端示例 (mock_client.py)

```python
"""
高仙机器人Mock客户端 - 用于开发和测试
"""
import asyncio
import random
from typing import Dict, List, Any
from uuid import uuid4
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MockGaoxianClient:
    """
    模拟高仙云平台API
    
    功能：
    - 模拟机器人状态
    - 模拟任务执行进度
    - 模拟电量消耗
    - 模拟随机故障
    """
    
    def __init__(self):
        # 模拟的机器人数据
        self._robots: Dict[str, dict] = {}
        self._init_mock_robots()
    
    def _init_mock_robots(self):
        """初始化模拟机器人"""
        for i in range(3):
            sn = f"GX-{1000 + i}"
            self._robots[sn] = {
                "serial_number": sn,
                "model": "GS-50",
                "status_code": 1,  # idle
                "battery_level": random.randint(60, 100),
                "water_level": random.randint(50, 100),
                "dustbin_level": random.randint(0, 50),
                "position": {"x": random.uniform(0, 50), "y": random.uniform(0, 50)},
                "current_task_id": None,
                "task_progress": None,
                "speed": 0,
                "error_code": None,
                "error_message": None,
            }
        logger.info(f"Mock client initialized with {len(self._robots)} robots")
    
    async def get_robots(self, org_id: str) -> List[dict]:
        """获取机器人列表"""
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return list(self._robots.values())
    
    async def get_robot_status(self, robot_sn: str) -> dict:
        """获取机器人状态"""
        await asyncio.sleep(0.05)  # 模拟网络延迟
        
        if robot_sn not in self._robots:
            raise ValueError(f"Robot {robot_sn} not found")
        
        robot = self._robots[robot_sn]
        
        # 模拟电量消耗
        if robot["status_code"] == 2:  # working
            robot["battery_level"] = max(0, robot["battery_level"] - 0.1)
            if robot["task_progress"] is not None:
                robot["task_progress"] = min(100, robot["task_progress"] + random.uniform(1, 3))
                if robot["task_progress"] >= 100:
                    robot["status_code"] = 1  # 任务完成，返回idle
                    robot["current_task_id"] = None
                    robot["task_progress"] = None
        
        # 模拟充电
        if robot["status_code"] == 4:  # charging
            robot["battery_level"] = min(100, robot["battery_level"] + 0.5)
            if robot["battery_level"] >= 100:
                robot["status_code"] = 1  # 充满电，返回idle
        
        # 随机故障（1%概率）
        if random.random() < 0.01 and robot["status_code"] == 2:
            robot["status_code"] = 5  # error
            robot["error_code"] = "E101"
            robot["error_message"] = "模拟传感器异常"
        
        return robot.copy()
    
    async def send_task(self, robot_sn: str, task: dict) -> dict:
        """发送任务"""
        await asyncio.sleep(0.1)
        
        if robot_sn not in self._robots:
            raise ValueError(f"Robot {robot_sn} not found")
        
        robot = self._robots[robot_sn]
        
        if robot["status_code"] not in [1, 4]:  # 只有idle或charging可以接收任务
            raise ValueError(f"Robot is busy: status={robot['status_code']}")
        
        task_id = f"mock-task-{uuid4().hex[:8]}"
        robot["status_code"] = 2  # working
        robot["current_task_id"] = task_id
        robot["task_progress"] = 0
        robot["speed"] = 0.5
        
        logger.info(f"Mock task started: {task_id}")
        
        return {
            "task_id": task_id,
            "status": "started",
            "estimated_duration": random.randint(20, 60)
        }
    
    async def control_robot(self, robot_sn: str, command: str, params: dict) -> dict:
        """控制机器人"""
        await asyncio.sleep(0.1)
        
        if robot_sn not in self._robots:
            raise ValueError(f"Robot {robot_sn} not found")
        
        robot = self._robots[robot_sn]
        
        if command == "pause":
            if robot["status_code"] == 2:  # working → paused
                robot["status_code"] = 3
                robot["speed"] = 0
                return {"status": "paused"}
        
        elif command == "resume":
            if robot["status_code"] == 3:  # paused → working
                robot["status_code"] = 2
                robot["speed"] = 0.5
                return {"status": "resumed"}
        
        elif command == "cancel_task":
            if robot["status_code"] in [2, 3]:  # working/paused → idle
                progress = robot["task_progress"]
                robot["status_code"] = 1
                robot["current_task_id"] = None
                robot["task_progress"] = None
                robot["speed"] = 0
                return {"status": "cancelled", "progress_at_cancel": progress}
        
        elif command == "go_to_charge":
            robot["status_code"] = 4  # charging
            robot["speed"] = 0
            return {"status": "returning_to_charge"}
        
        elif command == "go_to_location":
            target = params.get("target")
            robot["position"] = target
            return {"status": "navigating"}
        
        elif command == "clear_error":
            if robot["status_code"] == 5:  # error → idle
                robot["status_code"] = 1
                robot["error_code"] = None
                robot["error_message"] = None
                return {"status": "error_cleared"}
        
        return {"status": "unknown_command"}
```

---

## 8. 验收标准

### 8.1 功能验收

- [ ] 12个Tools全部实现
- [ ] Mock模式可正常工作
- [ ] 状态查询实时准确
- [ ] 任务控制流程完整（启动/暂停/恢复/取消）
- [ ] 电量和状态检查完善
- [ ] 故障处理逻辑正确

### 8.2 代码质量

- [ ] 类型注解完整
- [ ] 单元测试覆盖所有Tools
- [ ] Mock模拟器功能完整
- [ ] 错误处理完善
- [ ] 日志记录完整

### 8.3 性能要求

- 状态查询响应 < 200ms
- 支持批量查询20个机器人
- Mock模拟器可运行24小时不崩溃

---

## 9. 开发步骤建议

```
1. 创建目录结构
   src/mcp_servers/robot_gaoxian/
   ├── __init__.py
   ├── server.py
   ├── tools.py
   ├── storage.py
   ├── mock_client.py
   ├── gaoxian_client.py (预留，MVP阶段可为空)
   └── tests/
       ├── __init__.py
       ├── test_tools.py
       └── test_mock.py

2. 实现mock_client.py（Mock模拟器）
   - 这是MVP阶段的核心依赖
   - 确保模拟逻辑真实合理

3. 实现storage.py（机器人数据存储）

4. 实现tools.py（Tool逻辑）
   - 状态查询类Tools
   - 任务控制类Tools
   - 导航控制类Tools
   - 故障处理类Tools

5. 实现server.py（MCP Server入口）

6. 编写测试
   - 状态查询测试
   - 任务控制流程测试
   - 边界条件测试
   - Mock模拟器测试

7. 集成测试
   - 与M2任务管理联调
   - 完整任务执行流程
```

---

**预计开发时间**: 8-10小时（使用Claude Code）

**开发优先级**: P0（Agent执行依赖此模块）

**前置依赖**: F1数据模型、Mock模式配置
