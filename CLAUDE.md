# LinkC Platform - Claude 开发指南

> 此文件由Claude Code自动读取，作为项目上下文。
> 修改此文件需要技术负责人审核。

---

## 🚀 快速状态 (Quick Status)

| 项目 | 值 |
|------|-----|
| **当前周** | Week 2 |
| **总体进度** | 15% |
| **当前里程碑** | MS1 - MCP Server可运行 (60%) |
| **最后更新** | 2026-01-20 |

### 开始工作前，请先查看:
1. **开发进度**: `docs/PROGRESS.md` - 查看当前任务状态
2. **本周计划**: `docs/plan/WEEK_02.md` - 查看今日任务
3. **问题知识库**: `docs/LESSONS_LEARNED.md` - 避免重复踩坑

---

## 📋 项目概述

**LinkC** 是物业机器人协同平台的MVP项目，基于ECIS（企业群体智能系统）架构设计。

**核心价值**: 让清洁机器人从"各自为战"变成"协同作战"，同样的机器人数量，多清洁40%的面积。

**目标市场**: 香港物业管理行业，后续扩展至东南亚。

---

## 📊 开发计划总览

### 总计划文档
- **MASTER_PLAN.md**: `docs/MASTER_PLAN.md` - 24周完整开发计划
- **PROGRESS.md**: `docs/PROGRESS.md` - 实时进度追踪

### 周计划文档
| 周 | 文档 | 主题 |
|---|------|------|
| Week 2 | `docs/plan/WEEK_02.md` | M1空间MCP + M2任务MCP |
| Week 3 | `docs/plan/WEEK_03.md` | M3高仙MCP + D1/D2规格书 |
| Week 4 | `docs/plan/WEEK_04.md` | A1/A4规格书 + MS1验收 |

### 里程碑
| 里程碑 | 时间 | 内容 | 状态 |
|-------|------|------|------|
| MS1 | W4末 | M1+M2+M3联调通过 | 🔄 60% |
| MS2 | W8末 | Agent可自主调度 | ⬜ |
| MS3 | W12末 | 训练工作台可用 | ⬜ |
| MS4 | W16末 | 三层界面完成 | ⬜ |
| MS5 | W20末 | 系统可部署 | ⬜ |
| MS6 | W24末 | Pilot上线 | ⬜ |

---

## 📦 模块开发状态

### Layer 0: 基础设施
| 模块 | 名称 | 规格书 | 代码 | 说明 |
|------|------|--------|------|------|
| F1 | 数据模型 | N/A | ✅ 100% | `interfaces/data_models.py` |
| F2 | 共享工具 | N/A | ✅ 100% | `src/shared/logging.py` |
| F3 | 配置管理 | N/A | ✅ 100% | `src/shared/config.py` |
| F4 | 认证授权 | `specs/api/F4-auth.md` | ⬜ 0% | **待开发** |

### Layer 1: MCP Server
| 模块 | 名称 | 规格书 | 代码 | Tools |
|------|------|--------|------|-------|
| M1 | 空间管理 | `specs/mcp/M1-space-mcp.md` | ✅ 100% | 8/8 |
| M2 | 任务管理 | `specs/mcp/M2-task-mcp.md` | ✅ 100% | 10/10 |
| M3 | 高仙机器人 | `specs/mcp/M3-gaoxian-mcp.md` | ✅ 100% | 12/12 |
| M4 | 科沃斯机器人 | `specs/mcp/M4-ecovacs-mcp.md` | ⬜ 0% | W17 |

### Layer 2: 数据平台
| 模块 | 名称 | 规格书 | 代码 | 计划周 |
|------|------|--------|------|--------|
| D1 | 数据采集引擎 | `specs/data/D1-data-collector.md` | ⬜ | W5 |
| D2 | 数据存储服务 | `specs/data/D2-data-storage.md` | ⬜ | W5-6 |
| D3 | 数据查询API | `specs/data/D3-data-query.md` | ⬜ | W8 |

### Layer 3: Agent
| 模块 | 名称 | 规格书 | 代码 | 计划周 |
|------|------|--------|------|--------|
| A1 | Agent运行时 | `specs/agent/A1-agent-runtime.md` | ⬜ | W6 |
| A2 | 清洁调度 | `specs/agent/A2-cleaning-scheduler.md` | ⬜ | W7 |
| A3 | 对话助手 | `specs/agent/A3-conversation-agent.md` | ⬜ | W8 |
| A4 | 数据采集 | `specs/agent/A4-data-collection-agent.md` | ⬜ | W6 |

### Layer 4: API
| 模块 | 名称 | 规格书 | 代码 | 计划周 |
|------|------|--------|------|--------|
| G1 | 认证API | `specs/api/G1-auth-api.md` | ⬜ | W9 |
| G2 | 空间API | `specs/api/G2-space-api.md` | ⬜ | W9 |
| G3 | 任务API | `specs/api/G3-task-api.md` | ⬜ | W9 |
| G4 | 机器人API | `specs/api/G4-robot-api.md` | ⬜ | W9 |
| G5 | Agent API | `specs/api/G5-agent-api.md` | ⬜ | W10 |
| G6 | 数据API | `specs/api/G6-data-api.md` | ⬜ | W10 |
| G7 | 管理API | `specs/api/G7-admin-api.md` | ⬜ | W10 |

### Layer 5: 前端
| 模块 | 名称 | 规格书目录 | 计划周 |
|------|------|-----------|--------|
| T1-T4 | 训练工作台 | `specs/frontend/trainer/` | W11-12 |
| O1-O4 | 运营控制台 | `specs/frontend/operations/` | W13-14 |
| E1-E3 | 战略驾驶舱 | `specs/frontend/executive/` | W15 |
| P1-P3 | 移动端 | `specs/mobile/` | W16-17 |

---

## 📁 项目结构

```
linkc-platform/
├── CLAUDE.md                 # 本文件 - Claude Code 项目指令
├── docs/
│   ├── MASTER_PLAN.md       # 24周开发总计划
│   ├── PROGRESS.md          # 实时进度追踪 ⭐
│   ├── LESSONS_LEARNED.md   # 问题知识库
│   ├── ARCHITECTURE.md      # 系统架构
│   ├── plan/                # 周计划
│   │   ├── WEEK_02.md
│   │   ├── WEEK_03.md
│   │   └── WEEK_04.md
│   ├── specs/               # 模块规格书
│   │   ├── mcp/            # M1-M4 MCP Server
│   │   ├── agent/          # A1-A4 Agent
│   │   ├── api/            # G1-G7 + F4 API
│   │   ├── data/           # D1-D3 数据平台
│   │   ├── frontend/       # T/O/E 前端
│   │   └── mobile/         # P1-P3 移动端
│   └── templates/           # 模板文件
├── interfaces/              # 接口定义 (核心契约)
│   ├── data_models.py
│   ├── mcp_tools.py
│   ├── api_schemas.py
│   ├── agent_protocols.py
│   └── events.py
├── src/
│   ├── shared/              # 共享模块 F1-F4
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── exceptions.py
│   │   └── auth/           # F4 认证 (待实现)
│   ├── mcp_servers/         # MCP Server M1-M4
│   │   ├── space_manager/   # M1 ✅
│   │   ├── task_manager/    # M2 ✅
│   │   ├── robot_gaoxian/   # M3 ✅
│   │   └── robot_control/   # 通用控制
│   └── agents/              # Agent A1-A4
│       ├── runtime/
│       └── cleaning_scheduler/
├── backend/                 # FastAPI 后端
└── frontend/                # React 前端
```

---

## 🔧 技术栈

### 后端
- **Python 3.11+** / **FastAPI** / **MCP SDK**
- **Pydantic v2** / **SQLAlchemy 2.0** (async)
- **PostgreSQL** / **Redis**

### 前端
- **React 18** / **TypeScript** / **TailwindCSS**
- **React Query** / **Zustand**

### 基础设施
- **Docker + Docker Compose**
- **GitHub Actions** (CI/CD)

---

## ⚠️ 常见陷阱速查

> 完整版见: `docs/LESSONS_LEARNED.md`

### 1. Pydantic v2 验证器
```python
# ❌ 错误
@validator('name')
def validate_name(cls, v): ...

# ✅ 正确
@field_validator('name')
@classmethod
def validate_name(cls, v: str) -> str: ...
```

### 2. MCP Tool 返回值
```python
# ❌ 错误
return {"result": "ok"}

# ✅ 正确
return [TextContent(type="text", text=json.dumps(result))]
```

### 3. 异步函数必须 await
```python
# ❌ 错误
result = async_function()

# ✅ 正确
result = await async_function()
```

---

## 🚀 常用命令

```bash
# 运行测试
python3 -m pytest src/mcp_servers/space_manager/tests/ -v
python3 -m pytest src/mcp_servers/task_manager/tests/ -v

# 语法检查
python3 -m py_compile src/mcp_servers/space_manager/*.py

# Docker
docker compose up -d
docker compose logs -f
```

---

## 📝 工作流程

### 开始每日工作
1. 查看 `docs/PROGRESS.md` 了解当前状态
2. 查看 `docs/plan/WEEK_XX.md` 找到今日任务
3. 开始开发前阅读相关规格书

### 完成任务后
1. 运行相关测试确保通过
2. 更新 `docs/PROGRESS.md`
3. 如遇问题，记录到 `docs/LESSONS_LEARNED.md`
4. Git 提交

### Git 提交规范
```bash
feat(M1): 完成空间管理MCP Server
fix(A2): 修复调度死锁问题
docs: 更新LESSONS_LEARNED.md
test: 添加M3单元测试
```

---

## 📞 联系方式

- **技术负责人**: Jonathan Maang
- **问题反馈**: 更新 `docs/LESSONS_LEARNED.md` 并通知团队
