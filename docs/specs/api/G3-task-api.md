# G3 任务管理API规格书

## 文档信息

| 属性 | 值 |
|-----|-----|
| 模块ID | G3 |
| 模块名称 | 任务管理API (Task API) |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 规格书 |
| 前置依赖 | G1-认证授权, M2-任务MCP |

---

## 1. 模块概述

### 1.1 职责描述

任务管理API负责清洁任务的全生命周期管理：
1. **排程管理**：创建、更新、删除清洁排程
2. **任务查询**：查询任务状态和执行历史
3. **任务控制**：暂停、恢复、取消任务
4. **执行记录**：查询任务执行详情

### 1.2 API端点总览

| 端点 | 方法 | 描述 |
|-----|------|------|
| `/tasks/schedules` | GET/POST | 排程列表/创建 |
| `/tasks/schedules/{id}` | GET/PUT/DELETE | 排程详情/更新/删除 |
| `/tasks/schedules/{id}/enable` | POST | 启用排程 |
| `/tasks/schedules/{id}/disable` | POST | 禁用排程 |
| `/tasks` | GET | 任务列表 |
| `/tasks/{id}` | GET | 任务详情 |
| `/tasks/{id}/pause` | POST | 暂停任务 |
| `/tasks/{id}/resume` | POST | 恢复任务 |
| `/tasks/{id}/cancel` | POST | 取消任务 |
| `/tasks/executions` | GET | 执行记录列表 |

---

## 2. 接口定义

### 2.1 排程管理接口

#### GET /tasks/schedules

获取清洁排程列表。

**查询参数：**
| 参数 | 类型 | 必填 | 描述 |
|-----|------|-----|------|
| building_id | string | 否 | 按楼宇筛选 |
| zone_id | string | 否 | 按区域筛选 |
| status | string | 否 | 状态：enabled/disabled |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应：**
```json
{
  "items": [
    {
      "id": "schedule-001",
      "name": "大堂日常清洁",
      "zone_id": "zone-001",
      "zone_name": "大堂A区",
      "building_name": "新鸿基中心",
      "schedule_type": "daily",
      "start_time": "08:00",
      "cleaning_mode": "standard",
      "status": "enabled",
      "next_run_at": "2026-01-21T08:00:00Z",
      "last_run_at": "2026-01-20T08:00:00Z",
      "last_run_status": "completed"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

**所需权限：** `tasks:read`

#### POST /tasks/schedules

创建清洁排程。

**请求体：**
```json
{
  "name": "大堂日常清洁",
  "zone_id": "zone-001",
  "schedule_type": "daily",
  "start_time": "08:00",
  "cleaning_mode": "standard",
  "duration_minutes": 60,
  "repeat_config": {
    "type": "weekly",
    "days_of_week": [1, 2, 3, 4, 5]
  },
  "assigned_robot_id": null,
  "priority": "medium",
  "metadata": {
    "notify_on_complete": true
  }
}
```

**响应：**
```json
{
  "id": "schedule-001",
  "name": "大堂日常清洁",
  "zone_id": "zone-001",
  "schedule_type": "daily",
  "start_time": "08:00",
  "cleaning_mode": "standard",
  "status": "enabled",
  "next_run_at": "2026-01-21T08:00:00Z",
  "created_at": "2026-01-20T10:00:00Z"
}
```

**所需权限：** `tasks:write`

#### GET /tasks/schedules/{id}

获取排程详情。

**响应：**
```json
{
  "id": "schedule-001",
  "name": "大堂日常清洁",
  "zone": {
    "id": "zone-001",
    "name": "大堂A区",
    "floor_name": "1F",
    "building_name": "新鸿基中心"
  },
  "schedule_type": "daily",
  "start_time": "08:00",
  "cleaning_mode": "standard",
  "duration_minutes": 60,
  "repeat_config": {
    "type": "weekly",
    "days_of_week": [1, 2, 3, 4, 5]
  },
  "assigned_robot_id": null,
  "priority": "medium",
  "status": "enabled",
  "next_run_at": "2026-01-21T08:00:00Z",
  "statistics": {
    "total_runs": 50,
    "successful_runs": 48,
    "failed_runs": 2,
    "avg_duration_minutes": 55,
    "avg_coverage_rate": 0.95
  },
  "recent_executions": [
    {
      "id": "exec-001",
      "started_at": "2026-01-20T08:00:00Z",
      "completed_at": "2026-01-20T08:52:00Z",
      "status": "completed",
      "robot_id": "robot-001"
    }
  ],
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-15T00:00:00Z"
}
```

#### PUT /tasks/schedules/{id}

更新排程。

**请求体：**
```json
{
  "name": "大堂日常清洁（更新）",
  "start_time": "07:30",
  "cleaning_mode": "deep",
  "priority": "high"
}
```

**所需权限：** `tasks:write`

#### POST /tasks/schedules/{id}/enable

启用排程。

**响应：**
```json
{
  "id": "schedule-001",
  "status": "enabled",
  "next_run_at": "2026-01-21T08:00:00Z",
  "message": "排程已启用"
}
```

#### POST /tasks/schedules/{id}/disable

禁用排程。

**响应：**
```json
{
  "id": "schedule-001",
  "status": "disabled",
  "message": "排程已禁用"
}
```

### 2.2 任务查询接口

#### GET /tasks

获取任务列表。

**查询参数：**
| 参数 | 类型 | 必填 | 描述 |
|-----|------|-----|------|
| building_id | string | 否 | 按楼宇筛选 |
| zone_id | string | 否 | 按区域筛选 |
| robot_id | string | 否 | 按机器人筛选 |
| status | string | 否 | 状态筛选 |
| date_from | datetime | 否 | 开始日期 |
| date_to | datetime | 否 | 结束日期 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应：**
```json
{
  "items": [
    {
      "id": "task-001",
      "schedule_id": "schedule-001",
      "schedule_name": "大堂日常清洁",
      "zone_id": "zone-001",
      "zone_name": "大堂A区",
      "robot_id": "robot-001",
      "robot_name": "清洁机器人A",
      "status": "in_progress",
      "progress_percent": 65,
      "started_at": "2026-01-20T08:00:00Z",
      "estimated_completion": "2026-01-20T09:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

**所需权限：** `tasks:read`

#### GET /tasks/{id}

获取任务详情。

**响应：**
```json
{
  "id": "task-001",
  "schedule_id": "schedule-001",
  "schedule_name": "大堂日常清洁",
  "zone": {
    "id": "zone-001",
    "name": "大堂A区",
    "floor_name": "1F",
    "building_name": "新鸿基中心"
  },
  "robot": {
    "id": "robot-001",
    "name": "清洁机器人A",
    "model": "GS-100"
  },
  "cleaning_mode": "standard",
  "status": "in_progress",
  "progress_percent": 65,
  "cleaned_area_sqm": 325,
  "total_area_sqm": 500,
  "started_at": "2026-01-20T08:00:00Z",
  "estimated_completion": "2026-01-20T09:00:00Z",
  "route": {
    "planned_path": [...],
    "actual_path": [...],
    "current_position": {"x": 5.5, "y": 8.2}
  },
  "events": [
    {
      "timestamp": "2026-01-20T08:00:00Z",
      "event_type": "task_started",
      "message": "任务开始执行"
    },
    {
      "timestamp": "2026-01-20T08:30:00Z",
      "event_type": "obstacle_detected",
      "message": "检测到障碍物，绕行"
    }
  ],
  "created_at": "2026-01-20T07:55:00Z"
}
```

### 2.3 任务控制接口

#### POST /tasks/{id}/pause

暂停任务。

**请求体：**
```json
{
  "reason": "需要人工清理障碍物"
}
```

**响应：**
```json
{
  "id": "task-001",
  "status": "paused",
  "paused_at": "2026-01-20T08:35:00Z",
  "message": "任务已暂停"
}
```

**所需权限：** `tasks:write`

#### POST /tasks/{id}/resume

恢复任务。

**响应：**
```json
{
  "id": "task-001",
  "status": "in_progress",
  "resumed_at": "2026-01-20T08:40:00Z",
  "message": "任务已恢复"
}
```

#### POST /tasks/{id}/cancel

取消任务。

**请求体：**
```json
{
  "reason": "临时调整计划"
}
```

**响应：**
```json
{
  "id": "task-001",
  "status": "cancelled",
  "cancelled_at": "2026-01-20T08:35:00Z",
  "message": "任务已取消"
}
```

### 2.4 执行记录接口

#### GET /tasks/executions

获取历史执行记录。

**查询参数：**
| 参数 | 类型 | 必填 | 描述 |
|-----|------|-----|------|
| schedule_id | string | 否 | 按排程筛选 |
| zone_id | string | 否 | 按区域筛选 |
| robot_id | string | 否 | 按机器人筛选 |
| status | string | 否 | 状态：completed/failed/cancelled |
| date_from | datetime | 否 | 开始日期 |
| date_to | datetime | 否 | 结束日期 |

**响应：**
```json
{
  "items": [
    {
      "id": "exec-001",
      "task_id": "task-001",
      "schedule_name": "大堂日常清洁",
      "zone_name": "大堂A区",
      "robot_name": "清洁机器人A",
      "status": "completed",
      "started_at": "2026-01-20T08:00:00Z",
      "completed_at": "2026-01-20T08:52:00Z",
      "duration_minutes": 52,
      "cleaned_area_sqm": 480,
      "coverage_rate": 0.96
    }
  ],
  "total": 500,
  "page": 1,
  "page_size": 20
}
```

---

## 3. 数据模型

### 3.1 核心模型

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, time
from enum import Enum

class ScheduleType(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"

class CleaningMode(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"

class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RepeatConfig(BaseModel):
    type: str  # daily, weekly, monthly
    days_of_week: Optional[List[int]]  # 0-6, 0=Monday
    days_of_month: Optional[List[int]]  # 1-31

class CleaningSchedule(BaseModel):
    id: str
    tenant_id: str
    name: str
    zone_id: str
    schedule_type: ScheduleType
    start_time: time
    cleaning_mode: CleaningMode
    duration_minutes: int
    repeat_config: Optional[RepeatConfig]
    assigned_robot_id: Optional[str]
    priority: str = "medium"
    status: str = "enabled"
    next_run_at: Optional[datetime]
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

class CleaningTask(BaseModel):
    id: str
    tenant_id: str
    schedule_id: str
    zone_id: str
    robot_id: Optional[str]
    cleaning_mode: CleaningMode
    status: TaskStatus
    progress_percent: int = 0
    cleaned_area_sqm: float = 0
    total_area_sqm: float
    scheduled_start: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    error_message: Optional[str]
    metadata: Dict[str, Any] = {}
    created_at: datetime

class TaskExecution(BaseModel):
    id: str
    task_id: str
    schedule_id: str
    zone_id: str
    robot_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    duration_minutes: Optional[int]
    cleaned_area_sqm: float
    coverage_rate: float
    route_data: Optional[Dict[str, Any]]
    events: List[Dict[str, Any]] = []
```

### 3.2 请求/响应模型

```python
class ScheduleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    zone_id: str
    schedule_type: ScheduleType
    start_time: str  # HH:MM format
    cleaning_mode: CleaningMode = CleaningMode.STANDARD
    duration_minutes: int = Field(ge=10, le=480)
    repeat_config: Optional[RepeatConfig]
    assigned_robot_id: Optional[str]
    priority: str = "medium"
    metadata: Dict[str, Any] = {}

class ScheduleUpdate(BaseModel):
    name: Optional[str]
    start_time: Optional[str]
    cleaning_mode: Optional[CleaningMode]
    duration_minutes: Optional[int]
    repeat_config: Optional[RepeatConfig]
    assigned_robot_id: Optional[str]
    priority: Optional[str]
    metadata: Optional[Dict[str, Any]]

class TaskControlRequest(BaseModel):
    reason: Optional[str] = Field(max_length=500)
```

---

## 4. 实现要求

### 4.1 技术栈

- FastAPI
- SQLAlchemy
- APScheduler（排程触发）
- Redis（任务状态缓存）

### 4.2 核心实现

```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/tasks", tags=["任务管理"])

@router.get("/schedules", response_model=PaginatedResponse[ScheduleResponse])
async def list_schedules(
    building_id: Optional[str] = None,
    zone_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(require_permission("tasks:read")),
    db: AsyncSession = Depends(get_db)
):
    """获取排程列表"""
    query = (
        select(CleaningSchedule)
        .where(CleaningSchedule.tenant_id == user.tenant_id)
    )
    
    if zone_id:
        query = query.where(CleaningSchedule.zone_id == zone_id)
    if status:
        query = query.where(CleaningSchedule.status == status)
    if building_id:
        query = query.join(Zone).where(Zone.building_id == building_id)
    
    return await paginate(db, query, page, page_size)

@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    request: ScheduleCreate,
    user: User = Depends(require_permission("tasks:write")),
    db: AsyncSession = Depends(get_db),
    scheduler: SchedulerService = Depends(get_scheduler)
):
    """创建排程"""
    # 验证区域存在
    zone = await get_zone_or_404(db, request.zone_id, user.tenant_id)
    
    # 创建排程
    schedule = CleaningSchedule(
        id=generate_id("schedule"),
        tenant_id=user.tenant_id,
        **request.model_dump()
    )
    
    # 计算下次运行时间
    schedule.next_run_at = scheduler.calculate_next_run(
        schedule.schedule_type,
        schedule.start_time,
        schedule.repeat_config
    )
    
    db.add(schedule)
    await db.commit()
    
    # 注册到调度器
    await scheduler.register_schedule(schedule)
    
    return ScheduleResponse.from_orm(schedule)

@router.post("/{task_id}/pause")
async def pause_task(
    task_id: str,
    request: TaskControlRequest,
    user: User = Depends(require_permission("tasks:write")),
    db: AsyncSession = Depends(get_db),
    mcp: MCPClient = Depends(get_mcp_client)
):
    """暂停任务"""
    task = await get_task_or_404(db, task_id, user.tenant_id)
    
    if task.status != TaskStatus.IN_PROGRESS:
        raise HTTPException(400, "只能暂停进行中的任务")
    
    # 调用MCP暂停机器人
    if task.robot_id:
        await mcp.call_tool("pause_robot", {"robot_id": task.robot_id})
    
    task.status = TaskStatus.PAUSED
    task.metadata["pause_reason"] = request.reason
    task.metadata["paused_at"] = datetime.now().isoformat()
    await db.commit()
    
    return {
        "id": task_id,
        "status": "paused",
        "paused_at": task.metadata["paused_at"],
        "message": "任务已暂停"
    }
```

---

## 5. 测试要求

### 5.1 单元测试用例

```python
@pytest.mark.asyncio
async def test_create_schedule():
    """测试创建排程"""
    response = await client.post("/tasks/schedules", json={
        "name": "测试排程",
        "zone_id": "zone-001",
        "schedule_type": "daily",
        "start_time": "08:00",
        "cleaning_mode": "standard",
        "duration_minutes": 60
    }, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "enabled"
    assert "next_run_at" in data

@pytest.mark.asyncio
async def test_pause_and_resume_task():
    """测试暂停和恢复任务"""
    # 暂停
    response = await client.post(f"/tasks/{task_id}/pause", json={
        "reason": "测试暂停"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "paused"
    
    # 恢复
    response = await client.post(f"/tasks/{task_id}/resume", 
                                  headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
```

---

## 6. 验收标准

### 6.1 功能验收

- [ ] 排程CRUD操作正常
- [ ] 排程启用/禁用正常
- [ ] 任务列表查询正常
- [ ] 任务状态更新正确
- [ ] 暂停/恢复/取消任务正常
- [ ] 执行记录查询正常

### 6.2 性能要求

| 指标 | 要求 |
|-----|------|
| 排程列表响应时间 | < 200ms |
| 任务控制响应时间 | < 500ms |
| 执行记录查询 | < 300ms |

---

*文档版本：1.0*
*更新日期：2026年1月*
