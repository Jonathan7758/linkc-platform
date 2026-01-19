# LinkC Platform - Claude 开发指南

> 此文件由Claude Code自动读取，作为项目上下文。
> 修改此文件需要技术负责人审核。

---

## 项目概述

**LinkC** 是物业机器人协同平台的MVP项目，基于ECIS（企业群体智能系统）架构设计。

**核心价值主张**: 让清洁机器人从"各自为战"变成"协同作战"，同样的机器人数量，多清洁40%的面积。

**目标市场**: 香港物业管理行业，后续扩展至东南亚。

---

## 技术栈

### 后端
- **Python 3.11+** - 主要开发语言
- **FastAPI** - API框架
- **MCP SDK** - 机器人通信协议
- **Pydantic v2** - 数据验证
- **SQLAlchemy 2.0** - ORM (async)
- **PostgreSQL** - 主数据库
- **Redis** - 缓存和消息队列
- **structlog** - 结构化日志

### 前端
- **React 18** - 前端框架
- **TypeScript** - 类型安全
- **TailwindCSS** - 样式
- **React Query** - 数据获取
- **Zustand** - 状态管理

### 基础设施
- **Docker + Docker Compose** - 容器化
- **GitHub Actions** - CI/CD
- **Prometheus + Grafana** - 监控

---

## 代码规范

### Python
```python
# 命名规范
variable_name = "snake_case"
CONSTANT_NAME = "UPPER_SNAKE_CASE"
ClassName = "PascalCase"
function_name = "snake_case"

# 类型注解（必须）
async def get_robot(robot_id: str) -> Robot | None:
    ...

# Pydantic v2 语法
from pydantic import BaseModel, Field, field_validator

class Robot(BaseModel):
    id: str = Field(..., description="机器人唯一ID")
    name: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v.startswith('robot_'):
            raise ValueError('ID must start with robot_')
        return v

# 异步编程
async def process_task(task_id: str) -> TaskResult:
    async with get_db_session() as session:
        task = await session.get(Task, task_id)
        ...

# 错误处理
from src.shared.exceptions import NotFoundError, ValidationError

async def get_zone(zone_id: str) -> Zone:
    zone = await zone_repo.get(zone_id)
    if not zone:
        raise NotFoundError(f"Zone {zone_id} not found")
    return zone

# 日志
import structlog
logger = structlog.get_logger(__name__)

async def start_cleaning(robot_id: str):
    logger.info("starting_cleaning", robot_id=robot_id)
    ...
```

### TypeScript
```typescript
// 命名规范
const variableName = "camelCase";
const CONSTANT_NAME = "UPPER_SNAKE_CASE";
interface InterfaceName {} // PascalCase
type TypeName = {}; // PascalCase
function functionName() {} // camelCase

// 组件
const RobotCard: React.FC<RobotCardProps> = ({ robot }) => {
  ...
};

// 类型定义
interface Robot {
  id: string;
  name: string;
  status: RobotStatus;
}
```

---

## 核心接口文件（开发前必读）

在修改任何代码前，请先阅读以下接口定义：

| 文件 | 说明 | 影响范围 |
|-----|------|---------|
| `interfaces/data_models.py` | 核心数据模型 | 全部模块 |
| `interfaces/mcp_tools.py` | MCP Tool接口 | MCP Server |
| `interfaces/api_schemas.py` | API请求/响应Schema | API + 前端 |
| `interfaces/agent_protocols.py` | Agent协议 | Agent模块 |
| `interfaces/events.py` | 系统事件定义 | 全部模块 |

**⚠️ 重要**: 修改接口定义需要团队讨论，因为会影响多个模块。

---

## 模块开发指南

### MCP Server 开发
```bash
# 参考规格书
docs/specs/M1-space-mcp.md
docs/specs/M2-task-mcp.md
docs/specs/M3-gaoxian-mcp.md

# 实现位置
src/mcp_servers/[module_name]/
├── __init__.py
├── server.py      # MCP Server主入口
├── tools.py       # Tool实现
├── storage.py     # 数据存储层
└── tests/
    └── test_tools.py
```

### Agent 开发
```bash
# 参考规格书
docs/specs/A1-agent-runtime.md
docs/specs/A2-cleaning-agent.md
docs/specs/A3-conversation-agent.md

# 实现位置
src/agents/[agent_name]/
├── __init__.py
├── agent.py       # Agent主逻辑
├── strategies/    # 决策策略
└── tests/
```

### API 开发
```bash
# 参考规格书
docs/specs/G1-space-api.md
docs/specs/G2-task-api.md

# 实现位置
src/api/routers/[router_name].py
```

---

## ⚠️ 已知问题和解决方案

**详见**: `docs/LESSONS_LEARNED.md`

### 常见陷阱速查

#### 1. Pydantic v2 验证器语法
```python
# ❌ 错误（v1语法）
@validator('name')
def validate_name(cls, v):
    return v

# ✅ 正确（v2语法）
@field_validator('name')
@classmethod
def validate_name(cls, v: str) -> str:
    return v
```

#### 2. MCP Tool 返回值类型
```python
# ❌ 错误
async def call_tool(...) -> dict:
    return {"result": "ok"}

# ✅ 正确
async def call_tool(...) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({"result": "ok"}))]
```

#### 3. 异步函数必须await
```python
# ❌ 错误
result = async_function()  # 返回coroutine对象，不是结果！

# ✅ 正确
result = await async_function()
```

#### 4. 数据库会话管理
```python
# ❌ 错误
session = get_session()
result = await session.execute(...)

# ✅ 正确
async with get_session() as session:
    result = await session.execute(...)
```

---

## 项目命令

```bash
# 开发环境
make dev                    # 启动开发环境
make test                   # 运行所有测试
make lint                   # 代码检查
make format                 # 代码格式化

# 单独运行
pytest tests/mcp_servers/ -v           # 测试MCP Server
pytest tests/agents/ -v                # 测试Agent
uvicorn src.api.main:app --reload      # 启动API

# MCP Server调试
python -m src.mcp_servers.space_manager
python -m src.mcp_servers.task_manager

# Docker
docker compose up -d        # 启动所有服务
docker compose logs -f      # 查看日志
```

---

## 文件修改规则

1. **修改接口定义时** → 同步更新所有实现，通知相关开发者
2. **新增功能时** → 同时添加单元测试
3. **修复bug后** → 更新 `docs/LESSONS_LEARNED.md`
4. **修改CLAUDE.md** → 需要技术负责人审核

---

## Git 提交规范

```bash
# 格式
<type>(<scope>): <description>

# type
feat     # 新功能
fix      # Bug修复
docs     # 文档
refactor # 重构
test     # 测试
chore    # 构建/工具

# 示例
feat(M1): 完成空间管理MCP Server
fix(A2): 修复调度死锁问题
docs: 更新LESSONS_LEARNED.md
```

---

## 联系方式

- **技术负责人**: Jonathan Maang
- **问题反馈**: 更新 `docs/LESSONS_LEARNED.md` 并通知团队
