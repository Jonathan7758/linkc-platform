
"""
A4: 数据采集Agent - 主Agent实现
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from src.agents.runtime.base import BaseAgent, AgentConfig, AgentState, AutonomyLevel
from src.agents.runtime.decision import Decision, DecisionResult
from .config import (
    DataCollectionAgentConfig, 
    CollectionConfig, 
    DataType, 
    CollectionStrategy,
    CollectionResult,
    CollectionStats,
    HealthStatus,
)
from .publisher import (
    DataPublisher, 
    InMemoryDataPublisher,
    RobotStatusData,
    RobotPositionData,
)

logger = logging.getLogger(__name__)


class DataCollectionAgent(BaseAgent):
    def __init__(self, collection_config: DataCollectionAgentConfig, publisher: Optional[DataPublisher] = None):
        agent_config = AgentConfig(
            agent_id=collection_config.agent_id,
            name="Data Collection Agent",
            description="Collects robot status and position data",
            autonomy_level=AutonomyLevel.L2_LIMITED,
            tenant_id=collection_config.tenant_id,
        )
        super().__init__(agent_config)
        self.collection_config = collection_config
        self.publisher = publisher or InMemoryDataPublisher()
        self.stats: Dict[DataType, CollectionStats] = {dt: CollectionStats() for dt in DataType}
        self._running = False
        self._mcp_client = None

    @property
    def health_status(self) -> HealthStatus:
        checks = {"publisher_connected": hasattr(self.publisher, "_connected") and self.publisher._connected}
        issues = []
        now = datetime.now(timezone.utc)
        for dt, stats in self.stats.items():
            if stats.last_collection:
                delay = (now - stats.last_collection).total_seconds()
                if delay > self.collection_config.max_collection_delay_seconds:
                    issues.append(f"{dt.value} delayed {int(delay)}s")
        return HealthStatus(healthy=len(issues)==0, checks=checks, issues=issues)

    async def think(self, context: dict) -> Decision:
        actions = []
        now = datetime.now(timezone.utc)
        for config in self.collection_config.collections:
            if not config.enabled:
                continue
            stats = self.stats[config.data_type]
            should_collect = stats.last_collection is None or (now - stats.last_collection).total_seconds() >= config.interval_seconds
            if should_collect:
                actions.append({"action": "collect", "data_type": config.data_type.value, "config": config.model_dump()})
        return Decision(decision_type="data_collection", description=f"Collect {len(actions)} types", actions=actions, auto_approve=True, exceeds_boundary=False)

    async def execute(self, decision: Decision) -> DecisionResult:
        if decision.decision_type != "data_collection":
            return DecisionResult(success=False, error="Unknown decision type")
        results = []
        for action in decision.actions:
            if action["action"] == "collect":
                data_type = DataType(action["data_type"])
                config = CollectionConfig(**action["config"])
                try:
                    result = await self._collect_data(data_type, config)
                    results.append(result)
                    self.stats[data_type].record_success(result.duration_ms)
                except Exception as e:
                    self.stats[data_type].record_failure(str(e))
        total_success = sum(r.success_count for r in results)
        return DecisionResult(success=True, decision=decision, message=f"Collected {total_success} records")

    async def _collect_data(self, data_type: DataType, config: CollectionConfig) -> CollectionResult:
        start = datetime.now(timezone.utc)
        success, failed = 0, 0
        robots = []
        if self._mcp_client:
            result = await self._mcp_client.call_tool("robot_list_robots", {"tenant_id": self.collection_config.tenant_id})
            if result.success:
                robots = result.data.get("robots", [])
        for robot in robots:
            try:
                if data_type == DataType.STATUS:
                    await self._collect_status(robot.get("robot_id"))
                elif data_type == DataType.POSITION:
                    await self._collect_position(robot.get("robot_id"), robot)
                success += 1
            except:
                failed += 1
        duration = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
        return CollectionResult(data_type=data_type, timestamp=start, robot_count=len(robots), success_count=success, failed_count=failed, duration_ms=duration)

    async def _collect_status(self, robot_id: str):
        if not self._mcp_client:
            return
        result = await self._mcp_client.call_tool("robot_get_status", {"robot_id": robot_id})
        if result.success:
            data = result.data
            status = RobotStatusData(robot_id=robot_id, tenant_id=self.collection_config.tenant_id, timestamp=datetime.now(timezone.utc), state=data.get("status", "unknown"), battery_level=data.get("battery_level", 0))
            await self.publisher.publish_robot_status(status)

    async def _collect_position(self, robot_id: str, robot_data: dict):
        loc = robot_data.get("location", {})
        if not loc:
            return
        pos = RobotPositionData(robot_id=robot_id, tenant_id=self.collection_config.tenant_id, timestamp=datetime.now(timezone.utc), x=loc.get("x", 0.0), y=loc.get("y", 0.0), floor_id=loc.get("floor_id", ""))
        await self.publisher.publish_robot_position(pos)

    async def start_loop(self, interval: int = 30):
        self._running = True
        await self.publisher.connect()
        while self._running:
            try:
                await self.run_cycle({})
            except Exception as e:
                logger.error(f"Error: {e}")
            await asyncio.sleep(interval)

    async def stop_loop(self):
        self._running = False
        await self.publisher.disconnect()

    def get_stats(self) -> Dict[str, Any]:
        return {"agent_id": self.agent_id, "running": self._running, "stats": {dt.value: s.model_dump() for dt, s in self.stats.items()}}
