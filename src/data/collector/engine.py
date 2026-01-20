"""
D1: 数据采集引擎 - 核心引擎
============================
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

from .models import (
    CollectorConfig,
    CollectorState,
    CollectorStatus,
    CollectorType,
    CollectedData,
    RobotStatusData,
    MCPTarget,
)
from .normalizer import DataNormalizer
from .storage import CollectorDataStorage

logger = logging.getLogger(__name__)


class DataCollectorEngine:
    """数据采集引擎"""

    def __init__(self, storage: Optional[CollectorDataStorage] = None):
        self.collectors: Dict[str, CollectorConfig] = {}
        self.states: Dict[str, CollectorState] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.storage = storage or CollectorDataStorage()
        self.normalizer = DataNormalizer()
        self._running = False
        self._mcp_clients: Dict[str, Any] = {}

    async def start(self) -> None:
        """启动采集引擎"""
        if self._running:
            logger.warning("Engine already running")
            return

        logger.info("Starting Data Collector Engine...")
        self._running = True

        # 初始化MCP客户端
        await self._init_mcp_clients()

        # 启动所有已启用的采集器
        for collector_id, config in self.collectors.items():
            if config.enabled:
                await self._start_collector(collector_id)

        logger.info(f"Engine started with {len(self.collectors)} collectors")

    async def stop(self) -> None:
        """停止采集引擎"""
        if not self._running:
            return

        logger.info("Stopping Data Collector Engine...")
        self._running = False

        # 停止所有采集任务
        for task in self.tasks.values():
            task.cancel()

        # 等待任务完成
        if self.tasks:
            await asyncio.gather(*self.tasks.values(), return_exceptions=True)

        self.tasks.clear()
        logger.info("Engine stopped")

    async def _init_mcp_clients(self) -> None:
        """初始化MCP客户端连接"""
        # 导入MCP客户端
        try:
            from src.mcp_servers.robot_gaoxian.storage import InMemoryRobotStorage
            from src.mcp_servers.robot_gaoxian.mock_client import MockGaoxianClient
            from src.mcp_servers.robot_gaoxian.tools import RobotTools

            gaoxian_storage = InMemoryRobotStorage()
            gaoxian_client = MockGaoxianClient(gaoxian_storage)
            self._mcp_clients[MCPTarget.GAOXIAN] = RobotTools(gaoxian_client, gaoxian_storage)
            logger.info("Gaoxian MCP client initialized")
        except Exception as e:
            logger.error(f"Failed to init Gaoxian MCP: {e}")

    async def add_collector(self, config: CollectorConfig) -> str:
        """添加采集器"""
        self.collectors[config.collector_id] = config
        self.states[config.collector_id] = CollectorState(
            collector_id=config.collector_id,
            status=CollectorStatus.STOPPED
        )
        logger.info(f"Added collector: {config.collector_id} ({config.collector_type})")

        # 如果引擎已运行且采集器启用，立即启动
        if self._running and config.enabled:
            await self._start_collector(config.collector_id)

        return config.collector_id

    async def remove_collector(self, collector_id: str) -> bool:
        """移除采集器"""
        if collector_id not in self.collectors:
            return False

        # 停止采集任务
        await self._stop_collector(collector_id)

        # 移除配置
        del self.collectors[collector_id]
        del self.states[collector_id]
        logger.info(f"Removed collector: {collector_id}")
        return True

    async def enable_collector(self, collector_id: str) -> bool:
        """启用采集器"""
        if collector_id not in self.collectors:
            return False

        self.collectors[collector_id].enabled = True
        if self._running:
            await self._start_collector(collector_id)
        return True

    async def disable_collector(self, collector_id: str) -> bool:
        """禁用采集器"""
        if collector_id not in self.collectors:
            return False

        self.collectors[collector_id].enabled = False
        await self._stop_collector(collector_id)
        return True

    async def get_collector_status(self, collector_id: str) -> Optional[CollectorState]:
        """获取采集器状态"""
        return self.states.get(collector_id)

    async def list_collectors(self, tenant_id: Optional[str] = None) -> List[Dict]:
        """列出所有采集器"""
        result = []
        for cid, config in self.collectors.items():
            if tenant_id and config.tenant_id != tenant_id:
                continue
            state = self.states.get(cid)
            result.append({
                "config": config.model_dump(),
                "state": state.model_dump() if state else None
            })
        return result

    async def trigger_collect(self, collector_id: str) -> Dict:
        """手动触发一次采集"""
        if collector_id not in self.collectors:
            return {"success": False, "error": "Collector not found"}

        config = self.collectors[collector_id]
        try:
            data = await self._execute_collect(config)
            return {"success": True, "records": len(data) if data else 0}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _start_collector(self, collector_id: str) -> None:
        """启动单个采集器"""
        if collector_id in self.tasks:
            return

        config = self.collectors[collector_id]
        self.states[collector_id].status = CollectorStatus.RUNNING

        # 创建定时任务
        task = asyncio.create_task(self._collector_loop(config))
        self.tasks[collector_id] = task
        logger.info(f"Started collector: {collector_id}")

    async def _stop_collector(self, collector_id: str) -> None:
        """停止单个采集器"""
        if collector_id not in self.tasks:
            return

        self.tasks[collector_id].cancel()
        try:
            await self.tasks[collector_id]
        except asyncio.CancelledError:
            pass

        del self.tasks[collector_id]
        self.states[collector_id].status = CollectorStatus.STOPPED
        logger.info(f"Stopped collector: {collector_id}")

    async def _collector_loop(self, config: CollectorConfig) -> None:
        """采集器循环"""
        while self._running and config.enabled:
            try:
                await self._execute_collect(config)
                self.states[config.collector_id].last_success = datetime.utcnow()
            except Exception as e:
                logger.error(f"Collector {config.collector_id} error: {e}")
                state = self.states[config.collector_id]
                state.error_count += 1
                state.last_error = str(e)

            self.states[config.collector_id].last_run = datetime.utcnow()

            # 等待下一次采集
            await asyncio.sleep(config.interval_seconds)

    async def _execute_collect(self, config: CollectorConfig) -> List[CollectedData]:
        """执行采集"""
        mcp = self._mcp_clients.get(config.target_mcp)
        if not mcp:
            raise RuntimeError(f"MCP client not available: {config.target_mcp}")

        collected_data = []

        if config.collector_type == CollectorType.ROBOT_STATUS:
            collected_data = await self._collect_robot_status(config, mcp)
        elif config.collector_type == CollectorType.ROBOT_POSITION:
            collected_data = await self._collect_robot_position(config, mcp)
        elif config.collector_type == CollectorType.TASK_PROGRESS:
            collected_data = await self._collect_task_progress(config, mcp)

        # 更新统计
        self.states[config.collector_id].records_collected += len(collected_data)

        return collected_data

    async def _collect_robot_status(self, config: CollectorConfig, mcp) -> List[CollectedData]:
        """采集机器人状态"""
        result = await mcp.handle("robot_list_robots", {"tenant_id": config.tenant_id})
        if not result.success:
            raise RuntimeError(f"MCP call failed: {result.error}")

        collected = []
        for robot in result.data.get("robots", []):
            # 获取详细状态
            status_result = await mcp.handle("robot_get_status", {"robot_id": robot["robot_id"]})
            if status_result.success:
                # 标准化数据
                normalized = self.normalizer.normalize_robot_status(
                    status_result.data,
                    config.target_mcp.value,
                    config.tenant_id
                )

                # 创建采集记录
                data = CollectedData(
                    collector_id=config.collector_id,
                    tenant_id=config.tenant_id,
                    data_type=CollectorType.ROBOT_STATUS,
                    source=config.target_mcp.value,
                    data=normalized.model_dump()
                )
                collected.append(data)

                # 存储数据
                await self.storage.save(data)

        logger.debug(f"Collected {len(collected)} robot status records")
        return collected

    async def _collect_robot_position(self, config: CollectorConfig, mcp) -> List[CollectedData]:
        """采集机器人位置"""
        result = await mcp.handle("robot_list_robots", {"tenant_id": config.tenant_id})
        if not result.success:
            raise RuntimeError(f"MCP call failed: {result.error}")

        collected = []
        for robot in result.data.get("robots", []):
            status_result = await mcp.handle("robot_get_status", {"robot_id": robot["robot_id"]})
            if status_result.success and "location" in status_result.data:
                normalized = self.normalizer.normalize_robot_position(
                    status_result.data,
                    config.target_mcp.value,
                    config.tenant_id
                )

                data = CollectedData(
                    collector_id=config.collector_id,
                    tenant_id=config.tenant_id,
                    data_type=CollectorType.ROBOT_POSITION,
                    source=config.target_mcp.value,
                    data=normalized.model_dump() if normalized else {}
                )
                collected.append(data)
                await self.storage.save(data)

        return collected

    async def _collect_task_progress(self, config: CollectorConfig, mcp) -> List[CollectedData]:
        """采集任务进度"""
        # MVP简化：从M2获取任务状态
        # 实际应该调用M2 MCP
        return []
