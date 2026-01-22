"""
G6: 数据查询API - 数据模型
============================
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================
# 枚举类型
# ============================================================

class Granularity(str, Enum):
    """时间粒度"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class ComparisonType(str, Enum):
    """对比类型"""
    ROBOT = "robot"
    FLOOR = "floor"
    PERIOD = "period"


class ExportFormat(str, Enum):
    """导出格式"""
    XLSX = "xlsx"
    CSV = "csv"
    PDF = "pdf"


class ReportType(str, Enum):
    """报表类型"""
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_REPORT = "weekly_report"
    MONTHLY_REPORT = "monthly_report"
    CUSTOM = "custom"


class ExportStatus(str, Enum):
    """导出状态"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TrendDirection(str, Enum):
    """趋势方向"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


# ============================================================
# 请求模型
# ============================================================

class ComparisonRequest(BaseModel):
    """对比分析请求"""
    tenant_id: str
    comparison_type: ComparisonType
    subjects: List[str] = Field(min_length=2, max_length=10)
    metrics: List[str]
    start_date: date
    end_date: date


class DateRange(BaseModel):
    """日期范围"""
    start: date
    end: date


class ExportRequest(BaseModel):
    """导出请求"""
    tenant_id: str
    report_type: ReportType
    format: ExportFormat
    date_range: DateRange
    include_sections: List[str]
    filters: Optional[Dict[str, Any]] = None


# ============================================================
# 响应模型 - KPI
# ============================================================

class CleaningKPI(BaseModel):
    """清洁KPI"""
    tasks_completed: int = 0
    tasks_total: int = 0
    completion_rate: float = 0.0
    total_area_cleaned: float = 0.0
    average_efficiency: float = 0.0
    vs_yesterday: Optional[Dict[str, float]] = None


class RobotKPI(BaseModel):
    """机器人KPI"""
    total: int = 0
    active: int = 0
    idle: int = 0
    charging: int = 0
    error: int = 0
    average_utilization: float = 0.0
    average_battery: float = 0.0


class AlertKPI(BaseModel):
    """告警KPI"""
    critical: int = 0
    warning: int = 0
    info: int = 0


class AgentKPI(BaseModel):
    """Agent KPI"""
    decisions_today: int = 0
    escalations_today: int = 0
    auto_resolution_rate: float = 0.0
    average_feedback_score: float = 0.0


class KPIOverviewResponse(BaseModel):
    """KPI概览响应"""
    date: date
    cleaning: CleaningKPI
    robots: RobotKPI
    alerts: AlertKPI
    agent: AgentKPI


# ============================================================
# 响应模型 - 效率趋势
# ============================================================

class EfficiencyPoint(BaseModel):
    """效率数据点"""
    date: date
    efficiency: float
    area_cleaned: float
    tasks_completed: int
    working_hours: float


class EfficiencySummary(BaseModel):
    """效率汇总"""
    average_efficiency: float
    total_area: float
    total_tasks: int
    trend: TrendDirection
    trend_percent: float


class EfficiencyTrendResponse(BaseModel):
    """效率趋势响应"""
    granularity: Granularity
    series: List[EfficiencyPoint]
    summary: EfficiencySummary


# ============================================================
# 响应模型 - 利用率
# ============================================================

class RobotUtilization(BaseModel):
    """机器人利用率"""
    robot_id: str
    robot_name: str
    utilization_rate: float
    working_hours: float
    idle_hours: float
    charging_hours: float
    tasks_completed: int


class HourlyUtilization(BaseModel):
    """小时利用率"""
    hour: int
    utilization: float


class UtilizationOverall(BaseModel):
    """利用率汇总"""
    average_utilization: float
    total_working_hours: float
    peak_hour: int
    low_hour: int


class UtilizationResponse(BaseModel):
    """利用率响应"""
    by_robot: List[RobotUtilization]
    overall: UtilizationOverall
    by_hour: List[HourlyUtilization]


# ============================================================
# 响应模型 - 覆盖分析
# ============================================================

class ZoneCoverage(BaseModel):
    """区域覆盖"""
    zone_id: str
    zone_name: str
    area: float
    cleaned_area: float
    coverage_rate: float
    clean_count: int
    last_cleaned_at: Optional[datetime] = None


class FloorCoverage(BaseModel):
    """楼层覆盖"""
    floor_id: str
    floor_name: str
    total_area: float
    cleaned_area: float
    coverage_rate: float
    zones: List[ZoneCoverage]


class CoverageSummary(BaseModel):
    """覆盖汇总"""
    total_area: float
    cleaned_area: float
    overall_coverage: float
    uncovered_zones: int


class CoverageAnalysisResponse(BaseModel):
    """覆盖分析响应"""
    building_id: str
    date: date
    floors: List[FloorCoverage]
    summary: CoverageSummary


# ============================================================
# 响应模型 - 任务统计
# ============================================================

class TaskStatsSummary(BaseModel):
    """任务统计汇总"""
    total_tasks: int
    completed: int
    failed: int
    cancelled: int
    completion_rate: float
    average_duration: float
    total_area: float


class TaskStatisticsResponse(BaseModel):
    """任务统计响应"""
    summary: TaskStatsSummary
    by_status: Dict[str, int]
    by_failure_reason: Dict[str, int]
    by_zone_type: Dict[str, Dict[str, Any]]
    performance_distribution: Dict[str, int]


# ============================================================
# 响应模型 - 告警统计
# ============================================================

class AlertStatsSummary(BaseModel):
    """告警统计汇总"""
    total: int
    resolved: int
    pending: int
    average_resolution_time: float


class AlertTrend(BaseModel):
    """告警趋势"""
    date: date
    count: int


class TopAlertRobot(BaseModel):
    """告警最多的机器人"""
    robot_id: str
    robot_name: str
    alert_count: int


class AlertStatisticsResponse(BaseModel):
    """告警统计响应"""
    summary: AlertStatsSummary
    by_level: Dict[str, int]
    by_type: Dict[str, int]
    trend: List[AlertTrend]
    top_robots: List[TopAlertRobot]


# ============================================================
# 响应模型 - 对比分析
# ============================================================

class ComparisonResult(BaseModel):
    """对比结果"""
    subject_id: str
    subject_name: str
    metrics: Dict[str, float]
    rank: int


class ComparisonResponse(BaseModel):
    """对比分析响应"""
    comparison_type: ComparisonType
    period: Dict[str, str]
    results: List[ComparisonResult]
    best_performer: Dict[str, str]


# ============================================================
# 响应模型 - 导出
# ============================================================

class ExportCreateResponse(BaseModel):
    """导出创建响应"""
    export_id: str
    status: ExportStatus
    estimated_time: int = 30


class ExportStatusResponse(BaseModel):
    """导出状态响应"""
    export_id: str
    status: ExportStatus
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    file_size: Optional[int] = None
    error: Optional[str] = None


# ============================================================
# 响应模型 - 实时仪表板
# ============================================================

class RealtimeRobots(BaseModel):
    """实时机器人状态"""
    working: int
    idle: int
    charging: int
    error: int


class RealtimeTasks(BaseModel):
    """实时任务状态"""
    in_progress: int
    queued: int
    completed_today: int


class DashboardRealtimeResponse(BaseModel):
    """实时仪表板响应"""
    timestamp: datetime
    robots: RealtimeRobots
    current_tasks: RealtimeTasks
    efficiency_now: float
    coverage_today: float
    active_alerts: int
    pending_items: int


# ============================================================
# 通用响应
# ============================================================

class ApiResponse(BaseModel):
    """通用API响应"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None
