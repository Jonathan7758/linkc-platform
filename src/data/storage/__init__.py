"""
D2: 数据存储服务
================
统一的数据存储抽象层，支持 PostgreSQL、TimescaleDB、Redis

主要组件：
- DatabaseManager: 数据库连接管理
- StorageService: 存储服务抽象基类
- TimeSeriesService: 时序数据服务
- EventLogService: 事件日志服务
- Repositories: 业务数据仓储
"""

from .base import (
    # 基础类
    StorageService,
    TimeSeriesService,
    EventLogService,
    # 数据模型
    PagedResult,
    QueryFilter,
    SortOrder,
    AggregationSpec,
    TimeSeriesPoint,
    EventLog,
    EventLevel,
)

from .database import (
    DatabaseConfig,
    DatabaseManager,
    InMemoryDatabaseManager,
)

from .timeseries import (
    PostgresTimeSeriesService,
    InMemoryTimeSeriesService,
    RobotStatusData,
    RobotPositionData,
    TaskExecutionData,
)

from .events import (
    PostgresEventLogService,
    InMemoryEventLogService,
)

from .repositories import (
    # 实体模型
    Tenant,
    Robot,
    CleaningSchedule,
    CleaningTask,
    TaskStatus,
    # PostgreSQL 仓储
    RobotRepository,
    TaskRepository,
    ScheduleRepository,
    # 内存仓储
    InMemoryRobotRepository,
    InMemoryTaskRepository,
    InMemoryScheduleRepository,
)


__all__ = [
    # 基础类
    "StorageService",
    "TimeSeriesService",
    "EventLogService",
    # 数据模型
    "PagedResult",
    "QueryFilter",
    "SortOrder",
    "AggregationSpec",
    "TimeSeriesPoint",
    "EventLog",
    "EventLevel",
    # 数据库管理
    "DatabaseConfig",
    "DatabaseManager",
    "InMemoryDatabaseManager",
    # 时序服务
    "PostgresTimeSeriesService",
    "InMemoryTimeSeriesService",
    "RobotStatusData",
    "RobotPositionData",
    "TaskExecutionData",
    # 事件服务
    "PostgresEventLogService",
    "InMemoryEventLogService",
    # 实体模型
    "Tenant",
    "Robot",
    "CleaningSchedule",
    "CleaningTask",
    "TaskStatus",
    # 仓储
    "RobotRepository",
    "TaskRepository",
    "ScheduleRepository",
    "InMemoryRobotRepository",
    "InMemoryTaskRepository",
    "InMemoryScheduleRepository",
]
