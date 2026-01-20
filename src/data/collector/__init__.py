"""
D1: 数据采集引擎
================
从MCP Servers采集数据并标准化存储

主要功能:
- 定时采集机器人状态、位置、任务进度
- 数据格式标准化（适配不同MCP）
- 数据临时存储（后续对接D2）

用法示例:
    from src.data.collector import DataCollectorEngine, CollectorConfig, CollectorType

    # 创建引擎
    engine = DataCollectorEngine()

    # 添加采集器
    config = CollectorConfig(
        name="机器人状态采集",
        collector_type=CollectorType.ROBOT_STATUS,
        tenant_id="tenant_001",
        interval_seconds=30
    )
    await engine.add_collector(config)

    # 启动
    await engine.start()
"""

from .models import (
    CollectorType,
    CollectorStatus,
    CollectorConfig,
    CollectorState,
    CollectedData,
    RobotStatusData,
    RobotPositionData,
    TaskProgressData,
    MCPTarget,
)

from .engine import DataCollectorEngine
from .normalizer import DataNormalizer
from .storage import CollectorDataStorage

__all__ = [
    # Models
    "CollectorType",
    "CollectorStatus",
    "CollectorConfig",
    "CollectorState",
    "CollectedData",
    "RobotStatusData",
    "RobotPositionData",
    "TaskProgressData",
    "MCPTarget",
    # Core
    "DataCollectorEngine",
    "DataNormalizer",
    "CollectorDataStorage",
]
