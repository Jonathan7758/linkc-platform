"""
D3: 数据查询API - 查询服务
==========================
统一的数据查询服务实现
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta, timezone
from abc import ABC, abstractmethod
import logging
import json

from .models import (
    PagedResult,
    RobotCurrentStatus,
    RobotStatusPoint,
    PositionPoint,
    RobotUtilization,
    TaskSummary,
    TaskRecord,
    DailyTaskStats,
    ZoneCoverage,
    EfficiencyMetrics,
    ComparisonResult,
    TrendDirection,
    AnomalyEvent,
    AnomalyType,
)

logger = logging.getLogger(__name__)


# ============================================================
# 缓存接口
# ============================================================

class CacheService(ABC):
    """缓存服务接口"""

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass


class InMemoryCacheService(CacheService):
    """内存缓存服务（用于测试）"""

    def __init__(self):
        self._cache: Dict[str, tuple] = {}  # key -> (value, expire_time)

    async def get(self, key: str) -> Optional[str]:
        if key in self._cache:
            value, expire_time = self._cache[key]
            if expire_time is None or datetime.now(timezone.utc) < expire_time:
                return value
            del self._cache[key]
        return None

    async def set(self, key: str, value: str, ttl: int) -> None:
        expire_time = datetime.now(timezone.utc) + timedelta(seconds=ttl) if ttl > 0 else None
        self._cache[key] = (value, expire_time)

    async def delete(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self):
        self._cache.clear()


# ============================================================
# 数据查询服务
# ============================================================

class DataQueryService:
    """
    数据查询服务

    提供统一的数据查询接口，支持缓存
    """

    # 缓存配置
    CACHE_TTL = {
        "current_status": 30,       # 30秒
        "task_summary": 300,        # 5分钟
        "zone_coverage": 600,       # 10分钟
        "efficiency_metrics": 900,  # 15分钟
        "task_trend": 600,          # 10分钟
    }

    def __init__(
        self,
        timeseries_service=None,
        task_repository=None,
        robot_repository=None,
        cache: Optional[CacheService] = None
    ):
        """
        初始化查询服务

        Args:
            timeseries_service: 时序数据服务 (D2)
            task_repository: 任务仓储 (D2)
            robot_repository: 机器人仓储 (D2)
            cache: 缓存服务
        """
        self.timeseries = timeseries_service
        self.task_repo = task_repository
        self.robot_repo = robot_repository
        self.cache = cache or InMemoryCacheService()

    # ========== 机器人数据查询 ==========

    async def get_current_status(
        self,
        tenant_id: str,
        robot_ids: List[str] = None,
        building_id: str = None
    ) -> List[RobotCurrentStatus]:
        """获取机器人当前状态"""
        cache_key = f"robot:status:{tenant_id}:{building_id or 'all'}"

        # 尝试缓存
        cached = await self.cache.get(cache_key)
        if cached:
            data = json.loads(cached)
            return [RobotCurrentStatus(**item) for item in data]

        # 查询数据
        result = await self._query_current_status(tenant_id, robot_ids, building_id)

        # 写入缓存
        await self.cache.set(
            cache_key,
            json.dumps([r.model_dump(mode='json') for r in result]),
            self.CACHE_TTL["current_status"]
        )

        return result

    async def _query_current_status(
        self,
        tenant_id: str,
        robot_ids: List[str] = None,
        building_id: str = None
    ) -> List[RobotCurrentStatus]:
        """实际查询机器人当前状态"""
        # 如果有时序服务，从中获取最新状态
        if self.timeseries and hasattr(self.timeseries, '_data'):
            result = []
            status_table = self.timeseries._data.get("robot_status", [])

            # 获取每个机器人的最新状态
            robot_latest = {}
            for record in status_table:
                if record.get("tenant_id") != tenant_id:
                    continue
                rid = record.get("robot_id")
                if robot_ids and rid not in robot_ids:
                    continue
                if rid not in robot_latest or record.get("timestamp") > robot_latest[rid].get("timestamp"):
                    robot_latest[rid] = record

            for rid, data in robot_latest.items():
                result.append(RobotCurrentStatus(
                    robot_id=rid,
                    name=data.get("name", f"Robot-{rid}"),
                    brand=data.get("brand", "unknown"),
                    status=data.get("status", "unknown"),
                    battery_level=data.get("battery_level", 0),
                    position={
                        "x": data.get("position_x", 0),
                        "y": data.get("position_y", 0),
                        "floor_id": data.get("floor_id")
                    } if data.get("floor_id") else None,
                    current_task={"task_id": data.get("current_task_id")} if data.get("current_task_id") else None,
                    last_updated=data.get("timestamp", datetime.now(timezone.utc))
                ))

            return result

        return []

    async def get_status_history(
        self,
        tenant_id: str,
        robot_id: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "5m"
    ) -> List[RobotStatusPoint]:
        """获取机器人状态历史"""
        if not self.timeseries:
            return []

        # 从时序服务查询
        if hasattr(self.timeseries, '_data'):
            status_table = self.timeseries._data.get("robot_status", [])
            result = []

            for record in status_table:
                if record.get("tenant_id") != tenant_id:
                    continue
                if record.get("robot_id") != robot_id:
                    continue
                ts = record.get("timestamp")
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                if start_time <= ts <= end_time:
                    result.append(RobotStatusPoint(
                        timestamp=ts,
                        status=record.get("status", "unknown"),
                        battery_level=record.get("battery_level", 0)
                    ))

            return sorted(result, key=lambda x: x.timestamp)

        return []

    async def get_position_track(
        self,
        tenant_id: str,
        robot_id: str,
        start_time: datetime,
        end_time: datetime,
        sample_interval: str = "1m"
    ) -> List[PositionPoint]:
        """获取机器人位置轨迹"""
        if not self.timeseries:
            return []

        if hasattr(self.timeseries, '_data'):
            position_table = self.timeseries._data.get("robot_position", [])
            result = []

            for record in position_table:
                if record.get("tenant_id") != tenant_id:
                    continue
                if record.get("robot_id") != robot_id:
                    continue
                ts = record.get("timestamp")
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                if start_time <= ts <= end_time:
                    result.append(PositionPoint(
                        timestamp=ts,
                        x=record.get("x", 0),
                        y=record.get("y", 0),
                        floor_id=record.get("floor_id", "")
                    ))

            return sorted(result, key=lambda x: x.timestamp)

        return []

    async def get_utilization(
        self,
        tenant_id: str,
        robot_ids: List[str] = None,
        target_date: date = None
    ) -> List[RobotUtilization]:
        """获取机器人利用率"""
        if target_date is None:
            target_date = date.today()

        # 计算时间范围
        start_time = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_time = start_time + timedelta(days=1)

        # 获取状态历史
        result = []

        if self.timeseries and hasattr(self.timeseries, '_data'):
            status_table = self.timeseries._data.get("robot_status", [])

            # 按机器人分组计算
            robot_records: Dict[str, List] = {}
            for record in status_table:
                if record.get("tenant_id") != tenant_id:
                    continue
                rid = record.get("robot_id")
                if robot_ids and rid not in robot_ids:
                    continue
                ts = record.get("timestamp")
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                if start_time <= ts <= end_time:
                    if rid not in robot_records:
                        robot_records[rid] = []
                    robot_records[rid].append(record)

            # 计算每个机器人的利用率
            for rid, records in robot_records.items():
                records = sorted(records, key=lambda x: x.get("timestamp", ""))
                total_hours = 24.0  # 假设一天
                working_hours = sum(1 for r in records if r.get("status") == "working") * 0.5  # 简化计算
                charging_hours = sum(1 for r in records if r.get("status") == "charging") * 0.5
                idle_hours = total_hours - working_hours - charging_hours

                result.append(RobotUtilization(
                    robot_id=rid,
                    name=records[0].get("name", f"Robot-{rid}") if records else f"Robot-{rid}",
                    total_hours=total_hours,
                    working_hours=working_hours,
                    charging_hours=charging_hours,
                    idle_hours=max(0, idle_hours),
                    utilization_rate=round(working_hours / total_hours * 100, 1) if total_hours > 0 else 0
                ))

        return result

    # ========== 任务数据查询 ==========

    async def get_task_summary(
        self,
        tenant_id: str,
        target_date: date = None,
        building_id: str = None
    ) -> TaskSummary:
        """获取任务汇总"""
        if target_date is None:
            target_date = date.today()

        cache_key = f"task:summary:{tenant_id}:{target_date}:{building_id or 'all'}"

        # 尝试缓存
        cached = await self.cache.get(cache_key)
        if cached:
            return TaskSummary(**json.loads(cached))

        # 查询数据
        result = await self._query_task_summary(tenant_id, target_date, building_id)

        # 写入缓存
        await self.cache.set(
            cache_key,
            json.dumps(result.model_dump(mode='json')),
            self.CACHE_TTL["task_summary"]
        )

        return result

    async def _query_task_summary(
        self,
        tenant_id: str,
        target_date: date,
        building_id: str = None
    ) -> TaskSummary:
        """实际查询任务汇总"""
        total = completed = in_progress = pending = failed = cancelled = 0
        total_duration = 0
        total_area = 0.0
        completed_count = 0

        if self.task_repo and hasattr(self.task_repo, '_tasks'):
            for task in self.task_repo._tasks.values():
                if task.get("tenant_id") != tenant_id:
                    continue
                # 简化：只看创建日期
                created = task.get("created_at")
                if isinstance(created, str):
                    created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                if created and created.date() != target_date:
                    continue

                total += 1
                status = task.get("status", "")
                if status == "completed":
                    completed += 1
                    total_area += task.get("area_cleaned", 0)
                    if task.get("duration_minutes"):
                        total_duration += task.get("duration_minutes")
                        completed_count += 1
                elif status == "in_progress":
                    in_progress += 1
                elif status == "pending":
                    pending += 1
                elif status == "failed":
                    failed += 1
                elif status == "cancelled":
                    cancelled += 1

        completion_rate = round(completed / total * 100, 1) if total > 0 else 0
        avg_duration = round(total_duration / completed_count) if completed_count > 0 else 0

        return TaskSummary(
            date=target_date,
            total_tasks=total,
            completed=completed,
            in_progress=in_progress,
            pending=pending,
            failed=failed,
            cancelled=cancelled,
            completion_rate=completion_rate,
            avg_completion_time=avg_duration,
            total_area_cleaned=total_area
        )

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
        """获取任务历史记录"""
        records = []

        if self.task_repo and hasattr(self.task_repo, '_tasks'):
            for task in self.task_repo._tasks.values():
                if task.get("tenant_id") != tenant_id:
                    continue
                if zone_id and task.get("zone_id") != zone_id:
                    continue
                if robot_id and task.get("robot_id") != robot_id:
                    continue
                if status and task.get("status") != status:
                    continue

                created = task.get("created_at")
                if isinstance(created, str):
                    created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                if start_date and created and created.date() < start_date:
                    continue
                if end_date and created and created.date() > end_date:
                    continue

                records.append(TaskRecord(
                    task_id=task.get("task_id", ""),
                    tenant_id=tenant_id,
                    zone_id=task.get("zone_id", ""),
                    zone_name=task.get("zone_name"),
                    robot_id=task.get("robot_id"),
                    robot_name=task.get("robot_name"),
                    status=task.get("status", ""),
                    task_type=task.get("task_type", "cleaning"),
                    priority=task.get("priority", 0),
                    scheduled_start=task.get("scheduled_start"),
                    actual_start=task.get("actual_start"),
                    actual_end=task.get("actual_end"),
                    duration_minutes=task.get("duration_minutes"),
                    area_cleaned=task.get("area_cleaned", 0),
                    created_at=created or datetime.now(timezone.utc)
                ))

        # 排序和分页
        records = sorted(records, key=lambda x: x.created_at, reverse=True)
        total = len(records)
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        page_records = records[start_idx:end_idx]

        return PagedResult.create(page_records, total, page, size)

    async def get_task_trend(
        self,
        tenant_id: str,
        building_id: str = None,
        days: int = 7
    ) -> List[DailyTaskStats]:
        """获取任务趋势"""
        cache_key = f"task:trend:{tenant_id}:{building_id or 'all'}:{days}"

        cached = await self.cache.get(cache_key)
        if cached:
            data = json.loads(cached)
            return [DailyTaskStats(**item) for item in data]

        result = []
        today = date.today()

        for i in range(days):
            target_date = today - timedelta(days=i)
            summary = await self._query_task_summary(tenant_id, target_date, building_id)
            result.append(DailyTaskStats(
                date=target_date,
                total=summary.total_tasks,
                completed=summary.completed,
                failed=summary.failed,
                completion_rate=summary.completion_rate
            ))

        result = sorted(result, key=lambda x: x.date)

        await self.cache.set(
            cache_key,
            json.dumps([r.model_dump(mode='json') for r in result]),
            self.CACHE_TTL["task_trend"]
        )

        return result

    # ========== 统计分析查询 ==========

    async def get_efficiency_metrics(
        self,
        tenant_id: str,
        building_id: str = None,
        period: str = "day"
    ) -> EfficiencyMetrics:
        """获取效率指标"""
        cache_key = f"metrics:{tenant_id}:{building_id or 'all'}:{period}"

        cached = await self.cache.get(cache_key)
        if cached:
            return EfficiencyMetrics(**json.loads(cached))

        # 计算指标
        today = date.today()
        task_summary = await self._query_task_summary(tenant_id, today, building_id)
        utilization = await self.get_utilization(tenant_id)

        avg_utilization = 0
        if utilization:
            avg_utilization = sum(u.utilization_rate for u in utilization) / len(utilization)

        # 简化计算
        avg_area_per_hour = task_summary.total_area_cleaned / 8 if task_summary.total_area_cleaned > 0 else 0

        result = EfficiencyMetrics(
            period=str(today),
            avg_task_duration=task_summary.avg_completion_time,
            avg_area_per_hour=round(avg_area_per_hour, 1),
            avg_battery_usage=45.0,  # 模拟值
            robot_utilization=round(avg_utilization, 1),
            task_completion_rate=task_summary.completion_rate
        )

        await self.cache.set(
            cache_key,
            json.dumps(result.model_dump(mode='json')),
            self.CACHE_TTL["efficiency_metrics"]
        )

        return result

    async def get_comparison(
        self,
        tenant_id: str,
        metric: str,
        group_by: str,
        current_period: date,
        compare_period: date = None
    ) -> ComparisonResult:
        """对比分析"""
        if compare_period is None:
            compare_period = current_period - timedelta(days=7)

        current_summary = await self._query_task_summary(tenant_id, current_period)
        compare_summary = await self._query_task_summary(tenant_id, compare_period)

        # 根据指标类型获取值
        if metric == "completion_rate":
            current_value = current_summary.completion_rate
            compare_value = compare_summary.completion_rate
        elif metric == "total_tasks":
            current_value = float(current_summary.total_tasks)
            compare_value = float(compare_summary.total_tasks)
        else:
            current_value = current_summary.completion_rate
            compare_value = compare_summary.completion_rate

        change = current_value - compare_value
        change_percent = round(change / compare_value * 100, 2) if compare_value > 0 else 0

        if change > 0:
            trend = TrendDirection.UP
        elif change < 0:
            trend = TrendDirection.DOWN
        else:
            trend = TrendDirection.STABLE

        return ComparisonResult(
            metric=metric,
            current_value=current_value,
            compare_value=compare_value,
            change=round(change, 2),
            change_percent=change_percent,
            trend=trend
        )

    async def get_anomalies(
        self,
        tenant_id: str,
        start_time: datetime,
        end_time: datetime,
        types: List[str] = None
    ) -> List[AnomalyEvent]:
        """获取异常事件"""
        events = []

        # 从时序数据中检测异常
        if self.timeseries and hasattr(self.timeseries, '_data'):
            status_table = self.timeseries._data.get("robot_status", [])

            for record in status_table:
                if record.get("tenant_id") != tenant_id:
                    continue
                ts = record.get("timestamp")
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                if not (start_time <= ts <= end_time):
                    continue

                # 检测低电量
                battery = record.get("battery_level", 100)
                if battery < 20:
                    if types is None or "battery_low" in types:
                        events.append(AnomalyEvent(
                            event_id=f"evt-{len(events)}",
                            event_type=AnomalyType.BATTERY_LOW,
                            timestamp=ts,
                            robot_id=record.get("robot_id"),
                            description=f"机器人电量低: {battery}%",
                            severity="warning",
                            details={"battery_level": battery}
                        ))

                # 检测错误状态
                if record.get("error_code"):
                    if types is None or "error_alert" in types:
                        events.append(AnomalyEvent(
                            event_id=f"evt-{len(events)}",
                            event_type=AnomalyType.ERROR_ALERT,
                            timestamp=ts,
                            robot_id=record.get("robot_id"),
                            description=f"机器人错误: {record.get('error_code')}",
                            severity="error",
                            details={"error_code": record.get("error_code")}
                        ))

        return sorted(events, key=lambda x: x.timestamp, reverse=True)

    # ========== 空间数据查询 ==========

    async def get_zone_coverage(
        self,
        tenant_id: str,
        floor_id: str,
        target_date: date = None
    ) -> List[ZoneCoverage]:
        """获取区域覆盖率"""
        if target_date is None:
            target_date = date.today()

        cache_key = f"zone:coverage:{floor_id}:{target_date}"

        cached = await self.cache.get(cache_key)
        if cached:
            data = json.loads(cached)
            return [ZoneCoverage(**item) for item in data]

        # 模拟数据
        result = [
            ZoneCoverage(
                zone_id="zone-001",
                zone_name="大堂",
                area_sqm=500,
                cleaned_area=485,
                coverage_rate=97.0,
                clean_count=3
            ),
            ZoneCoverage(
                zone_id="zone-002",
                zone_name="走廊",
                area_sqm=200,
                cleaned_area=190,
                coverage_rate=95.0,
                clean_count=2
            )
        ]

        await self.cache.set(
            cache_key,
            json.dumps([r.model_dump(mode='json') for r in result]),
            self.CACHE_TTL["zone_coverage"]
        )

        return result
