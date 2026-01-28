"""能耗API单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.core.database import get_async_session


def create_test_app():
    """创建测试用的FastAPI app"""
    from fastapi.middleware.cors import CORSMiddleware
    from app.api.energy import router as energy_router
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

    test_app.include_router(energy_router)

    return test_app


class TestEnergyAPI:
    """能耗API测试"""

    @pytest.fixture
    def mock_db(self):
        """创建mock数据库会话"""
        return MagicMock()

    @pytest.fixture
    def test_app(self, mock_db):
        """创建测试app"""
        app = create_test_app()

        async def override_get_session():
            yield mock_db

        app.dependency_overrides[get_async_session] = override_get_session
        return app

    @pytest.mark.asyncio
    async def test_get_consumption(self, test_app, mock_db):
        """测试获取能耗数据"""
        reading = MagicMock()
        reading.meter_id = "MTR-001"
        reading.energy_type = "electricity"
        reading.value = 100.0
        reading.unit = "kWh"
        reading.building = "A栋"
        reading.timestamp = datetime.now(timezone.utc)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [reading]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/energy/consumption")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_readings"] == 1

    @pytest.mark.asyncio
    async def test_get_trend(self, test_app, mock_db):
        """测试获取能耗趋势"""
        reading = MagicMock()
        reading.energy_type = "electricity"
        reading.value = 100.0
        reading.timestamp = datetime(2026, 1, 25, 10, 0, tzinfo=timezone.utc)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [reading]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/energy/trend")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "trend" in data["data"]

    @pytest.mark.asyncio
    async def test_get_comparison(self, test_app, mock_db):
        """测试获取能耗对比"""
        mock_current = MagicMock()
        mock_current.scalar.return_value = 1000.0

        mock_previous = MagicMock()
        mock_previous.scalar.return_value = 800.0

        mock_db.execute = AsyncMock(side_effect=[mock_current, mock_previous])

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/energy/comparison")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "change_rate" in data["data"]

    @pytest.mark.asyncio
    async def test_get_ranking(self, test_app, mock_db):
        """测试获取能耗排名"""
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("A栋", 1000.0),
            ("B栋", 800.0),
        ]
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/energy/ranking")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["ranking"]) == 2

    @pytest.mark.asyncio
    async def test_get_anomaly(self, test_app, mock_db):
        """测试检测能耗异常"""
        reading = MagicMock()
        reading.meter_id = "MTR-001"
        reading.energy_type = "electricity"
        reading.value = 100.0
        reading.building = "A栋"
        reading.timestamp = datetime.now(timezone.utc)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [reading]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/energy/anomaly")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "anomaly_count" in data["data"]

    @pytest.mark.asyncio
    async def test_get_consumption_with_params(self, test_app, mock_db):
        """测试带参数的能耗查询"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/energy/consumption?energy_type=electricity&building=A栋"
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_trend_with_params(self, test_app, mock_db):
        """测试带参数的趋势查询"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/energy/trend?period=hour&days=3"
            )

        assert response.status_code == 200
