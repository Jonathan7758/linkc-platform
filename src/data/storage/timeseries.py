"""
D2: 数据存储服务 - 时序数据服务
================================
处理机器人状态、位置轨迹等时序数据
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
import logging

from .base import TimeSeriesService, AggregationSpec
from .database import DatabaseManager

logger = logging.getLogger(__name__)


# ============================================================
# 时序数据模型
# ============================================================

@dataclass
class RobotStatusData:
    """机器人状态数据"""
    timestamp: datetime
    robot_id: str
    tenant_id: str
    status: str
    battery_level: int
    position_x: float = 0.0
    position_y: float = 0.0
    floor_id: Optional[str] = None
    zone_id: Optional[str] = None
    current_task_id: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class RobotPositionData:
    """机器人位置数据"""
    timestamp: datetime
    robot_id: str
    tenant_id: str
    x: float
    y: float
    floor_id: str
    heading: float = 0.0
    speed: float = 0.0


@dataclass
class TaskExecutionData:
    """任务执行数据"""
    timestamp: datetime
    task_id: str
    tenant_id: str
    robot_id: str
    event_type: str  # started, progress, completed, failed
    progress: int = 0
    area_cleaned: float = 0.0
    details: Dict[str, Any] = None


# ============================================================
# PostgreSQL/TimescaleDB 时序服务实现
# ============================================================

class PostgresTimeSeriesService(TimeSeriesService):
    """
    PostgreSQL/TimescaleDB 时序数据服务

    使用 TimescaleDB 扩展处理时序数据
    """

    def __init__(self, db: DatabaseManager):
        """
        初始化时序服务

        Args:
            db: 数据库管理器
        """
        self.db = db

    async def insert(
        self,
        table: str,
        data: List[Dict[str, Any]],
        timestamp_field: str = "timestamp"
    ) -> int:
        """
        批量插入时序数据

        Args:
            table: 表名
            data: 数据列表
            timestamp_field: 时间戳字段名

        Returns:
            插入的记录数
        """
        if not data:
            return 0

        # 获取所有字段
        first_record = data[0]
        columns = list(first_record.keys())

        # 重命名时间戳字段为 'time'（TimescaleDB 惯例）
        if timestamp_field in columns and timestamp_field != "time":
            columns = ["time" if c == timestamp_field else c for c in columns]

        # 构建 INSERT 语句
        placeholders = ", ".join([f"${i+1}" for i in range(len(columns))])
        column_names = ", ".join(columns)
        query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"

        # 准备数据
        records = []
        for record in data:
            row = []
            for key in first_record.keys():
                value = record.get(key)
                # 转换时间戳
                if key == timestamp_field and isinstance(value, str):
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                row.append(value)
            records.append(tuple(row))

        # 批量执行
        async with self.db.connection() as conn:
            await conn.executemany(query, records)

        logger.debug(f"Inserted {len(data)} records into {table}")
        return len(data)

    async def query_range(
        self,
        table: str,
        start_time: datetime,
        end_time: datetime,
        filters: Dict[str, Any] = None,
        columns: List[str] = None,
        limit: int = 1000,
        order_desc: bool = True
    ) -> List[Dict[str, Any]]:
        """
        时间范围查询

        Args:
            table: 表名
            start_time: 开始时间
            end_time: 结束时间
            filters: 筛选条件
            columns: 返回的列
            limit: 返回数量限制
            order_desc: 是否降序

        Returns:
            记录列表
        """
        # 构建 SELECT
        select_columns = ", ".join(columns) if columns else "*"
        query = f"SELECT {select_columns} FROM {table} WHERE time >= $1 AND time <= $2"

        params = [start_time, end_time]
        param_idx = 3

        # 添加过滤条件
        if filters:
            for key, value in filters.items():
                query += f" AND {key} = ${param_idx}"
                params.append(value)
                param_idx += 1

        # 排序
        order = "DESC" if order_desc else "ASC"
        query += f" ORDER BY time {order}"

        # 限制
        if limit:
            query += f" LIMIT {limit}"

        # 执行查询
        async with self.db.connection() as conn:
            rows = await conn.fetch(query, *params)

        return [dict(row) for row in rows]

    async def query_latest(
        self,
        table: str,
        group_by: str,
        filters: Dict[str, Any] = None,
        columns: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        查询每组最新记录

        Args:
            table: 表名
            group_by: 分组字段
            filters: 筛选条件
            columns: 返回的列

        Returns:
            每组最新记录列表
        """
        select_columns = ", ".join(columns) if columns else "*"

        # 使用 DISTINCT ON 获取每组最新记录（PostgreSQL 特性）
        query = f"""
            SELECT DISTINCT ON ({group_by}) {select_columns}
            FROM {table}
        """

        params = []
        param_idx = 1

        # 添加过滤条件
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = ${param_idx}")
                params.append(value)
                param_idx += 1
            query += " WHERE " + " AND ".join(conditions)

        query += f" ORDER BY {group_by}, time DESC"

        async with self.db.connection() as conn:
            rows = await conn.fetch(query, *params)

        return [dict(row) for row in rows]

    async def aggregate(
        self,
        table: str,
        start_time: datetime,
        end_time: datetime,
        aggregations: List[AggregationSpec],
        group_by: List[str] = None,
        interval: str = None,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        聚合查询

        Args:
            table: 表名
            start_time: 开始时间
            end_time: 结束时间
            aggregations: 聚合规格列表
            group_by: 分组字段列表
            interval: 时间桶间隔 (1m, 5m, 1h, 1d)
            filters: 筛选条件

        Returns:
            聚合结果列表
        """
        # 构建聚合表达式
        agg_expressions = []
        for agg in aggregations:
            alias = agg.alias or f"{agg.function}_{agg.field}"
            agg_expressions.append(f"{agg.function.upper()}({agg.field}) AS {alias}")

        agg_str = ", ".join(agg_expressions)

        # 构建分组
        group_parts = list(group_by) if group_by else []

        # 时间桶
        if interval:
            # 转换间隔格式（1m -> 1 minute）
            interval_pg = self._convert_interval(interval)
            agg_str = f"time_bucket('{interval_pg}', time) AS bucket, " + agg_str
            group_parts.insert(0, "bucket")

        # 构建查询
        query = f"""
            SELECT {agg_str}
            FROM {table}
            WHERE time >= $1 AND time <= $2
        """

        params = [start_time, end_time]
        param_idx = 3

        # 添加过滤条件
        if filters:
            for key, value in filters.items():
                query += f" AND {key} = ${param_idx}"
                params.append(value)
                param_idx += 1

        # 添加分组
        if group_parts:
            query += " GROUP BY " + ", ".join(group_parts)
            query += " ORDER BY " + ", ".join(group_parts)

        async with self.db.connection() as conn:
            rows = await conn.fetch(query, *params)

        return [dict(row) for row in rows]

    async def delete_range(
        self,
        table: str,
        start_time: datetime,
        end_time: datetime,
        filters: Dict[str, Any] = None
    ) -> int:
        """
        删除时间范围内的数据

        Args:
            table: 表名
            start_time: 开始时间
            end_time: 结束时间
            filters: 额外筛选条件

        Returns:
            删除的记录数
        """
        query = f"DELETE FROM {table} WHERE time >= $1 AND time <= $2"
        params = [start_time, end_time]
        param_idx = 3

        if filters:
            for key, value in filters.items():
                query += f" AND {key} = ${param_idx}"
                params.append(value)
                param_idx += 1

        async with self.db.connection() as conn:
            result = await conn.execute(query, *params)
            # 解析 DELETE count
            count = int(result.split()[-1]) if result else 0

        logger.info(f"Deleted {count} records from {table}")
        return count

    def _convert_interval(self, interval: str) -> str:
        """转换时间间隔格式"""
        mapping = {
            "s": "second",
            "m": "minute",
            "h": "hour",
            "d": "day",
            "w": "week"
        }
        if interval[-1] in mapping:
            return f"{interval[:-1]} {mapping[interval[-1]]}"
        return interval


# ============================================================
# 内存时序服务（测试用）
# ============================================================

class InMemoryTimeSeriesService(TimeSeriesService):
    """
    内存时序数据服务

    用于单元测试
    """

    def __init__(self):
        self._tables: Dict[str, List[Dict[str, Any]]] = {}

    async def insert(
        self,
        table: str,
        data: List[Dict[str, Any]],
        timestamp_field: str = "timestamp"
    ) -> int:
        if table not in self._tables:
            self._tables[table] = []

        # 标准化时间戳字段
        for record in data:
            if timestamp_field in record:
                record["time"] = record.pop(timestamp_field)

        self._tables[table].extend(data)
        return len(data)

    async def query_range(
        self,
        table: str,
        start_time: datetime,
        end_time: datetime,
        filters: Dict[str, Any] = None,
        columns: List[str] = None,
        limit: int = 1000,
        order_desc: bool = True
    ) -> List[Dict[str, Any]]:
        if table not in self._tables:
            return []

        results = []
        for record in self._tables[table]:
            time = record.get("time")
            if isinstance(time, str):
                time = datetime.fromisoformat(time.replace('Z', '+00:00'))

            if start_time <= time <= end_time:
                # 检查过滤条件
                if filters:
                    match = all(record.get(k) == v for k, v in filters.items())
                    if not match:
                        continue

                # 选择列
                if columns:
                    results.append({k: record.get(k) for k in columns})
                else:
                    results.append(record.copy())

        # 排序
        results.sort(key=lambda x: x.get("time", ""), reverse=order_desc)

        # 限制
        if limit:
            results = results[:limit]

        return results

    async def query_latest(
        self,
        table: str,
        group_by: str,
        filters: Dict[str, Any] = None,
        columns: List[str] = None
    ) -> List[Dict[str, Any]]:
        if table not in self._tables:
            return []

        # 按分组字段分组
        groups: Dict[str, Dict[str, Any]] = {}

        for record in self._tables[table]:
            # 检查过滤条件
            if filters:
                match = all(record.get(k) == v for k, v in filters.items())
                if not match:
                    continue

            group_value = record.get(group_by)
            if group_value is None:
                continue

            # 保留最新的
            existing = groups.get(group_value)
            if existing is None:
                groups[group_value] = record
            else:
                existing_time = existing.get("time", "")
                record_time = record.get("time", "")
                if record_time > existing_time:
                    groups[group_value] = record

        results = list(groups.values())

        # 选择列
        if columns:
            results = [{k: r.get(k) for k in columns} for r in results]

        return results

    async def aggregate(
        self,
        table: str,
        start_time: datetime,
        end_time: datetime,
        aggregations: List[AggregationSpec],
        group_by: List[str] = None,
        interval: str = None,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        # 简化实现：仅返回范围内数据的简单聚合
        data = await self.query_range(table, start_time, end_time, filters)

        if not data:
            return []

        # 简单聚合（不支持分组和时间桶）
        result = {}
        for agg in aggregations:
            values = [d.get(agg.field) for d in data if d.get(agg.field) is not None]
            if not values:
                result[agg.alias or f"{agg.function}_{agg.field}"] = None
                continue

            if agg.function == "avg":
                result[agg.alias or f"avg_{agg.field}"] = sum(values) / len(values)
            elif agg.function == "sum":
                result[agg.alias or f"sum_{agg.field}"] = sum(values)
            elif agg.function == "min":
                result[agg.alias or f"min_{agg.field}"] = min(values)
            elif agg.function == "max":
                result[agg.alias or f"max_{agg.field}"] = max(values)
            elif agg.function == "count":
                result[agg.alias or f"count_{agg.field}"] = len(values)

        return [result]

    async def delete_range(
        self,
        table: str,
        start_time: datetime,
        end_time: datetime,
        filters: Dict[str, Any] = None
    ) -> int:
        if table not in self._tables:
            return 0

        original_count = len(self._tables[table])

        def should_keep(record):
            time = record.get("time")
            if isinstance(time, str):
                time = datetime.fromisoformat(time.replace('Z', '+00:00'))

            # 在范围内则删除
            if start_time <= time <= end_time:
                # 检查过滤条件
                if filters:
                    match = all(record.get(k) == v for k, v in filters.items())
                    return not match  # 匹配则删除
                return False  # 在范围内，删除
            return True  # 不在范围内，保留

        self._tables[table] = [r for r in self._tables[table] if should_keep(r)]
        return original_count - len(self._tables[table])

    def clear(self):
        """清空所有数据"""
        self._tables.clear()
