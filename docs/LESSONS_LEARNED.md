# Lessons Learned - 问题知识库

> 记录开发过程中遇到的问题和解决方案，确保Claude和团队成员不重复犯错。
> 
> **更新规则**: 发现值得记录的问题后，立即添加到此文档并提交。

---

## 更新日志

| 日期 | 编号 | 问题 | 发现人 |
|-----|------|------|-------|
| 2026-01-19 | LL-001 | Pydantic v2验证器语法 | Jonathan |
| 2026-01-19 | LL-002 | MCP Tool返回值类型 | Jonathan |
| 2026-01-19 | LL-003 | 异步函数必须await | Jonathan |

---

## 🔴 严重问题

### LL-001: Pydantic v2 验证器语法变化

**问题描述**: 使用 `@validator` 装饰器报错

**错误信息**: 
```
PydanticUserError: `@validator` is deprecated, use `@field_validator` instead
```

**错误代码**:
```python
from pydantic import BaseModel, validator

class Robot(BaseModel):
    name: str
    
    @validator('name')
    def validate_name(cls, v):
        return v.strip()
```

**正确代码**:
```python
from pydantic import BaseModel, field_validator

class Robot(BaseModel):
    name: str
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()
```

**关键区别**:
1. 使用 `@field_validator` 而非 `@validator`
2. 必须添加 `@classmethod` 装饰器
3. 必须添加类型注解

**影响范围**: 所有使用Pydantic的模块

**参考文档**: https://docs.pydantic.dev/latest/migration/

---

### LL-002: MCP Tool必须返回list[TextContent]

**问题描述**: MCP Tool返回dict导致类型错误

**错误信息**:
```
TypeError: Expected list[TextContent], got dict
```

**错误代码**:
```python
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    result = await process(arguments)
    return {"success": True, "data": result}  # ❌ 错误！
```

**正确代码**:
```python
from mcp.types import TextContent
import json

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    result = await process(arguments)
    return [TextContent(
        type="text", 
        text=json.dumps({"success": True, "data": result})
    )]
```

**影响范围**: 所有MCP Server

---

### LL-003: 异步函数必须await

**问题描述**: 调用async函数时忘记await导致获得coroutine对象

**错误信息**:
```
TypeError: 'coroutine' object is not subscriptable
# 或
RuntimeWarning: coroutine 'xxx' was never awaited
```

**错误代码**:
```python
async def get_robots():
    # 忘记await
    robots = robot_service.list_all()  # 返回coroutine，不是list！
    return robots[0]  # TypeError!
```

**正确代码**:
```python
async def get_robots():
    robots = await robot_service.list_all()  # 正确await
    return robots[0]
```

**排查方法**:
1. 检查调用的函数是否是 `async def`
2. 如果是，确保前面有 `await`
3. IDE通常会警告 "coroutine was never awaited"

**影响范围**: 所有异步代码

---

## 🟡 中等问题

### LL-004: FastAPI路由装饰器顺序

**问题描述**: 动态路由和静态路由顺序错误导致匹配失败

**错误场景**:
```python
# ❌ 错误顺序
@router.get("/{robot_id}")      # 先定义动态路由
async def get_robot(robot_id: str): ...

@router.get("/status")           # 后定义静态路由
async def get_status(): ...
# 结果: /status 被匹配为 robot_id="status"
```

**正确代码**:
```python
# ✅ 正确顺序
@router.get("/status")           # 先定义静态路由
async def get_status(): ...

@router.get("/{robot_id}")       # 后定义动态路由
async def get_robot(robot_id: str): ...
```

**规则**: 静态路由必须在动态路由之前定义

---

### LL-005: SQLAlchemy 2.0 异步会话管理

**问题描述**: 数据库会话未正确关闭导致连接泄漏

**错误代码**:
```python
async def get_robot(robot_id: str):
    session = async_session_maker()
    result = await session.execute(select(Robot).where(Robot.id == robot_id))
    return result.scalar_one_or_none()
    # session未关闭！
```

**正确代码**:
```python
async def get_robot(robot_id: str):
    async with async_session_maker() as session:
        result = await session.execute(select(Robot).where(Robot.id == robot_id))
        return result.scalar_one_or_none()
    # 自动关闭
```

**或使用依赖注入**:
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

@router.get("/robots/{robot_id}")
async def get_robot(robot_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Robot).where(Robot.id == robot_id))
    return result.scalar_one_or_none()
```

---

### LL-006: pytest-asyncio fixture配置

**问题描述**: 异步测试fixture默认scope="function"，导致每个测试重复初始化

**错误代码**:
```python
@pytest.fixture
async def db_session():
    # 每个测试函数都会执行一次
    engine = create_async_engine(...)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    ...
```

**正确代码**:
```python
import pytest_asyncio

@pytest_asyncio.fixture(scope="module")
async def db_session():
    # 每个模块只执行一次
    engine = create_async_engine(...)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    ...
```

**同时需要在 `pyproject.toml` 配置**:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

---

## 🟢 小问题

### LL-007: JSON序列化datetime

**问题描述**: datetime对象无法直接JSON序列化

**错误信息**:
```
TypeError: Object of type datetime is not JSON serializable
```

**解决方案**:
```python
import json
from datetime import datetime

# 方案1: 使用default参数
def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

json.dumps(data, default=json_serial)

# 方案2: 使用Pydantic
from pydantic import BaseModel

class Response(BaseModel):
    created_at: datetime
    
response.model_dump_json()  # 自动处理datetime
```

---

### LL-008: Redis连接池配置

**问题描述**: 默认连接池大小(10)在高并发时不足

**警告信息**:
```
ConnectionPool: max_connections (10) reached, waiting for free connection...
```

**解决方案**:
```python
import redis.asyncio as redis

pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,  # 根据并发量调整
    decode_responses=True
)
client = redis.Redis(connection_pool=pool)
```

---

### LL-009: Docker Compose环境变量

**问题描述**: `.env` 文件中的变量在docker-compose.yml中未生效

**原因**: docker compose默认不加载 `.env` 文件中的变量到容器环境

**解决方案**:
```yaml
# docker-compose.yml
services:
  api:
    env_file:
      - .env  # 明确指定env文件
    environment:
      - DATABASE_URL=${DATABASE_URL}  # 或显式传递
```

---

## 📝 待验证

### LL-010: MCP连接超时

**假设**: MCP Server长时间无请求时连接会断开

**观察**: 某些情况下MCP调用失败，可能与连接超时有关

**待验证**: 
1. 添加心跳机制
2. 添加重连逻辑
3. 压测观察连接状态

---

### LL-011: Agent并发决策冲突

**假设**: 多个Agent同时操作同一机器人可能产生冲突

**待验证**: 
1. 添加分布式锁
2. 或使用乐观锁机制
3. 或单Agent串行处理

---

## 模板

### 添加新问题的模板

```markdown
### LL-XXX: [问题标题]

**问题描述**: [简要描述问题]

**错误信息**:
```
[粘贴错误信息]
```

**错误代码**:
```python
# ❌ 错误
[导致问题的代码]
```

**正确代码**:
```python
# ✅ 正确
[解决后的代码]
```

**影响范围**: [哪些模块受影响]
**发现日期**: [日期]
**发现人**: [姓名]
```

---

## 问题分类说明

| 级别 | 说明 | 标记 |
|-----|------|------|
| 🔴 严重 | 会导致程序崩溃或功能完全失效 | 必须立即了解 |
| 🟡 中等 | 会导致部分功能异常或性能问题 | 开发时注意 |
| 🟢 小问题 | 边缘情况或小坑 | 遇到时查阅 |
| 📝 待验证 | 疑似问题，需要进一步验证 | 关注 |
