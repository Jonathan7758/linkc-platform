# LinkC MVP 开发指导

## 给本地Claude Code使用的开发上下文包

**日期**: 2026年1月19日
**当前阶段**: Week 1-2（基础设施 + MCP Server）

---

# 一、项目概述

## 1.1 LinkC是什么

LinkC是物业机器人协同平台MVP，核心功能：
- 统一管理多品牌清洁机器人（高仙、科沃斯等）
- AI Agent自主调度清洁任务
- 三层终端：训练工作台 / 运营控制台 / 战略驾驶舱

## 1.2 技术栈

```
后端:
├── Python 3.11+
├── MCP SDK (Model Context Protocol)
├── FastAPI (API层)
├── Pydantic v2 (数据验证)
├── PostgreSQL + Redis (存储)
└── asyncio (异步)

前端:
├── React + TypeScript
├── TailwindCSS
└── Vite
```

## 1.3 当前开发重点

```
Week 1-2 目标:
├── F1-F4 基础设施模块
├── M1 空间管理MCP Server ✅ 规格书完成
├── M2 任务管理MCP Server ✅ 规格书完成
└── M3 高仙机器人MCP Server ✅ 规格书完成
```

---

# 二、项目结构

```
linkc-platform/
├── CLAUDE.md                 # Claude Code项目指令
├── docs/
│   ├── LESSONS_LEARNED.md   # 问题知识库
│   └── specs/               # 规格书
│       ├── M1-space-mcp.md
│       ├── M2-task-mcp.md
│       └── M3-gaoxian-mcp.md
├── interfaces/              # 接口定义
│   ├── data_models.py
│   ├── mcp_tools.py
│   ├── api_schemas.py
│   ├── agent_protocols.py
│   └── events.py
├── shared/                  # 共享模块
│   ├── config.py           # F3
│   ├── auth.py             # F4
│   └── utils.py            # F2
└── src/
    └── mcp_servers/
        ├── space_manager/   # M1
        ├── task_manager/    # M2
        └── robot_gaoxian/   # M3
```

---

# 三、核心数据模型摘要

## 3.1 空间模型

```python
# Building → Floor → Zone → Point 层级结构

class Zone(BaseModel):
    zone_id: UUID
    floor_id: UUID
    name: str
    zone_type: ZoneType        # lobby, corridor, office, restroom, etc.
    area_sqm: float
    cleaning_priority: int     # 1-5
    polygon: List[Point]       # 区域边界
```

## 3.2 机器人模型

```python
class RobotStatus(str, Enum):
    OFFLINE = "offline"
    IDLE = "idle"
    WORKING = "working"
    PAUSED = "paused"
    CHARGING = "charging"
    ERROR = "error"

class Robot(BaseModel):
    robot_id: UUID
    name: str
    brand: RobotBrand          # gaoxian, ecovacs
    status: RobotStatus
    battery_level: int         # 0-100
    current_location: Location
```

## 3.3 任务模型

```python
class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CleaningTask(BaseModel):
    task_id: UUID
    zone_id: UUID
    task_type: TaskType        # routine, deep, spot, emergency
    status: TaskStatus
    priority: int              # 1-10, 1最高
    assigned_robot_id: Optional[UUID]
```

---

# 四、MCP Tool返回格式

所有MCP Tool必须返回 `ToolResult`:

```python
class ToolResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None

# MCP Server入口必须返回 list[TextContent]
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    result = await tools.handle(name, arguments)
    return [TextContent(type="text", text=json.dumps(result.model_dump()))]
```

---

# 五、开发提示词模板

## 5.1 开发M2任务管理MCP Server

```
开发 M2 任务管理 MCP Server

## 参考文档
请参考规格书 docs/specs/M2-task-mcp.md

## 项目上下文
- 这是LinkC物业机器人协同平台的MVP项目
- 使用MCP (Model Context Protocol) 架构
- Python 3.11+, Pydantic v2, asyncio

## 要实现的文件
src/mcp_servers/task_manager/
├── __init__.py
├── server.py      # MCP Server主入口，定义Tools列表
├── tools.py       # 10个Tool的实现
├── storage.py     # 内存存储层
└── tests/
    └── test_tools.py

## 核心要求
1. 实现10个Tools: task_list_schedules, task_get_schedule, task_create_schedule, 
   task_update_schedule, task_list_tasks, task_get_task, task_create_task, 
   task_update_status, task_get_pending_tasks, task_generate_daily_tasks
2. 任务状态机: pending → assigned → in_progress → completed/failed
3. 状态流转验证完整
4. 多租户数据隔离(tenant_id)
5. 返回格式统一使用ToolResult

## 特别注意
1. MCP Tool返回必须是 list[TextContent]
2. Pydantic v2语法：使用 @field_validator 而非 @validator
3. emergency任务自动设置priority=1
4. 完成任务必须有completion_rate
5. 失败任务必须有failure_reason

请先生成 storage.py 和 tools.py
```

## 5.2 开发M3高仙机器人MCP Server

```
开发 M3 高仙机器人 MCP Server

## 参考文档
请参考规格书 docs/specs/M3-gaoxian-mcp.md

## 项目上下文
- 这是LinkC物业机器人协同平台的MVP项目
- M3负责与高仙品牌机器人通信
- MVP阶段使用Mock模拟器，不直接连接真实设备

## 要实现的文件
src/mcp_servers/robot_gaoxian/
├── __init__.py
├── server.py      # MCP Server主入口
├── tools.py       # 12个Tool的实现
├── storage.py     # 机器人数据存储
├── mock_client.py # ⭐ Mock模拟器（重要！）
└── tests/
    └── test_tools.py

## 核心要求
1. 实现12个Tools: robot_list_robots, robot_get_robot, robot_get_status,
   robot_batch_get_status, robot_start_task, robot_pause_task, robot_resume_task,
   robot_cancel_task, robot_go_to_location, robot_go_to_charge, 
   robot_get_errors, robot_clear_error
2. Mock模拟器必须完整可用
3. 启动任务前检查：状态、电量、故障
4. 状态流转验证

## 业务规则
- 电量 < 20% 拒绝启动任务
- 只有idle/charging状态可接收任务
- 有error/critical故障时不能启动任务
- force=True可强制取消任务返回充电

## Mock模拟器要求
- 模拟3个机器人
- 模拟电量消耗和充电
- 模拟任务进度更新
- 模拟随机故障（1%概率）

请先生成 mock_client.py，这是开发测试的基础
```

## 5.3 继续开发/修复Bug

```
继续开发 [模块名称]

## 上次完成
[描述上次完成的内容]

## 本次任务
[描述本次要完成的内容]

## 当前代码状态
[粘贴现有代码或描述]

## 注意
- 保持与现有代码风格一致
- 如果遇到问题，记录到LESSONS_LEARNED.md
```

## 5.4 修复错误

```
修复以下问题：

## 错误信息
```
[粘贴完整错误堆栈]
```

## 相关文件
[文件路径]

## 期望行为
[描述正确的行为]

## 要求
1. 分析根因
2. 修复代码
3. 如果是通用问题，建议添加到 LESSONS_LEARNED.md
```

---

# 六、已知问题和解决方案

记录到 `docs/LESSONS_LEARNED.md`：

## LL-001: Pydantic v2 验证器语法变化
```python
# ❌ 错误（v1语法）
@validator('name')
def validate_name(cls, v):
    return v

# ✅ 正确（v2语法）  
@field_validator('name')
@classmethod
def validate_name(cls, v):
    return v
```

## LL-002: MCP Tool必须返回list[TextContent]
```python
# ❌ 错误
return {"result": "success"}

# ✅ 正确
return [TextContent(type="text", text=json.dumps(result.model_dump()))]
```

## LL-003: asyncio.sleep在Mock中使用
```python
# 模拟网络延迟
await asyncio.sleep(0.1)
```

---

# 七、开发顺序建议

```
Day 5-6: 
├── 1. 创建项目脚手架目录结构
├── 2. 实现shared/（F2-F3）
├── 3. 开始M2 storage.py

Day 7-8:
├── 4. 完成M2 tools.py
├── 5. 完成M2 server.py
├── 6. M2单元测试

Day 9-10:
├── 7. M3 mock_client.py
├── 8. M3 storage.py + tools.py
├── 9. M3 server.py
└── 10. M3单元测试
```

---

# 八、验收检查清单

## M2任务管理MCP Server

- [ ] 10个Tools全部实现
- [ ] 状态机流转验证完整
- [ ] 每日任务生成幂等
- [ ] emergency任务自动priority=1
- [ ] 单元测试通过

## M3高仙机器人MCP Server

- [ ] 12个Tools全部实现
- [ ] Mock模拟器可运行
- [ ] 电量检查正确
- [ ] 故障检查正确
- [ ] 状态流转正确
- [ ] 单元测试通过

---

**祝开发顺利！🚀**

如有问题，请更新 LESSONS_LEARNED.md 并同步到团队。
