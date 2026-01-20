"""
D1: 数据采集引擎 - 数据存储
============================
采集数据的临时存储（MVP使用内存存储）
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from .models import CollectedData, CollectorType

logger = logging.getLogger(__name__)


class CollectorDataStorage:
    """
    采集数据存储

    MVP阶段使用内存存储，后续接入D2数据存储服务
    """

    def __init__(self, max_records_per_type: int = 10000, retention_hours: int = 24):
        """
        初始化存储

        Args:
            max_records_per_type: 每种类型最大记录数
            retention_hours: 数据保留时间（小时）
        """
        self.max_records = max_records_per_type
        self.retention_hours = retention_hours

        # 按数据类型分组存储
        self._data: Dict[CollectorType, List[CollectedData]] = defaultdict(list)

        # 按robot_id索引（用于快速查询）
        self._robot_index: Dict[str, List[CollectedData]] = defaultdict(list)

        # 统计信息
        self._stats = {
            "total_saved": 0,
            "total_cleaned": 0,
        }

    async def save(self, data: CollectedData) -> str:
        """
        保存采集数据

        Args:
            data: 采集的数据

        Returns:
            data_id
        """
        # 添加到类型存储
        self._data[data.data_type].append(data)

        # 更新robot索引
        robot_id = data.data.get("robot_id")
        if robot_id:
            self._robot_index[robot_id].append(data)

        self._stats["total_saved"] += 1

        # 检查是否需要清理
        if len(self._data[data.data_type]) > self.max_records:
            await self._cleanup(data.data_type)

        logger.debug(f"Saved data: {data.data_id} ({data.data_type})")
        return data.data_id

    async def get_latest(
        self,
        data_type: CollectorType,
        tenant_id: Optional[str] = None,
        robot_id: Optional[str] = None,
        limit: int = 100
    ) -> List[CollectedData]:
        """
        获取最新数据

        Args:
            data_type: 数据类型
            tenant_id: 租户ID筛选
            robot_id: 机器人ID筛选
            limit: 返回数量限制

        Returns:
            数据列表（按时间倒序）
        """
        records = self._data.get(data_type, [])

        # 筛选
        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]
        if robot_id:
            records = [r for r in records if r.data.get("robot_id") == robot_id]

        # 按时间倒序，取最新的
        records = sorted(records, key=lambda x: x.timestamp, reverse=True)
        return records[:limit]

    async def get_by_robot(
        self,
        robot_id: str,
        data_type: Optional[CollectorType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[CollectedData]:
        """
        获取机器人的数据

        Args:
            robot_id: 机器人ID
            data_type: 数据类型筛选
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制

        Returns:
            数据列表
        """
        records = self._robot_index.get(robot_id, [])

        # 筛选
        if data_type:
            records = [r for r in records if r.data_type == data_type]
        if start_time:
            records = [r for r in records if r.timestamp >= start_time]
        if end_time:
            records = [r for r in records if r.timestamp <= end_time]

        # 排序
        records = sorted(records, key=lambda x: x.timestamp, reverse=True)
        return records[:limit]

    async def get_time_series(
        self,
        data_type: CollectorType,
        robot_id: str,
        field: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """
        获取时间序列数据

        Args:
            data_type: 数据类型
            robot_id: 机器人ID
            field: 要提取的字段
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            时间序列数据 [{"timestamp": ..., "value": ...}, ...]
        """
        records = await self.get_by_robot(
            robot_id=robot_id,
            data_type=data_type,
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )

        series = []
        for record in records:
            value = record.data.get(field)
            if value is not None:
                series.append({
                    "timestamp": record.timestamp.isoformat(),
                    "value": value
                })

        # 按时间正序
        series.sort(key=lambda x: x["timestamp"])
        return series

    async def get_stats(self) -> Dict:
        """获取存储统计"""
        type_counts = {t.value: len(records) for t, records in self._data.items()}
        return {
            "total_saved": self._stats["total_saved"],
            "total_cleaned": self._stats["total_cleaned"],
            "current_records": sum(type_counts.values()),
            "by_type": type_counts,
            "indexed_robots": len(self._robot_index),
        }

    async def _cleanup(self, data_type: CollectorType) -> int:
        """
        清理过期数据

        Args:
            data_type: 数据类型

        Returns:
            清理的记录数
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        original_count = len(self._data[data_type])

        # 保留未过期的数据
        self._data[data_type] = [
            r for r in self._data[data_type]
            if r.timestamp > cutoff_time
        ]

        # 如果仍然超过限制，删除最老的
        if len(self._data[data_type]) > self.max_records:
            self._data[data_type] = sorted(
                self._data[data_type],
                key=lambda x: x.timestamp,
                reverse=True
            )[:self.max_records]

        cleaned_count = original_count - len(self._data[data_type])
        self._stats["total_cleaned"] += cleaned_count

        if cleaned_count > 0:
            logger.info(f"Cleaned {cleaned_count} records from {data_type}")

        return cleaned_count

    async def clear(self, data_type: Optional[CollectorType] = None) -> int:
        """
        清空数据

        Args:
            data_type: 要清空的数据类型，None表示全部

        Returns:
            清空的记录数
        """
        if data_type:
            count = len(self._data.get(data_type, []))
            self._data[data_type] = []
        else:
            count = sum(len(records) for records in self._data.values())
            self._data.clear()
            self._robot_index.clear()

        return count
