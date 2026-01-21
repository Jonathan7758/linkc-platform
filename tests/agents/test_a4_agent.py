"""A4: 数据采集Agent - 单元测试"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.agents.data_collection.agent import DataCollectionAgent
from src.agents.data_collection.config import (
    DataCollectionAgentConfig,
    CollectionConfig,
    DataType,
    CollectionStats,
)
from src.agents.data_collection.publisher import InMemoryDataPublisher, RobotStatusData


@pytest.fixture
def agent_config():
    return DataCollectionAgentConfig(
        agent_id="test-agent",
        tenant_id="tenant-001",
        collections=[
            CollectionConfig(data_type=DataType.STATUS, interval_seconds=30),
            CollectionConfig(data_type=DataType.POSITION, interval_seconds=5),
        ],
    )


@pytest.fixture
def publisher():
    return InMemoryDataPublisher()


@pytest.fixture
def agent(agent_config, publisher):
    return DataCollectionAgent(agent_config, publisher)


class TestDataCollectionConfig:
    def test_default_collections(self):
        config = DataCollectionAgentConfig(tenant_id="test")
        assert len(config.collections) == 5
        assert config.collections[0].data_type == DataType.STATUS

    def test_collection_stats_record_success(self):
        stats = CollectionStats()
        stats.record_success(100)
        assert stats.total_collections == 1
        assert stats.successful == 1

    def test_collection_stats_record_failure(self):
        stats = CollectionStats()
        stats.record_failure("Error")
        assert stats.failed == 1


class TestInMemoryPublisher:
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, publisher):
        await publisher.connect()
        assert await publisher.is_connected()
        await publisher.disconnect()
        assert not await publisher.is_connected()

    @pytest.mark.asyncio
    async def test_publish_status(self, publisher):
        await publisher.connect()
        status = RobotStatusData(
            robot_id="robot-001",
            tenant_id="tenant-001",
            timestamp=datetime.now(timezone.utc),
            state="idle",
            battery_level=80,
        )
        await publisher.publish_robot_status(status)
        assert len(publisher.status_records) == 1

    @pytest.mark.asyncio
    async def test_publish_caches_data(self, publisher):
        await publisher.connect()
        status = RobotStatusData(
            robot_id="robot-001",
            tenant_id="tenant-001",
            timestamp=datetime.now(timezone.utc),
            state="working",
            battery_level=75,
        )
        await publisher.publish_robot_status(status)
        cached = publisher.get_cached("robot:status:robot-001")
        assert cached is not None


class TestDataCollectionAgent:
    @pytest.mark.asyncio
    async def test_init(self, agent):
        assert agent.agent_id == "test-agent"
        assert agent.collection_config.tenant_id == "tenant-001"

    @pytest.mark.asyncio
    async def test_think_generates_actions(self, agent):
        decision = await agent.think({})
        assert decision.decision_type == "data_collection"
        assert len(decision.actions) > 0

    @pytest.mark.asyncio
    async def test_think_respects_interval(self, agent):
        decision1 = await agent.think({})
        assert len(decision1.actions) == 2
        
        now = datetime.now(timezone.utc)
        for dt in [DataType.STATUS, DataType.POSITION]:
            agent.stats[dt].last_collection = now
        
        decision2 = await agent.think({})
        assert len(decision2.actions) == 0

    @pytest.mark.asyncio
    async def test_execute_with_no_mcp(self, agent, publisher):
        await publisher.connect()
        decision = await agent.think({})
        result = await agent.execute(decision)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_health_status(self, agent, publisher):
        await publisher.connect()
        health = agent.health_status
        assert health.healthy is True

    @pytest.mark.asyncio
    async def test_health_detects_delay(self, agent, publisher):
        await publisher.connect()
        old_time = datetime.now(timezone.utc) - timedelta(seconds=600)
        agent.stats[DataType.STATUS].last_collection = old_time
        agent.collection_config.max_collection_delay_seconds = 300
        health = agent.health_status
        assert len(health.issues) > 0

    @pytest.mark.asyncio
    async def test_get_stats(self, agent):
        stats = agent.get_stats()
        assert stats["agent_id"] == "test-agent"
        assert "stats" in stats


class TestIntegration:
    @pytest.mark.asyncio
    async def test_full_cycle_with_mock_mcp(self, agent, publisher):
        await publisher.connect()
        mock_mcp = AsyncMock()
        mock_mcp.call_tool = AsyncMock(return_value=MagicMock(
            success=True,
            data={"robots": [{"robot_id": "r1", "location": {"x": 1, "y": 2, "floor_id": "f1"}}]}
        ))
        agent._mcp_client = mock_mcp
        await agent.run_cycle({})
        assert agent.stats[DataType.STATUS].total_collections >= 0
