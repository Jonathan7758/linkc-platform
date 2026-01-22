"""
G6: 数据查询API
==================
提供统一的数据查询和统计分析接口
"""

from .models import (
    # 枚举
    Granularity,
    ComparisonType,
    ExportFormat,
    ReportType,
    ExportStatus,
    TrendDirection,
    # 请求模型
    ComparisonRequest,
    DateRange,
    ExportRequest,
    # KPI响应
    CleaningKPI,
    RobotKPI,
    AlertKPI,
    AgentKPI,
    KPIOverviewResponse,
    # 效率响应
    EfficiencyPoint,
    EfficiencySummary,
    EfficiencyTrendResponse,
    # 利用率响应
    RobotUtilization,
    HourlyUtilization,
    UtilizationOverall,
    UtilizationResponse,
    # 覆盖分析响应
    ZoneCoverage,
    FloorCoverage,
    CoverageSummary,
    CoverageAnalysisResponse,
    # 任务统计响应
    TaskStatsSummary,
    TaskStatisticsResponse,
    # 告警统计响应
    AlertStatsSummary,
    AlertTrend,
    TopAlertRobot,
    AlertStatisticsResponse,
    # 对比分析响应
    ComparisonResult,
    ComparisonResponse,
    # 导出响应
    ExportCreateResponse,
    ExportStatusResponse,
    # 实时仪表板
    RealtimeRobots,
    RealtimeTasks,
    DashboardRealtimeResponse,
    # 通用
    ApiResponse,
)

from .service import DataService
from .router import router

__all__ = [
    # 枚举
    "Granularity",
    "ComparisonType",
    "ExportFormat",
    "ReportType",
    "ExportStatus",
    "TrendDirection",
    # 请求模型
    "ComparisonRequest",
    "DateRange",
    "ExportRequest",
    # KPI响应
    "CleaningKPI",
    "RobotKPI",
    "AlertKPI",
    "AgentKPI",
    "KPIOverviewResponse",
    # 效率响应
    "EfficiencyPoint",
    "EfficiencySummary",
    "EfficiencyTrendResponse",
    # 利用率响应
    "RobotUtilization",
    "HourlyUtilization",
    "UtilizationOverall",
    "UtilizationResponse",
    # 覆盖分析响应
    "ZoneCoverage",
    "FloorCoverage",
    "CoverageSummary",
    "CoverageAnalysisResponse",
    # 任务统计响应
    "TaskStatsSummary",
    "TaskStatisticsResponse",
    # 告警统计响应
    "AlertStatsSummary",
    "AlertTrend",
    "TopAlertRobot",
    "AlertStatisticsResponse",
    # 对比分析响应
    "ComparisonResult",
    "ComparisonResponse",
    # 导出响应
    "ExportCreateResponse",
    "ExportStatusResponse",
    # 实时仪表板
    "RealtimeRobots",
    "RealtimeTasks",
    "DashboardRealtimeResponse",
    # 通用
    "ApiResponse",
    # 服务
    "DataService",
    # 路由
    "router",
]
