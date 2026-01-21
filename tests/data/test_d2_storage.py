"""
D2: 数据存储服务 - 单元测试
============================
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta

from src.data.storage.base import (
    QueryFilter,
    SortOrder,
    AggregationSpec,
    EventLevel,
)
from src.data.storage.repositories import (
    Robot,
    CleaningTask,
    CleaningSchedule,
    TaskStatus,
    InMemoryRobotRepository,
    InMemoryTaskRepository,
    InMemoryScheduleRepository,
)
from src.data.storage.timeseries import InMemoryTimeSeriesService
from src.data.storage.events import InMemoryEventLogService


# ============================================================
# Repository Tests
# ============================================================

class TestRobotRepository:
    """机器人仓储测试"""

    @pytest.fixture
    def repo(self):
        return InMemoryRobotRepository()

    @pytest.fixture
    def sample_robot(self):
        return Robot(
            robot_id="robot_001",
            tenant_id="tenant_001",
            name="Test Robot 1",
            brand="gaoxian",
            model="GX-100"
        )

    @pytest.mark.asyncio
    async def test_save_and_get(self, repo, sample_robot):
        """测试保存和获取"""
        saved = await repo.save(sample_robot)
        assert saved.robot_id == "robot_001"

        retrieved = await repo.get("robot_001")
        assert retrieved is not None
        assert retrieved.name == "Test Robot 1"
        assert retrieved.brand == "gaoxian"

    @pytest.mark.asyncio
    async def test_save_many(self, repo):
        """测试批量保存"""
        robots = [
            Robot(robot_id=f"robot_{i}", tenant_id="tenant_001", name=f"Robot {i}", brand="gaoxian")
            for i in range(5)
        ]
        saved = await repo.save_many(robots)
        assert len(saved) == 5

        count = await repo.count()
        assert count == 5

    @pytest.mark.asyncio
    async def test_query_with_filters(self, repo):
        """测试条件查询"""
        # 准备数据
        for i in range(10):
            brand = "gaoxian" if i < 6 else "ecovacs"
            await repo.save(Robot(
                robot_id=f"robot_{i}",
                tenant_id="tenant_001",
                name=f"Robot {i}",
                brand=brand
            ))

        # 按品牌过滤
        result = await repo.query(
            filters=[QueryFilter(field="brand", operator="eq", value="gaoxian")]
        )
        assert result.total == 6
        assert all(r.brand == "gaoxian" for r in result.items)

    @pytest.mark.asyncio
    async def test_query_with_pagination(self, repo):
        """测试分页"""
        for i in range(25):
            await repo.save(Robot(
                robot_id=f"robot_{i}",
                tenant_id="tenant_001",
                name=f"Robot {i}",
                brand="gaoxian"
            ))

        # 第一页
        page1 = await repo.query(page=1, size=10)
        assert len(page1.items) == 10
        assert page1.total == 25
        assert page1.pages == 3
        assert page1.has_next

        # 最后一页
        page3 = await repo.query(page=3, size=10)
        assert len(page3.items) == 5
        assert not page3.has_next

    @pytest.mark.asyncio
    async def test_query_with_sort(self, repo):
        """测试排序"""
        await repo.save(Robot(robot_id="a", tenant_id="t1", name="Alice", brand="gaoxian"))
        await repo.save(Robot(robot_id="b", tenant_id="t1", name="Bob", brand="gaoxian"))
        await repo.save(Robot(robot_id="c", tenant_id="t1", name="Charlie", brand="gaoxian"))

        result = await repo.query(sort=[SortOrder(field="name", direction="desc")])
        names = [r.name for r in result.items]
        assert names == ["Charlie", "Bob", "Alice"]

    @pytest.mark.asyncio
    async def test_update(self, repo, sample_robot):
        """测试更新"""
        await repo.save(sample_robot)

        updated = await repo.update("robot_001", {"name": "Updated Robot", "model": "GX-200"})
        assert updated is not None
        assert updated.name == "Updated Robot"
        assert updated.model == "GX-200"

        # 验证更新持久化
        retrieved = await repo.get("robot_001")
        assert retrieved.name == "Updated Robot"

    @pytest.mark.asyncio
    async def test_delete(self, repo, sample_robot):
        """测试删除"""
        await repo.save(sample_robot)

        result = await repo.delete("robot_001")
        assert result is True

        # 确认已删除
        retrieved = await repo.get("robot_001")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_exists(self, repo, sample_robot):
        """测试存在检查"""
        assert await repo.exists("robot_001") is False

        await repo.save(sample_robot)
        assert await repo.exists("robot_001") is True

    @pytest.mark.asyncio
    async def test_count_with_filters(self, repo):
        """测试带条件的计数"""
        for i in range(10):
            tenant = "tenant_001" if i < 7 else "tenant_002"
            await repo.save(Robot(
                robot_id=f"robot_{i}",
                tenant_id=tenant,
                name=f"Robot {i}",
                brand="gaoxian"
            ))

        total = await repo.count()
        assert total == 10

        tenant1_count = await repo.count(
            filters=[QueryFilter(field="tenant_id", operator="eq", value="tenant_001")]
        )
        assert tenant1_count == 7


class TestTaskRepository:
    """任务仓储测试"""

    @pytest.fixture
    def repo(self):
        return InMemoryTaskRepository()

    @pytest.mark.asyncio
    async def test_task_lifecycle(self, repo):
        """测试任务生命周期"""
        # 创建任务
        task = CleaningTask(
            task_id="task_001",
            tenant_id="tenant_001",
            zone_id="zone_001",
            task_type="routine",
            priority=5
        )
        await repo.save(task)

        # 验证初始状态
        retrieved = await repo.get("task_001")
        assert retrieved.status == TaskStatus.PENDING

        # 分配机器人
        await repo.update("task_001", {
            "status": TaskStatus.ASSIGNED,
            "assigned_robot_id": "robot_001"
        })
        retrieved = await repo.get("task_001")
        assert retrieved.status == TaskStatus.ASSIGNED
        assert retrieved.assigned_robot_id == "robot_001"

        # 开始执行
        await repo.update("task_001", {
            "status": TaskStatus.IN_PROGRESS,
            "actual_start": datetime.now(timezone.utc)
        })
        retrieved = await repo.get("task_001")
        assert retrieved.status == TaskStatus.IN_PROGRESS

        # 完成
        await repo.update("task_001", {
            "status": TaskStatus.COMPLETED,
            "actual_end": datetime.now(timezone.utc),
            "completion_rate": 95
        })
        retrieved = await repo.get("task_001")
        assert retrieved.status == TaskStatus.COMPLETED
        assert retrieved.completion_rate == 95


# ============================================================
# Time Series Tests
# ============================================================

class TestTimeSeriesService:
    """时序数据服务测试"""

    @pytest.fixture
    def service(self):
        return InMemoryTimeSeriesService()

    @pytest.mark.asyncio
    async def test_insert_and_query(self, service):
        """测试插入和查询"""
        now = datetime.now(timezone.utc)

        # 插入数据
        data = [
            {
                "timestamp": now - timedelta(hours=2),
                "robot_id": "robot_001",
                "tenant_id": "tenant_001",
                "status": "working",
                "battery_level": 80
            },
            {
                "timestamp": now - timedelta(hours=1),
                "robot_id": "robot_001",
                "tenant_id": "tenant_001",
                "status": "working",
                "battery_level": 60
            },
            {
                "timestamp": now,
                "robot_id": "robot_001",
                "tenant_id": "tenant_001",
                "status": "idle",
                "battery_level": 40
            }
        ]
        count = await service.insert("robot_status_ts", data)
        assert count == 3

        # 查询范围
        results = await service.query_range(
            "robot_status_ts",
            start_time=now - timedelta(hours=3),
            end_time=now + timedelta(hours=1)
        )
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_query_with_filters(self, service):
        """测试带过滤的查询"""
        now = datetime.now(timezone.utc)

        # 插入多个机器人的数据
        data = []
        for i in range(10):
            data.append({
                "timestamp": now - timedelta(minutes=i),
                "robot_id": f"robot_{i % 3}",  # 3个机器人
                "tenant_id": "tenant_001",
                "status": "working",
                "battery_level": 100 - i * 5
            })
        await service.insert("robot_status_ts", data)

        # 查询特定机器人
        results = await service.query_range(
            "robot_status_ts",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            filters={"robot_id": "robot_0"}
        )
        assert all(r["robot_id"] == "robot_0" for r in results)

    @pytest.mark.asyncio
    async def test_query_latest(self, service):
        """测试查询最新记录"""
        now = datetime.now(timezone.utc)

        # 插入历史数据
        for robot_id in ["robot_001", "robot_002", "robot_003"]:
            for i in range(5):
                await service.insert("robot_status_ts", [{
                    "timestamp": now - timedelta(minutes=i),
                    "robot_id": robot_id,
                    "tenant_id": "tenant_001",
                    "status": "working" if i > 0 else "idle",
                    "battery_level": 100 - i * 10
                }])

        # 获取每个机器人最新状态
        results = await service.query_latest(
            "robot_status_ts",
            group_by="robot_id"
        )

        assert len(results) == 3
        # 最新的应该是 idle 状态
        for r in results:
            assert r["status"] == "idle"
            assert r["battery_level"] == 100

    @pytest.mark.asyncio
    async def test_aggregate(self, service):
        """测试聚合查询"""
        now = datetime.now(timezone.utc)

        # 插入数据
        data = []
        for i in range(10):
            data.append({
                "timestamp": now - timedelta(minutes=i),
                "robot_id": "robot_001",
                "tenant_id": "tenant_001",
                "status": "working",
                "battery_level": 100 - i * 5  # 100, 95, 90, ..., 55
            })
        await service.insert("robot_status_ts", data)

        # 聚合查询
        results = await service.aggregate(
            "robot_status_ts",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            aggregations=[
                AggregationSpec(field="battery_level", function="avg"),
                AggregationSpec(field="battery_level", function="min"),
                AggregationSpec(field="battery_level", function="max"),
                AggregationSpec(field="battery_level", function="count"),
            ]
        )

        assert len(results) == 1
        result = results[0]
        assert result["avg_battery_level"] == 77.5  # (100+95+...+55)/10
        assert result["min_battery_level"] == 55
        assert result["max_battery_level"] == 100
        assert result["count_battery_level"] == 10

    @pytest.mark.asyncio
    async def test_delete_range(self, service):
        """测试范围删除"""
        now = datetime.now(timezone.utc)

        # 插入数据
        for i in range(10):
            await service.insert("robot_status_ts", [{
                "timestamp": now - timedelta(days=i),
                "robot_id": "robot_001",
                "tenant_id": "tenant_001",
                "status": "working",
                "battery_level": 80
            }])

        # 删除7天前的数据
        deleted = await service.delete_range(
            "robot_status_ts",
            start_time=now - timedelta(days=30),
            end_time=now - timedelta(days=7)
        )
        assert deleted == 3  # day 7, 8, 9

        # 验证剩余数据
        remaining = await service.query_range(
            "robot_status_ts",
            start_time=now - timedelta(days=30),
            end_time=now + timedelta(days=1)
        )
        assert len(remaining) == 7


# ============================================================
# Event Log Tests
# ============================================================

class TestEventLogService:
    """事件日志服务测试"""

    @pytest.fixture
    def service(self):
        return InMemoryEventLogService()

    @pytest.mark.asyncio
    async def test_log_and_query(self, service):
        """测试记录和查询"""
        # 记录事件
        event_id = await service.log_event(
            event_type="robot.started",
            tenant_id="tenant_001",
            source="robot_001",
            data={"zone_id": "zone_001"},
            level=EventLevel.INFO,
            tags=["robot", "task"]
        )
        assert event_id.startswith("evt_")

        # 查询事件
        result = await service.query_events(tenant_id="tenant_001")
        assert result.total == 1
        assert result.items[0].event_type == "robot.started"

    @pytest.mark.asyncio
    async def test_query_by_level(self, service):
        """测试按级别查询"""
        # 记录不同级别的事件
        await service.log_event("info_event", "tenant_001", "source", {}, EventLevel.INFO)
        await service.log_event("warn_event", "tenant_001", "source", {}, EventLevel.WARN)
        await service.log_event("error_event", "tenant_001", "source", {}, EventLevel.ERROR)

        # 只查询错误
        result = await service.query_events(
            tenant_id="tenant_001",
            level=EventLevel.ERROR
        )
        assert result.total == 1
        assert result.items[0].event_type == "error_event"

    @pytest.mark.asyncio
    async def test_query_by_event_types(self, service):
        """测试按事件类型查询"""
        await service.log_event("robot.started", "tenant_001", "robot", {})
        await service.log_event("robot.stopped", "tenant_001", "robot", {})
        await service.log_event("task.created", "tenant_001", "task", {})

        result = await service.query_events(
            tenant_id="tenant_001",
            event_types=["robot.started", "robot.stopped"]
        )
        assert result.total == 2

    @pytest.mark.asyncio
    async def test_query_by_time_range(self, service):
        """测试按时间范围查询"""
        now = datetime.now(timezone.utc)

        # 手动设置时间戳进行测试
        for i in range(5):
            event_id = await service.log_event(
                f"event_{i}",
                "tenant_001",
                "source",
                {}
            )
            # 修改事件时间
            for event in service._events:
                if event.event_id == event_id:
                    event.timestamp = now - timedelta(hours=i)

        # 查询最近2小时
        result = await service.query_events(
            tenant_id="tenant_001",
            start_time=now - timedelta(hours=2),
            end_time=now + timedelta(hours=1)
        )
        assert result.total == 3  # event_0, event_1, event_2

    @pytest.mark.asyncio
    async def test_get_event(self, service):
        """测试获取单个事件"""
        event_id = await service.log_event(
            "test_event",
            "tenant_001",
            "source",
            {"key": "value"},
            tags=["test"]
        )

        event = await service.get_event(event_id)
        assert event is not None
        assert event.event_type == "test_event"
        assert event.data == {"key": "value"}
        assert "test" in event.tags

    @pytest.mark.asyncio
    async def test_pagination(self, service):
        """测试分页"""
        for i in range(25):
            await service.log_event(f"event_{i}", "tenant_001", "source", {})

        # 第一页
        page1 = await service.query_events(tenant_id="tenant_001", page=1, size=10)
        assert len(page1.items) == 10
        assert page1.total == 25

        # 最后一页
        page3 = await service.query_events(tenant_id="tenant_001", page=3, size=10)
        assert len(page3.items) == 5


# ============================================================
# Integration Tests
# ============================================================

class TestStorageIntegration:
    """存储服务集成测试"""

    @pytest.mark.asyncio
    async def test_robot_task_flow(self):
        """测试机器人-任务流程"""
        robot_repo = InMemoryRobotRepository()
        task_repo = InMemoryTaskRepository()
        ts_service = InMemoryTimeSeriesService()
        event_service = InMemoryEventLogService()

        tenant_id = "tenant_001"

        # 1. 创建机器人
        robot = Robot(
            robot_id="robot_001",
            tenant_id=tenant_id,
            name="Cleaning Bot 1",
            brand="gaoxian"
        )
        await robot_repo.save(robot)

        # 2. 创建任务
        task = CleaningTask(
            task_id="task_001",
            tenant_id=tenant_id,
            zone_id="zone_001",
            task_type="routine",
            priority=5
        )
        await task_repo.save(task)

        # 3. 记录任务创建事件
        await event_service.log_event(
            "task.created",
            tenant_id,
            "task_manager",
            {"task_id": "task_001", "zone_id": "zone_001"},
            EventLevel.INFO
        )

        # 4. 分配任务
        await task_repo.update("task_001", {
            "status": TaskStatus.ASSIGNED,
            "assigned_robot_id": "robot_001"
        })

        # 5. 记录机器人状态
        now = datetime.now(timezone.utc)
        await ts_service.insert("robot_status_ts", [{
            "timestamp": now,
            "robot_id": "robot_001",
            "tenant_id": tenant_id,
            "status": "working",
            "battery_level": 85
        }])

        # 6. 完成任务
        await task_repo.update("task_001", {
            "status": TaskStatus.COMPLETED,
            "completion_rate": 95,
            "actual_end": now
        })

        # 7. 记录完成事件
        await event_service.log_event(
            "task.completed",
            tenant_id,
            "robot_001",
            {"task_id": "task_001", "completion_rate": 95},
            EventLevel.INFO
        )

        # 验证最终状态
        final_task = await task_repo.get("task_001")
        assert final_task.status == TaskStatus.COMPLETED

        events = await event_service.query_events(tenant_id)
        assert events.total == 2

        robot_status = await ts_service.query_latest("robot_status_ts", "robot_id")
        assert len(robot_status) == 1
        assert robot_status[0]["status"] == "working"
