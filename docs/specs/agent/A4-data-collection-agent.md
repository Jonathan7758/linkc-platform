# A4 数据采集Agent规格书

## 文档信息

| 属性 | 值 |
|-----|-----|
| 模块ID | A4 |
| 模块名称 | 数据采集Agent (Data Collection Agent) |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 规格书 |
| 前置依赖 | A1-agent-runtime, D1-data-collector, M3/M4 MCP Servers |

---

## 1. 模块概述

### 1.1 职责描述

数据采集Agent是一个自主运行的智能体，负责：
1. **定时采集**：按预定策略从各MCP Server采集机器人状态数据
2. **事件订阅**：监听机器人事件并实时处理
3. **数据路由**：将采集的数据发送到数据存储服务
4. **健康监控**：监控数据采集流水线的健康状态
5. **异常上报**：发现数据异常时触发告警

### 1.2 在系统中的位置

```
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Layer                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                Data Collection Agent (A4)                │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │   │
│  │  │ScheduledJob │ │EventListener│ │DataPublisher│       │   │
│  │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘       │   │
│  └─────────┼───────────────┼───────────────┼───────────────┘   │
│            │               │               │                    │
│  ┌─────────▼───────────────▼───────────────▼───────────────┐   │
│  │                    A1 Agent Runtime                      │   │
│  └─────────┬───────────────────────────────────────────────┘   │
└────────────┼────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────────┐
│                        MCP Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ M3 高仙 MCP  │  │ M4 科沃斯MCP │  │  M1 空间MCP  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │D1 数据采集引擎│  │ D2 数据存储  │  │ Redis Pub/Sub│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 核心工作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    数据采集Agent工作流程                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 初始化阶段                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  加载配置 → 注册MCP客户端 → 初始化调度器 → 启动事件监听   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  2. 定时采集循环                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  定时触发 → 获取机器人列表 → 逐个采集状态 → 数据标准化    │   │
│  │      │                                                   │   │
│  │      └──→ 发布到Redis → 写入时序数据库                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  3. 事件处理循环                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  接收事件 → 解析事件类型 → 数据转换 → 存储/转发          │   │
│  │                                     │                    │   │
│  │                                     └──→ 异常检测        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  4. 健康监控                                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  每分钟检查 → 采集延迟 → 数据完整性 → 连接状态           │   │
│  │                          │                               │   │
│  │                          └──→ 超过阈值则上报告警         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 接口定义

### 2.1 Agent配置接口

```python
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import timedelta
from enum import Enum

class CollectionStrategy(str, Enum):
    """采集策略"""
    POLLING = "polling"          # 轮询
    EVENT_DRIVEN = "event"       # 事件驱动
    HYBRID = "hybrid"            # 混合模式

class DataType(str, Enum):
    """数据类型"""
    STATUS = "status"            # 状态数据
    POSITION = "position"        # 位置数据
    TASK_PROGRESS = "task"       # 任务进度
    CONSUMABLES = "consumables"  # 耗材数据
    ERRORS = "errors"            # 错误日志

class CollectionConfig(BaseModel):
    """单项数据采集配置"""
    data_type: DataType
    enabled: bool = True
    interval_seconds: int = Field(ge=1, le=3600)
    strategy: CollectionStrategy = CollectionStrategy.POLLING
    batch_size: int = Field(default=10, ge=1, le=100)
    timeout_seconds: int = Field(default=30, ge=5, le=120)
    retry_count: int = Field(default=3, ge=0, le=5)

class DataCollectionAgentConfig(BaseModel):
    """数据采集Agent配置"""
    agent_id: str = "data-collection-agent"
    tenant_id: str
    
    # MCP连接配置
    mcp_endpoints: Dict[str, str]  # {"gaoxian": "localhost:5001", "ecovacs": "localhost:5002"}
    
    # 采集配置
    collections: List[CollectionConfig] = [
        CollectionConfig(data_type=DataType.STATUS, interval_seconds=30),
        CollectionConfig(data_type=DataType.POSITION, interval_seconds=5),
        CollectionConfig(data_type=DataType.TASK_PROGRESS, interval_seconds=10),
        CollectionConfig(data_type=DataType.CONSUMABLES, interval_seconds=3600),
        CollectionConfig(data_type=DataType.ERRORS, interval_seconds=60, strategy=CollectionStrategy.EVENT_DRIVEN),
    ]
    
    # 健康监控配置
    health_check_interval_seconds: int = 60
    max_collection_delay_seconds: int = 300  # 超过此延迟告警
    
    # Redis配置
    redis_url: str = "redis://localhost:6379"
    redis_channel_prefix: str = "linkc:data:"
```

### 2.2 Agent接口定义

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, List
from datetime import datetime

class DataCollectionAgentInterface(ABC):
    """数据采集Agent接口"""
    
    @abstractmethod
    async def start(self) -> None:
        """启动Agent"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """停止Agent"""
        pass
    
    @abstractmethod
    async def get_status(self) -> "AgentStatus":
        """获取Agent状态"""
        pass
    
    @abstractmethod
    async def trigger_collection(self, data_type: DataType) -> CollectionResult:
        """手动触发一次采集"""
        pass
    
    @abstractmethod
    async def update_config(self, config: DataCollectionAgentConfig) -> None:
        """更新配置（热更新）"""
        pass

class CollectionResult(BaseModel):
    """采集结果"""
    data_type: DataType
    timestamp: datetime
    robot_count: int
    success_count: int
    failed_count: int
    duration_ms: int
    errors: List[str] = []

class AgentStatus(BaseModel):
    """Agent状态"""
    agent_id: str
    state: str  # running, stopped, error
    uptime_seconds: int
    last_collection: Dict[DataType, datetime]
    collection_stats: Dict[DataType, CollectionStats]
    health: HealthStatus

class CollectionStats(BaseModel):
    """采集统计"""
    total_collections: int
    successful: int
    failed: int
    avg_duration_ms: float
    last_error: Optional[str]
    last_error_time: Optional[datetime]

class HealthStatus(BaseModel):
    """健康状态"""
    healthy: bool
    checks: Dict[str, bool]  # {"mcp_connection": True, "redis_connection": True, ...}
    issues: List[str]
```

### 2.3 数据发布接口

```python
class DataPublisher(ABC):
    """数据发布接口"""
    
    @abstractmethod
    async def publish_robot_status(self, status: "RobotStatusData") -> None:
        """发布机器人状态"""
        pass
    
    @abstractmethod
    async def publish_robot_position(self, position: "RobotPositionData") -> None:
        """发布机器人位置"""
        pass
    
    @abstractmethod
    async def publish_task_progress(self, progress: "TaskProgressData") -> None:
        """发布任务进度"""
        pass
    
    @abstractmethod
    async def publish_error_event(self, event: "RobotErrorEvent") -> None:
        """发布错误事件"""
        pass
    
    @abstractmethod
    async def publish_batch(self, data_list: List[Any]) -> int:
        """批量发布，返回成功数量"""
        pass

# 数据模型定义
class RobotStatusData(BaseModel):
    """机器人状态数据"""
    robot_id: str
    tenant_id: str
    timestamp: datetime
    state: str
    battery_level: int
    is_charging: bool
    current_task_id: Optional[str]
    error_code: Optional[str]
    metadata: Dict[str, Any] = {}

class RobotPositionData(BaseModel):
    """机器人位置数据"""
    robot_id: str
    tenant_id: str
    timestamp: datetime
    x: float
    y: float
    floor_id: str
    heading: Optional[float]
    speed: Optional[float]

class TaskProgressData(BaseModel):
    """任务进度数据"""
    task_id: str
    robot_id: str
    tenant_id: str
    timestamp: datetime
    progress_percent: int
    cleaned_area_sqm: float
    remaining_area_sqm: float
    estimated_completion: Optional[datetime]

class RobotErrorEvent(BaseModel):
    """机器人错误事件"""
    event_id: str
    robot_id: str
    tenant_id: str
    timestamp: datetime
    error_code: str
    error_message: str
    severity: str  # info, warning, error, critical
    resolved: bool = False
```

---

## 3. 数据模型

### 3.1 采集任务模型

```python
class CollectionJob(BaseModel):
    """采集任务"""
    job_id: str
    data_type: DataType
    scheduled_time: datetime
    status: str  # pending, running, completed, failed
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[CollectionResult]

class CollectionQueue(BaseModel):
    """采集队列"""
    pending_jobs: List[CollectionJob]
    running_jobs: List[CollectionJob]
    completed_jobs: List[CollectionJob]  # 最近100个
    failed_jobs: List[CollectionJob]     # 最近100个
```

### 3.2 品牌适配器模型

```python
class BrandAdapter(ABC):
    """机器人品牌适配器"""
    brand: str
    
    @abstractmethod
    async def get_all_robots(self, tenant_id: str) -> List[str]:
        """获取所有机器人ID"""
        pass
    
    @abstractmethod
    async def get_robot_status(self, robot_id: str) -> RobotStatusData:
        """获取机器人状态"""
        pass
    
    @abstractmethod
    async def get_robot_position(self, robot_id: str) -> RobotPositionData:
        """获取机器人位置"""
        pass
    
    @abstractmethod
    async def subscribe_events(self) -> AsyncIterator[RobotErrorEvent]:
        """订阅事件流"""
        pass

class GaoxianAdapter(BrandAdapter):
    """高仙机器人适配器"""
    brand = "gaoxian"
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp = mcp_client

class EcovacsAdapter(BrandAdapter):
    """科沃斯机器人适配器"""
    brand = "ecovacs"
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp = mcp_client
```

---

## 4. 实现要求

### 4.1 技术栈

- Python 3.11+
- asyncio + APScheduler（定时调度）
- aioredis（Redis连接）
- A1 Agent Runtime（基础框架）
- MCP SDK（MCP通信）

### 4.2 核心实现

#### 4.2.1 Agent主类

```python
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

class DataCollectionAgent(BaseAgent):
    """数据采集Agent实现"""
    
    def __init__(self, config: DataCollectionAgentConfig):
        super().__init__(
            agent_id=config.agent_id,
            agent_type="data_collection"
        )
        self.config = config
        self.scheduler = AsyncIOScheduler()
        self.adapters: Dict[str, BrandAdapter] = {}
        self.publisher: DataPublisher = None
        self.stats: Dict[DataType, CollectionStats] = {}
        
    async def _on_start(self) -> None:
        """启动时初始化"""
        # 初始化MCP客户端和适配器
        for brand, endpoint in self.config.mcp_endpoints.items():
            mcp_client = await self._create_mcp_client(brand, endpoint)
            self.adapters[brand] = self._create_adapter(brand, mcp_client)
        
        # 初始化数据发布器
        self.publisher = RedisDataPublisher(self.config.redis_url)
        await self.publisher.connect()
        
        # 注册采集任务
        for collection in self.config.collections:
            if collection.enabled and collection.strategy in [CollectionStrategy.POLLING, CollectionStrategy.HYBRID]:
                self.scheduler.add_job(
                    self._collect_data,
                    trigger=IntervalTrigger(seconds=collection.interval_seconds),
                    args=[collection],
                    id=f"collect_{collection.data_type}",
                    name=f"Collect {collection.data_type}"
                )
        
        # 启动事件监听
        for brand, adapter in self.adapters.items():
            asyncio.create_task(self._listen_events(brand, adapter))
        
        # 启动健康检查
        self.scheduler.add_job(
            self._health_check,
            trigger=IntervalTrigger(seconds=self.config.health_check_interval_seconds),
            id="health_check"
        )
        
        self.scheduler.start()
    
    async def _on_stop(self) -> None:
        """停止时清理"""
        self.scheduler.shutdown()
        await self.publisher.disconnect()
        for adapter in self.adapters.values():
            await adapter.close()
    
    async def _collect_data(self, collection: CollectionConfig) -> CollectionResult:
        """执行数据采集"""
        start_time = datetime.now()
        success_count = 0
        failed_count = 0
        errors = []
        
        try:
            # 获取所有机器人
            all_robots = []
            for brand, adapter in self.adapters.items():
                robots = await adapter.get_all_robots(self.config.tenant_id)
                all_robots.extend([(brand, rid) for rid in robots])
            
            # 批量采集
            for batch in self._batch_iter(all_robots, collection.batch_size):
                tasks = []
                for brand, robot_id in batch:
                    tasks.append(self._collect_single(
                        collection.data_type,
                        self.adapters[brand],
                        robot_id
                    ))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        failed_count += 1
                        errors.append(str(result))
                    else:
                        success_count += 1
            
            # 记录活动
            await self.log_activity(
                activity_type="collection_completed",
                details={
                    "data_type": collection.data_type,
                    "success": success_count,
                    "failed": failed_count
                }
            )
            
        except Exception as e:
            await self.log_activity(
                activity_type="collection_error",
                details={"error": str(e)},
                level="error"
            )
            raise
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return CollectionResult(
            data_type=collection.data_type,
            timestamp=start_time,
            robot_count=len(all_robots),
            success_count=success_count,
            failed_count=failed_count,
            duration_ms=duration_ms,
            errors=errors[:10]  # 只保留前10个错误
        )
    
    async def _collect_single(
        self,
        data_type: DataType,
        adapter: BrandAdapter,
        robot_id: str
    ) -> None:
        """采集单个机器人数据"""
        if data_type == DataType.STATUS:
            data = await adapter.get_robot_status(robot_id)
            await self.publisher.publish_robot_status(data)
        elif data_type == DataType.POSITION:
            data = await adapter.get_robot_position(robot_id)
            await self.publisher.publish_robot_position(data)
        # ... 其他数据类型
    
    async def _listen_events(self, brand: str, adapter: BrandAdapter) -> None:
        """监听事件流"""
        try:
            async for event in adapter.subscribe_events():
                await self.publisher.publish_error_event(event)
                
                # 检查是否需要升级
                if event.severity == "critical":
                    await self.escalate(
                        level=EscalationLevel.ERROR,
                        reason=f"机器人严重错误: {event.error_message}",
                        context={"robot_id": event.robot_id, "error": event.error_code}
                    )
        except Exception as e:
            await self.log_activity(
                activity_type="event_listener_error",
                details={"brand": brand, "error": str(e)},
                level="error"
            )
    
    async def _health_check(self) -> None:
        """健康检查"""
        issues = []
        
        # 检查MCP连接
        for brand, adapter in self.adapters.items():
            if not await adapter.is_connected():
                issues.append(f"MCP {brand} 连接断开")
        
        # 检查采集延迟
        for data_type, stats in self.stats.items():
            if stats.last_collection:
                delay = (datetime.now() - stats.last_collection).total_seconds()
                if delay > self.config.max_collection_delay_seconds:
                    issues.append(f"{data_type} 采集延迟 {delay}s")
        
        # 检查Redis连接
        if not await self.publisher.is_connected():
            issues.append("Redis 连接断开")
        
        if issues:
            await self.escalate(
                level=EscalationLevel.WARNING,
                reason="数据采集健康检查发现问题",
                context={"issues": issues}
            )
```

#### 4.2.2 Redis数据发布器

```python
import aioredis
import json

class RedisDataPublisher(DataPublisher):
    """Redis数据发布器实现"""
    
    def __init__(self, redis_url: str, channel_prefix: str = "linkc:data:"):
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self.redis: aioredis.Redis = None
    
    async def connect(self) -> None:
        self.redis = await aioredis.from_url(self.redis_url)
    
    async def disconnect(self) -> None:
        if self.redis:
            await self.redis.close()
    
    async def is_connected(self) -> bool:
        try:
            await self.redis.ping()
            return True
        except:
            return False
    
    async def publish_robot_status(self, status: RobotStatusData) -> None:
        channel = f"{self.channel_prefix}status:{status.tenant_id}"
        await self.redis.publish(channel, status.model_dump_json())
        
        # 同时写入实时缓存
        key = f"robot:status:{status.robot_id}"
        await self.redis.setex(key, 60, status.model_dump_json())
    
    async def publish_robot_position(self, position: RobotPositionData) -> None:
        channel = f"{self.channel_prefix}position:{position.tenant_id}"
        await self.redis.publish(channel, position.model_dump_json())
        
        # 更新位置缓存
        key = f"robot:position:{position.robot_id}"
        await self.redis.setex(key, 30, position.model_dump_json())
    
    async def publish_task_progress(self, progress: TaskProgressData) -> None:
        channel = f"{self.channel_prefix}task:{progress.tenant_id}"
        await self.redis.publish(channel, progress.model_dump_json())
    
    async def publish_error_event(self, event: RobotErrorEvent) -> None:
        channel = f"{self.channel_prefix}error:{event.tenant_id}"
        await self.redis.publish(channel, event.model_dump_json())
        
        # 写入错误列表
        key = f"robot:errors:{event.robot_id}"
        await self.redis.lpush(key, event.model_dump_json())
        await self.redis.ltrim(key, 0, 99)  # 保留最近100条
    
    async def publish_batch(self, data_list: List[Any]) -> int:
        """批量发布"""
        pipe = self.redis.pipeline()
        count = 0
        
        for data in data_list:
            if isinstance(data, RobotStatusData):
                channel = f"{self.channel_prefix}status:{data.tenant_id}"
                pipe.publish(channel, data.model_dump_json())
                count += 1
            # ... 其他类型
        
        await pipe.execute()
        return count
```

### 4.3 代码规范

1. **异常处理**：采集失败不应影响其他采集任务
2. **超时控制**：每次采集必须设置超时
3. **重试机制**：采集失败自动重试（指数退避）
4. **日志记录**：记录所有采集活动和异常

---

## 5. 详细功能说明

### 5.1 功能点列表

| 功能 | 描述 | 优先级 |
|-----|------|-------|
| 定时状态采集 | 按配置间隔采集机器人状态 | P0 |
| 定时位置采集 | 按配置间隔采集机器人位置 | P0 |
| 任务进度采集 | 采集正在执行的任务进度 | P0 |
| 事件监听 | 监听机器人错误事件 | P0 |
| 数据发布 | 发布数据到Redis通道 | P0 |
| 实时缓存 | 维护机器人最新状态缓存 | P1 |
| 健康监控 | 监控采集流水线健康 | P1 |
| 手动触发 | 支持手动触发采集 | P2 |
| 配置热更新 | 运行时更新采集配置 | P2 |

### 5.2 业务规则

1. **采集频率规则**
   - 位置数据：5秒
   - 状态数据：30秒
   - 任务进度：10秒
   - 耗材数据：1小时

2. **数据缓存规则**
   - 状态缓存：60秒TTL
   - 位置缓存：30秒TTL
   - 错误列表：保留最近100条

3. **告警规则**
   - 采集延迟超过5分钟：WARNING
   - MCP连接断开：ERROR
   - Redis连接断开：CRITICAL

### 5.3 边界条件

1. **MCP连接断开**
   - 自动重连，最多重试3次
   - 重试间隔：5s, 15s, 45s
   - 重连失败后触发告警

2. **Redis连接断开**
   - 数据暂存内存队列（最多1000条）
   - 恢复连接后批量发送

3. **机器人离线**
   - 标记离线状态
   - 继续尝试采集（可能恢复）

---

## 6. 测试要求

### 6.1 单元测试用例

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

@pytest.mark.asyncio
async def test_collect_robot_status():
    """测试状态采集"""
    # Arrange
    agent = DataCollectionAgent(config)
    mock_adapter = AsyncMock(spec=BrandAdapter)
    mock_adapter.get_all_robots.return_value = ["robot-1", "robot-2"]
    mock_adapter.get_robot_status.return_value = RobotStatusData(
        robot_id="robot-1",
        tenant_id="tenant-1",
        timestamp=datetime.now(),
        state="idle",
        battery_level=80,
        is_charging=False
    )
    agent.adapters["gaoxian"] = mock_adapter
    
    # Act
    result = await agent._collect_data(CollectionConfig(
        data_type=DataType.STATUS,
        interval_seconds=30
    ))
    
    # Assert
    assert result.success_count == 2
    assert result.failed_count == 0
    mock_adapter.get_robot_status.assert_called()

@pytest.mark.asyncio
async def test_collect_with_failure():
    """测试部分采集失败"""
    # Arrange
    agent = DataCollectionAgent(config)
    mock_adapter = AsyncMock(spec=BrandAdapter)
    mock_adapter.get_all_robots.return_value = ["robot-1", "robot-2"]
    mock_adapter.get_robot_status.side_effect = [
        RobotStatusData(...),  # 成功
        Exception("Connection timeout")  # 失败
    ]
    agent.adapters["gaoxian"] = mock_adapter
    
    # Act
    result = await agent._collect_data(CollectionConfig(
        data_type=DataType.STATUS,
        interval_seconds=30
    ))
    
    # Assert
    assert result.success_count == 1
    assert result.failed_count == 1
    assert len(result.errors) == 1

@pytest.mark.asyncio
async def test_health_check_detects_delay():
    """测试健康检查检测延迟"""
    # Arrange
    agent = DataCollectionAgent(config)
    agent.stats[DataType.STATUS] = CollectionStats(
        last_collection=datetime.now() - timedelta(minutes=10)  # 10分钟前
    )
    agent.config.max_collection_delay_seconds = 300  # 5分钟
    
    # Act
    await agent._health_check()
    
    # Assert
    # 应该触发告警
    assert agent.escalation_handler.escalate.called

@pytest.mark.asyncio
async def test_redis_publish():
    """测试Redis发布"""
    # Arrange
    publisher = RedisDataPublisher("redis://localhost:6379")
    await publisher.connect()
    
    status = RobotStatusData(
        robot_id="robot-1",
        tenant_id="tenant-1",
        timestamp=datetime.now(),
        state="cleaning",
        battery_level=65,
        is_charging=False
    )
    
    # Act
    await publisher.publish_robot_status(status)
    
    # Assert
    cached = await publisher.redis.get("robot:status:robot-1")
    assert cached is not None
```

### 6.2 集成测试场景

| 场景 | 描述 | 预期结果 |
|-----|------|---------|
| 正常采集 | 启动Agent，等待30秒 | 状态数据被采集和发布 |
| MCP重连 | 断开MCP后重连 | 自动重连并恢复采集 |
| Redis重连 | 断开Redis后重连 | 缓存数据被补发 |
| 配置更新 | 更新采集间隔 | 立即生效 |

---

## 7. 验收标准

### 7.1 功能验收

- [ ] 能够按配置间隔采集机器人状态
- [ ] 能够按配置间隔采集机器人位置
- [ ] 能够监听机器人错误事件
- [ ] 数据正确发布到Redis通道
- [ ] 实时缓存正确维护
- [ ] 健康检查能检测异常并告警
- [ ] 支持手动触发采集

### 7.2 性能要求

| 指标 | 要求 |
|-----|------|
| 单次状态采集延迟 | < 100ms |
| 支持的机器人数量 | 100+ |
| 采集调度精度 | ±1秒 |
| Redis发布延迟 | < 10ms |
| 内存占用 | < 200MB |

### 7.3 代码质量

- [ ] 单元测试覆盖率 > 80%
- [ ] 所有函数有类型注解
- [ ] 关键逻辑有注释
- [ ] 符合项目代码规范

---

*文档版本：1.0*
*更新日期：2026年1月*
