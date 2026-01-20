"""
D1: 数据采集引擎 - 单元测试
============================
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from src.data.collector.models import (
    CollectorConfig,
    CollectorType,
    CollectorStatus,
    CollectedData,
    MCPTarget,
)
from src.data.collector.engine import DataCollectorEngine
from src.data.collector.normalizer import DataNormalizer
from src.data.collector.storage import CollectorDataStorage


# ============================================================
# Storage Tests
# ============================================================

class TestCollectorDataStorage:
    """存储测试"""

    @pytest.fixture
    def storage(self):
        return CollectorDataStorage(max_records_per_type=100, retention_hours=1)

    @pytest.mark.asyncio
    async def test_save_and_get(self, storage):
        """测试保存和获取"""
        data = CollectedData(
            collector_id="col_001",
            tenant_id="tenant_001",
            data_type=CollectorType.ROBOT_STATUS,
            source="gaoxian",
            data={"robot_id": "robot_001", "status": "idle", "battery_level": 80}
        )

        data_id = await storage.save(data)
        assert data_id is not None

        records = await storage.get_latest(CollectorType.ROBOT_STATUS)
        assert len(records) == 1
        assert records[0].data["robot_id"] == "robot_001"

    @pytest.mark.asyncio
    async def test_filter_by_tenant(self, storage):
        """测试按租户筛选"""
        # 保存两个不同租户的数据
        for tenant in ["tenant_001", "tenant_002"]:
            data = CollectedData(
                collector_id="col_001",
                tenant_id=tenant,
                data_type=CollectorType.ROBOT_STATUS,
                source="gaoxian",
                data={"robot_id": f"robot_{tenant}", "status": "idle"}
            )
            await storage.save(data)

        # 筛选租户1
        records = await storage.get_latest(
            CollectorType.ROBOT_STATUS,
            tenant_id="tenant_001"
        )
        assert len(records) == 1
        assert records[0].tenant_id == "tenant_001"

    @pytest.mark.asyncio
    async def test_filter_by_robot(self, storage):
        """测试按机器人筛选"""
        for robot_id in ["robot_001", "robot_002"]:
            data = CollectedData(
                collector_id="col_001",
                tenant_id="tenant_001",
                data_type=CollectorType.ROBOT_STATUS,
                source="gaoxian",
                data={"robot_id": robot_id, "status": "idle"}
            )
            await storage.save(data)

        records = await storage.get_by_robot("robot_001")
        assert len(records) == 1
        assert records[0].data["robot_id"] == "robot_001"

    @pytest.mark.asyncio
    async def test_get_stats(self, storage):
        """测试统计信息"""
        for i in range(5):
            data = CollectedData(
                collector_id="col_001",
                tenant_id="tenant_001",
                data_type=CollectorType.ROBOT_STATUS,
                source="gaoxian",
                data={"robot_id": f"robot_{i}", "status": "idle"}
            )
            await storage.save(data)

        stats = await storage.get_stats()
        assert stats["total_saved"] == 5
        assert stats["current_records"] == 5

    @pytest.mark.asyncio
    async def test_clear(self, storage):
        """测试清空数据"""
        for i in range(3):
            data = CollectedData(
                collector_id="col_001",
                tenant_id="tenant_001",
                data_type=CollectorType.ROBOT_STATUS,
                source="gaoxian",
                data={"robot_id": f"robot_{i}"}
            )
            await storage.save(data)

        count = await storage.clear()
        assert count == 3

        records = await storage.get_latest(CollectorType.ROBOT_STATUS)
        assert len(records) == 0


# ============================================================
# Normalizer Tests
# ============================================================

class TestDataNormalizer:
    """标准化器测试"""

    @pytest.fixture
    def normalizer(self):
        return DataNormalizer()

    def test_normalize_robot_status_gaoxian(self, normalizer):
        """测试高仙机器人状态标准化"""
        raw_data = {
            "robot_id": "robot_001",
            "status": "working",
            "battery_level": 75,
            "location": {"x": 10.5, "y": 20.3, "floor_id": "floor_001"},
            "current_task_id": "task_001"
        }

        result = normalizer.normalize_robot_status(raw_data, "gaoxian", "tenant_001")

        assert result.robot_id == "robot_001"
        assert result.status == "working"
        assert result.battery_level == 75
        assert result.position_x == 10.5
        assert result.position_y == 20.3
        assert result.floor_id == "floor_001"
        assert result.current_task_id == "task_001"
        assert result.tenant_id == "tenant_001"

    def test_normalize_robot_status_ecovacs(self, normalizer):
        """测试科沃斯机器人状态标准化"""
        raw_data = {
            "robot_id": "robot_002",
            "status": "cleaning",  # 科沃斯用cleaning
            "battery_level": 60,
        }

        result = normalizer.normalize_robot_status(raw_data, "ecovacs", "tenant_001")

        assert result.robot_id == "robot_002"
        assert result.status == "working"  # 标准化为working
        assert result.battery_level == 60

    def test_normalize_robot_position(self, normalizer):
        """测试位置数据标准化"""
        raw_data = {
            "robot_id": "robot_001",
            "location": {"x": 15.0, "y": 25.0, "floor_id": "floor_001"},
            "speed": 0.5
        }

        result = normalizer.normalize_robot_position(raw_data, "gaoxian", "tenant_001")

        assert result is not None
        assert result.robot_id == "robot_001"
        assert result.x == 15.0
        assert result.y == 25.0
        assert result.floor_id == "floor_001"
        assert result.speed == 0.5

    def test_normalize_position_no_location(self, normalizer):
        """测试无位置数据时返回None"""
        raw_data = {"robot_id": "robot_001", "status": "idle"}

        result = normalizer.normalize_robot_position(raw_data, "gaoxian", "tenant_001")

        assert result is None


# ============================================================
# Engine Tests
# ============================================================

class TestDataCollectorEngine:
    """采集引擎测试"""

    @pytest.fixture
    def engine(self):
        return DataCollectorEngine()

    @pytest.mark.asyncio
    async def test_add_collector(self, engine):
        """测试添加采集器"""
        config = CollectorConfig(
            name="Test Collector",
            collector_type=CollectorType.ROBOT_STATUS,
            tenant_id="tenant_001",
            interval_seconds=60
        )

        collector_id = await engine.add_collector(config)
        assert collector_id is not None

        collectors = await engine.list_collectors()
        assert len(collectors) == 1
        assert collectors[0]["config"]["name"] == "Test Collector"

    @pytest.mark.asyncio
    async def test_remove_collector(self, engine):
        """测试移除采集器"""
        config = CollectorConfig(
            name="Test Collector",
            collector_type=CollectorType.ROBOT_STATUS,
            tenant_id="tenant_001"
        )

        collector_id = await engine.add_collector(config)
        result = await engine.remove_collector(collector_id)

        assert result is True
        collectors = await engine.list_collectors()
        assert len(collectors) == 0

    @pytest.mark.asyncio
    async def test_get_collector_status(self, engine):
        """测试获取采集器状态"""
        config = CollectorConfig(
            name="Test Collector",
            collector_type=CollectorType.ROBOT_STATUS,
            tenant_id="tenant_001"
        )

        collector_id = await engine.add_collector(config)
        status = await engine.get_collector_status(collector_id)

        assert status is not None
        assert status.collector_id == collector_id
        assert status.status == CollectorStatus.STOPPED

    @pytest.mark.asyncio
    async def test_enable_disable_collector(self, engine):
        """测试启用/禁用采集器"""
        config = CollectorConfig(
            name="Test Collector",
            collector_type=CollectorType.ROBOT_STATUS,
            tenant_id="tenant_001",
            enabled=True
        )

        collector_id = await engine.add_collector(config)

        # 禁用
        result = await engine.disable_collector(collector_id)
        assert result is True
        assert engine.collectors[collector_id].enabled is False

        # 启用
        result = await engine.enable_collector(collector_id)
        assert result is True
        assert engine.collectors[collector_id].enabled is True

    @pytest.mark.asyncio
    async def test_list_collectors_by_tenant(self, engine):
        """测试按租户筛选采集器"""
        for tenant in ["tenant_001", "tenant_002"]:
            config = CollectorConfig(
                name=f"Collector {tenant}",
                collector_type=CollectorType.ROBOT_STATUS,
                tenant_id=tenant
            )
            await engine.add_collector(config)

        collectors = await engine.list_collectors(tenant_id="tenant_001")
        assert len(collectors) == 1
        assert collectors[0]["config"]["tenant_id"] == "tenant_001"


# ============================================================
# Integration Tests
# ============================================================

class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_storage_time_series(self):
        """测试时间序列数据查询"""
        storage = CollectorDataStorage()

        # 模拟采集电量数据
        base_time = datetime.utcnow()
        for i in range(10):
            data = CollectedData(
                collector_id="col_001",
                tenant_id="tenant_001",
                data_type=CollectorType.ROBOT_STATUS,
                source="gaoxian",
                timestamp=base_time + timedelta(minutes=i),
                data={
                    "robot_id": "robot_001",
                    "battery_level": 100 - i * 5  # 电量递减
                }
            )
            await storage.save(data)

        # 查询时间序列
        series = await storage.get_time_series(
            data_type=CollectorType.ROBOT_STATUS,
            robot_id="robot_001",
            field="battery_level",
            start_time=base_time,
            end_time=base_time + timedelta(hours=1)
        )

        assert len(series) == 10
        assert series[0]["value"] == 100
        assert series[-1]["value"] == 55
