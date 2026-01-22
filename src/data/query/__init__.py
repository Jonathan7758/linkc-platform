"""
D3: 数据查询API
===============
统一的数据查询接口，提供：
- 实时数据查询
- 历史数据查询
- 统计分析查询
- 报表数据查询
"""

from .models import (
    # 通用模型
    PagedResult,
    TimeRange,
    TrendDirection,
    # 机器人模型
    RobotCurrentStatus,
    RobotStatusPoint,
    PositionPoint,
    RobotUtilization,
    # 任务模型
    TaskSummary,
    TaskRecord,
    DailyTaskStats,
    # 空间模型
    ZoneCoverage,
    FloorHeatmapData,
    # 统计模型
    EfficiencyMetrics,
    ComparisonResult,
    AnomalyEvent,
    AnomalyType,
)

from .service import (
    CacheService,
    InMemoryCacheService,
    DataQueryService,
)

__all__ = [
    # 通用模型
    "PagedResult",
    "TimeRange",
    "TrendDirection",
    # 机器人模型
    "RobotCurrentStatus",
    "RobotStatusPoint",
    "PositionPoint",
    "RobotUtilization",
    # 任务模型
    "TaskSummary",
    "TaskRecord",
    "DailyTaskStats",
    # 空间模型
    "ZoneCoverage",
    "FloorHeatmapData",
    # 统计模型
    "EfficiencyMetrics",
    "ComparisonResult",
    "AnomalyEvent",
    "AnomalyType",
    # 服务
    "CacheService",
    "InMemoryCacheService",
    "DataQueryService",
]
