"""
D2: 数据存储服务 - 事件日志服务
================================
记录系统事件、操作日志、告警等
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
import uuid
import logging

from .base import EventLogService, EventLog, EventLevel, PagedResult
from .database import DatabaseManager

logger = logging.getLogger(__name__)


# ============================================================
# PostgreSQL/TimescaleDB 事件日志服务
# ============================================================

class PostgresEventLogService(EventLogService):
    """
    PostgreSQL/TimescaleDB 事件日志服务

    将事件存储在 TimescaleDB 的 event_logs 表中
    """

    def __init__(self, db: DatabaseManager):
        """
        初始化事件日志服务

        Args:
            db: 数据库管理器
        """
        self.db = db

    async def log_event(
        self,
        event_type: str,
        tenant_id: str,
        source: str,
        data: Dict[str, Any],
        level: EventLevel = EventLevel.INFO,
        tags: List[str] = None
    ) -> str:
        """
        记录事件

        Args:
            event_type: 事件类型
            tenant_id: 租户ID
            source: 事件来源
            data: 事件数据
            level: 事件级别
            tags: 标签列表

        Returns:
            事件ID
        """
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        query = """
            INSERT INTO event_logs (time, event_id, tenant_id, event_type, level, source, data, tags)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """

        import json
        data_json = json.dumps(data) if data else "{}"

        async with self.db.connection() as conn:
            await conn.execute(
                query,
                now,
                event_id,
                tenant_id,
                event_type,
                level.value if isinstance(level, EventLevel) else level,
                source,
                data_json,
                tags or []
            )

        logger.debug(f"Event logged: {event_type} from {source}")
        return event_id

    async def query_events(
        self,
        tenant_id: str,
        event_types: List[str] = None,
        level: EventLevel = None,
        start_time: datetime = None,
        end_time: datetime = None,
        source: str = None,
        tags: List[str] = None,
        page: int = 1,
        size: int = 50
    ) -> PagedResult[EventLog]:
        """
        查询事件日志

        Args:
            tenant_id: 租户ID
            event_types: 事件类型列表
            level: 事件级别
            start_time: 开始时间
            end_time: 结束时间
            source: 事件来源
            tags: 标签
            page: 页码
            size: 每页大小

        Returns:
            分页结果
        """
        # 构建查询
        conditions = ["tenant_id = $1"]
        params = [tenant_id]
        param_idx = 2

        if event_types:
            placeholders = ", ".join([f"${param_idx + i}" for i in range(len(event_types))])
            conditions.append(f"event_type IN ({placeholders})")
            params.extend(event_types)
            param_idx += len(event_types)

        if level:
            conditions.append(f"level = ${param_idx}")
            params.append(level.value if isinstance(level, EventLevel) else level)
            param_idx += 1

        if start_time:
            conditions.append(f"time >= ${param_idx}")
            params.append(start_time)
            param_idx += 1

        if end_time:
            conditions.append(f"time <= ${param_idx}")
            params.append(end_time)
            param_idx += 1

        if source:
            conditions.append(f"source = ${param_idx}")
            params.append(source)
            param_idx += 1

        if tags:
            conditions.append(f"tags && ${param_idx}")
            params.append(tags)
            param_idx += 1

        where_clause = " AND ".join(conditions)

        # 计算总数
        count_query = f"SELECT COUNT(*) FROM event_logs WHERE {where_clause}"

        # 数据查询
        offset = (page - 1) * size
        data_query = f"""
            SELECT event_id, time, tenant_id, event_type, level, source, data, tags
            FROM event_logs
            WHERE {where_clause}
            ORDER BY time DESC
            LIMIT {size} OFFSET {offset}
        """

        async with self.db.connection() as conn:
            total = await conn.fetchval(count_query, *params)
            rows = await conn.fetch(data_query, *params)

        # 转换为 EventLog 对象
        import json
        events = []
        for row in rows:
            data_dict = row["data"]
            if isinstance(data_dict, str):
                data_dict = json.loads(data_dict)

            events.append(EventLog(
                event_id=row["event_id"],
                timestamp=row["time"],
                tenant_id=row["tenant_id"],
                event_type=row["event_type"],
                level=EventLevel(row["level"]),
                source=row["source"],
                data=data_dict,
                tags=list(row["tags"]) if row["tags"] else []
            ))

        return PagedResult(
            items=events,
            total=total or 0,
            page=page,
            size=size
        )

    async def get_event(self, event_id: str) -> Optional[EventLog]:
        """
        获取单个事件

        Args:
            event_id: 事件ID

        Returns:
            事件日志或None
        """
        query = """
            SELECT event_id, time, tenant_id, event_type, level, source, data, tags
            FROM event_logs
            WHERE event_id = $1
        """

        async with self.db.connection() as conn:
            row = await conn.fetchrow(query, event_id)

        if not row:
            return None

        import json
        data_dict = row["data"]
        if isinstance(data_dict, str):
            data_dict = json.loads(data_dict)

        return EventLog(
            event_id=row["event_id"],
            timestamp=row["time"],
            tenant_id=row["tenant_id"],
            event_type=row["event_type"],
            level=EventLevel(row["level"]),
            source=row["source"],
            data=data_dict,
            tags=list(row["tags"]) if row["tags"] else []
        )


# ============================================================
# 内存事件日志服务（测试用）
# ============================================================

class InMemoryEventLogService(EventLogService):
    """
    内存事件日志服务

    用于单元测试
    """

    def __init__(self):
        self._events: List[EventLog] = []

    async def log_event(
        self,
        event_type: str,
        tenant_id: str,
        source: str,
        data: Dict[str, Any],
        level: EventLevel = EventLevel.INFO,
        tags: List[str] = None
    ) -> str:
        """记录事件"""
        event = EventLog(
            tenant_id=tenant_id,
            event_type=event_type,
            level=level if isinstance(level, EventLevel) else EventLevel(level),
            source=source,
            data=data or {},
            tags=tags or []
        )
        self._events.append(event)
        return event.event_id

    async def query_events(
        self,
        tenant_id: str,
        event_types: List[str] = None,
        level: EventLevel = None,
        start_time: datetime = None,
        end_time: datetime = None,
        source: str = None,
        tags: List[str] = None,
        page: int = 1,
        size: int = 50
    ) -> PagedResult[EventLog]:
        """查询事件日志"""
        results = []

        for event in self._events:
            # 租户过滤
            if event.tenant_id != tenant_id:
                continue

            # 事件类型过滤
            if event_types and event.event_type not in event_types:
                continue

            # 级别过滤
            if level and event.level != level:
                continue

            # 时间过滤
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue

            # 来源过滤
            if source and event.source != source:
                continue

            # 标签过滤
            if tags:
                if not any(t in event.tags for t in tags):
                    continue

            results.append(event)

        # 按时间倒序
        results.sort(key=lambda x: x.timestamp, reverse=True)

        # 分页
        total = len(results)
        offset = (page - 1) * size
        results = results[offset:offset + size]

        return PagedResult(
            items=results,
            total=total,
            page=page,
            size=size
        )

    async def get_event(self, event_id: str) -> Optional[EventLog]:
        """获取单个事件"""
        for event in self._events:
            if event.event_id == event_id:
                return event
        return None

    def clear(self):
        """清空所有事件"""
        self._events.clear()

    def get_all(self) -> List[EventLog]:
        """获取所有事件（测试用）"""
        return self._events.copy()
