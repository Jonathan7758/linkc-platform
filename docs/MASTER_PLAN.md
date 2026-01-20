# LinkC MVP 开发执行计划 v3

## 包含规格书编制的完整版

**版本**: 3.0  
**创建日期**: 2026-01-20  
**当前状态**: Week 1 Day 5 完成

---

# 一、规格书总览

## 1.1 规格书完成状态

### 已完成 ✅

| 模块 | 规格书 | 行数 | 完成日期 |
|------|--------|------|---------|
| M1 | 空间管理MCP | ~400 | Week 1 |
| M2 | 任务管理MCP | 1,299 | Week 1 |
| M3 | 高仙机器人MCP | 1,535 | Week 1 |

### 待编制 ⬜

| 模块 | 规格书 | 级别 | 预估行数 | 计划周 |
|------|--------|------|---------|-------|
| **数据层** |
| D1 | 数据采集引擎 | L1详细 | 800-1000 | W3 |
| D2 | 数据存储服务 | L2标准 | 500-600 | W3 |
| D3 | 数据查询API | L2标准 | 400-500 | W6 |
| **Agent层** |
| A1 | Agent运行时框架 | L1详细 | 1000-1200 | W4 |
| A2 | 清洁调度Agent | L1详细 | 1000-1200 | W5 |
| A3 | 对话助手Agent | L2标准 | 500-600 | W5 |
| A4 | 数据采集Agent | L2标准 | 400-500 | W4 |
| **API层** |
| G1-G4 | 核心API规格 | L2标准 | 600-800 | W7 |
| G5-G7 | 辅助API规格 | L2标准 | 400-500 | W8 |
| **前端层** |
| T1-T4 | 训练工作台规格 | L3简化 | 400-500 | W9 |
| O1-O4 | 运营控制台规格 | L3简化 | 400-500 | W11 |
| E1-E3 | 战略驾驶舱规格 | L3简化 | 300-400 | W13 |
| **移动端** |
| P1 | 训练师移动端规格 | L3简化 | 300-400 | W15 |
| P3 | 通知服务规格 | L2标准 | 400-500 | W15 |
| **扩展** |
| M4 | 科沃斯MCP | L2标准 | 800-1000 | W17 |
| I-ALL | 部署监控规格 | L3简化 | 300-400 | W18 |

**总计**: 18个规格书，约9,000-11,000行

## 1.2 规格书级别定义

| 级别 | 内容要求 | 行数 | 适用场景 |
|------|---------|------|---------|
| **L1详细** | 完整Tool定义+数据模型+业务规则+状态机+示例代码+测试用例 | 800-1200 | MCP Server、核心Agent |
| **L2标准** | 接口定义+数据模型+关键业务规则+示例代码 | 400-800 | 数据服务、辅助模块、API |
| **L3简化** | 组件定义+接口说明+交互流程 | 200-500 | 前端组件、简单服务 |

---

# 二、24周开发计划（含规格书编制）

## 2.1 时间线总览

```
     规格书编制                开发工作                里程碑
Week ──────────────────────────────────────────────────────────
 1   ████ M1/M2/M3规格书      F1-F4基础               
 2                            F4认证+M1开发           
 3   ████ D1/D2规格书         M1完成+M2开发           
 4   ████ A1/A4规格书         M2/M3开发               ★ MS1
 5   ████ A2/A3规格书         D1/D2开发               
 6   ████ D3规格书            A1/A4开发               
 7   ████ G1-G4规格书         A2开发                  
 8   ████ G5-G7规格书         A3/D3开发               ★ MS2
 9   ████ T1-T4规格书         G1-G4开发               
10                            G5-G7开发               
11   ████ O1-O4规格书         T1-T4开发               
12                            T1-T4完成               ★ MS3
13   ████ E1-E3规格书         O1-O4开发               
14                            O1-O4完成               
15   ████ P1/P3规格书         E1-E3开发               
16                            P3通知开发              ★ MS4
17   ████ M4规格书            P1移动端开发            
18   ████ I-ALL规格书         M4科沃斯开发            
19                            I1-I2部署               
20                            I3监控                  ★ MS5
21-24                         测试+Pilot              ★ MS6
```

## 2.2 里程碑定义

| 里程碑 | 时间 | 验收标准 |
|-------|------|---------|
| **MS1** | W4末 | M1+M2+M3联调通过，Mock机器人可控制 |
| **MS2** | W8末 | Agent可自主调度任务，端到端流程通过 |
| **MS3** | W12末 | 训练工作台可用，人类可监控Agent |
| **MS4** | W16末 | 三层终端界面完成，通知服务可用 |
| **MS5** | W20末 | 系统可Docker部署，CI/CD就绪 |
| **MS6** | W24末 | Pilot客户环境稳定运行 |

---

# 三、Phase 1: 基础设施 (Week 1-4)

## Week 1: 接口定义 + 基础模块 ✅ 已完成

| Day | 任务 | 状态 |
|-----|------|------|
| D1 | 项目脚手架 + data_models.py | ✅ |
| D2 | mcp_tools.py + api_schemas.py + events.py | ✅ |
| D3 | agent_protocols.py + F2/F3 | ✅ |
| D4 | M1规格书 + 部署配置 | ✅ |
| D5 | F1配置 + F2日志 + F3异常 + M2/M3规格书 | ✅ |

---

## Week 2: F4认证 + M1开发

### Day 6 (01-20)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W2D6-01 | F4认证授权模块 | 开发 | 4h | shared/auth.py |
| W2D6-02 | 共享工具库完善 | 开发 | 2h | shared/utils.py |

### Day 7 (01-21)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W2D7-01 | M1空间MCP Storage层 | 开发 | 3h | storage.py |
| W2D7-02 | M1空间MCP Tools(前4个) | 开发 | 3h | tools.py(部分) |

### Day 8 (01-22)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W2D8-01 | M1空间MCP Tools(后4个) | 开发 | 3h | tools.py(完整) |
| W2D8-02 | M1空间MCP Server入口 | 开发 | 2h | server.py |

### Day 9 (01-23)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W2D9-01 | M1单元测试完善 | 测试 | 3h | test_space_manager.py |
| W2D9-02 | M1集成测试 | 测试 | 2h | test_m1_integration.py |

### Day 10 (01-24)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W2D10-01 | Week 2代码审查 | Review | 2h | 审查报告 |
| W2D10-02 | 文档更新 | 文档 | 1h | PROGRESS.md更新 |

---

## Week 3: M2开发 + D1/D2规格书

### Day 11 (01-27)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W3D11-01 | **D1数据采集引擎规格书** | 📝规格书 | 5h | docs/specs/D1-data-collector.md |

**D1规格书内容大纲**:
```yaml
级别: L1详细
预估行数: 800-1000

章节:
  1. 模块概述
     - 职责：从MCP Server采集机器人和任务数据
     - 数据流向图
  
  2. 架构设计
     - 采集器类型：ScheduledCollector, EventCollector
     - 采集调度器
     - 数据缓冲区
  
  3. 接口定义
     - CollectorBase (抽象基类)
     - RobotStatusCollector
     - TaskStatusCollector
     - EventCollector
  
  4. 数据模型
     - CollectorConfig
     - CollectorStatus
     - DataRecord
     - CollectionResult
  
  5. 采集规则
     - 机器人状态：每30秒采集
     - 任务状态：事件驱动+每5分钟全量
     - 异常事件：实时采集
  
  6. 错误处理
     - 采集失败重试（3次，指数退避）
     - 数据补偿机制
     - 采集器故障隔离
  
  7. 与MCP的交互
     - 调用M3 robot_batch_get_status
     - 调用M2 task_list_tasks
  
  8. 示例代码
     - 完整的RobotStatusCollector实现
  
  9. 测试要点
     - 采集频率测试
     - 故障恢复测试
```

### Day 12 (01-28)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W3D12-01 | **D2数据存储服务规格书** | 📝规格书 | 4h | docs/specs/D2-data-storage.md |
| W3D12-02 | M2任务MCP Storage层 | 开发 | 2h | storage.py |

**D2规格书内容大纲**:
```yaml
级别: L2标准
预估行数: 500-600

章节:
  1. 模块概述
     - 职责：存储采集的数据，提供查询接口
  
  2. 存储架构
     - 时序数据存储（机器人状态历史）
     - 事件存储（任务事件、异常事件）
     - 聚合数据存储（统计数据）
  
  3. 接口定义
     - StorageService
     - TimeSeriesStorage
     - EventStorage
     - AggregateStorage
  
  4. 数据模型
     - TimeSeriesRecord
     - EventRecord
     - AggregateRecord
  
  5. 数据保留策略
     - 原始数据：7天
     - 小时聚合：30天
     - 日聚合：365天
  
  6. 示例代码
```

### Day 13 (01-29)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W3D13-01 | M2任务MCP Tools(排程) | 开发 | 4h | tools.py(排程部分) |
| W3D13-02 | M2任务MCP Tools(任务) | 开发 | 2h | tools.py(任务部分) |

### Day 14 (01-30)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W3D14-01 | M2任务MCP完成+Server | 开发 | 3h | server.py |
| W3D14-02 | M2单元测试 | 测试 | 3h | test_task_manager.py |

### Day 15 (01-31)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W3D15-01 | M1+M2联调测试 | 测试 | 3h | test_m1_m2_integration.py |
| W3D15-02 | Week 3 Review | Review | 2h | 审查报告 |

---

## Week 4: M3开发 + A1/A4规格书 + MS1

### Day 16 (02-03)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W4D16-01 | **A1 Agent运行时框架规格书(上)** | 📝规格书 | 4h | docs/specs/A1-agent-runtime.md |
| W4D16-02 | M3 Mock模拟器 | 开发 | 2h | mock_client.py |

**A1规格书内容大纲**:
```yaml
级别: L1详细
预估行数: 1000-1200

章节:
  1. 模块概述
     - Agent运行时的职责
     - 与MCP Server的关系
     - 在ECIS架构中的位置
  
  2. 架构设计
     - Agent生命周期（初始化→运行→暂停→停止）
     - 决策循环（感知→思考→行动）
     - MCP调用机制
  
  3. 核心接口
     - AgentBase (抽象基类)
       - async def perceive() -> PerceptionResult
       - async def think(perception) -> Decision
       - async def act(decision) -> ActionResult
       - async def learn(feedback) -> None
     
     - MCPClient
       - async def call_tool(server, tool, params) -> ToolResult
       - async def batch_call(calls) -> list[ToolResult]
     
     - DecisionEngine
       - async def make_decision(context) -> Decision
       - async def evaluate_options(options) -> RankedOptions
     
     - EscalationManager
       - async def check_escalation(event) -> EscalationDecision
       - async def escalate(event, level) -> None
  
  4. 5级自治定义
     - Level 1 (Notification): 只通知，不行动
     - Level 2 (Suggestion): 建议方案，等待确认
     - Level 3 (Autonomous-Report): 自主执行，事后报告
     - Level 4 (Full-Autonomous): 完全自主，仅异常报告
     - Level 5 (Strategic): 可调整策略参数
     
     各级别详细行为定义...
  
  5. 升级机制
     - 升级触发条件
     - 升级流程
     - 升级超时处理
  
  6. 可观测性
     - 决策日志格式
     - 性能指标
     - 告警规则
  
  7. 数据模型
     - AgentConfig
     - AgentState
     - Decision
     - EscalationEvent
     - PerceptionResult
     - ActionResult
  
  8. 示例代码
     - 简单Agent实现
     - MCP调用示例
     - 升级处理示例
  
  9. 测试要点
```

### Day 17 (02-04)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W4D17-01 | **A1规格书(下)** | 📝规格书 | 3h | 完成A1规格书 |
| W4D17-02 | **A4数据采集Agent规格书** | 📝规格书 | 3h | docs/specs/A4-data-collector-agent.md |

**A4规格书内容大纲**:
```yaml
级别: L2标准
预估行数: 400-500

章节:
  1. 模块概述
     - 职责：驱动D1采集引擎，监控采集状态
  
  2. Agent配置
     - 采集目标列表
     - 采集频率配置
     - 异常阈值
  
  3. 行为定义
     - 启动流程
     - 采集循环
     - 异常检测
     - 自动恢复
  
  4. 与D1的交互
     - 启动采集器
     - 监控采集状态
     - 处理采集失败
  
  5. 自治等级（建议L3）
     - 自动启动采集
     - 自动重试失败
     - 异常时升级
  
  6. 示例代码
```

### Day 18 (02-05)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W4D18-01 | M3 Storage层 | 开发 | 2h | storage.py |
| W4D18-02 | M3 Tools(状态查询) | 开发 | 4h | tools.py(状态部分) |

### Day 19 (02-06)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W4D19-01 | M3 Tools(任务控制) | 开发 | 3h | tools.py(控制部分) |
| W4D19-02 | M3 Tools(导航+故障) | 开发 | 3h | tools.py(完整) |

### Day 20 (02-07)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W4D20-01 | M3 Server + 测试 | 开发 | 4h | server.py + tests |
| W4D20-02 | **MS1端到端测试** | 测试 | 3h | test_mcp_e2e.py |

### Day 21 (02-08) - MS1里程碑日

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W4D21-01 | Bug修复 | 开发 | 2h | 修复代码 |
| W4D21-02 | **MS1验收** | 验收 | 2h | MS1验收报告 |
| W4D21-03 | Week 4 Review + 规格书Review | Review | 2h | 审查报告 |

**MS1验收检查清单**:
```yaml
功能验收:
  - [ ] M1空间MCP: 8个Tool全部可用
  - [ ] M2任务MCP: 10个Tool全部可用
  - [ ] M3高仙MCP: 12个Tool全部可用
  - [ ] Mock机器人可控制
  - [ ] M1+M2+M3联调通过

规格书验收:
  - [ ] D1规格书完成并Review
  - [ ] D2规格书完成并Review
  - [ ] A1规格书完成并Review
  - [ ] A4规格书完成并Review

质量验收:
  - [ ] 单元测试覆盖率 > 70%
  - [ ] 集成测试全部通过
  - [ ] 无P0级Bug
```

---

# 四、Phase 2: 数据+Agent (Week 5-8)

## Week 5: D1/D2开发 + A2/A3规格书

### Day 22 (02-10)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W5D22-01 | **A2清洁调度Agent规格书(上)** | 📝规格书 | 4h | docs/specs/A2-cleaning-scheduler.md |
| W5D22-02 | D1采集引擎-框架 | 开发 | 2h | collector/base.py |

**A2规格书内容大纲**:
```yaml
级别: L1详细
预估行数: 1000-1200

章节:
  1. 模块概述
     - 核心业务Agent
     - 职责边界
  
  2. 调度策略
     - 任务优先级计算公式
     - 机器人选择算法
     - 负载均衡策略
  
  3. 决策流程
     - 任务分配决策树
     - 机器人选择决策树
     - 紧急任务处理流程
  
  4. MCP调用序列
     - 获取待执行任务 (M2)
     - 获取可用机器人 (M3)
     - 分配任务 (M2)
     - 启动执行 (M3)
     - 监控进度 (M3)
     - 更新状态 (M2)
  
  5. 异常处理
     - 机器人故障：重新分配
     - 任务失败：重试或升级
     - 电量不足：派往充电
     - 清洁区域被占用：等待或跳过
  
  6. 升级规则
     - L3运营升级条件
       - 连续3次任务失败
       - 机器人故障无法自动恢复
     - L4管理升级条件
       - 影响SLA的重大故障
       - 需要调整策略参数
  
  7. 自治等级配置
     - L1-L5各级别行为定义
  
  8. 数据模型
     - SchedulingContext
     - AssignmentDecision
     - RobotSelection
  
  9. 示例代码
     - 完整调度循环
     - 任务分配逻辑
  
  10. 测试场景
      - 正常调度流程
      - 机器人故障场景
      - 高负载场景
```

### Day 23 (02-11)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W5D23-01 | **A2规格书(下)** | 📝规格书 | 3h | 完成A2规格书 |
| W5D23-02 | **A3对话助手Agent规格书** | 📝规格书 | 3h | docs/specs/A3-conversation-agent.md |

**A3规格书内容大纲**:
```yaml
级别: L2标准
预估行数: 500-600

章节:
  1. 模块概述
     - 提供自然语言交互能力
  
  2. 对话能力
     - 意图识别类型
     - 实体提取规则
  
  3. 支持的命令
     - 查询类：状态查询、历史查询
     - 控制类：启动、暂停、取消
     - 配置类：调整参数
  
  4. 意图到MCP调用映射
     - "机器人状态" → M3.robot_get_status
     - "今日任务" → M2.task_list_tasks
     - ...
  
  5. 上下文管理
     - 会话状态
     - 多轮对话
  
  6. 示例对话
```

### Day 24-28 (02-12 ~ 02-16)

| Day | 任务 | 类型 | 产出 |
|-----|------|------|------|
| D24 | D1采集器实现 | 开发 | robot_collector.py, task_collector.py |
| D25 | D1测试+D2存储框架 | 开发 | D1测试, storage/base.py |
| D26 | D2存储实现 | 开发 | timeseries.py, events.py |
| D27 | D1+D2集成测试 | 测试 | test_data_platform.py |
| D28 | Week 5 Review | Review | 审查报告 |

---

## Week 6: A1/A4开发 + D3规格书

### Day 29 (02-17)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W6D29-01 | **D3数据查询API规格书** | 📝规格书 | 3h | docs/specs/D3-data-query-api.md |
| W6D29-02 | A1运行时-基础框架 | 开发 | 3h | runtime/base.py |

**D3规格书内容大纲**:
```yaml
级别: L2标准
预估行数: 400-500

章节:
  1. API概述
  
  2. 查询接口
     - 时序数据查询
       - GET /data/timeseries/{metric}
     - 聚合数据查询
       - GET /data/aggregate/{metric}
     - 事件查询
       - GET /data/events
  
  3. 请求参数
     - 时间范围
     - 聚合粒度
     - 过滤条件
  
  4. 响应格式
  
  5. 分页
  
  6. 性能考虑
```

### Day 30-35 (02-18 ~ 02-23)

| Day | 任务 | 类型 | 产出 |
|-----|------|------|------|
| D30 | A1 MCP客户端 | 开发 | mcp_client.py |
| D31 | A1 决策引擎 | 开发 | decision_engine.py |
| D32 | A1 升级管理 | 开发 | escalation.py |
| D33 | A4 数据采集Agent | 开发 | data_collector_agent.py |
| D34 | A1+A4测试 | 测试 | test_agent_runtime.py |
| D35 | Week 6 Review | Review | 审查报告 |

---

## Week 7: A2开发 + G1-G4规格书

### Day 36 (02-24)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W7D36-01 | **G1-G4核心API规格书** | 📝规格书 | 5h | docs/specs/G-core-api.md |

**G1-G4规格书内容大纲**:
```yaml
级别: L2标准
预估行数: 600-800

章节:
  1. API设计原则
     - RESTful规范
     - 认证方式
     - 错误码体系
  
  2. G1空间API
     - GET /spaces/buildings
     - GET /spaces/buildings/{id}
     - GET /spaces/floors
     - GET /spaces/zones
     ...
  
  3. G2任务API
     - GET /tasks/schedules
     - POST /tasks/schedules
     - GET /tasks/tasks
     - PATCH /tasks/tasks/{id}/status
     ...
  
  4. G3机器人API
     - GET /robots
     - GET /robots/{id}
     - GET /robots/{id}/status
     - POST /robots/{id}/commands
     ...
  
  5. G4监控API
     - GET /monitoring/agent-logs
     - GET /monitoring/events
     - WebSocket /monitoring/realtime
     ...
  
  6. 通用响应格式
  7. 错误处理
  8. 示例
```

### Day 37-42 (02-25 ~ 03-02)

| Day | 任务 | 类型 | 产出 |
|-----|------|------|------|
| D37 | A2调度策略实现 | 开发 | scheduler/strategy.py |
| D38 | A2任务分配逻辑 | 开发 | scheduler/assigner.py |
| D39 | A2机器人选择逻辑 | 开发 | scheduler/selector.py |
| D40 | A2完整Agent | 开发 | cleaning_scheduler_agent.py |
| D41 | A2测试 | 测试 | test_cleaning_scheduler.py |
| D42 | Week 7 Review | Review | 审查报告 |

---

## Week 8: A3/D3开发 + G5-G7规格书 + MS2

### Day 43 (03-03)

| 任务ID | 任务名称 | 类型 | 时长 | 产出 |
|--------|---------|------|------|------|
| W8D43-01 | **G5-G7辅助API规格书** | 📝规格书 | 4h | docs/specs/G-auxiliary-api.md |
| W8D43-02 | A3对话Agent开始 | 开发 | 2h | conversation/base.py |

**G5-G7规格书内容大纲**:
```yaml
级别: L2标准
预估行数: 400-500

章节:
  1. G5 Agent交互API
     - POST /agent/chat
     - GET /agent/decisions
     - POST /agent/feedback
     - PATCH /agent/config
  
  2. G6 报表API
     - GET /reports/daily
     - GET /reports/weekly
     - GET /reports/kpi
  
  3. G7 用户API
     - POST /auth/login
     - POST /auth/refresh
     - GET /users/me
     - PUT /users/me
```

### Day 44-49 (03-04 ~ 03-09)

| Day | 任务 | 类型 | 产出 |
|-----|------|------|------|
| D44 | A3完成 | 开发 | conversation_agent.py |
| D45 | D3查询API | 开发 | query_api.py |
| D46 | Agent层集成测试 | 测试 | test_agents_integration.py |
| D47 | **MS2端到端测试** | 测试 | test_ms2_e2e.py |
| D48 | Bug修复 | 开发 | 修复代码 |
| D49 | **MS2验收** + Week 8 Review | 验收 | MS2验收报告 |

**MS2验收检查清单**:
```yaml
功能验收:
  - [ ] D1数据采集引擎可用
  - [ ] D2数据存储服务可用
  - [ ] D3数据查询API可用
  - [ ] A1 Agent运行时框架可用
  - [ ] A2清洁调度Agent可自主执行任务
  - [ ] A3对话Agent可响应
  - [ ] A4数据采集Agent可运行
  - [ ] 端到端任务调度流程通过

规格书验收:
  - [ ] A2规格书完成
  - [ ] A3规格书完成
  - [ ] D3规格书完成
  - [ ] G1-G4规格书完成
  - [ ] G5-G7规格书完成

质量验收:
  - [ ] 测试覆盖率 > 70%
  - [ ] 无P0级Bug
```

---

# 五、Phase 3-6 概要计划

## Phase 3: Week 9-12 (API+训练台)

| Week | 规格书编制 | 开发工作 | 里程碑 |
|------|-----------|---------|--------|
| W9 | T1-T4训练工作台规格书 | G1-G4 API | |
| W10 | - | G5-G7 API | |
| W11 | O1-O4运营控制台规格书 | T1-T2组件 | |
| W12 | - | T3-T4组件 | **MS3** |

## Phase 4: Week 13-16 (运营台+战略舱)

| Week | 规格书编制 | 开发工作 | 里程碑 |
|------|-----------|---------|--------|
| W13 | E1-E3战略驾驶舱规格书 | O1-O2 | |
| W14 | - | O3-O4 | |
| W15 | P1/P3移动端规格书 | E1-E3 | |
| W16 | - | P3通知服务 | **MS4** |

## Phase 5: Week 17-20 (移动端+部署)

| Week | 规格书编制 | 开发工作 | 里程碑 |
|------|-----------|---------|--------|
| W17 | M4科沃斯MCP规格书 | P1移动端 | |
| W18 | I-ALL部署监控规格书 | M4科沃斯MCP | |
| W19 | - | I1-I2部署 | |
| W20 | - | I3监控 | **MS5** |

## Phase 6: Week 21-24 (测试+上线)

| Week | 工作内容 | 里程碑 |
|------|---------|--------|
| W21 | 集成测试 | |
| W22 | Bug修复+优化 | |
| W23 | Pilot部署 | |
| W24 | 反馈迭代 | **MS6** |

---

# 六、规格书工作量统计

## 6.1 按周分布

| 周 | 规格书任务 | 预估时间 | 开发时间 |
|----|-----------|---------|---------|
| W3 | D1(5h)+D2(4h) | 9h | ~21h |
| W4 | A1(7h)+A4(3h) | 10h | ~20h |
| W5 | A2(7h)+A3(3h) | 10h | ~20h |
| W6 | D3(3h) | 3h | ~27h |
| W7 | G1-G4(5h) | 5h | ~25h |
| W8 | G5-G7(4h) | 4h | ~26h |
| W9 | T1-T4(5h) | 5h | ~25h |
| W11 | O1-O4(4h) | 4h | ~26h |
| W13 | E1-E3(3h) | 3h | ~27h |
| W15 | P1(2h)+P3(3h) | 5h | ~25h |
| W17 | M4(5h) | 5h | ~25h |
| W18 | I-ALL(3h) | 3h | ~27h |

## 6.2 总计

| 类别 | 数量 | 总时间 |
|------|------|--------|
| L1详细规格书 | 3个 | ~19h |
| L2标准规格书 | 8个 | ~32h |
| L3简化规格书 | 4个 | ~15h |
| **总计** | **15个** | **~66h** |

---

# 七、Claude Code提示词库

## 7.1 规格书编制提示词

### L1详细规格书
```
请编制 [模块ID] [模块名称] 规格书。

级别: L1详细
参考:
- 接口定义: interfaces/[相关文件]
- 类似规格书: docs/specs/M3-gaoxian-mcp.md (参考结构)
- 项目文档: [相关文档]

预估行数: 800-1200行

请按照以下结构编写:
1. 模块概述（目的、职责、系统位置）
2. 架构设计（组件、数据流）
3. 接口定义（所有接口详细定义）
4. 数据模型（完整Pydantic定义）
5. 业务规则（所有规则详细说明）
6. 错误处理（错误码、重试策略）
7. 示例代码（关键实现）
8. 测试要点（测试场景列表）

要求:
- 接口与interfaces/定义保持一致
- 示例代码可运行
- 业务规则清晰可执行
```

### L2标准规格书
```
请编制 [模块ID] [模块名称] 规格书。

级别: L2标准
参考: interfaces/[相关文件]
预估行数: 400-800行

请按照以下结构编写:
1. 模块概述
2. 接口定义
3. 数据模型
4. 关键业务规则
5. 示例代码片段
6. 测试要点
```

### L3简化规格书
```
请编制 [模块名称] 规格书。

级别: L3简化
预估行数: 200-400行

请按照以下结构编写:
1. 概述（一段话）
2. 组件列表
3. 接口说明
4. 实现要点
5. 测试清单
```

## 7.2 每日开始工作

```
请帮我开始今天的开发工作。

当前: Week [X] Day [Y]

请执行:
1. 读取 PROGRESS.md 确认进度
2. 读取本周计划，列出今日任务
3. 检查是否有规格书需要编制
4. 检查前置依赖
5. 建议执行顺序
```

## 7.3 规格书Review

```
请帮我Review [规格书名称]。

检查项:
1. 完整性：所有接口是否都有定义
2. 一致性：是否与interfaces/一致
3. 可实现性：示例代码是否可运行
4. 测试可行性：测试用例是否可执行

输出: Review报告 + 修改建议
```

---

# 八、进度追踪

## PROGRESS.md 更新模板

```markdown
# LinkC MVP 开发进度追踪

**最后更新**: YYYY-MM-DD HH:MM

## 当前状态
- **当前周**: Week X
- **当前日**: Day Y
- **整体进度**: X% (X/24 weeks)

## 规格书状态

### 已完成
| 规格书 | 行数 | 完成日期 |
|-------|------|---------|
| M1 | ~400 | W1 |
| M2 | 1,299 | W1 |
| M3 | 1,535 | W1 |

### 进行中
| 规格书 | 进度 | 预计完成 |
|-------|------|---------|

### 待开始
| 规格书 | 计划周 |
|-------|-------|
| D1 | W3 |
| D2 | W3 |
| ... | ... |

## 开发状态
[与之前格式相同]

## 今日任务
[与之前格式相同]
```

---

**文档版本**: 3.0  
**创建日期**: 2026-01-20  
**特点**: 包含完整的规格书编制计划
