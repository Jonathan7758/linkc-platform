# 模块开发规格书：M2 任务管理 MCP Server

## 文档信息

| 项目 | 内容 |
|-----|------|
| 模块ID | M2 |
| 模块名称 | 任务管理 MCP Server |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | F1数据模型、M1空间管理MCP |

---

## 1. 模块概述

### 1.1 职责描述

任务管理MCP Server负责管理清洁排程和任务，包括：
- **排程管理**：定义周期性清洁计划（哪个区域、什么频率、什么时间）
- **任务管理**：创建、查询、更新具体清洁任务
- **任务执行追踪**：记录任务的执行状态和结果
- **调度支持**：为Agent提供待执行任务列表和调度依据

### 1.2 在系统中的位置

```
┌─────────────────────────────────────────────────────────────┐
│                         Agent层                             │
│  ┌─────────────────┐ ┌─────────────────┐                   │
│  │ 清洁调度Agent    │ │ 数据采集Agent   │                   │
│  └────────┬────────┘ └────────┬────────┘                   │
│           │                   │                             │
│           ▼                   ▼                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   MCP Client                         │   │
│  └─────────────────────────┬───────────────────────────┘   │
└────────────────────────────┼───────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────┐
│                    MCP Server层                             │
│  ┌─────────────────┐ ┌─────────────────┐                   │
│  │  M1 空间管理    │ │ 【M2 任务管理】  │                   │
│  │  MCP Server     │ │  MCP Server     │                   │
│  │                 │ │  ◄── 本模块     │                   │
│  └─────────────────┘ └────────┬────────┘                   │
│                               │                             │
│                               ▼                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   数据存储层                         │   │
│  │            PostgreSQL / In-Memory                    │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

### 1.3 输入/输出概述

| 类型 | 内容 |
|-----|------|
| **输入** | Agent通过MCP协议发送的排程/任务管理请求 |
| **输出** | 排程列表、任务详情、任务状态更新结果 |
| **依赖** | M1空间管理（获取区域信息）、数据存储层 |

### 1.4 核心业务流程

```
排程定义流程：
运营人员 → 创建排程(zone_id, frequency, time_slots) → 存储排程

任务生成流程：
定时触发 → 根据排程生成今日任务 → 任务队列

任务执行流程：
Agent查询待执行任务 → 分配给机器人 → 更新任务状态 → 记录执行结果
```

---

## 2. 接口定义

### 2.1 本模块提供的MCP Tools

本模块必须实现以下 **10个Tools**：

#### Tool 1: task_list_schedules
```python
async def task_list_schedules(
    tenant_id: str,
    zone_id: str = None,          # 可选，按区域筛选
    building_id: str = None,      # 可选，按楼宇筛选
    is_active: bool = True        # 只返回启用的排程
) -> ToolResult:
    """
    获取清洁排程列表
    
    返回:
        success=True时，data为排程列表 List[CleaningSchedule]
        
    示例返回:
    {
        "success": true,
        "data": {
            "schedules": [
                {
                    "schedule_id": "uuid",
                    "zone_id": "uuid",
                    "zone_name": "1F大堂",
                    "task_type": "routine",
                    "frequency": "daily",
                    "time_slots": [{"start": "08:00", "end": "10:00"}],
                    "priority": 3,
                    "is_active": true
                }
            ],
            "total": 15
        }
    }
    """
```

#### Tool 2: task_get_schedule
```python
async def task_get_schedule(
    schedule_id: str
) -> ToolResult:
    """
    获取单个排程详情
    
    返回:
        success=True时，data为排程对象 CleaningSchedule（含关联的区域信息）
    """
```

#### Tool 3: task_create_schedule
```python
async def task_create_schedule(
    tenant_id: str,
    zone_id: str,
    task_type: str,               # "routine" | "deep" | "spot" | "emergency"
    frequency: str,               # "once" | "daily" | "weekly" | "monthly"
    time_slots: List[dict],       # [{"start": "08:00", "end": "10:00", "days": [1,2,3,4,5]}]
    priority: int = 5,            # 1-10, 1最高
    estimated_duration: int = 30, # 预计时长（分钟）
    created_by: str = "system"
) -> ToolResult:
    """
    创建清洁排程
    
    业务规则:
    - 同一区域不能有时间重叠的排程
    - priority必须在1-10范围内
    - time_slots至少包含一个时间段
    
    返回:
        success=True时，data为新创建的排程对象
    """
```

#### Tool 4: task_update_schedule
```python
async def task_update_schedule(
    schedule_id: str,
    updates: dict    # 可更新字段: is_active, priority, time_slots, frequency
) -> ToolResult:
    """
    更新排程信息
    
    可更新字段:
    - is_active: bool
    - priority: int (1-10)
    - time_slots: List[dict]
    - frequency: str
    
    返回:
        success=True时，data为更新后的排程对象
    """
```

#### Tool 5: task_list_tasks
```python
async def task_list_tasks(
    tenant_id: str,
    zone_id: str = None,
    robot_id: str = None,
    status: str = None,           # "pending" | "assigned" | "in_progress" | "completed" | "failed" | "cancelled"
    date_from: str = None,        # ISO日期 "2026-01-19"
    date_to: str = None,
    limit: int = 50,
    offset: int = 0
) -> ToolResult:
    """
    获取任务列表（支持多条件筛选）
    
    返回:
        success=True时，data包含任务列表和分页信息
        
    示例返回:
    {
        "success": true,
        "data": {
            "tasks": [...],
            "total": 128,
            "limit": 50,
            "offset": 0
        }
    }
    """
```

#### Tool 6: task_get_task
```python
async def task_get_task(
    task_id: str
) -> ToolResult:
    """
    获取单个任务详情
    
    返回:
        success=True时，data为任务对象 CleaningTask（含执行历史）
    """
```

#### Tool 7: task_create_task
```python
async def task_create_task(
    tenant_id: str,
    zone_id: str,
    task_type: str,               # "routine" | "deep" | "spot" | "emergency"
    priority: int = 5,
    scheduled_start: str = None,  # ISO时间，为空则立即执行
    schedule_id: str = None,      # 关联的排程ID
    created_by: str = "system",
    notes: str = None
) -> ToolResult:
    """
    创建清洁任务
    
    业务规则:
    - emergency类型任务自动设置priority=1
    - 必须验证zone_id存在
    
    返回:
        success=True时，data为新创建的任务对象
    """
```

#### Tool 8: task_update_status
```python
async def task_update_status(
    task_id: str,
    status: str,                  # "assigned" | "in_progress" | "completed" | "failed" | "cancelled"
    robot_id: str = None,         # 当status="assigned"时必填
    actual_start: str = None,     # 当status="in_progress"时设置
    actual_end: str = None,       # 当status="completed"/"failed"时设置
    completion_rate: float = None,# 完成率 0-100
    failure_reason: str = None,   # 当status="failed"时说明原因
    updated_by: str = "system"
) -> ToolResult:
    """
    更新任务状态（状态机）
    
    状态流转规则:
    pending → assigned → in_progress → completed/failed
    pending → cancelled
    assigned → cancelled
    
    业务规则:
    - 不允许跳跃状态（如pending直接到completed）
    - completed状态必须有completion_rate
    - failed状态必须有failure_reason
    
    返回:
        success=True时，data为更新后的任务对象
    """
```

#### Tool 9: task_get_pending_tasks
```python
async def task_get_pending_tasks(
    tenant_id: str,
    zone_ids: List[str] = None,   # 可选，限定区域范围
    max_count: int = 20
) -> ToolResult:
    """
    获取待执行任务列表（供Agent调度使用）
    
    排序规则:
    1. priority升序（1最优先）
    2. scheduled_start升序（早的优先）
    3. created_at升序（先创建的优先）
    
    返回:
        success=True时，data为按优先级排序的待执行任务列表
    """
```

#### Tool 10: task_generate_daily_tasks
```python
async def task_generate_daily_tasks(
    tenant_id: str,
    date: str                     # ISO日期 "2026-01-19"
) -> ToolResult:
    """
    根据排程生成指定日期的任务
    
    业务规则:
    - 检查排程的frequency和time_slots.days
    - 跳过已生成的任务（幂等）
    - 只处理is_active=True的排程
    
    返回:
        success=True时，data包含生成的任务数量和列表
        
    示例返回:
    {
        "success": true,
        "data": {
            "generated_count": 12,
            "skipped_count": 3,
            "tasks": [...]
        }
    }
    """
```

### 2.2 本模块依赖的接口

```python
# 依赖M1空间管理MCP Server（用于验证zone_id）
# 在创建排程/任务时需要验证区域存在

# 数据模型依赖
from interfaces.data_models import (
    CleaningSchedule,
    CleaningTask,
    TaskStatus,
    TaskType,
    CleaningFrequency,
    TimeSlot
)
```

---

## 3. 数据模型

### 3.1 核心数据结构

```python
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, time

class TaskType(str, Enum):
    """任务类型"""
    ROUTINE = "routine"      # 日常清洁
    DEEP = "deep"            # 深度清洁
    SPOT = "spot"            # 局部清洁
    EMERGENCY = "emergency"  # 紧急清洁

class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"          # 待分配
    ASSIGNED = "assigned"        # 已分配
    IN_PROGRESS = "in_progress"  # 执行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消

class CleaningFrequency(str, Enum):
    """清洁频率"""
    ONCE = "once"        # 一次性
    DAILY = "daily"      # 每天
    WEEKLY = "weekly"    # 每周
    MONTHLY = "monthly"  # 每月

class TimeSlot(BaseModel):
    """时间段"""
    start: str = Field(..., description="开始时间 HH:MM")
    end: str = Field(..., description="结束时间 HH:MM")
    days: Optional[List[int]] = Field(
        default=[1,2,3,4,5,6,7], 
        description="星期几执行，1=周一，7=周日"
    )

class CleaningSchedule(BaseModel):
    """清洁排程"""
    schedule_id: UUID
    tenant_id: UUID
    zone_id: UUID
    zone_name: Optional[str] = None  # 冗余字段，便于展示
    
    task_type: TaskType
    frequency: CleaningFrequency
    time_slots: List[TimeSlot]
    priority: int = Field(default=5, ge=1, le=10)
    estimated_duration: int = Field(default=30, description="预计时长(分钟)")
    
    is_active: bool = True
    created_by: str = "system"
    created_at: datetime
    updated_at: datetime

class CleaningTask(BaseModel):
    """清洁任务"""
    task_id: UUID
    tenant_id: UUID
    zone_id: UUID
    zone_name: Optional[str] = None
    
    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    priority: int = Field(default=5, ge=1, le=10)
    
    # 时间相关
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    
    # 执行相关
    assigned_robot_id: Optional[UUID] = None
    assigned_robot_name: Optional[str] = None
    completion_rate: Optional[float] = None  # 0-100
    failure_reason: Optional[str] = None
    
    # 关联
    schedule_id: Optional[UUID] = None  # 关联的排程
    
    # 元信息
    notes: Optional[str] = None
    created_by: str = "system"
    created_at: datetime
    updated_at: datetime
```

### 3.2 状态机定义

```
任务状态流转图:

                  ┌──────────────────┐
                  │                  │
                  ▼                  │
┌─────────┐   ┌─────────┐   ┌─────────────┐   ┌───────────┐
│ PENDING │──►│ ASSIGNED│──►│ IN_PROGRESS │──►│ COMPLETED │
└────┬────┘   └────┬────┘   └──────┬──────┘   └───────────┘
     │             │               │
     │             │               │         ┌────────┐
     │             │               └────────►│ FAILED │
     │             │                         └────────┘
     │             │
     ▼             ▼
┌───────────────────┐
│    CANCELLED      │
└───────────────────┘

合法状态流转:
- pending → assigned (分配机器人)
- pending → cancelled (取消任务)
- assigned → in_progress (开始执行)
- assigned → cancelled (取消任务)
- in_progress → completed (完成)
- in_progress → failed (失败)
```

---

## 4. 实现要求

### 4.1 技术栈约束

| 项目 | 要求 |
|-----|------|
| Python版本 | 3.11+ |
| MCP SDK | mcp >= 1.0.0 |
| 数据验证 | Pydantic v2 |
| 异步框架 | asyncio |
| 存储 | MVP阶段使用内存存储，预留PostgreSQL接口 |

### 4.2 代码规范

```python
# 文件头模板
"""
M2: 任务管理 MCP Server - [文件描述]

职责: [简要说明]
"""

# 类型注解：所有函数必须有完整的类型注解
async def task_create_task(
    tenant_id: str,
    zone_id: str,
    task_type: str,
    ...
) -> ToolResult:
    ...

# 错误处理：统一使用ToolResult返回
return ToolResult(
    success=False,
    error="Task not found",
    error_code="NOT_FOUND"
)

# 日志：关键操作必须记录日志
import logging
logger = logging.getLogger(__name__)
logger.info(f"Task created: {task_id}")
```

### 4.3 错误码定义

| 错误码 | 说明 | HTTP等价 |
|-------|------|---------|
| `INVALID_PARAM` | 参数无效 | 400 |
| `NOT_FOUND` | 资源不存在 | 404 |
| `CONFLICT` | 资源冲突（如时间重叠） | 409 |
| `INVALID_STATE` | 状态流转非法 | 422 |
| `INTERNAL_ERROR` | 内部错误 | 500 |

### 4.4 日志要求

```python
# 必须记录的日志
- 排程创建/更新/删除
- 任务创建/状态变更
- 每日任务生成结果
- 所有错误和异常
```

---

## 5. 详细功能说明

### 5.1 功能点列表

| 功能 | 描述 | 优先级 |
|-----|------|-------|
| 排程CRUD | 创建、查询、更新排程 | P0 |
| 任务CRUD | 创建、查询任务 | P0 |
| 状态管理 | 任务状态流转（含验证） | P0 |
| 每日任务生成 | 根据排程自动生成任务 | P0 |
| 待执行任务查询 | 按优先级返回待处理任务 | P0 |
| 多租户隔离 | tenant_id数据隔离 | P0 |
| 时间冲突检测 | 排程时间重叠检查 | P1 |
| 执行统计 | 任务完成率统计 | P2 |

### 5.2 业务规则

#### 排程规则
```
1. 同一zone_id的排程时间段不能重叠
2. 删除排程不会影响已生成的任务
3. 停用排程(is_active=False)后不再生成新任务
4. priority范围1-10，1最高优先
```

#### 任务规则
```
1. emergency类型任务自动priority=1
2. 状态流转必须符合状态机定义
3. 完成任务必须记录completion_rate
4. 失败任务必须记录failure_reason
5. 取消只能从pending或assigned状态进行
```

#### 每日任务生成规则
```
1. 检查排程的frequency确定是否需要生成
2. 检查time_slots.days确定星期几执行
3. 同一排程同一天只生成一次（幂等）
4. scheduled_start根据time_slots计算
```

### 5.3 边界条件处理

| 场景 | 处理方式 |
|-----|---------|
| zone_id不存在 | 返回NOT_FOUND错误 |
| 时间段格式错误 | 返回INVALID_PARAM错误 |
| 状态流转非法 | 返回INVALID_STATE错误 |
| 重复生成任务 | 跳过，返回skipped_count |
| tenant_id不匹配 | 返回NOT_FOUND（不暴露存在性） |

---

## 6. 测试要求

### 6.1 单元测试用例

```python
# tests/test_task_tools.py

import pytest
from uuid import uuid4

class TestScheduleTools:
    """排程管理测试"""
    
    async def test_create_schedule_success(self):
        """测试正常创建排程"""
        result = await tools.handle("task_create_schedule", {
            "tenant_id": str(uuid4()),
            "zone_id": str(uuid4()),
            "task_type": "routine",
            "frequency": "daily",
            "time_slots": [{"start": "08:00", "end": "10:00"}],
            "priority": 3
        })
        assert result.success
        assert result.data["schedule"]["priority"] == 3
    
    async def test_create_schedule_invalid_priority(self):
        """测试无效优先级"""
        result = await tools.handle("task_create_schedule", {
            "tenant_id": str(uuid4()),
            "zone_id": str(uuid4()),
            "task_type": "routine",
            "frequency": "daily",
            "time_slots": [{"start": "08:00", "end": "10:00"}],
            "priority": 15  # 超出范围
        })
        assert not result.success
        assert result.error_code == "INVALID_PARAM"

class TestTaskTools:
    """任务管理测试"""
    
    async def test_create_task_success(self):
        """测试正常创建任务"""
        pass
    
    async def test_update_status_valid_transition(self):
        """测试合法状态流转"""
        # pending → assigned
        pass
    
    async def test_update_status_invalid_transition(self):
        """测试非法状态流转"""
        # pending → completed (应失败)
        pass
    
    async def test_emergency_task_priority(self):
        """测试紧急任务自动设置优先级"""
        pass

class TestDailyTaskGeneration:
    """每日任务生成测试"""
    
    async def test_generate_daily_tasks(self):
        """测试根据排程生成任务"""
        pass
    
    async def test_generate_idempotent(self):
        """测试重复生成的幂等性"""
        pass
    
    async def test_generate_respects_days(self):
        """测试按星期几生成"""
        pass
```

### 6.2 集成测试场景

```
场景1: 完整任务生命周期
1. 创建排程
2. 生成每日任务
3. 分配任务给机器人
4. 更新状态为执行中
5. 完成任务
6. 验证任务记录

场景2: 与M1空间管理联调
1. 从M1获取zone列表
2. 为zone创建排程
3. 验证zone信息正确关联
```

---

## 7. 示例代码

### 7.1 MCP Server主入口 (server.py)

```python
"""
M2: 任务管理 MCP Server
"""
import asyncio
import json
from mcp.server import Server
from mcp.types import Tool, TextContent

from .tools import TaskTools
from .storage import InMemoryTaskStorage

# 创建MCP Server实例
app = Server("task-manager")
storage = InMemoryTaskStorage()
tools = TaskTools(storage)

# Tool定义列表
TASK_MANAGER_TOOLS = [
    {
        "name": "task_list_schedules",
        "description": "获取清洁排程列表",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "format": "uuid"},
                "zone_id": {"type": "string", "format": "uuid"},
                "building_id": {"type": "string", "format": "uuid"},
                "is_active": {"type": "boolean", "default": True}
            },
            "required": ["tenant_id"]
        }
    },
    {
        "name": "task_get_schedule",
        "description": "获取单个排程详情",
        "inputSchema": {
            "type": "object",
            "properties": {
                "schedule_id": {"type": "string", "format": "uuid"}
            },
            "required": ["schedule_id"]
        }
    },
    {
        "name": "task_create_schedule",
        "description": "创建清洁排程",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "format": "uuid"},
                "zone_id": {"type": "string", "format": "uuid"},
                "task_type": {"type": "string", "enum": ["routine", "deep", "spot", "emergency"]},
                "frequency": {"type": "string", "enum": ["once", "daily", "weekly", "monthly"]},
                "time_slots": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "string"},
                            "end": {"type": "string"},
                            "days": {"type": "array", "items": {"type": "integer"}}
                        }
                    }
                },
                "priority": {"type": "integer", "minimum": 1, "maximum": 10},
                "estimated_duration": {"type": "integer"},
                "created_by": {"type": "string"}
            },
            "required": ["tenant_id", "zone_id", "task_type", "frequency", "time_slots"]
        }
    },
    {
        "name": "task_update_schedule",
        "description": "更新排程信息",
        "inputSchema": {
            "type": "object",
            "properties": {
                "schedule_id": {"type": "string", "format": "uuid"},
                "updates": {"type": "object"}
            },
            "required": ["schedule_id", "updates"]
        }
    },
    {
        "name": "task_list_tasks",
        "description": "获取任务列表（支持多条件筛选）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "format": "uuid"},
                "zone_id": {"type": "string", "format": "uuid"},
                "robot_id": {"type": "string", "format": "uuid"},
                "status": {"type": "string"},
                "date_from": {"type": "string", "format": "date"},
                "date_to": {"type": "string", "format": "date"},
                "limit": {"type": "integer", "default": 50},
                "offset": {"type": "integer", "default": 0}
            },
            "required": ["tenant_id"]
        }
    },
    {
        "name": "task_get_task",
        "description": "获取单个任务详情",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "format": "uuid"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "task_create_task",
        "description": "创建清洁任务",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "format": "uuid"},
                "zone_id": {"type": "string", "format": "uuid"},
                "task_type": {"type": "string", "enum": ["routine", "deep", "spot", "emergency"]},
                "priority": {"type": "integer", "minimum": 1, "maximum": 10},
                "scheduled_start": {"type": "string", "format": "date-time"},
                "schedule_id": {"type": "string", "format": "uuid"},
                "created_by": {"type": "string"},
                "notes": {"type": "string"}
            },
            "required": ["tenant_id", "zone_id", "task_type"]
        }
    },
    {
        "name": "task_update_status",
        "description": "更新任务状态",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "format": "uuid"},
                "status": {"type": "string", "enum": ["assigned", "in_progress", "completed", "failed", "cancelled"]},
                "robot_id": {"type": "string", "format": "uuid"},
                "actual_start": {"type": "string", "format": "date-time"},
                "actual_end": {"type": "string", "format": "date-time"},
                "completion_rate": {"type": "number", "minimum": 0, "maximum": 100},
                "failure_reason": {"type": "string"},
                "updated_by": {"type": "string"}
            },
            "required": ["task_id", "status"]
        }
    },
    {
        "name": "task_get_pending_tasks",
        "description": "获取待执行任务列表（供Agent调度）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "format": "uuid"},
                "zone_ids": {"type": "array", "items": {"type": "string", "format": "uuid"}},
                "max_count": {"type": "integer", "default": 20}
            },
            "required": ["tenant_id"]
        }
    },
    {
        "name": "task_generate_daily_tasks",
        "description": "根据排程生成指定日期的任务",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "format": "uuid"},
                "date": {"type": "string", "format": "date"}
            },
            "required": ["tenant_id", "date"]
        }
    }
]


@app.list_tools()
async def list_tools() -> list[Tool]:
    """返回支持的Tools列表"""
    return [Tool(**t) for t in TASK_MANAGER_TOOLS]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理Tool调用"""
    result = await tools.handle(name, arguments)
    return [TextContent(type="text", text=json.dumps(result.model_dump()))]


async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())
```

### 7.2 Tool实现示例 (tools.py 片段)

```python
"""
任务管理Tool实现
"""
from typing import Dict, Any, List
from uuid import uuid4
from datetime import datetime, date
import logging

from interfaces.data_models import (
    CleaningSchedule, CleaningTask, 
    TaskStatus, TaskType, CleaningFrequency, TimeSlot
)
from interfaces.mcp_tools import ToolResult

logger = logging.getLogger(__name__)


# 状态流转规则
VALID_TRANSITIONS = {
    TaskStatus.PENDING: [TaskStatus.ASSIGNED, TaskStatus.CANCELLED],
    TaskStatus.ASSIGNED: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
    TaskStatus.IN_PROGRESS: [TaskStatus.COMPLETED, TaskStatus.FAILED],
    TaskStatus.COMPLETED: [],
    TaskStatus.FAILED: [],
    TaskStatus.CANCELLED: [],
}


class TaskTools:
    def __init__(self, storage):
        self.storage = storage
    
    async def handle(self, name: str, arguments: dict) -> ToolResult:
        """路由Tool调用"""
        handlers = {
            "task_list_schedules": self._list_schedules,
            "task_get_schedule": self._get_schedule,
            "task_create_schedule": self._create_schedule,
            "task_update_schedule": self._update_schedule,
            "task_list_tasks": self._list_tasks,
            "task_get_task": self._get_task,
            "task_create_task": self._create_task,
            "task_update_status": self._update_status,
            "task_get_pending_tasks": self._get_pending_tasks,
            "task_generate_daily_tasks": self._generate_daily_tasks,
        }
        
        handler = handlers.get(name)
        if not handler:
            return ToolResult(success=False, error=f"Unknown tool: {name}", error_code="NOT_FOUND")
        
        try:
            return await handler(arguments)
        except Exception as e:
            logger.exception(f"Error handling {name}")
            return ToolResult(success=False, error=str(e), error_code="INTERNAL_ERROR")
    
    async def _create_task(self, args: Dict[str, Any]) -> ToolResult:
        """创建清洁任务"""
        tenant_id = args.get("tenant_id")
        zone_id = args.get("zone_id")
        task_type = args.get("task_type")
        
        if not all([tenant_id, zone_id, task_type]):
            return ToolResult(
                success=False, 
                error="tenant_id, zone_id, task_type are required",
                error_code="INVALID_PARAM"
            )
        
        # 紧急任务自动设置最高优先级
        priority = args.get("priority", 5)
        if task_type == "emergency":
            priority = 1
        
        task = CleaningTask(
            task_id=uuid4(),
            tenant_id=tenant_id,
            zone_id=zone_id,
            task_type=TaskType(task_type),
            status=TaskStatus.PENDING,
            priority=priority,
            scheduled_start=args.get("scheduled_start"),
            schedule_id=args.get("schedule_id"),
            notes=args.get("notes"),
            created_by=args.get("created_by", "system"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await self.storage.save_task(task)
        logger.info(f"Task created: {task.task_id}")
        
        return ToolResult(success=True, data={"task": task.model_dump()})
    
    async def _update_status(self, args: Dict[str, Any]) -> ToolResult:
        """更新任务状态"""
        task_id = args.get("task_id")
        new_status = args.get("status")
        
        if not all([task_id, new_status]):
            return ToolResult(
                success=False,
                error="task_id and status are required",
                error_code="INVALID_PARAM"
            )
        
        task = await self.storage.get_task(task_id)
        if not task:
            return ToolResult(success=False, error="Task not found", error_code="NOT_FOUND")
        
        # 验证状态流转
        new_status_enum = TaskStatus(new_status)
        if new_status_enum not in VALID_TRANSITIONS.get(task.status, []):
            return ToolResult(
                success=False,
                error=f"Invalid status transition: {task.status.value} → {new_status}",
                error_code="INVALID_STATE"
            )
        
        # 特殊验证
        if new_status_enum == TaskStatus.ASSIGNED and not args.get("robot_id"):
            return ToolResult(
                success=False,
                error="robot_id is required when assigning task",
                error_code="INVALID_PARAM"
            )
        
        if new_status_enum == TaskStatus.COMPLETED and args.get("completion_rate") is None:
            return ToolResult(
                success=False,
                error="completion_rate is required when completing task",
                error_code="INVALID_PARAM"
            )
        
        if new_status_enum == TaskStatus.FAILED and not args.get("failure_reason"):
            return ToolResult(
                success=False,
                error="failure_reason is required when task fails",
                error_code="INVALID_PARAM"
            )
        
        # 更新任务
        updates = {
            "status": new_status_enum,
            "updated_at": datetime.utcnow()
        }
        
        if args.get("robot_id"):
            updates["assigned_robot_id"] = args["robot_id"]
        if args.get("actual_start"):
            updates["actual_start"] = args["actual_start"]
        if args.get("actual_end"):
            updates["actual_end"] = args["actual_end"]
        if args.get("completion_rate") is not None:
            updates["completion_rate"] = args["completion_rate"]
        if args.get("failure_reason"):
            updates["failure_reason"] = args["failure_reason"]
        
        updated_task = await self.storage.update_task(task_id, updates)
        logger.info(f"Task {task_id} status updated: {task.status.value} → {new_status}")
        
        return ToolResult(success=True, data={"task": updated_task.model_dump()})
    
    async def _get_pending_tasks(self, args: Dict[str, Any]) -> ToolResult:
        """获取待执行任务列表"""
        tenant_id = args.get("tenant_id")
        if not tenant_id:
            return ToolResult(
                success=False,
                error="tenant_id is required",
                error_code="INVALID_PARAM"
            )
        
        zone_ids = args.get("zone_ids")
        max_count = args.get("max_count", 20)
        
        tasks = await self.storage.get_pending_tasks(
            tenant_id=tenant_id,
            zone_ids=zone_ids,
            max_count=max_count
        )
        
        # 按优先级和计划时间排序
        tasks.sort(key=lambda t: (t.priority, t.scheduled_start or datetime.max, t.created_at))
        
        return ToolResult(
            success=True,
            data={
                "tasks": [t.model_dump() for t in tasks],
                "count": len(tasks)
            }
        )
```

### 7.3 存储层示例 (storage.py)

```python
"""
任务管理内存存储层
"""
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime, date

from interfaces.data_models import CleaningSchedule, CleaningTask, TaskStatus


class InMemoryTaskStorage:
    """内存存储实现（MVP阶段）"""
    
    def __init__(self):
        self._schedules: Dict[str, CleaningSchedule] = {}
        self._tasks: Dict[str, CleaningTask] = {}
        self._generated_tasks: set = set()  # (schedule_id, date) 用于幂等检查
    
    # ========== 排程操作 ==========
    
    async def save_schedule(self, schedule: CleaningSchedule) -> CleaningSchedule:
        self._schedules[str(schedule.schedule_id)] = schedule
        return schedule
    
    async def get_schedule(self, schedule_id: str) -> Optional[CleaningSchedule]:
        return self._schedules.get(str(schedule_id))
    
    async def list_schedules(
        self,
        tenant_id: str,
        zone_id: str = None,
        is_active: bool = None
    ) -> List[CleaningSchedule]:
        result = []
        for schedule in self._schedules.values():
            if str(schedule.tenant_id) != str(tenant_id):
                continue
            if zone_id and str(schedule.zone_id) != str(zone_id):
                continue
            if is_active is not None and schedule.is_active != is_active:
                continue
            result.append(schedule)
        return result
    
    async def update_schedule(
        self, 
        schedule_id: str, 
        updates: dict
    ) -> Optional[CleaningSchedule]:
        schedule = self._schedules.get(str(schedule_id))
        if not schedule:
            return None
        
        for key, value in updates.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)
        schedule.updated_at = datetime.utcnow()
        
        return schedule
    
    # ========== 任务操作 ==========
    
    async def save_task(self, task: CleaningTask) -> CleaningTask:
        self._tasks[str(task.task_id)] = task
        return task
    
    async def get_task(self, task_id: str) -> Optional[CleaningTask]:
        return self._tasks.get(str(task_id))
    
    async def list_tasks(
        self,
        tenant_id: str,
        zone_id: str = None,
        robot_id: str = None,
        status: str = None,
        date_from: date = None,
        date_to: date = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[CleaningTask], int]:
        result = []
        for task in self._tasks.values():
            if str(task.tenant_id) != str(tenant_id):
                continue
            if zone_id and str(task.zone_id) != str(zone_id):
                continue
            if robot_id and str(task.assigned_robot_id) != str(robot_id):
                continue
            if status and task.status.value != status:
                continue
            if date_from and task.created_at.date() < date_from:
                continue
            if date_to and task.created_at.date() > date_to:
                continue
            result.append(task)
        
        total = len(result)
        result = result[offset:offset + limit]
        return result, total
    
    async def update_task(self, task_id: str, updates: dict) -> Optional[CleaningTask]:
        task = self._tasks.get(str(task_id))
        if not task:
            return None
        
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        return task
    
    async def get_pending_tasks(
        self,
        tenant_id: str,
        zone_ids: List[str] = None,
        max_count: int = 20
    ) -> List[CleaningTask]:
        result = []
        for task in self._tasks.values():
            if str(task.tenant_id) != str(tenant_id):
                continue
            if task.status != TaskStatus.PENDING:
                continue
            if zone_ids and str(task.zone_id) not in [str(z) for z in zone_ids]:
                continue
            result.append(task)
            if len(result) >= max_count:
                break
        return result
    
    # ========== 任务生成 ==========
    
    async def is_task_generated(self, schedule_id: str, task_date: date) -> bool:
        """检查是否已生成任务（幂等检查）"""
        return (str(schedule_id), task_date) in self._generated_tasks
    
    async def mark_task_generated(self, schedule_id: str, task_date: date):
        """标记任务已生成"""
        self._generated_tasks.add((str(schedule_id), task_date))
```

---

## 8. 验收标准

### 8.1 功能验收

- [ ] 10个Tools全部实现
- [ ] 每个Tool的输入/输出符合接口定义
- [ ] 状态机流转验证完整
- [ ] 错误处理完善，返回正确的错误码
- [ ] 支持多租户数据隔离
- [ ] 每日任务生成幂等

### 8.2 代码质量

- [ ] 类型注解完整
- [ ] 单元测试覆盖所有Tools
- [ ] 状态流转有完整测试
- [ ] 无lint错误

### 8.3 性能要求

- 单Tool响应时间 < 100ms
- 支持并发调用
- 每日任务生成 < 1s（100个排程）

---

## 9. 开发步骤建议

```
1. 创建目录结构
   src/mcp_servers/task_manager/
   ├── __init__.py
   ├── server.py
   ├── tools.py
   ├── storage.py
   └── tests/
       ├── __init__.py
       └── test_tools.py

2. 实现storage.py（内存存储层）

3. 实现tools.py（核心Tool逻辑）
   - 先实现排程相关Tools
   - 再实现任务相关Tools
   - 最后实现每日任务生成

4. 实现server.py（MCP Server入口）

5. 编写测试
   - 排程CRUD测试
   - 任务CRUD测试
   - 状态流转测试
   - 每日任务生成测试

6. 集成测试
```

---

**预计开发时间**: 6-8小时（使用Claude Code）

**开发优先级**: P0（Agent调度依赖此模块）

**前置依赖**: F1数据模型、共享工具库
