# 模块开发规格书：D3 数据查询 API

## 文档信息

| 项目 | 内容 |
|-----|------|
| 模块ID | D3 |
| 模块名称 | 数据查询 API |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | D2数据存储服务 |

---

## 1. 模块概述

### 1.1 职责描述

数据查询API为上层应用提供统一的数据查询接口，包括：
- **实时数据查询**：获取机器人当前状态
- **历史数据查询**：时间范围查询、轨迹查询
- **统计分析查询**：聚合统计、趋势分析
- **报表数据查询**：为报表模块提供数据

### 1.2 在系统中的位置

```
┌─────────────────────────────────────────────────────────────┐
│                       数据消费者                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Agent层     │ │ API网关层  │ │ 报表模块    │           │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           │
│         │               │               │                   │
│         └───────────────┴───────────────┘                   │
│                         │                                   │
│                         ▼                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           【D3 数据查询API】 ◄── 本模块              │   │
│  │   统一查询接口 / 缓存 / 分页 / 权限                  │   │
│  └─────────────────────────┬───────────────────────────┘   │
│                            │                               │
│                            ▼                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   D2 数据存储服务                    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 接口定义

### 2.1 机器人数据查询

```python
class RobotDataQuery:
    """机器人数据查询服务"""
    
    async def get_current_status(
        self,
        tenant_id: str,
        robot_ids: List[str] = None,
        building_id: str = None
    ) -> List[RobotCurrentStatus]:
        """
        获取机器人当前状态
        
        使用Redis缓存，实时性高
        
        Returns:
            [{
                "robot_id": "xxx",
                "name": "清洁机器人-01",
                "status": "working",
                "battery_level": 75,
                "position": {"x": 10.5, "y": 20.3, "floor_id": "xxx"},
                "current_task": {"task_id": "xxx", "progress": 65},
                "last_updated": "2026-01-20T10:30:00Z"
            }]
        """
        pass
    
    async def get_status_history(
        self,
        tenant_id: str,
        robot_id: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "5m"        # 聚合间隔
    ) -> List[RobotStatusPoint]:
        """
        获取机器人状态历史
        
        Returns:
            [{
                "timestamp": "2026-01-20T10:00:00Z",
                "status": "working",
                "battery_level": 80
            }]
        """
        pass
    
    async def get_position_track(
        self,
        tenant_id: str,
        robot_id: str,
        start_time: datetime,
        end_time: datetime,
        sample_interval: str = "1m"  # 采样间隔
    ) -> List[PositionPoint]:
        """
        获取机器人位置轨迹
        
        Returns:
            [{
                "timestamp": "2026-01-20T10:00:00Z",
                "x": 10.5,
                "y": 20.3,
                "floor_id": "xxx"
            }]
        """
        pass
    
    async def get_utilization(
        self,
        tenant_id: str,
        robot_ids: List[str] = None,
        date: date = None           # 默认今天
    ) -> List[RobotUtilization]:
        """
        获取机器人利用率
        
        Returns:
            [{
                "robot_id": "xxx",
                "name": "清洁机器人-01",
                "total_hours": 8.5,
                "working_hours": 5.2,
                "charging_hours": 2.1,
                "idle_hours": 1.2,
                "utilization_rate": 61.2
            }]
        """
        pass
```

### 2.2 任务数据查询

```python
class TaskDataQuery:
    """任务数据查询服务"""
    
    async def get_task_summary(
        self,
        tenant_id: str,
        date: date = None,
        building_id: str = None
    ) -> TaskSummary:
        """
        获取任务汇总
        
        Returns:
            {
                "date": "2026-01-20",
                "total_tasks": 50,
                "completed": 42,
                "in_progress": 5,
                "pending": 2,
                "failed": 1,
                "completion_rate": 84.0,
                "avg_completion_time": 35,
                "total_area_cleaned": 12500.5
            }
        """
        pass
    
    async def get_task_history(
        self,
        tenant_id: str,
        zone_id: str = None,
        robot_id: str = None,
        status: str = None,
        start_date: date = None,
        end_date: date = None,
        page: int = 1,
        size: int = 20
    ) -> PagedResult[TaskRecord]:
        """
        获取任务历史记录（分页）
        """
        pass
    
    async def get_task_trend(
        self,
        tenant_id: str,
        building_id: str = None,
        days: int = 7
    ) -> List[DailyTaskStats]:
        """
        获取任务趋势（近N天）
        
        Returns:
            [{
                "date": "2026-01-19",
                "total": 48,
                "completed": 45,
                "completion_rate": 93.75
            }]
        """
        pass
```

### 2.3 空间数据查询

```python
class SpaceDataQuery:
    """空间数据查询服务"""
    
    async def get_zone_coverage(
        self,
        tenant_id: str,
        floor_id: str,
        date: date = None
    ) -> List[ZoneCoverage]:
        """
        获取区域清洁覆盖率
        
        Returns:
            [{
                "zone_id": "xxx",
                "zone_name": "大堂",
                "area_sqm": 500,
                "cleaned_area": 485,
                "coverage_rate": 97.0,
                "clean_count": 3
            }]
        """
        pass
    
    async def get_floor_heatmap(
        self,
        tenant_id: str,
        floor_id: str,
        metric: str,                # coverage/frequency/duration
        start_date: date,
        end_date: date
    ) -> FloorHeatmapData:
        """
        获取楼层热力图数据
        
        用于可视化展示清洁频率、覆盖率等
        """
        pass
```

### 2.4 统计分析查询

```python
class AnalyticsQuery:
    """统计分析查询服务"""
    
    async def get_efficiency_metrics(
        self,
        tenant_id: str,
        building_id: str = None,
        period: str = "day"         # day/week/month
    ) -> EfficiencyMetrics:
        """
        获取效率指标
        
        Returns:
            {
                "period": "2026-01-20",
                "avg_task_duration": 32,
                "avg_area_per_hour": 150.5,
                "avg_battery_usage": 45,
                "robot_utilization": 65.2,
                "task_completion_rate": 92.5
            }
        """
        pass
    
    async def get_comparison(
        self,
        tenant_id: str,
        metric: str,                # completion_rate/utilization/efficiency
        group_by: str,              # robot/zone/building
        current_period: date,
        compare_period: date = None # 默认上一周期
    ) -> ComparisonResult:
        """
        对比分析
        
        Returns:
            {
                "metric": "completion_rate",
                "current_value": 92.5,
                "compare_value": 88.3,
                "change": 4.2,
                "change_percent": 4.76,
                "trend": "up"
            }
        """
        pass
    
    async def get_anomalies(
        self,
        tenant_id: str,
        start_time: datetime,
        end_time: datetime,
        types: List[str] = None     # battery_low/task_failed/offline
    ) -> List[AnomalyEvent]:
        """
        获取异常事件
        """
        pass
```

---

## 3. 数据模型

### 3.1 查询结果模型

```python
from pydantic import BaseModel
from typing import List, Optional, Generic, TypeVar
from datetime import datetime, date

T = TypeVar('T')

class PagedResult(BaseModel, Generic[T]):
    """分页结果"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    
class RobotCurrentStatus(BaseModel):
    """机器人当前状态"""
    robot_id: str
    name: str
    brand: str
    status: str
    battery_level: int
    position: Optional[dict] = None
    current_task: Optional[dict] = None
    last_updated: datetime
    
class RobotUtilization(BaseModel):
    """机器人利用率"""
    robot_id: str
    name: str
    total_hours: float
    working_hours: float
    charging_hours: float
    idle_hours: float
    utilization_rate: float
    
class TaskSummary(BaseModel):
    """任务汇总"""
    date: date
    total_tasks: int
    completed: int
    in_progress: int
    pending: int
    failed: int
    completion_rate: float
    avg_completion_time: int        # 分钟
    total_area_cleaned: float       # 平方米
    
class ZoneCoverage(BaseModel):
    """区域覆盖率"""
    zone_id: str
    zone_name: str
    area_sqm: float
    cleaned_area: float
    coverage_rate: float
    clean_count: int
    
class EfficiencyMetrics(BaseModel):
    """效率指标"""
    period: str
    avg_task_duration: int
    avg_area_per_hour: float
    avg_battery_usage: float
    robot_utilization: float
    task_completion_rate: float
```

---

## 4. 实现要求

### 4.1 技术栈

```
语言: Python 3.11+
框架: FastAPI (作为内部服务)
缓存: Redis
数据库: 通过D2服务访问
```

### 4.2 缓存策略

```python
CACHE_CONFIG = {
    "current_status": {
        "ttl": 30,          # 30秒
        "key_pattern": "robot:status:{robot_id}"
    },
    "task_summary": {
        "ttl": 300,         # 5分钟
        "key_pattern": "task:summary:{tenant_id}:{date}"
    },
    "zone_coverage": {
        "ttl": 600,         # 10分钟
        "key_pattern": "zone:coverage:{floor_id}:{date}"
    },
    "efficiency_metrics": {
        "ttl": 900,         # 15分钟
        "key_pattern": "metrics:{tenant_id}:{period}"
    }
}
```

### 4.3 核心实现

```python
from functools import wraps
import redis.asyncio as redis

class DataQueryService:
    def __init__(self, storage: StorageService, cache: redis.Redis):
        self.storage = storage
        self.cache = cache
    
    async def _cache_get(self, key: str) -> Optional[str]:
        return await self.cache.get(key)
    
    async def _cache_set(self, key: str, value: str, ttl: int):
        await self.cache.set(key, value, ex=ttl)
    
    def cached(self, key_pattern: str, ttl: int):
        """缓存装饰器"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 构建缓存key
                cache_key = key_pattern.format(**kwargs)
                
                # 尝试从缓存获取
                cached = await self._cache_get(cache_key)
                if cached:
                    return json.loads(cached)
                
                # 调用实际函数
                result = await func(*args, **kwargs)
                
                # 写入缓存
                await self._cache_set(cache_key, json.dumps(result), ttl)
                
                return result
            return wrapper
        return decorator
```

---

## 5. 测试要求

### 5.1 单元测试用例

```python
class TestDataQuery:
    async def test_get_current_status(self):
        """测试获取当前状态"""
        pass
    
    async def test_get_status_history(self):
        """测试获取状态历史"""
        pass
    
    async def test_task_summary(self):
        """测试任务汇总"""
        pass
    
    async def test_cache_hit(self):
        """测试缓存命中"""
        pass
    
    async def test_cache_miss(self):
        """测试缓存未命中"""
        pass
```

---

## 6. 验收标准

### 6.1 功能验收

- [ ] 实时状态查询正常
- [ ] 历史数据查询正常
- [ ] 统计分析查询正常
- [ ] 分页功能正常
- [ ] 缓存机制生效
- [ ] 多租户隔离正确

### 6.2 性能要求

- 实时查询响应 < 50ms
- 历史查询响应 < 200ms
- 聚合查询响应 < 500ms
- 缓存命中率 > 80%
