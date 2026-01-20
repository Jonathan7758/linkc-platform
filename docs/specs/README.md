# LinkC MVP 模块规格书汇总

## 文档信息

| 属性 | 值 |
|-----|-----|
| 版本 | 1.0 |
| 日期 | 2026-01-20 |
| 状态 | 完成 |
| 规格书总数 | 32个 |

---

## 规格书清单

### Layer 1: MCP服务层 (4个)

| ID | 名称 | 文件 | 说明 |
|----|------|------|------|
| M1 | 空间管理MCP Server | `mcp/M1-space-mcp.md` | 管理楼宇/楼层/区域/点位 |
| M2 | 任务管理MCP Server | `mcp/M2-task-mcp.md` | 管理清洁任务和排程 |
| M3 | 高仙机器人MCP Server | `mcp/M3-gaoxian-mcp.md` | 对接高仙机器人API |
| M4 | 科沃斯MCP Server | `mcp/M4-ecovacs-mcp.md` | 对接科沃斯机器人API |

### Layer 2: 数据平台层 (3个)

| ID | 名称 | 文件 | 说明 |
|----|------|------|------|
| D1 | 数据采集引擎 | `data/D1-data-collector.md` | 定时/事件驱动数据采集 |
| D2 | 数据存储服务 | `data/D2-data-storage.md` | 数据持久化和索引 |
| D3 | 数据查询API | `data/D3-data-query.md` | 提供数据查询接口 |

### Layer 3: Agent层 (4个)

| ID | 名称 | 文件 | 说明 |
|----|------|------|------|
| A1 | Agent运行时框架 | `agent/A1-agent-runtime.md` | Agent生命周期管理 |
| A2 | 清洁调度Agent | `agent/A2-cleaning-scheduler.md` | 清洁任务智能调度 |
| A3 | 对话助手Agent | `agent/A3-conversation-agent.md` | 自然语言交互 |
| A4 | 数据采集Agent | `agent/A4-data-collection-agent.md` | 定时采集机器人状态 |

### Layer 4: API网关层 (7个)

| ID | 名称 | 文件 | 说明 |
|----|------|------|------|
| G1 | 认证授权API | `api/G1-auth-api.md` | 用户认证、JWT、权限 |
| G2 | 空间API | `api/G2-space-api.md` | 空间数据CRUD接口 |
| G3 | 任务API | `api/G3-task-api.md` | 任务数据CRUD接口 |
| G4 | 机器人API | `api/G4-robot-api.md` | 机器人状态和控制 |
| G5 | Agent交互API | `api/G5-agent-api.md` | Agent对话和命令 |
| G6 | 数据查询API | `api/G6-data-api.md` | 统计和报表数据 |
| G7 | 管理API | `api/G7-admin-api.md` | 系统管理和配置 |

### Layer 5: 前端层 (14个)

#### 训练工作台 (4个)

| ID | 名称 | 文件 | 说明 |
|----|------|------|------|
| T1 | Agent活动流 | `frontend/trainer/T1-activity-feed.md` | 展示Agent决策历史 |
| T2 | 待处理队列 | `frontend/trainer/T2-pending-queue.md` | 展示和处理待确认事项 |
| T3 | 反馈面板 | `frontend/trainer/T3-feedback-panel.md` | Agent反馈录入 |
| T4 | 机器人地图 | `frontend/trainer/T4-robot-map.md` | 实时机器人位置展示 |

#### 运营控制台 (4个)

| ID | 名称 | 文件 | 说明 |
|----|------|------|------|
| O1 | 运营仪表盘 | `frontend/operations/O1-operations-dashboard.md` | 核心KPI展示 |
| O2 | 任务管理 | `frontend/operations/O2-task-management.md` | 任务调度和管理 |
| O3 | 机器人监控 | `frontend/operations/O3-robot-monitoring.md` | 车队状态监控 |
| O4 | 告警管理 | `frontend/operations/O4-alert-management.md` | 告警处理中心 |

#### 战略驾驶舱 (3个)

| ID | 名称 | 文件 | 说明 |
|----|------|------|------|
| E1 | 总览首页 | `frontend/executive/E1-executive-overview.md` | 关键指标一览 |
| E2 | 分析仪表盘 | `frontend/executive/E2-analytics-dashboard.md` | 数据分析和趋势 |
| E3 | 报告页面 | `frontend/executive/E3-reports.md` | 详细报告展示 |

#### 移动端 (3个)

| ID | 名称 | 文件 | 说明 |
|----|------|------|------|
| P1 | 移动监控 | `mobile/P1-mobile-monitor.md` | 机器人状态监控 |
| P2 | 移动任务 | `mobile/P2-mobile-task.md` | 任务管理 |
| P3 | 移动告警 | `mobile/P3-mobile-alert.md` | 告警处理 |

---

## 目录结构

```
linkc-specs/
├── README.md                           # 本文件
├── mcp/                                # MCP服务层
│   ├── M1-space-mcp.md
│   ├── M2-task-mcp.md
│   ├── M3-gaoxian-mcp.md
│   └── M4-ecovacs-mcp.md
├── data/                               # 数据平台层
│   ├── D1-data-collector.md
│   ├── D2-data-storage.md
│   └── D3-data-query.md
├── agent/                              # Agent层
│   ├── A1-agent-runtime.md
│   ├── A2-cleaning-scheduler.md
│   ├── A3-conversation-agent.md
│   └── A4-data-collection-agent.md
├── api/                                # API网关层
│   ├── G1-auth-api.md
│   ├── G2-space-api.md
│   ├── G3-task-api.md
│   ├── G4-robot-api.md
│   ├── G5-agent-api.md
│   ├── G6-data-api.md
│   └── G7-admin-api.md
├── frontend/                           # 前端层
│   ├── trainer/                        # 训练工作台
│   │   ├── T1-activity-feed.md
│   │   ├── T2-pending-queue.md
│   │   ├── T3-feedback-panel.md
│   │   └── T4-robot-map.md
│   ├── operations/                     # 运营控制台
│   │   ├── O1-operations-dashboard.md
│   │   ├── O2-task-management.md
│   │   ├── O3-robot-monitoring.md
│   │   └── O4-alert-management.md
│   └── executive/                      # 战略驾驶舱
│       ├── E1-executive-overview.md
│       ├── E2-analytics-dashboard.md
│       └── E3-reports.md
└── mobile/                             # 移动端
    ├── P1-mobile-monitor.md
    ├── P2-mobile-task.md
    └── P3-mobile-alert.md
```

---

## 技术栈汇总

### 后端

| 组件 | 技术 |
|-----|------|
| 语言 | Python 3.11+ |
| API框架 | FastAPI |
| MCP SDK | mcp>=0.9.0 |
| 数据验证 | Pydantic v2 |
| 数据库 | PostgreSQL + TimescaleDB |
| 缓存 | Redis |
| 消息队列 | Redis Streams |
| ORM | SQLAlchemy 2.0 (async) |

### 前端 (Web)

| 组件 | 技术 |
|-----|------|
| 框架 | React 18 + TypeScript |
| 状态管理 | Zustand |
| UI组件 | Ant Design 5.x |
| 图表 | ECharts / Recharts |
| 地图 | Leaflet |
| 构建工具 | Vite |

### 移动端

| 组件 | 技术 |
|-----|------|
| 框架 | React Native |
| 状态管理 | Zustand |
| 推送 | Firebase Cloud Messaging |
| 离线存储 | AsyncStorage |

---

## 开发顺序建议

### Phase 1: 基础设施 (Week 1-2)
1. F1-F4 基础设施模块
2. M1 空间管理MCP
3. M2 任务管理MCP

### Phase 2: 数据与Agent (Week 3-6)
1. D1-D3 数据平台
2. M3 高仙机器人MCP
3. A1-A4 Agent层

### Phase 3: API层 (Week 7-10)
1. G1-G7 API网关

### Phase 4: 前端 (Week 11-20)
1. T1-T4 训练工作台
2. O1-O4 运营控制台
3. E1-E3 战略驾驶舱
4. P1-P3 移动端

### Phase 5: 集成测试 (Week 21-24)
1. 集成测试
2. 性能优化
3. Pilot部署

---

## 使用说明

### 开发前必读

1. 阅读对应模块的规格书
2. 理解模块依赖关系
3. 遵循接口定义
4. 参考测试用例

### 规格书结构

每个规格书包含：
1. 文档信息（ID、版本、状态、依赖）
2. 模块概述（职责、功能、设计原则）
3. 数据模型（TypeScript/Python接口定义）
4. 接口定义（API/Tool定义）
5. 实现示例
6. 测试要求
7. 性能要求
8. 验收标准

---

*文档版本: 1.0*
*生成日期: 2026-01-20*
