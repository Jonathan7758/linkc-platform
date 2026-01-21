"""
D2: 数据存储服务 - 基础类
==========================
存储服务抽象基类和通用数据模型
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid

T = TypeVar('T')


# ============================================================
# 通用数据模型
# ============================================================

@dataclass
class PagedResult(Generic[T]):
    """分页结果"""
    items: List[T]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        """总页数"""
        return (self.total + self.size - 1) // self.size if self.size > 0 else 0

    @property
    def has_next(self) -> bool:
        """是否有下一页"""
        return self.page < self.pages

    @property
    def has_prev(self) -> bool:
        """是否有上一页"""
        return self.page > 1

    def to_dict(self) -> dict:
        return {
            "items": [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.items],
            "total": self.total,
            "page": self.page,
            "size": self.size,
            "pages": self.pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev
        }


@dataclass
class QueryFilter:
    """查询过滤器"""
    field: str
    operator: str  # eq, ne, gt, gte, lt, lte, in, like, between
    value: Any

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value
        }


@dataclass
class SortOrder:
    """排序选项"""
    field: str
    direction: str = "asc"  # asc, desc


# ============================================================
# 存储服务抽象基类
# ============================================================

class StorageService(ABC, Generic[T]):
    """
    存储服务抽象基类

    提供通用的 CRUD 操作接口
    """

    @abstractmethod
    async def save(self, entity: T) -> T:
        """
        保存单个实体

        Args:
            entity: 要保存的实体

        Returns:
            保存后的实体（包含生成的ID等）
        """
        pass

    @abstractmethod
    async def save_many(self, entities: List[T]) -> List[T]:
        """
        批量保存实体

        Args:
            entities: 实体列表

        Returns:
            保存后的实体列表
        """
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        """
        根据ID获取单个实体

        Args:
            id: 实体ID

        Returns:
            实体对象或None
        """
        pass

    @abstractmethod
    async def query(
        self,
        filters: List[QueryFilter] = None,
        sort: List[SortOrder] = None,
        page: int = 1,
        size: int = 20
    ) -> PagedResult[T]:
        """
        条件查询

        Args:
            filters: 过滤条件列表
            sort: 排序选项列表
            page: 页码（从1开始）
            size: 每页大小

        Returns:
            分页结果
        """
        pass

    @abstractmethod
    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[T]:
        """
        更新实体

        Args:
            id: 实体ID
            updates: 要更新的字段字典

        Returns:
            更新后的实体或None
        """
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        删除实体

        Args:
            id: 实体ID

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    async def exists(self, id: str) -> bool:
        """
        检查实体是否存在

        Args:
            id: 实体ID

        Returns:
            是否存在
        """
        pass

    @abstractmethod
    async def count(self, filters: List[QueryFilter] = None) -> int:
        """
        计数

        Args:
            filters: 过滤条件

        Returns:
            匹配的记录数
        """
        pass


# ============================================================
# 时序数据服务接口
# ============================================================

@dataclass
class TimeSeriesPoint:
    """时序数据点"""
    timestamp: datetime
    values: Dict[str, Any]
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class AggregationSpec:
    """聚合规格"""
    field: str
    function: str  # avg, sum, min, max, count, first, last
    alias: Optional[str] = None


class TimeSeriesService(ABC):
    """
    时序数据服务抽象基类

    用于处理机器人状态、位置轨迹等时序数据
    """

    @abstractmethod
    async def insert(
        self,
        table: str,
        data: List[Dict[str, Any]],
        timestamp_field: str = "timestamp"
    ) -> int:
        """
        插入时序数据

        Args:
            table: 表名
            data: 数据列表
            timestamp_field: 时间戳字段名

        Returns:
            插入的记录数
        """
        pass

    @abstractmethod
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
            columns: 返回的列（默认全部）
            limit: 返回数量限制
            order_desc: 是否降序（最新在前）

        Returns:
            记录列表
        """
        pass

    @abstractmethod
    async def query_latest(
        self,
        table: str,
        group_by: str,
        filters: Dict[str, Any] = None,
        columns: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        查询每组最新记录

        常用于获取每台机器人的最新状态

        Args:
            table: 表名
            group_by: 分组字段（如 robot_id）
            filters: 筛选条件
            columns: 返回的列

        Returns:
            每组最新记录列表
        """
        pass

    @abstractmethod
    async def aggregate(
        self,
        table: str,
        start_time: datetime,
        end_time: datetime,
        aggregations: List[AggregationSpec],
        group_by: List[str] = None,
        interval: str = None,  # 1m, 5m, 1h, 1d
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
            interval: 时间桶间隔
            filters: 筛选条件

        Returns:
            聚合结果列表
        """
        pass

    @abstractmethod
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
        pass


# ============================================================
# 事件日志服务接口
# ============================================================

class EventLevel(str, Enum):
    """事件级别"""
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class EventLog:
    """事件日志"""
    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tenant_id: str = ""
    event_type: str = ""
    level: EventLevel = EventLevel.INFO
    source: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "tenant_id": self.tenant_id,
            "event_type": self.event_type,
            "level": self.level.value,
            "source": self.source,
            "data": self.data,
            "tags": self.tags
        }


class EventLogService(ABC):
    """
    事件日志服务抽象基类

    用于记录系统事件、操作日志、告警等
    """

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def get_event(self, event_id: str) -> Optional[EventLog]:
        """
        获取单个事件

        Args:
            event_id: 事件ID

        Returns:
            事件日志或None
        """
        pass
