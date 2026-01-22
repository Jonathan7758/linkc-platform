"""
D3: 数据查询API 测试
====================
"""

import pytest
from datetime import datetime, date, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from src.data.query import (
    DataQueryService,
    InMemoryCacheService,
    PagedResult,
    RobotCurrentStatus,
    RobotUtilization,
    TaskSummary,
    DailyTaskStats,
    EfficiencyMetrics,
    TrendDirection,
)


class TestInMemoryCacheService:
    """内存缓存服务测试"""

    @pytest.fixture
    def cache(self):
        return InMemoryCacheService()

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """测试设置和获取"""
        await cache.set("key1", "value1", 60)
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        """测试获取不存在的键"""
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """测试删除"""
        await cache.set("key1", "value1", 60)
        await cache.delete("key1")
        result = await cache.get("key1")
        assert result is None


class TestDataQueryService:
    """数据查询服务测试"""

    @pytest.fixture
    def mock_timeseries(self):
        """模拟时序服务"""
        service = MagicMock()
        service._data = {
            "robot_status": [
                {
                    "tenant_id": "tenant_001",
                    "robot_id": "robot_001",
                    "name": "清洁机器人1号",
                    "status": "working",
                    "battery_level": 75,
                    "position_x": 10.5,
                    "position_y": 20.3,
                    "floor_id": "floor_001",
                    "timestamp": datetime.now(timezone.utc)
                },
                {
                    "tenant_id": "tenant_001",
                    "robot_id": "robot_002",
                    "name": "清洁机器人2号",
                    "status": "charging",
                    "battery_level": 15,
                    "position_x": 5.0,
                    "position_y": 5.0,
                    "floor_id": "floor_001",
                    "timestamp": datetime.now(timezone.utc)
                }
            ],
            "robot_position": [
                {
                    "tenant_id": "tenant_001",
                    "robot_id": "robot_001",
                    "x": 10.5,
                    "y": 20.3,
                    "floor_id": "floor_001",
                    "timestamp": datetime.now(timezone.utc)
                }
            ]
        }
        return service

    @pytest.fixture
    def mock_task_repo(self):
        """模拟任务仓储"""
        repo = MagicMock()
        repo._tasks = {
            "task_001": {
                "task_id": "task_001",
                "tenant_id": "tenant_001",
                "zone_id": "zone_001",
                "status": "completed",
                "task_type": "cleaning",
                "area_cleaned": 100.0,
                "duration_minutes": 30,
                "created_at": datetime.now(timezone.utc)
            },
            "task_002": {
                "task_id": "task_002",
                "tenant_id": "tenant_001",
                "zone_id": "zone_002",
                "status": "in_progress",
                "task_type": "cleaning",
                "created_at": datetime.now(timezone.utc)
            },
            "task_003": {
                "task_id": "task_003",
                "tenant_id": "tenant_001",
                "zone_id": "zone_001",
                "status": "pending",
                "task_type": "cleaning",
                "created_at": datetime.now(timezone.utc)
            }
        }
        return repo

    @pytest.fixture
    def service(self, mock_timeseries, mock_task_repo):
        return DataQueryService(
            timeseries_service=mock_timeseries,
            task_repository=mock_task_repo,
            cache=InMemoryCacheService()
        )

    # ========== 机器人查询测试 ==========

    @pytest.mark.asyncio
    async def test_get_current_status(self, service):
        """测试获取当前状态"""
        result = await service.get_current_status("tenant_001")

        assert len(result) == 2
        assert all(isinstance(r, RobotCurrentStatus) for r in result)

        robot1 = next(r for r in result if r.robot_id == "robot_001")
        assert robot1.status == "working"
        assert robot1.battery_level == 75

    @pytest.mark.asyncio
    async def test_get_current_status_cached(self, service):
        """测试状态查询缓存"""
        # 第一次查询
        result1 = await service.get_current_status("tenant_001")
        # 第二次查询应该命中缓存
        result2 = await service.get_current_status("tenant_001")

        assert len(result1) == len(result2)

    @pytest.mark.asyncio
    async def test_get_status_history(self, service):
        """测试获取状态历史"""
        now = datetime.now(timezone.utc)
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)

        result = await service.get_status_history(
            "tenant_001", "robot_001", start, end
        )

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_position_track(self, service):
        """测试获取位置轨迹"""
        now = datetime.now(timezone.utc)
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)

        result = await service.get_position_track(
            "tenant_001", "robot_001", start, end
        )

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_utilization(self, service):
        """测试获取利用率"""
        result = await service.get_utilization("tenant_001")

        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, RobotUtilization)
            assert 0 <= item.utilization_rate <= 100

    # ========== 任务查询测试 ==========

    @pytest.mark.asyncio
    async def test_get_task_summary(self, service):
        """测试获取任务汇总"""
        result = await service.get_task_summary("tenant_001")

        assert isinstance(result, TaskSummary)
        assert result.total_tasks == 3
        assert result.completed == 1
        assert result.in_progress == 1
        assert result.pending == 1

    @pytest.mark.asyncio
    async def test_get_task_summary_cached(self, service):
        """测试任务汇总缓存"""
        result1 = await service.get_task_summary("tenant_001")
        result2 = await service.get_task_summary("tenant_001")

        assert result1.total_tasks == result2.total_tasks

    @pytest.mark.asyncio
    async def test_get_task_history(self, service):
        """测试获取任务历史"""
        result = await service.get_task_history("tenant_001", page=1, size=10)

        assert isinstance(result, PagedResult)
        assert result.total == 3
        assert len(result.items) == 3

    @pytest.mark.asyncio
    async def test_get_task_history_with_filter(self, service):
        """测试带过滤的任务历史"""
        result = await service.get_task_history(
            "tenant_001",
            status="completed",
            page=1,
            size=10
        )

        assert result.total == 1
        assert result.items[0].status == "completed"

    @pytest.mark.asyncio
    async def test_get_task_trend(self, service):
        """测试获取任务趋势"""
        result = await service.get_task_trend("tenant_001", days=7)

        assert isinstance(result, list)
        assert len(result) == 7
        for item in result:
            assert isinstance(item, DailyTaskStats)

    # ========== 统计分析测试 ==========

    @pytest.mark.asyncio
    async def test_get_efficiency_metrics(self, service):
        """测试获取效率指标"""
        result = await service.get_efficiency_metrics("tenant_001")

        assert isinstance(result, EfficiencyMetrics)
        assert 0 <= result.task_completion_rate <= 100

    @pytest.mark.asyncio
    async def test_get_comparison(self, service):
        """测试对比分析"""
        today = date.today()
        result = await service.get_comparison(
            "tenant_001",
            metric="completion_rate",
            group_by="robot",
            current_period=today
        )

        assert result.metric == "completion_rate"
        assert result.trend in [TrendDirection.UP, TrendDirection.DOWN, TrendDirection.STABLE]

    @pytest.mark.asyncio
    async def test_get_anomalies(self, service):
        """测试获取异常事件"""
        now = datetime.now(timezone.utc)
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)

        result = await service.get_anomalies("tenant_001", start, end)

        assert isinstance(result, list)
        # 应该检测到低电量异常
        low_battery = [e for e in result if e.event_type.value == "battery_low"]
        assert len(low_battery) >= 1

    # ========== 空间查询测试 ==========

    @pytest.mark.asyncio
    async def test_get_zone_coverage(self, service):
        """测试获取区域覆盖率"""
        result = await service.get_zone_coverage("tenant_001", "floor_001")

        assert isinstance(result, list)
        assert len(result) > 0
        for item in result:
            assert 0 <= item.coverage_rate <= 100


class TestPagedResult:
    """分页结果测试"""

    def test_create_paged_result(self):
        """测试创建分页结果"""
        items = ["a", "b", "c"]
        result = PagedResult.create(items, total=10, page=1, size=3)

        assert result.items == items
        assert result.total == 10
        assert result.page == 1
        assert result.size == 3
        assert result.pages == 4

    def test_empty_paged_result(self):
        """测试空分页结果"""
        result = PagedResult.create([], total=0, page=1, size=10)

        assert result.items == []
        assert result.total == 0
        assert result.pages == 0
