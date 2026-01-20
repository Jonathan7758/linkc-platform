# 模块开发规格书：D2 数据存储服务

## 文档信息

| 项目 | 内容 |
|-----|------|
| 模块ID | D2 |
| 模块名称 | 数据存储服务 |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | F1数据模型、PostgreSQL、TimescaleDB |

---

## 1. 模块概述

### 1.1 职责描述

数据存储服务负责持久化存储和管理所有业务数据，包括：
- **时序数据存储**：机器人状态、位置轨迹等时序数据
- **业务数据存储**：空间、任务、排程等业务实体
- **事件日志存储**：系统事件、告警、操作日志
- **数据归档**：历史数据压缩和归档
- **数据索引**：优化查询性能的索引管理

### 1.2 在系统中的位置

```
┌─────────────────────────────────────────────────────────────┐
│                       数据生产者                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ D1数据采集  │ │ MCP Server  │ │ API Gateway │           │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           │
│         │               │               │                   │
│         └───────────────┴───────────────┘                   │
│                         │                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               【D2 数据存储服务】 ◄── 本模块                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  存储抽象层                          │   │
│  │   save() / query() / delete() / archive()           │   │
│  └─────────────────────────┬───────────────────────────┘   │
│                            │                               │
│            ┌───────────────┼───────────────┐               │
│            ▼               ▼               ▼               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ PostgreSQL  │ │ TimescaleDB │ │   Redis     │          │
│  │ (业务数据)  │ │ (时序数据)  │ │ (缓存/实时) │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 数据类型分类

| 数据类型 | 存储引擎 | 示例 | 保留策略 |
|---------|---------|------|---------|
| 业务实体 | PostgreSQL | 空间、任务、排程、用户 | 永久 |
| 时序数据 | TimescaleDB | 机器人状态、位置 | 90天原始，聚合永久 |
| 实时数据 | Redis | 当前状态、会话 | 24小时 |
| 事件日志 | TimescaleDB | 操作日志、告警 | 1年 |

---

## 2. 接口定义

### 2.1 存储服务接口

```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional
from datetime import datetime

T = TypeVar('T')

class StorageService(ABC, Generic[T]):
    """存储服务抽象基类"""
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """保存单个实体"""
        pass
    
    @abstractmethod
    async def save_many(self, entities: List[T]) -> List[T]:
        """批量保存"""
        pass
    
    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        """根据ID获取"""
        pass
    
    @abstractmethod
    async def query(self, filters: dict, page: int = 1, size: int = 20) -> dict:
        """条件查询"""
        pass
    
    @abstractmethod
    async def update(self, id: str, updates: dict) -> Optional[T]:
        """更新实体"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除实体"""
        pass
```

### 2.2 时序数据服务接口

```python
class TimeSeriesService:
    """时序数据服务"""
    
    async def insert(
        self,
        table: str,
        data: List[dict],
        timestamp_field: str = "timestamp"
    ) -> int:
        """
        插入时序数据
        
        Args:
            table: 表名（如 robot_status_ts）
            data: 数据列表
            timestamp_field: 时间戳字段名
            
        Returns:
            插入的记录数
        """
        pass
    
    async def query_range(
        self,
        table: str,
        start_time: datetime,
        end_time: datetime,
        filters: dict = None,
        aggregation: str = None,    # avg/max/min/sum/count
        interval: str = None,       # 1m/5m/1h/1d
        limit: int = 1000
    ) -> List[dict]:
        """
        时间范围查询
        
        Args:
            table: 表名
            start_time: 开始时间
            end_time: 结束时间
            filters: 筛选条件
            aggregation: 聚合函数
            interval: 聚合间隔
            limit: 返回数量限制
        """
        pass
    
    async def query_latest(
        self,
        table: str,
        group_by: str,              # 如 robot_id
        filters: dict = None
    ) -> List[dict]:
        """
        查询每组最新记录
        
        常用于获取每台机器人的最新状态
        """
        pass
    
    async def aggregate(
        self,
        table: str,
        start_time: datetime,
        end_time: datetime,
        aggregations: List[dict],   # [{field: "battery", func: "avg"}]
        group_by: List[str] = None,
        interval: str = None
    ) -> List[dict]:
        """
        聚合查询
        """
        pass
```

### 2.3 事件日志服务接口

```python
class EventLogService:
    """事件日志服务"""
    
    async def log_event(
        self,
        event_type: str,
        tenant_id: str,
        source: str,
        data: dict,
        level: str = "info",        # debug/info/warn/error
        tags: List[str] = None
    ) -> str:
        """记录事件"""
        pass
    
    async def query_events(
        self,
        tenant_id: str,
        event_types: List[str] = None,
        level: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        source: str = None,
        page: int = 1,
        size: int = 50
    ) -> dict:
        """查询事件日志"""
        pass
```

---

## 3. 数据库Schema

### 3.1 业务数据表（PostgreSQL）

```sql
-- 租户表
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 楼宇表
CREATE TABLE buildings (
    building_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    name VARCHAR(255) NOT NULL,
    address TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_buildings_tenant ON buildings(tenant_id);

-- 楼层表
CREATE TABLE floors (
    floor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id UUID NOT NULL REFERENCES buildings(building_id),
    tenant_id UUID NOT NULL,
    floor_number INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    area_sqm DECIMAL(10,2),
    map_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_floors_building ON floors(building_id);

-- 区域表
CREATE TABLE zones (
    zone_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    floor_id UUID NOT NULL REFERENCES floors(floor_id),
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    zone_type VARCHAR(50) NOT NULL,
    area_sqm DECIMAL(10,2),
    priority INT DEFAULT 5,
    boundaries JSONB,
    cleaning_requirements JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_zones_floor ON zones(floor_id);
CREATE INDEX idx_zones_tenant ON zones(tenant_id);

-- 机器人表
CREATE TABLE robots (
    robot_id VARCHAR(100) PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(50) NOT NULL,     -- gaoxian/ecovacs
    model VARCHAR(100),
    capabilities JSONB DEFAULT '{}',
    home_zone_id UUID REFERENCES zones(zone_id),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_robots_tenant ON robots(tenant_id);

-- 清洁排程表
CREATE TABLE cleaning_schedules (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    zone_id UUID NOT NULL REFERENCES zones(zone_id),
    task_type VARCHAR(50) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    time_slots JSONB NOT NULL,
    priority INT DEFAULT 5,
    estimated_duration INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_schedules_tenant ON cleaning_schedules(tenant_id);
CREATE INDEX idx_schedules_zone ON cleaning_schedules(zone_id);

-- 清洁任务表
CREATE TABLE cleaning_tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    schedule_id UUID REFERENCES cleaning_schedules(schedule_id),
    zone_id UUID NOT NULL REFERENCES zones(zone_id),
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority INT DEFAULT 5,
    assigned_robot_id VARCHAR(100) REFERENCES robots(robot_id),
    scheduled_start TIMESTAMPTZ,
    actual_start TIMESTAMPTZ,
    actual_end TIMESTAMPTZ,
    completion_rate INT,
    area_cleaned DECIMAL(10,2),
    failure_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_tasks_tenant ON cleaning_tasks(tenant_id);
CREATE INDEX idx_tasks_status ON cleaning_tasks(status);
CREATE INDEX idx_tasks_scheduled ON cleaning_tasks(scheduled_start);
```

### 3.2 时序数据表（TimescaleDB）

```sql
-- 机器人状态时序表
CREATE TABLE robot_status_ts (
    time TIMESTAMPTZ NOT NULL,
    robot_id VARCHAR(100) NOT NULL,
    tenant_id UUID NOT NULL,
    status VARCHAR(50),
    battery_level INT,
    position_x DECIMAL(10,4),
    position_y DECIMAL(10,4),
    floor_id UUID,
    zone_id UUID,
    current_task_id UUID,
    error_code VARCHAR(50)
);
-- 转换为hypertable
SELECT create_hypertable('robot_status_ts', 'time');
CREATE INDEX idx_robot_status_robot ON robot_status_ts(robot_id, time DESC);

-- 机器人位置轨迹表（高频）
CREATE TABLE robot_position_ts (
    time TIMESTAMPTZ NOT NULL,
    robot_id VARCHAR(100) NOT NULL,
    tenant_id UUID NOT NULL,
    x DECIMAL(10,4) NOT NULL,
    y DECIMAL(10,4) NOT NULL,
    floor_id UUID NOT NULL,
    heading DECIMAL(6,2),
    speed DECIMAL(6,2)
);
SELECT create_hypertable('robot_position_ts', 'time');
CREATE INDEX idx_robot_position ON robot_position_ts(robot_id, time DESC);

-- 任务执行记录时序表
CREATE TABLE task_execution_ts (
    time TIMESTAMPTZ NOT NULL,
    task_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    robot_id VARCHAR(100),
    event_type VARCHAR(50),         -- started/progress/completed/failed
    progress INT,
    area_cleaned DECIMAL(10,2),
    details JSONB
);
SELECT create_hypertable('task_execution_ts', 'time');

-- 事件日志表
CREATE TABLE event_logs (
    time TIMESTAMPTZ NOT NULL,
    event_id UUID DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    level VARCHAR(20) NOT NULL,
    source VARCHAR(100),
    data JSONB,
    tags TEXT[]
);
SELECT create_hypertable('event_logs', 'time');
CREATE INDEX idx_events_tenant_type ON event_logs(tenant_id, event_type, time DESC);
```

### 3.3 数据保留策略

```sql
-- 设置数据保留策略
-- 位置数据保留30天
SELECT add_retention_policy('robot_position_ts', INTERVAL '30 days');

-- 状态数据保留90天
SELECT add_retention_policy('robot_status_ts', INTERVAL '90 days');

-- 事件日志保留1年
SELECT add_retention_policy('event_logs', INTERVAL '1 year');

-- 创建连续聚合（自动汇总）
CREATE MATERIALIZED VIEW robot_status_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    robot_id,
    tenant_id,
    AVG(battery_level) as avg_battery,
    COUNT(*) as record_count
FROM robot_status_ts
GROUP BY bucket, robot_id, tenant_id;
```

---

## 4. 实现要求

### 4.1 技术栈

```
语言: Python 3.11+
ORM: SQLAlchemy 2.0 + asyncpg
数据库: PostgreSQL 15 + TimescaleDB
缓存: Redis 7
连接池: asyncpg pool
```

### 4.2 核心实现

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

class DatabaseManager:
    """数据库连接管理"""
    
    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True
        )
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncSession:
        async with self.async_session() as session:
            yield session

class RobotRepository:
    """机器人数据仓储"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, robot: Robot) -> Robot:
        self.session.add(robot)
        await self.session.commit()
        await self.session.refresh(robot)
        return robot
    
    async def get(self, robot_id: str) -> Optional[Robot]:
        result = await self.session.execute(
            select(Robot).where(Robot.robot_id == robot_id)
        )
        return result.scalar_one_or_none()
    
    async def query(
        self,
        tenant_id: str,
        status: str = None,
        page: int = 1,
        size: int = 20
    ) -> dict:
        query = select(Robot).where(Robot.tenant_id == tenant_id)
        if status:
            query = query.where(Robot.status == status)
        
        # 分页
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.session.execute(query)
        robots = result.scalars().all()
        
        # 计算总数
        count_query = select(func.count()).select_from(Robot).where(Robot.tenant_id == tenant_id)
        total = (await self.session.execute(count_query)).scalar()
        
        return {
            "items": robots,
            "total": total,
            "page": page,
            "size": size
        }
```

### 4.3 时序数据处理

```python
class TimeSeriesRepository:
    """时序数据仓储"""
    
    async def insert_robot_status(self, data: List[RobotStatusData]) -> int:
        """批量插入机器人状态"""
        query = """
            INSERT INTO robot_status_ts 
            (time, robot_id, tenant_id, status, battery_level, position_x, position_y, floor_id, zone_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        async with self.pool.acquire() as conn:
            await conn.executemany(query, [
                (d.timestamp, d.robot_id, d.tenant_id, d.status, d.battery_level,
                 d.position_x, d.position_y, d.floor_id, d.zone_id)
                for d in data
            ])
        return len(data)
    
    async def query_status_range(
        self,
        robot_id: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "5m"
    ) -> List[dict]:
        """查询时间范围内的状态（带聚合）"""
        query = f"""
            SELECT 
                time_bucket('{interval}', time) AS bucket,
                robot_id,
                AVG(battery_level) as avg_battery,
                MODE() WITHIN GROUP (ORDER BY status) as main_status
            FROM robot_status_ts
            WHERE robot_id = $1 AND time BETWEEN $2 AND $3
            GROUP BY bucket, robot_id
            ORDER BY bucket
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, robot_id, start_time, end_time)
        return [dict(row) for row in rows]
```

---

## 5. 测试要求

### 5.1 单元测试用例

```python
class TestStorageService:
    """存储服务测试"""
    
    async def test_save_robot(self):
        """测试保存机器人"""
        pass
    
    async def test_query_robots(self):
        """测试查询机器人列表"""
        pass
    
    async def test_insert_timeseries(self):
        """测试插入时序数据"""
        pass
    
    async def test_query_timeseries_range(self):
        """测试时间范围查询"""
        pass
    
    async def test_aggregation(self):
        """测试聚合查询"""
        pass
```

---

## 6. 验收标准

### 6.1 功能验收

- [ ] 业务数据CRUD正常
- [ ] 时序数据插入正常
- [ ] 时间范围查询正常
- [ ] 聚合查询正常
- [ ] 数据保留策略生效
- [ ] 多租户隔离正确

### 6.2 性能要求

- 单条插入 < 10ms
- 批量插入1000条 < 500ms
- 时间范围查询 < 200ms
- 连接池大小20，支持100并发
