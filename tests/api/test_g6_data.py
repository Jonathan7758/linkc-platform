"""
G6: 数据查询API 测试
======================
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.data import (
    router, DataService,
    ComparisonRequest, ExportRequest, DateRange,
    Granularity, ComparisonType, ReportType, ExportFormat
)


@pytest.fixture
def app():
    """创建测试应用"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def service():
    """创建服务实例"""
    return DataService()


class TestDataService:
    """数据服务测试"""

    @pytest.mark.asyncio
    async def test_get_kpi_overview(self, service):
        """测试KPI概览"""
        result = await service.get_kpi_overview("tenant_001")

        assert result.date is not None
        assert result.cleaning.tasks_completed >= 0
        assert result.robots.total >= 0
        assert result.alerts is not None

    @pytest.mark.asyncio
    async def test_get_kpi_overview_with_date(self, service):
        """测试指定日期的KPI"""
        query_date = date.today() - timedelta(days=1)
        result = await service.get_kpi_overview("tenant_001", query_date=query_date)

        assert result.date == query_date

    @pytest.mark.asyncio
    async def test_get_efficiency_trend(self, service):
        """测试效率趋势"""
        start = date.today() - timedelta(days=7)
        end = date.today()

        result = await service.get_efficiency_trend(
            "tenant_001", start, end
        )

        assert len(result.series) > 0
        assert result.summary.average_efficiency > 0
        assert result.granularity == Granularity.DAY

    @pytest.mark.asyncio
    async def test_get_efficiency_trend_weekly(self, service):
        """测试周粒度效率趋势"""
        start = date.today() - timedelta(days=30)
        end = date.today()

        result = await service.get_efficiency_trend(
            "tenant_001", start, end,
            granularity=Granularity.WEEK
        )

        assert result.granularity == Granularity.WEEK

    @pytest.mark.asyncio
    async def test_get_utilization(self, service):
        """测试机器人利用率"""
        start = date.today() - timedelta(days=7)
        end = date.today()

        result = await service.get_utilization("tenant_001", start, end)

        assert len(result.by_robot) > 0
        assert len(result.by_hour) == 24
        assert result.overall.average_utilization > 0

    @pytest.mark.asyncio
    async def test_get_coverage_analysis(self, service):
        """测试覆盖分析"""
        result = await service.get_coverage_analysis(
            "tenant_001", "building_001"
        )

        assert result.building_id == "building_001"
        assert len(result.floors) > 0
        assert result.summary.overall_coverage >= 0

    @pytest.mark.asyncio
    async def test_get_task_statistics(self, service):
        """测试任务统计"""
        start = date.today() - timedelta(days=7)
        end = date.today()

        result = await service.get_task_statistics("tenant_001", start, end)

        assert result.summary.total_tasks > 0
        assert result.summary.completion_rate >= 0
        assert "completed" in result.by_status

    @pytest.mark.asyncio
    async def test_get_alert_statistics(self, service):
        """测试告警统计"""
        start = date.today() - timedelta(days=7)
        end = date.today()

        result = await service.get_alert_statistics("tenant_001", start, end)

        assert result.summary.total >= 0
        assert "critical" in result.by_level
        assert len(result.trend) > 0

    @pytest.mark.asyncio
    async def test_compare_data(self, service):
        """测试对比分析"""
        request = ComparisonRequest(
            tenant_id="tenant_001",
            comparison_type=ComparisonType.ROBOT,
            subjects=["robot_001", "robot_002", "robot_003"],
            metrics=["efficiency", "utilization"],
            start_date=date.today() - timedelta(days=7),
            end_date=date.today()
        )

        result = await service.compare_data(request)

        assert result.comparison_type == ComparisonType.ROBOT
        assert len(result.results) == 3
        assert "efficiency" in result.best_performer

    @pytest.mark.asyncio
    async def test_create_export(self, service):
        """测试创建导出"""
        request = ExportRequest(
            tenant_id="tenant_001",
            report_type=ReportType.DAILY_SUMMARY,
            format=ExportFormat.XLSX,
            date_range=DateRange(
                start=date.today() - timedelta(days=7),
                end=date.today()
            ),
            include_sections=["kpi", "efficiency"]
        )

        result = await service.create_export(request)

        assert result.export_id is not None
        assert result.status.value == "processing"

    @pytest.mark.asyncio
    async def test_get_export_status(self, service):
        """测试获取导出状态"""
        # 先创建导出
        request = ExportRequest(
            tenant_id="tenant_001",
            report_type=ReportType.DAILY_SUMMARY,
            format=ExportFormat.XLSX,
            date_range=DateRange(
                start=date.today() - timedelta(days=7),
                end=date.today()
            ),
            include_sections=["kpi"]
        )
        create_result = await service.create_export(request)

        # 获取状态
        result = await service.get_export_status(create_result.export_id)

        assert result is not None
        assert result.export_id == create_result.export_id

    @pytest.mark.asyncio
    async def test_get_export_status_not_found(self, service):
        """测试获取不存在的导出"""
        result = await service.get_export_status("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_realtime_dashboard(self, service):
        """测试实时仪表板"""
        result = await service.get_realtime_dashboard("tenant_001")

        assert result.timestamp is not None
        assert result.robots.working >= 0
        assert result.current_tasks.in_progress >= 0


class TestDataRouter:
    """数据路由测试"""

    def test_get_kpi_overview(self, client):
        """测试KPI概览接口"""
        response = client.get("/api/v1/data/kpi/overview")

        assert response.status_code == 200
        data = response.json()
        assert "cleaning" in data
        assert "robots" in data

    def test_get_efficiency_trend(self, client):
        """测试效率趋势接口"""
        start = (date.today() - timedelta(days=7)).isoformat()
        end = date.today().isoformat()

        response = client.get(
            "/api/v1/data/efficiency/trend",
            params={"start_date": start, "end_date": end}
        )

        assert response.status_code == 200
        data = response.json()
        assert "series" in data
        assert "summary" in data

    def test_get_efficiency_trend_with_granularity(self, client):
        """测试带粒度的效率趋势"""
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()

        response = client.get(
            "/api/v1/data/efficiency/trend",
            params={"start_date": start, "end_date": end, "granularity": "week"}
        )

        assert response.status_code == 200
        assert response.json()["granularity"] == "week"

    def test_get_robot_utilization(self, client):
        """测试机器人利用率接口"""
        start = (date.today() - timedelta(days=7)).isoformat()
        end = date.today().isoformat()

        response = client.get(
            "/api/v1/data/robots/utilization",
            params={"start_date": start, "end_date": end}
        )

        assert response.status_code == 200
        data = response.json()
        assert "by_robot" in data
        assert "by_hour" in data

    def test_get_coverage_analysis(self, client):
        """测试覆盖分析接口"""
        response = client.get(
            "/api/v1/data/coverage/analysis",
            params={"building_id": "building_001"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "floors" in data
        assert "summary" in data

    def test_get_task_statistics(self, client):
        """测试任务统计接口"""
        start = (date.today() - timedelta(days=7)).isoformat()
        end = date.today().isoformat()

        response = client.get(
            "/api/v1/data/tasks/statistics",
            params={"start_date": start, "end_date": end}
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "by_status" in data

    def test_get_alert_statistics(self, client):
        """测试告警统计接口"""
        start = (date.today() - timedelta(days=7)).isoformat()
        end = date.today().isoformat()

        response = client.get(
            "/api/v1/data/alerts/statistics",
            params={"start_date": start, "end_date": end}
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "by_level" in data

    def test_compare_data(self, client):
        """测试对比分析接口"""
        start = (date.today() - timedelta(days=7)).isoformat()
        end = date.today().isoformat()

        response = client.post(
            "/api/v1/data/comparison",
            json={
                "tenant_id": "tenant_001",
                "comparison_type": "robot",
                "subjects": ["robot_001", "robot_002"],
                "metrics": ["efficiency", "utilization"],
                "start_date": start,
                "end_date": end
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2

    def test_create_export(self, client):
        """测试创建导出接口"""
        start = (date.today() - timedelta(days=7)).isoformat()
        end = date.today().isoformat()

        response = client.post(
            "/api/v1/data/export",
            json={
                "tenant_id": "tenant_001",
                "report_type": "daily_summary",
                "format": "xlsx",
                "date_range": {"start": start, "end": end},
                "include_sections": ["kpi", "efficiency"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "export_id" in data

    def test_get_export_status(self, client):
        """测试获取导出状态接口"""
        # 先创建
        start = (date.today() - timedelta(days=7)).isoformat()
        end = date.today().isoformat()

        create_response = client.post(
            "/api/v1/data/export",
            json={
                "tenant_id": "tenant_001",
                "report_type": "daily_summary",
                "format": "xlsx",
                "date_range": {"start": start, "end": end},
                "include_sections": ["kpi"]
            }
        )
        export_id = create_response.json()["export_id"]

        # 获取状态
        response = client.get(f"/api/v1/data/export/{export_id}")

        assert response.status_code == 200
        assert response.json()["export_id"] == export_id

    def test_get_export_status_not_found(self, client):
        """测试获取不存在的导出"""
        response = client.get("/api/v1/data/export/nonexistent")
        assert response.status_code == 404

    def test_get_realtime_dashboard(self, client):
        """测试实时仪表板接口"""
        response = client.get("/api/v1/data/dashboard/realtime")

        assert response.status_code == 200
        data = response.json()
        assert "robots" in data
        assert "current_tasks" in data
        assert "efficiency_now" in data
