"""
D2: 数据存储服务 - 业务数据仓储
================================
机器人、任务、空间等业务实体的数据访问层
"""

from typing import List, Dict, Any, Optional, TypeVar, Generic
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import logging

from .base import StorageService, QueryFilter, SortOrder, PagedResult
from .database import DatabaseManager

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================
# 业务实体模型
# ============================================================

@dataclass
class Tenant:
    """租户"""
    tenant_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class Robot:
    """机器人"""
    robot_id: str = ""
    tenant_id: str = ""
    name: str = ""
    brand: str = ""  # gaoxian, ecovacs
    model: str = ""
    capabilities: Dict[str, Any] = field(default_factory=dict)
    home_zone_id: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "robot_id": self.robot_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "brand": self.brand,
            "model": self.model,
            "capabilities": self.capabilities,
            "home_zone_id": self.home_zone_id,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class CleaningSchedule:
    """清洁排程"""
    schedule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    zone_id: str = ""
    task_type: str = ""
    frequency: str = ""  # daily, weekly, monthly
    time_slots: List[Dict[str, str]] = field(default_factory=list)
    priority: int = 5
    estimated_duration: Optional[int] = None
    is_active: bool = True
    created_by: str = "system"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "schedule_id": self.schedule_id,
            "tenant_id": self.tenant_id,
            "zone_id": self.zone_id,
            "task_type": self.task_type,
            "frequency": self.frequency,
            "time_slots": self.time_slots,
            "priority": self.priority,
            "estimated_duration": self.estimated_duration,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CleaningTask:
    """清洁任务"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    schedule_id: Optional[str] = None
    zone_id: str = ""
    task_type: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5
    assigned_robot_id: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    completion_rate: Optional[int] = None
    area_cleaned: Optional[float] = None
    failure_reason: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "schedule_id": self.schedule_id,
            "zone_id": self.zone_id,
            "task_type": self.task_type,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "priority": self.priority,
            "assigned_robot_id": self.assigned_robot_id,
            "scheduled_start": self.scheduled_start.isoformat() if self.scheduled_start else None,
            "actual_start": self.actual_start.isoformat() if self.actual_start else None,
            "actual_end": self.actual_end.isoformat() if self.actual_end else None,
            "completion_rate": self.completion_rate,
            "area_cleaned": self.area_cleaned,
            "failure_reason": self.failure_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================
# PostgreSQL 仓储基类
# ============================================================

class PostgresRepository(StorageService[T], Generic[T]):
    """
    PostgreSQL 仓储基类

    提供通用的 CRUD 操作实现
    """

    def __init__(self, db: DatabaseManager, table_name: str, id_field: str):
        """
        初始化仓储

        Args:
            db: 数据库管理器
            table_name: 表名
            id_field: ID字段名
        """
        self.db = db
        self.table_name = table_name
        self.id_field = id_field

    async def save(self, entity: T) -> T:
        """保存实体"""
        data = entity.to_dict() if hasattr(entity, 'to_dict') else asdict(entity)

        # 更新时间
        data["updated_at"] = datetime.now(timezone.utc)

        columns = list(data.keys())
        placeholders = ", ".join([f"${i+1}" for i in range(len(columns))])
        column_names = ", ".join(columns)

        # UPSERT
        updates = ", ".join([f"{c} = EXCLUDED.{c}" for c in columns if c != self.id_field])

        query = f"""
            INSERT INTO {self.table_name} ({column_names})
            VALUES ({placeholders})
            ON CONFLICT ({self.id_field}) DO UPDATE SET {updates}
            RETURNING *
        """

        import json
        values = []
        for col in columns:
            val = data[col]
            if isinstance(val, dict) or isinstance(val, list):
                val = json.dumps(val)
            values.append(val)

        async with self.db.connection() as conn:
            row = await conn.fetchrow(query, *values)

        return self._row_to_entity(row)

    async def save_many(self, entities: List[T]) -> List[T]:
        """批量保存"""
        results = []
        for entity in entities:
            saved = await self.save(entity)
            results.append(saved)
        return results

    async def get(self, id: str) -> Optional[T]:
        """根据ID获取"""
        query = f"SELECT * FROM {self.table_name} WHERE {self.id_field} = $1"

        async with self.db.connection() as conn:
            row = await conn.fetchrow(query, id)

        if not row:
            return None

        return self._row_to_entity(row)

    async def query(
        self,
        filters: List[QueryFilter] = None,
        sort: List[SortOrder] = None,
        page: int = 1,
        size: int = 20
    ) -> PagedResult[T]:
        """条件查询"""
        # 构建 WHERE 子句
        conditions = []
        params = []
        param_idx = 1

        if filters:
            for f in filters:
                op = self._get_operator(f.operator)
                if f.operator == "in":
                    placeholders = ", ".join([f"${param_idx + i}" for i in range(len(f.value))])
                    conditions.append(f"{f.field} IN ({placeholders})")
                    params.extend(f.value)
                    param_idx += len(f.value)
                elif f.operator == "like":
                    conditions.append(f"{f.field} ILIKE ${param_idx}")
                    params.append(f"%{f.value}%")
                    param_idx += 1
                else:
                    conditions.append(f"{f.field} {op} ${param_idx}")
                    params.append(f.value)
                    param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # 构建 ORDER BY
        order_clause = ""
        if sort:
            order_parts = [f"{s.field} {s.direction.upper()}" for s in sort]
            order_clause = "ORDER BY " + ", ".join(order_parts)

        # 计算总数
        count_query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {where_clause}"

        # 数据查询
        offset = (page - 1) * size
        data_query = f"""
            SELECT * FROM {self.table_name}
            WHERE {where_clause}
            {order_clause}
            LIMIT {size} OFFSET {offset}
        """

        async with self.db.connection() as conn:
            total = await conn.fetchval(count_query, *params)
            rows = await conn.fetch(data_query, *params)

        items = [self._row_to_entity(row) for row in rows]

        return PagedResult(
            items=items,
            total=total or 0,
            page=page,
            size=size
        )

    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[T]:
        """更新实体"""
        if not updates:
            return await self.get(id)

        updates["updated_at"] = datetime.now(timezone.utc)

        set_parts = []
        params = []
        param_idx = 1

        import json
        for key, value in updates.items():
            if isinstance(value, dict) or isinstance(value, list):
                value = json.dumps(value)
            set_parts.append(f"{key} = ${param_idx}")
            params.append(value)
            param_idx += 1

        params.append(id)

        query = f"""
            UPDATE {self.table_name}
            SET {", ".join(set_parts)}
            WHERE {self.id_field} = ${param_idx}
            RETURNING *
        """

        async with self.db.connection() as conn:
            row = await conn.fetchrow(query, *params)

        if not row:
            return None

        return self._row_to_entity(row)

    async def delete(self, id: str) -> bool:
        """删除实体"""
        query = f"DELETE FROM {self.table_name} WHERE {self.id_field} = $1"

        async with self.db.connection() as conn:
            result = await conn.execute(query, id)

        return "DELETE 1" in result

    async def exists(self, id: str) -> bool:
        """检查是否存在"""
        query = f"SELECT 1 FROM {self.table_name} WHERE {self.id_field} = $1"

        async with self.db.connection() as conn:
            result = await conn.fetchval(query, id)

        return result is not None

    async def count(self, filters: List[QueryFilter] = None) -> int:
        """计数"""
        conditions = []
        params = []
        param_idx = 1

        if filters:
            for f in filters:
                op = self._get_operator(f.operator)
                conditions.append(f"{f.field} {op} ${param_idx}")
                params.append(f.value)
                param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {where_clause}"

        async with self.db.connection() as conn:
            return await conn.fetchval(query, *params)

    def _get_operator(self, op: str) -> str:
        """转换操作符"""
        mapping = {
            "eq": "=",
            "ne": "!=",
            "gt": ">",
            "gte": ">=",
            "lt": "<",
            "lte": "<=",
            "like": "ILIKE",
            "in": "IN"
        }
        return mapping.get(op, "=")

    def _row_to_entity(self, row) -> T:
        """将数据库行转换为实体（子类实现）"""
        raise NotImplementedError


# ============================================================
# 具体仓储实现
# ============================================================

class RobotRepository(PostgresRepository[Robot]):
    """机器人仓储"""

    def __init__(self, db: DatabaseManager):
        super().__init__(db, "robots", "robot_id")

    def _row_to_entity(self, row) -> Robot:
        import json
        capabilities = row["capabilities"]
        if isinstance(capabilities, str):
            capabilities = json.loads(capabilities)

        settings = row["settings"]
        if isinstance(settings, str):
            settings = json.loads(settings)

        return Robot(
            robot_id=row["robot_id"],
            tenant_id=str(row["tenant_id"]),
            name=row["name"],
            brand=row["brand"],
            model=row["model"],
            capabilities=capabilities or {},
            home_zone_id=str(row["home_zone_id"]) if row["home_zone_id"] else None,
            settings=settings or {},
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    async def get_by_tenant(self, tenant_id: str) -> List[Robot]:
        """获取租户的所有机器人"""
        result = await self.query(
            filters=[QueryFilter(field="tenant_id", operator="eq", value=tenant_id)]
        )
        return result.items


class TaskRepository(PostgresRepository[CleaningTask]):
    """任务仓储"""

    def __init__(self, db: DatabaseManager):
        super().__init__(db, "cleaning_tasks", "task_id")

    def _row_to_entity(self, row) -> CleaningTask:
        status = row["status"]
        if isinstance(status, str):
            status = TaskStatus(status)

        return CleaningTask(
            task_id=str(row["task_id"]),
            tenant_id=str(row["tenant_id"]),
            schedule_id=str(row["schedule_id"]) if row["schedule_id"] else None,
            zone_id=str(row["zone_id"]),
            task_type=row["task_type"],
            status=status,
            priority=row["priority"],
            assigned_robot_id=row["assigned_robot_id"],
            scheduled_start=row["scheduled_start"],
            actual_start=row["actual_start"],
            actual_end=row["actual_end"],
            completion_rate=row["completion_rate"],
            area_cleaned=float(row["area_cleaned"]) if row["area_cleaned"] else None,
            failure_reason=row["failure_reason"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    async def get_pending_tasks(self, tenant_id: str, limit: int = 10) -> List[CleaningTask]:
        """获取待执行任务"""
        result = await self.query(
            filters=[
                QueryFilter(field="tenant_id", operator="eq", value=tenant_id),
                QueryFilter(field="status", operator="eq", value="pending")
            ],
            sort=[SortOrder(field="priority", direction="asc")],
            size=limit
        )
        return result.items


class ScheduleRepository(PostgresRepository[CleaningSchedule]):
    """排程仓储"""

    def __init__(self, db: DatabaseManager):
        super().__init__(db, "cleaning_schedules", "schedule_id")

    def _row_to_entity(self, row) -> CleaningSchedule:
        import json
        time_slots = row["time_slots"]
        if isinstance(time_slots, str):
            time_slots = json.loads(time_slots)

        return CleaningSchedule(
            schedule_id=str(row["schedule_id"]),
            tenant_id=str(row["tenant_id"]),
            zone_id=str(row["zone_id"]),
            task_type=row["task_type"],
            frequency=row["frequency"],
            time_slots=time_slots or [],
            priority=row["priority"],
            estimated_duration=row["estimated_duration"],
            is_active=row["is_active"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )


# ============================================================
# 内存仓储（测试用）
# ============================================================

class InMemoryRepository(StorageService[T], Generic[T]):
    """内存仓储基类（测试用）"""

    def __init__(self, id_field: str):
        self._data: Dict[str, T] = {}
        self.id_field = id_field

    async def save(self, entity: T) -> T:
        entity_id = getattr(entity, self.id_field)
        if hasattr(entity, 'updated_at'):
            entity.updated_at = datetime.now(timezone.utc)
        self._data[entity_id] = entity
        return entity

    async def save_many(self, entities: List[T]) -> List[T]:
        results = []
        for entity in entities:
            saved = await self.save(entity)
            results.append(saved)
        return results

    async def get(self, id: str) -> Optional[T]:
        return self._data.get(id)

    async def query(
        self,
        filters: List[QueryFilter] = None,
        sort: List[SortOrder] = None,
        page: int = 1,
        size: int = 20
    ) -> PagedResult[T]:
        results = list(self._data.values())

        # 过滤
        if filters:
            for f in filters:
                results = [
                    r for r in results
                    if self._match_filter(r, f)
                ]

        # 排序
        if sort:
            for s in reversed(sort):
                results.sort(
                    key=lambda x: getattr(x, s.field, None) or "",
                    reverse=(s.direction == "desc")
                )

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

    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[T]:
        entity = self._data.get(id)
        if not entity:
            return None

        for key, value in updates.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        entity.updated_at = datetime.now(timezone.utc)
        return entity

    async def delete(self, id: str) -> bool:
        if id in self._data:
            del self._data[id]
            return True
        return False

    async def exists(self, id: str) -> bool:
        return id in self._data

    async def count(self, filters: List[QueryFilter] = None) -> int:
        if not filters:
            return len(self._data)

        count = 0
        for entity in self._data.values():
            if all(self._match_filter(entity, f) for f in filters):
                count += 1
        return count

    def _match_filter(self, entity: T, f: QueryFilter) -> bool:
        value = getattr(entity, f.field, None)

        if f.operator == "eq":
            return value == f.value
        elif f.operator == "ne":
            return value != f.value
        elif f.operator == "gt":
            return value > f.value
        elif f.operator == "gte":
            return value >= f.value
        elif f.operator == "lt":
            return value < f.value
        elif f.operator == "lte":
            return value <= f.value
        elif f.operator == "in":
            return value in f.value
        elif f.operator == "like":
            return f.value.lower() in str(value).lower()

        return True

    def clear(self):
        """清空数据"""
        self._data.clear()


class InMemoryRobotRepository(InMemoryRepository[Robot]):
    """内存机器人仓储"""

    def __init__(self):
        super().__init__("robot_id")


class InMemoryTaskRepository(InMemoryRepository[CleaningTask]):
    """内存任务仓储"""

    def __init__(self):
        super().__init__("task_id")


class InMemoryScheduleRepository(InMemoryRepository[CleaningSchedule]):
    """内存排程仓储"""

    def __init__(self):
        super().__init__("schedule_id")
