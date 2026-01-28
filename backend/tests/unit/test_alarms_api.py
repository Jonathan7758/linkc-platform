"""告警API单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.core.database import get_async_session


def create_test_app():
    """创建测试用的FastAPI app"""
    from fastapi.middleware.cors import CORSMiddleware
    from app.api.alarms import router as alarms_router
    from app.core.config import get_settings

    settings = get_settings()

    test_app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
    )

    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    test_app.include_router(alarms_router)

    return test_app


class TestAlarmsAPI:
    """告警API测试"""

    @pytest.fixture
    def mock_db(self):
        """创建mock数据库会话"""
        mock = MagicMock()
        mock.add = MagicMock()
        mock.flush = AsyncMock()
        mock.commit = AsyncMock()
        return mock

    @pytest.fixture
    def test_app(self, mock_db):
        """创建测试app"""
        app = create_test_app()

        async def override_get_session():
            yield mock_db

        app.dependency_overrides[get_async_session] = override_get_session
        return app

    @pytest.fixture
    def sample_alarm(self):
        """示例告警"""
        alarm = MagicMock()
        alarm.alarm_id = "ALM-001"
        alarm.title = "温度过高"
        alarm.description = "设备温度超过阈值"
        alarm.severity = "critical"
        alarm.status = "active"
        alarm.category = "threshold"
        alarm.device_id = "DEV-001"
        alarm.triggered_at = datetime.now(timezone.utc)
        alarm.acknowledged_at = None
        alarm.resolved_at = None
        return alarm

    @pytest.mark.asyncio
    async def test_get_alarms_list(self, test_app, mock_db, sample_alarm):
        """测试获取告警列表"""
        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # Mock alarms query
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_alarm]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/alarms")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 1

    @pytest.mark.asyncio
    async def test_get_alarms_with_filter(self, test_app, mock_db, sample_alarm):
        """测试筛选告警"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_alarm]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/alarms?status=active&severity=critical"
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_alarm_stats(self, test_app, mock_db):
        """测试获取告警统计"""
        mock_alarm = MagicMock()
        mock_alarm.severity = "critical"
        mock_alarm.status = "active"

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_alarm]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/alarms/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "statistics" in data["data"]

    @pytest.mark.asyncio
    async def test_get_alarm_detail(self, test_app, mock_db, sample_alarm):
        """测试获取告警详情"""
        # Mock alarm查询
        sample_alarm.trigger_value = 85.5
        sample_alarm.threshold_value = 80.0
        sample_alarm.trigger_parameter = "temperature"
        sample_alarm.acknowledged_by = None
        sample_alarm.resolved_by = None
        sample_alarm.resolution_notes = None

        mock_alarm_result = MagicMock()
        mock_alarm_result.scalar_one_or_none.return_value = sample_alarm

        # Mock device查询
        mock_device = MagicMock()
        mock_device.device_id = "DEV-001"
        mock_device.name = "空调1号"
        mock_device.device_type = "hvac"
        mock_device.location = "A栋1层"

        mock_device_result = MagicMock()
        mock_device_result.scalar_one_or_none.return_value = mock_device

        mock_db.execute = AsyncMock(side_effect=[mock_alarm_result, mock_device_result])

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/alarms/ALM-001")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["alarm_id"] == "ALM-001"

    @pytest.mark.asyncio
    async def test_get_alarm_detail_not_found(self, test_app, mock_db):
        """测试告警不存在"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/alarms/NONEXISTENT")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_acknowledge_alarm(self, test_app, mock_db, sample_alarm):
        """测试确认告警"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_alarm
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/alarms/ALM-001/acknowledge",
                json={"comment": "已通知维修"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "acknowledged"

    @pytest.mark.asyncio
    async def test_acknowledge_alarm_not_found(self, test_app, mock_db):
        """测试确认不存在的告警"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/alarms/NONEXISTENT/acknowledge",
                json={}
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_resolve_alarm(self, test_app, mock_db, sample_alarm):
        """测试解决告警"""
        sample_alarm.status = "acknowledged"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_alarm
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/alarms/ALM-001/resolve",
                json={"resolution": "已更换传感器", "comment": "温度恢复正常"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_resolve_alarm_missing_resolution(self, test_app, mock_db):
        """测试解决告警缺少解决方案"""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/alarms/ALM-001/resolve",
                json={}
            )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_alarm_suggestions(self, test_app, mock_db, sample_alarm):
        """测试获取处理建议"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_alarm
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/alarms/ALM-001/suggestions")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_get_alarm_suggestions_not_found(self, test_app, mock_db):
        """测试获取不存在告警的建议"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/alarms/NONEXISTENT/suggestions")

        assert response.status_code == 404
