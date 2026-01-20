# 模块开发规格书：D1 数据采集引擎

## 文档信息

| 项目 | 内容 |
|-----|------|
| 模块ID | D1 |
| 模块名称 | 数据采集引擎 |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | F1数据模型、M3/M4机器人MCP |

---

## 1. 模块概述

### 1.1 职责描述

数据采集引擎负责从各类数据源采集数据并存储，包括：
- **定时采集**：周期性采集机器人状态、位置、电量等
- **事件采集**：监听并记录关键事件（任务完成、故障、告警）
- **数据清洗**：标准化不同来源的数据格式
- **数据路由**：将数据发送到存储层和实时流

### 1.2 在系统中的位置

```
┌─────────────────────────────────────────────────────────────┐
│                       MCP Server层                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ M1空间管理  │ │ M3高仙MCP   │ │ M4科沃斯MCP │           │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           │
│         │               │               │                   │
│         └───────────────┼───────────────┘                   │
│                         │                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     数据平台层                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              【D1 数据采集引擎】 ◄── 本模块          │   │
│  │   ┌─────────┐ ┌─────────┐ ┌─────────┐              │   │
│  │   │定时采集器│ │事件监听器│ │数据清洗器│              │   │
│  │   └────┬────┘ └────┬────┘ └────┬────┘              │   │
│  │        │           │           │                    │   │
│  │        └───────────┴───────────┘                    │   │
│  │                    │                                │   │
│  │                    ▼                                │   │
│  │            ┌───────────────┐                        │   │
│  │            │   数据路由器   │                        │   │
│  │            └───────┬───────┘                        │   │
│  └────────────────────┼────────────────────────────────┘   │
│                       │                                     │
│           ┌───────────┼───────────┐                        │
│           ▼           ▼           ▼                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ D2数据存储  │ │ Redis实时流 │ │ 事件总线    │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 输入/输出概述

| 类型 | 内容 |
|-----|------|
| **输入** | MCP Server的数据响应、WebSocket事件流 |
| **输出** | 标准化的时序数据、事件记录 |
| **依赖** | M3/M4 MCP Server、D2数据存储、Redis |

---

## 2. 接口定义

### 2.1 采集任务配置接口

```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class CollectorType(str, Enum):
    ROBOT_STATUS = "robot_status"      # 机器人状态采集
    ROBOT_POSITION = "robot_position"  # 机器人位置采集
    TASK_PROGRESS = "task_progress"    # 任务进度采集
    CONSUMABLES = "consumables"        # 耗材状态采集
    EVENTS = "events"                  # 事件采集

class CollectorConfig(BaseModel):
    """采集器配置"""
    collector_id: str
    collector_type: CollectorType
    tenant_id: str
    enabled: bool = True
    interval_seconds: int = 30         # 采集间隔
    target_mcp: str                    # 目标MCP Server (gaoxian/ecovacs)
    filters: Optional[dict] = None     # 筛选条件
    
class CollectorStatus(BaseModel):
    """采集器状态"""
    collector_id: str
    status: str                        # running/stopped/error
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    records_collected: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
```

### 2.2 采集引擎API

```python
class DataCollectorEngine:
    """数据采集引擎"""
    
    async def start(self) -> None:
        """启动采集引擎"""
        pass
    
    async def stop(self) -> None:
        """停止采集引擎"""
        pass
    
    async def add_collector(self, config: CollectorConfig) -> str:
        """
        添加采集器
        
        Args:
            config: 采集器配置
            
        Returns:
            collector_id
        """
        pass
    
    async def remove_collector(self, collector_id: str) -> bool:
        """移除采集器"""
        pass
    
    async def get_collector_status(self, collector_id: str) -> CollectorStatus:
        """获取采集器状态"""
        pass
    
    async def list_collectors(self, tenant_id: str = None) -> List[CollectorStatus]:
        """列出所有采集器"""
        pass
    
    async def trigger_collect(self, collector_id: str) -> dict:
        """手动触发一次采集"""
        pass
```

### 2.3 数据输出格式

```python
class CollectedData(BaseModel):
    """采集到的数据"""
    data_id: str
    collector_id: str
    tenant_id: str
    data_type: CollectorType
    source: str                        # 数据来源MCP
    timestamp: datetime
    data: dict                         # 实际数据内容
    metadata: Optional[dict] = None    # 元数据
    
class RobotStatusData(BaseModel):
    """机器人状态数据（标准化后）"""
    robot_id: str
    tenant_id: str
    timestamp: datetime
    status: str
    battery_level: int
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    floor_id: Optional[str] = None
    zone_id: Optional[str] = None
    current_task_id: Optional[str] = None
    error_code: Optional[str] = None
    
class RobotPositionData(BaseModel):
    """机器人位置数据（高频采集）"""
    robot_id: str
    tenant_id: str
    timestamp: datetime
    x: float
    y: float
    floor_id: str
    heading: Optional[float] = None    # 朝向角度
    speed: Optional[float] = None      # 移动速度
```

---

## 3. 详细功能说明

### 3.1 功能点列表

| 功能 | 描述 | 优先级 |
|-----|------|-------|
| 定时状态采集 | 周期性采集机器人状态 | P0 |
| 位置轨迹采集 | 高频采集位置数据用于轨迹分析 | P0 |
| 事件监听采集 | 监听MCP事件并记录 | P0 |
| 数据格式标准化 | 统一不同MCP的数据格式 | P0 |
| 数据路由分发 | 将数据发送到不同目的地 | P0 |
| 采集器管理 | 动态添加/移除采集器 | P1 |
| 采集状态监控 | 监控采集器健康状态 | P1 |
| 数据去重 | 避免重复数据 | P1 |
| 断点续采 | 采集中断后恢复 | P2 |

### 3.2 采集策略

```python
# 默认采集配置
DEFAULT_COLLECTORS = {
    "robot_status": {
        "interval": 30,        # 30秒采集一次状态
        "enabled": True
    },
    "robot_position": {
        "interval": 5,         # 5秒采集一次位置（清洁中）
        "idle_interval": 60,   # 空闲时60秒
        "enabled": True
    },
    "task_progress": {
        "interval": 10,        # 10秒采集任务进度
        "enabled": True
    },
    "consumables": {
        "interval": 3600,      # 1小时采集耗材状态
        "enabled": True
    }
}
```

### 3.3 数据标准化规则

```python
# 不同MCP数据标准化映射
NORMALIZATION_RULES = {
    "gaoxian": {
        "status_mapping": {
            "IDLE": "idle",
            "CLEANING": "working",
            "CHARGING": "charging",
            "ERROR": "error"
        },
        "position_transform": lambda p: {"x": p["x"], "y": p["y"]}
    },
    "ecovacs": {
        "status_mapping": {
            "idle": "idle",
            "working": "working",
            "charging": "charging",
            "error": "error"
        },
        "position_transform": lambda p: {"x": p["x"], "y": p["y"]}
    }
}
```

---

## 4. 实现要求

### 4.1 技术栈

```
语言: Python 3.11+
框架: asyncio + APScheduler
消息: Redis Pub/Sub
存储: 通过D2模块
```

### 4.2 核心实现架构

```python
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import Dict, Callable

class DataCollectorEngine:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.collectors: Dict[str, CollectorConfig] = {}
        self.mcp_clients: Dict[str, MCPClient] = {}
        self.data_router = DataRouter()
        
    async def start(self):
        """启动引擎"""
        # 初始化MCP客户端
        await self._init_mcp_clients()
        # 启动调度器
        self.scheduler.start()
        # 加载已配置的采集器
        await self._load_collectors()
        
    async def _collect_robot_status(self, config: CollectorConfig):
        """执行机器人状态采集"""
        mcp = self.mcp_clients[config.target_mcp]
        # 调用MCP获取状态
        result = await mcp.call_tool(
            f"{config.target_mcp}_list_robots",
            {"tenant_id": config.tenant_id}
        )
        if result.success:
            # 标准化数据
            normalized = self._normalize_data(result.data, config.target_mcp)
            # 路由数据
            await self.data_router.route(normalized)
```

### 4.3 数据路由器

```python
class DataRouter:
    """数据路由器"""
    
    def __init__(self):
        self.routes: List[DataRoute] = []
        
    async def route(self, data: CollectedData):
        """路由数据到目的地"""
        for route in self.routes:
            if route.matches(data):
                await route.send(data)
                
class DataRoute:
    """路由规则"""
    destination: str      # "storage" | "redis" | "event_bus"
    data_types: List[str] # 匹配的数据类型
    
    def matches(self, data: CollectedData) -> bool:
        return data.data_type in self.data_types
        
    async def send(self, data: CollectedData):
        if self.destination == "storage":
            await storage_service.save(data)
        elif self.destination == "redis":
            await redis_client.publish(f"data:{data.data_type}", data.json())
```

---

## 5. 测试要求

### 5.1 单元测试用例

```python
class TestDataCollector:
    """数据采集引擎测试"""
    
    async def test_add_collector(self):
        """测试添加采集器"""
        pass
    
    async def test_collect_robot_status(self):
        """测试采集机器人状态"""
        pass
    
    async def test_data_normalization(self):
        """测试数据标准化"""
        # 高仙数据应转换为标准格式
        # 科沃斯数据应转换为标准格式
        pass
    
    async def test_data_routing(self):
        """测试数据路由"""
        pass
    
    async def test_collector_error_handling(self):
        """测试采集器错误处理"""
        pass
```

---

## 6. 验收标准

### 6.1 功能验收

- [ ] 能定时采集机器人状态
- [ ] 能高频采集位置数据
- [ ] 数据标准化正确
- [ ] 数据正确路由到存储层
- [ ] 采集器可动态管理
- [ ] 采集异常有告警

### 6.2 性能要求

- 支持100+采集任务并行
- 单次采集延迟 < 1s
- 数据丢失率 < 0.1%

### 6.3 代码质量

- 单元测试覆盖率 > 80%
- 异步代码正确处理
- 日志完整可追踪
