"""
G6: 数据查询API - 服务层
============================
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime, timezone, timedelta
import logging
import uuid
import random

from .models import (
    Granularity, ComparisonType, ExportFormat, ReportType, ExportStatus, TrendDirection,
    ComparisonRequest, ExportRequest,
    CleaningKPI, RobotKPI, AlertKPI, AgentKPI, KPIOverviewResponse,
    EfficiencyPoint, EfficiencySummary, EfficiencyTrendResponse,
    RobotUtilization, HourlyUtilization, UtilizationOverall, UtilizationResponse,
    ZoneCoverage, FloorCoverage, CoverageSummary, CoverageAnalysisResponse,
    TaskStatsSummary, TaskStatisticsResponse,
    AlertStatsSummary, AlertTrend, TopAlertRobot, AlertStatisticsResponse,
    ComparisonResult, ComparisonResponse,
    ExportCreateResponse, ExportStatusResponse,
    RealtimeRobots, RealtimeTasks, DashboardRealtimeResponse
)

logger = logging.getLogger(__name__)


class DataService:
    """数据查询服务"""

    def __init__(self, query_service=None, cache=None):
        self.query_service = query_service
        self.cache = cache
        self._exports: Dict[str, Dict[str, Any]] = {}

    # ========== KPI概览 ==========

    async def get_kpi_overview(
        self,
        tenant_id: str,
        building_id: Optional[str] = None,
        query_date: Optional[date] = None
    ) -> KPIOverviewResponse:
        """获取KPI概览"""
        if query_date is None:
            query_date = date.today()

        # 模拟数据
        return KPIOverviewResponse(
            date=query_date,
            cleaning=CleaningKPI(
                tasks_completed=45,
                tasks_total=48,
                completion_rate=93.75,
                total_area_cleaned=12500.5,
                average_efficiency=145.8,
                vs_yesterday={
                    "tasks_completed": 2,
                    "completion_rate": 1.5,
                    "efficiency": -2.3
                }
            ),
            robots=RobotKPI(
                total=15,
                active=12,
                idle=2,
                charging=1,
                error=0,
                average_utilization=78.5,
                average_battery=72.3
            ),
            alerts=AlertKPI(
                critical=0,
                warning=2,
                info=5
            ),
            agent=AgentKPI(
                decisions_today=156,
                escalations_today=3,
                auto_resolution_rate=94.5,
                average_feedback_score=4.2
            )
        )

    # ========== 效率趋势 ==========

    async def get_efficiency_trend(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date,
        building_id: Optional[str] = None,
        granularity: Granularity = Granularity.DAY,
        robot_id: Optional[str] = None
    ) -> EfficiencyTrendResponse:
        """获取效率趋势"""
        # 生成模拟数据
        series = []
        current = start_date
        total_efficiency = 0.0
        total_area = 0.0
        total_tasks = 0

        while current <= end_date:
            efficiency = 140 + random.uniform(-10, 15)
            area = 10000 + random.uniform(-2000, 3000)
            tasks = 40 + random.randint(-5, 8)
            hours = 75 + random.uniform(-10, 15)

            series.append(EfficiencyPoint(
                date=current,
                efficiency=round(efficiency, 1),
                area_cleaned=round(area, 1),
                tasks_completed=tasks,
                working_hours=round(hours, 1)
            ))

            total_efficiency += efficiency
            total_area += area
            total_tasks += tasks

            if granularity == Granularity.DAY:
                current += timedelta(days=1)
            elif granularity == Granularity.WEEK:
                current += timedelta(weeks=1)
            else:
                current += timedelta(days=1)

        avg_efficiency = total_efficiency / len(series) if series else 0
        trend = TrendDirection.UP if series and series[-1].efficiency > series[0].efficiency else TrendDirection.DOWN

        return EfficiencyTrendResponse(
            granularity=granularity,
            series=series,
            summary=EfficiencySummary(
                average_efficiency=round(avg_efficiency, 1),
                total_area=round(total_area, 1),
                total_tasks=total_tasks,
                trend=trend,
                trend_percent=round(random.uniform(1, 5), 1)
            )
        )

    # ========== 利用率 ==========

    async def get_utilization(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date,
        building_id: Optional[str] = None,
        granularity: Granularity = Granularity.DAY
    ) -> UtilizationResponse:
        """获取机器人利用率"""
        # 模拟机器人数据
        robots = []
        for i in range(1, 6):
            util_rate = 70 + random.uniform(-15, 20)
            working = util_rate * 2
            idle = (100 - util_rate) * 1.5
            charging = random.uniform(10, 25)

            robots.append(RobotUtilization(
                robot_id=f"robot_00{i}",
                robot_name=f"清洁机器人{i}号",
                utilization_rate=round(util_rate, 1),
                working_hours=round(working, 1),
                idle_hours=round(idle, 1),
                charging_hours=round(charging, 1),
                tasks_completed=50 + random.randint(-10, 20)
            ))

        # 小时利用率
        hourly = []
        for hour in range(24):
            if 8 <= hour <= 18:
                util = 60 + random.uniform(10, 30)
            elif 6 <= hour <= 22:
                util = 30 + random.uniform(-10, 20)
            else:
                util = 10 + random.uniform(-5, 10)
            hourly.append(HourlyUtilization(hour=hour, utilization=round(util, 1)))

        avg_util = sum(r.utilization_rate for r in robots) / len(robots)
        total_working = sum(r.working_hours for r in robots)
        peak_hour = max(hourly, key=lambda x: x.utilization).hour
        low_hour = min(hourly, key=lambda x: x.utilization).hour

        return UtilizationResponse(
            by_robot=robots,
            overall=UtilizationOverall(
                average_utilization=round(avg_util, 1),
                total_working_hours=round(total_working, 1),
                peak_hour=peak_hour,
                low_hour=low_hour
            ),
            by_hour=hourly
        )

    # ========== 覆盖分析 ==========

    async def get_coverage_analysis(
        self,
        tenant_id: str,
        building_id: str,
        floor_id: Optional[str] = None,
        query_date: Optional[date] = None
    ) -> CoverageAnalysisResponse:
        """获取区域覆盖分析"""
        if query_date is None:
            query_date = date.today()

        now = datetime.now(timezone.utc)

        # 模拟楼层数据
        floors = []
        total_area = 0
        total_cleaned = 0
        uncovered_zones = 0

        for fi in range(1, 4):
            zones = []
            floor_area = 0
            floor_cleaned = 0

            zone_names = ["大堂", "走廊A", "走廊B", "会议室区", "办公区"]
            for zi, name in enumerate(zone_names):
                area = 200 + random.uniform(100, 500)
                coverage = 85 + random.uniform(-20, 15)
                cleaned = area * coverage / 100

                zones.append(ZoneCoverage(
                    zone_id=f"zone_{fi}_{zi+1}",
                    zone_name=name,
                    area=round(area, 1),
                    cleaned_area=round(cleaned, 1),
                    coverage_rate=round(coverage, 2),
                    clean_count=random.randint(1, 4),
                    last_cleaned_at=now - timedelta(hours=random.randint(1, 12))
                ))

                floor_area += area
                floor_cleaned += cleaned
                if coverage < 80:
                    uncovered_zones += 1

            floor_coverage = (floor_cleaned / floor_area * 100) if floor_area > 0 else 0
            floors.append(FloorCoverage(
                floor_id=f"floor_00{fi}",
                floor_name=f"{fi}F",
                total_area=round(floor_area, 1),
                cleaned_area=round(floor_cleaned, 1),
                coverage_rate=round(floor_coverage, 2),
                zones=zones
            ))

            total_area += floor_area
            total_cleaned += floor_cleaned

        overall_coverage = (total_cleaned / total_area * 100) if total_area > 0 else 0

        return CoverageAnalysisResponse(
            building_id=building_id,
            date=query_date,
            floors=floors,
            summary=CoverageSummary(
                total_area=round(total_area, 1),
                cleaned_area=round(total_cleaned, 1),
                overall_coverage=round(overall_coverage, 1),
                uncovered_zones=uncovered_zones
            )
        )

    # ========== 任务统计 ==========

    async def get_task_statistics(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date,
        building_id: Optional[str] = None
    ) -> TaskStatisticsResponse:
        """获取任务统计"""
        total = 215
        completed = 198
        failed = 8
        cancelled = 9

        return TaskStatisticsResponse(
            summary=TaskStatsSummary(
                total_tasks=total,
                completed=completed,
                failed=failed,
                cancelled=cancelled,
                completion_rate=round(completed / total * 100, 1),
                average_duration=42.5,
                total_area=58500.5
            ),
            by_status={
                "completed": completed,
                "failed": failed,
                "cancelled": cancelled
            },
            by_failure_reason={
                "robot_error": 3,
                "battery_low": 2,
                "obstacle": 2,
                "timeout": 1
            },
            by_zone_type={
                "lobby": {"count": 45, "area": 12500.0},
                "corridor": {"count": 80, "area": 20000.0},
                "office": {"count": 60, "area": 18000.0},
                "restroom": {"count": 30, "area": 8000.5}
            },
            performance_distribution={
                "excellent": 85,
                "good": 78,
                "average": 30,
                "poor": 5
            }
        )

    # ========== 告警统计 ==========

    async def get_alert_statistics(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date
    ) -> AlertStatisticsResponse:
        """获取告警统计"""
        # 生成趋势数据
        trend = []
        current = start_date
        while current <= end_date:
            trend.append(AlertTrend(
                date=current,
                count=random.randint(3, 12)
            ))
            current += timedelta(days=1)

        return AlertStatisticsResponse(
            summary=AlertStatsSummary(
                total=45,
                resolved=40,
                pending=5,
                average_resolution_time=15.3
            ),
            by_level={
                "critical": 2,
                "warning": 18,
                "info": 25
            },
            by_type={
                "battery_anomaly": 8,
                "task_timeout": 12,
                "robot_error": 5,
                "coverage_low": 10,
                "schedule_conflict": 10
            },
            trend=trend,
            top_robots=[
                TopAlertRobot(robot_id="robot_003", robot_name="3号", alert_count=8),
                TopAlertRobot(robot_id="robot_007", robot_name="7号", alert_count=6),
                TopAlertRobot(robot_id="robot_002", robot_name="2号", alert_count=5)
            ]
        )

    # ========== 对比分析 ==========

    async def compare_data(
        self,
        request: ComparisonRequest
    ) -> ComparisonResponse:
        """多维度对比分析"""
        results = []
        best_performer = {}

        for i, subject_id in enumerate(request.subjects):
            metrics = {}
            for metric in request.metrics:
                if metric == "efficiency":
                    value = 140 + random.uniform(-15, 20)
                elif metric == "utilization":
                    value = 75 + random.uniform(-10, 15)
                elif metric == "task_count":
                    value = float(50 + random.randint(-10, 20))
                elif metric == "error_rate":
                    value = 1 + random.uniform(0, 3)
                else:
                    value = random.uniform(50, 100)
                metrics[metric] = round(value, 1)

            results.append(ComparisonResult(
                subject_id=subject_id,
                subject_name=f"对象{i+1}",
                metrics=metrics,
                rank=i + 1
            ))

        # 确定最佳表现者
        for metric in request.metrics:
            if metric == "error_rate":
                best = min(results, key=lambda x: x.metrics.get(metric, float('inf')))
            else:
                best = max(results, key=lambda x: x.metrics.get(metric, 0))
            best_performer[metric] = best.subject_id

        # 重新计算排名
        for metric in request.metrics:
            sorted_results = sorted(
                results,
                key=lambda x: x.metrics.get(metric, 0),
                reverse=(metric != "error_rate")
            )
            for rank, r in enumerate(sorted_results, 1):
                if r.rank > rank:
                    r.rank = rank

        return ComparisonResponse(
            comparison_type=request.comparison_type,
            period={
                "start": request.start_date.isoformat(),
                "end": request.end_date.isoformat()
            },
            results=results,
            best_performer=best_performer
        )

    # ========== 导出 ==========

    async def create_export(
        self,
        request: ExportRequest
    ) -> ExportCreateResponse:
        """创建导出任务"""
        export_id = f"export_{uuid.uuid4().hex[:8]}"

        self._exports[export_id] = {
            "export_id": export_id,
            "request": request,
            "status": ExportStatus.PROCESSING.value,
            "created_at": datetime.now(timezone.utc)
        }

        return ExportCreateResponse(
            export_id=export_id,
            status=ExportStatus.PROCESSING,
            estimated_time=30
        )

    async def get_export_status(
        self,
        export_id: str
    ) -> Optional[ExportStatusResponse]:
        """获取导出状态"""
        if export_id not in self._exports:
            return None

        export = self._exports[export_id]

        # 模拟完成
        if export["status"] == ExportStatus.PROCESSING.value:
            export["status"] = ExportStatus.COMPLETED.value
            export["download_url"] = f"https://storage.linkc.com/exports/{export_id}.xlsx"
            export["expires_at"] = datetime.now(timezone.utc) + timedelta(hours=24)
            export["file_size"] = 256000

        return ExportStatusResponse(
            export_id=export_id,
            status=ExportStatus(export["status"]),
            download_url=export.get("download_url"),
            expires_at=export.get("expires_at"),
            file_size=export.get("file_size")
        )

    # ========== 实时仪表板 ==========

    async def get_realtime_dashboard(
        self,
        tenant_id: str,
        building_id: Optional[str] = None
    ) -> DashboardRealtimeResponse:
        """获取实时仪表板数据"""
        return DashboardRealtimeResponse(
            timestamp=datetime.now(timezone.utc),
            robots=RealtimeRobots(
                working=8,
                idle=4,
                charging=2,
                error=1
            ),
            current_tasks=RealtimeTasks(
                in_progress=8,
                queued=3,
                completed_today=32
            ),
            efficiency_now=147.5,
            coverage_today=68.5,
            active_alerts=2,
            pending_items=1
        )
