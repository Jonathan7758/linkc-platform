"""
G3: 任务管理API - 单元测试
===========================
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.gateway.task.models import ScheduleType, CleaningMode, TaskStatus, ScheduleStatus
from src.api.gateway.task.service import TaskService, InMemoryTaskStorage
from src.api.gateway.task.router import router, set_task_service
from src.api.gateway.auth.service import AuthService, InMemoryAuthStorage
from src.api.gateway.auth.router import router as auth_router, set_auth_service


# ============================================================
# 测试设置
# ============================================================

@pytest.fixture
def auth_service():
    """创建测试用认证服务"""
    storage = InMemoryAuthStorage()
    return AuthService(storage=storage)


@pytest.fixture
def task_service():
    """创建测试用任务服务"""
    storage = InMemoryTaskStorage()
    return TaskService(storage=storage)


@pytest.fixture
def app(auth_service, task_service):
    """创建测试应用"""
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(router)
    set_auth_service(auth_service)
    set_task_service(task_service)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    """获取管理员Token"""
    response = client.post("/auth/login", json={
        "username": "admin@linkc.com",
        "password": "admin123"
    })
    return response.json()["access_token"]


# ============================================================
# 排程管理测试
# ============================================================

class TestScheduleEndpoints:
    """排程管理测试"""

    def test_list_schedules(self, client, admin_token):
        """测试获取排程列表"""
        response = client.get(
            "/tasks/schedules",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1

    def test_create_schedule(self, client, admin_token):
        """测试创建排程"""
        response = client.post(
            "/tasks/schedules",
            json={
                "name": "测试排程",
                "zone_id": "zone-001",
                "schedule_type": "daily",
                "start_time": "09:00",
                "cleaning_mode": "standard",
                "duration_minutes": 45
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "测试排程"
        assert data["status"] == "enabled"
        assert "next_run_at" in data

    def test_create_schedule_with_repeat(self, client, admin_token):
        """测试创建带重复配置的排程"""
        response = client.post(
            "/tasks/schedules",
            json={
                "name": "周一至周五清洁",
                "zone_id": "zone-001",
                "schedule_type": "weekly",
                "start_time": "08:30",
                "cleaning_mode": "deep",
                "duration_minutes": 90,
                "repeat_config": {
                    "type": "weekly",
                    "days_of_week": [1, 2, 3, 4, 5]
                },
                "priority": "high"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["priority"] == "high"
        assert data["cleaning_mode"] == "deep"

    def test_get_schedule(self, client, admin_token):
        """测试获取排程详情"""
        response = client.get(
            "/tasks/schedules/schedule-001",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "大堂日常清洁"
        assert "statistics" in data
        assert "recent_executions" in data

    def test_get_schedule_not_found(self, client, admin_token):
        """测试获取不存在的排程"""
        response = client.get(
            "/tasks/schedules/nonexistent",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404

    def test_update_schedule(self, client, admin_token):
        """测试更新排程"""
        response = client.put(
            "/tasks/schedules/schedule-001",
            json={
                "name": "大堂日常清洁（更新）",
                "start_time": "07:30",
                "priority": "low"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "更新" in data["name"]
        assert data["start_time"] == "07:30"
        assert data["priority"] == "low"

    def test_delete_schedule(self, client, admin_token):
        """测试删除排程"""
        # 先创建排程
        create_response = client.post(
            "/tasks/schedules",
            json={
                "name": "删除测试排程",
                "zone_id": "zone-001",
                "schedule_type": "once",
                "start_time": "10:00"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        schedule_id = create_response.json()["id"]

        # 删除排程
        response = client.delete(
            f"/tasks/schedules/{schedule_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

        # 确认已删除
        get_response = client.get(
            f"/tasks/schedules/{schedule_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 404

    def test_enable_schedule(self, client, admin_token, task_service):
        """测试启用排程"""
        # 先禁用
        task_service.storage.schedules["schedule-001"].status = ScheduleStatus.DISABLED

        response = client.post(
            "/tasks/schedules/schedule-001/enable",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "enabled"
        assert "next_run_at" in data

    def test_disable_schedule(self, client, admin_token):
        """测试禁用排程"""
        response = client.post(
            "/tasks/schedules/schedule-001/disable",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "disabled"


# ============================================================
# 任务查询测试
# ============================================================

class TestTaskEndpoints:
    """任务查询测试"""

    def test_list_tasks(self, client, admin_token):
        """测试获取任务列表"""
        response = client.get(
            "/tasks",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_list_tasks_filter_status(self, client, admin_token):
        """测试按状态筛选任务"""
        response = client.get(
            "/tasks?status=in_progress",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        for task in data["items"]:
            assert task["status"] == "in_progress"

    def test_get_task(self, client, admin_token):
        """测试获取任务详情"""
        response = client.get(
            "/tasks/task-001",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert "zone" in data
        assert "robot" in data
        assert "events" in data

    def test_get_task_not_found(self, client, admin_token):
        """测试获取不存在的任务"""
        response = client.get(
            "/tasks/nonexistent",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404


# ============================================================
# 任务控制测试
# ============================================================

class TestTaskControlEndpoints:
    """任务控制测试"""

    def test_pause_task(self, client, admin_token):
        """测试暂停任务"""
        response = client.post(
            "/tasks/task-001/pause",
            json={"reason": "测试暂停"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"
        assert "paused_at" in data

    def test_resume_task(self, client, admin_token, task_service):
        """测试恢复任务"""
        # 先暂停任务
        task_service.storage.tasks["task-001"].status = TaskStatus.PAUSED

        response = client.post(
            "/tasks/task-001/resume",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert "resumed_at" in data

    def test_cancel_task(self, client, admin_token, task_service):
        """测试取消任务"""
        # 确保任务状态可取消
        task_service.storage.tasks["task-001"].status = TaskStatus.IN_PROGRESS

        response = client.post(
            "/tasks/task-001/cancel",
            json={"reason": "计划变更"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    def test_pause_non_running_task_fails(self, client, admin_token, task_service):
        """测试暂停非进行中任务失败"""
        # 将任务设为已完成
        task_service.storage.tasks["task-001"].status = TaskStatus.COMPLETED

        response = client.post(
            "/tasks/task-001/pause",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 400
        assert "只能暂停进行中的任务" in response.json()["detail"]

    def test_resume_non_paused_task_fails(self, client, admin_token, task_service):
        """测试恢复非暂停任务失败"""
        # 确保任务不是暂停状态
        task_service.storage.tasks["task-001"].status = TaskStatus.IN_PROGRESS

        response = client.post(
            "/tasks/task-001/resume",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 400
        assert "只能恢复已暂停的任务" in response.json()["detail"]


# ============================================================
# 执行记录测试
# ============================================================

class TestExecutionEndpoints:
    """执行记录测试"""

    def test_list_executions(self, client, admin_token):
        """测试获取执行记录列表"""
        response = client.get(
            "/tasks/executions",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_list_executions_filter_schedule(self, client, admin_token):
        """测试按排程筛选执行记录"""
        response = client.get(
            "/tasks/executions?schedule_id=schedule-001",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_execution_has_metrics(self, client, admin_token):
        """测试执行记录包含指标"""
        response = client.get(
            "/tasks/executions",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        if data["items"]:
            exec_record = data["items"][0]
            assert "duration_minutes" in exec_record
            assert "cleaned_area_sqm" in exec_record
            assert "coverage_rate" in exec_record


# ============================================================
# 服务层测试
# ============================================================

class TestTaskService:
    """任务服务测试"""

    @pytest.mark.asyncio
    async def test_schedule_crud(self, task_service):
        """测试排程CRUD"""
        from src.api.gateway.task.models import ScheduleCreate, ScheduleUpdate

        # Create
        schedule = await task_service.create_schedule(
            "tenant_001",
            ScheduleCreate(
                name="服务测试排程",
                zone_id="zone-001",
                schedule_type=ScheduleType.DAILY,
                start_time="10:00"
            )
        )
        assert schedule.name == "服务测试排程"
        assert schedule.status == ScheduleStatus.ENABLED

        # Read
        detail = await task_service.get_schedule(schedule.id, "tenant_001")
        assert detail is not None
        assert detail.name == "服务测试排程"

        # Update
        updated = await task_service.update_schedule(
            schedule.id, "tenant_001",
            ScheduleUpdate(name="更新后的名称", priority="high")
        )
        assert updated.name == "更新后的名称"

        # Delete
        success = await task_service.delete_schedule(schedule.id, "tenant_001")
        assert success is True

    @pytest.mark.asyncio
    async def test_task_status_transitions(self, task_service):
        """测试任务状态转换"""
        # IN_PROGRESS -> PAUSED
        result = await task_service.pause_task("task-001", "tenant_001", "测试暂停")
        assert result["status"] == TaskStatus.PAUSED

        # PAUSED -> IN_PROGRESS
        result = await task_service.resume_task("task-001", "tenant_001")
        assert result["status"] == TaskStatus.IN_PROGRESS

        # IN_PROGRESS -> CANCELLED
        result = await task_service.cancel_task("task-001", "tenant_001", "测试取消")
        assert result["status"] == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, task_service):
        """测试租户隔离"""
        # tenant_001的排程
        schedules = await task_service.list_schedules("tenant_001")
        assert schedules["total"] >= 1

        # tenant_002的排程（应该为空）
        schedules_other = await task_service.list_schedules("tenant_002")
        assert schedules_other["total"] == 0
