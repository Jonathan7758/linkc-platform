# Week 4 详细任务计划

**周期**: 2026-02-05 ~ 2026-02-11  
**主题**: 数据平台 + Agent框架启动  
**目标**: 完成D1/D2数据平台，启动A1 Agent运行时

---

## 周目标

| 目标 | 验收标准 | 优先级 |
|------|---------|-------|
| D1数据采集引擎 | 可从MCP Server采集数据 | P0 |
| D2数据存储服务 | 可持久化和查询数据 | P0 |
| A1 Agent运行时框架 | Agent可调用MCP Tools | P1 |
| MCP层稳定 | 无回归Bug | P0 |

---

## Day 22 (02-05, 周三) - D1数据采集启动

### 任务列表

```yaml
- id: W4D1-01
  name: 创建数据平台目录结构
  duration: 0.5h
  output:
    - src/data_platform/collector/__init__.py
    - src/data_platform/storage/__init__.py
    - src/data_platform/query/__init__.py

- id: W4D1-02
  name: 设计D1数据采集架构
  duration: 1.5h
  output: docs/design/D1-collector-design.md
  claude_prompt: |
    设计D1数据采集引擎的架构:
    
    采集目标:
    1. 机器人状态（周期性，每30秒）
    2. 任务状态变更（事件驱动）
    3. 区域清洁记录（任务完成时）
    
    设计要点:
    1. 定时采集 vs 事件驱动
    2. 数据格式标准化
    3. 错误重试机制
    4. 背压处理

- id: W4D1-03
  name: 实现D1基础框架
  duration: 4h
  output: src/data_platform/collector/
  test: pytest tests/data_platform/collector/test_base.py
  claude_prompt: |
    实现D1数据采集引擎基础框架:
    
    核心类:
    1. Collector - 采集器基类
    2. ScheduledCollector - 定时采集器
    3. EventCollector - 事件采集器
    4. CollectorManager - 采集器管理
    
    参考interfaces/events.py中的事件定义
```

### 验收检查
```bash
pytest tests/data_platform/collector/ -v
```

---

## Day 23 (02-06, 周四) - D1机器人状态采集

### 任务列表

```yaml
- id: W4D2-01
  name: 实现机器人状态采集器
  duration: 3h
  output: src/data_platform/collector/robot_collector.py
  test: pytest tests/data_platform/collector/test_robot_collector.py
  claude_prompt: |
    实现机器人状态采集器:
    
    功能:
    1. 周期性调用M3的robot_batch_get_status
    2. 转换为标准化的StatusRecord
    3. 发送到存储层
    
    配置:
    - 采集间隔: 30秒（可配置）
    - 批量大小: 20个机器人/次
    - 重试次数: 3次

- id: W4D2-02
  name: 实现任务状态采集器
  duration: 3h
  output: src/data_platform/collector/task_collector.py
  test: pytest tests/data_platform/collector/test_task_collector.py
  claude_prompt: |
    实现任务状态采集器:
    
    功能:
    1. 监听M2的任务状态变更事件
    2. 记录状态变更历史
    3. 计算任务统计指标
```

---

## Day 24 (02-07, 周五) - D2数据存储

### 任务列表

```yaml
- id: W4D3-01
  name: 实现D2存储服务
  duration: 4h
  output: src/data_platform/storage/
  test: pytest tests/data_platform/storage/
  claude_prompt: |
    实现D2数据存储服务:
    
    MVP阶段使用内存+文件存储:
    1. TimeSeriesStorage - 时序数据存储（机器人状态）
    2. EventStorage - 事件存储（任务状态变更）
    3. AggregateStorage - 聚合数据存储（日统计）
    
    预留PostgreSQL接口

- id: W4D3-02
  name: 实现数据聚合逻辑
  duration: 2h
  output: src/data_platform/storage/aggregator.py
  claude_prompt: |
    实现数据聚合逻辑:
    
    聚合指标:
    1. 每日任务完成数
    2. 每日清洁面积
    3. 机器人利用率
    4. 平均任务时长
```

---

## Day 25 (02-08, 周六) - D1+D2集成

### 任务列表

```yaml
- id: W4D4-01
  name: D1+D2集成测试
  duration: 3h
  output: tests/integration/test_data_platform.py
  test: pytest tests/integration/test_data_platform.py -v
  claude_prompt: |
    编写D1+D2集成测试:
    
    测试场景:
    1. 采集器启动→采集数据→存储→查询
    2. 模拟1小时的数据采集
    3. 验证聚合数据正确性

- id: W4D4-02
  name: 与MCP层集成测试
  duration: 3h
  output: tests/integration/test_mcp_data.py
  claude_prompt: |
    测试数据平台与MCP Server的集成:
    
    1. 启动M1/M2/M3
    2. 启动D1采集器
    3. 模拟任务执行
    4. 验证数据被正确采集和存储
```

---

## Day 26 (02-09, 周日) - A1 Agent运行时启动

### 任务列表

```yaml
- id: W4D5-01
  name: 设计A1 Agent运行时架构
  duration: 2h
  output: docs/design/A1-agent-runtime-design.md
  claude_prompt: |
    设计A1 Agent运行时框架架构:
    
    核心组件:
    1. AgentBase - Agent基类
    2. MCPClient - MCP调用客户端
    3. DecisionEngine - 决策引擎
    4. EscalationManager - 升级管理
    5. ObservabilityLayer - 可观测性
    
    参考interfaces/agent_protocols.py中的协议定义

- id: W4D5-02
  name: 实现Agent基类
  duration: 4h
  output: src/agents/runtime/base_agent.py
  test: pytest tests/agents/runtime/test_base.py
  claude_prompt: |
    实现Agent基类:
    
    功能:
    1. 生命周期管理（start/stop/pause）
    2. MCP Tool调用封装
    3. 决策记录
    4. 自治等级控制
    
    参考agent_protocols.py中的AgentInterface
```

---

## Day 27 (02-10, 周一) - A1 MCP客户端

### 任务列表

```yaml
- id: W4D6-01
  name: 实现MCP客户端
  duration: 4h
  output: src/agents/runtime/mcp_client.py
  test: pytest tests/agents/runtime/test_mcp_client.py
  claude_prompt: |
    实现Agent用的MCP客户端:
    
    功能:
    1. 连接多个MCP Server
    2. Tool调用封装
    3. 结果解析
    4. 错误处理和重试
    
    支持的Server:
    - M1空间管理
    - M2任务管理
    - M3机器人控制

- id: W4D6-02
  name: 实现升级管理器
  duration: 2h
  output: src/agents/runtime/escalation.py
  test: pytest tests/agents/runtime/test_escalation.py
  claude_prompt: |
    实现升级管理器:
    
    升级规则（参考agent_protocols.py）:
    1. 机器人故障 → L3运营
    2. 策略变更请求 → L4管理
    3. 预算超支 → L5战略
    
    通知方式（MVP简化）:
    - 记录日志
    - 发送事件
```

---

## Day 28 (02-11, 周二) - Week 4总结

### 任务列表

```yaml
- id: W4D7-01
  name: 全量回归测试
  duration: 2h
  output: 回归测试报告
  test: pytest tests/ -v --cov=src
  claude_prompt: |
    运行全量回归测试，确保:
    1. MCP Server层无回归
    2. 数据平台功能正常
    3. Agent运行时基础可用

- id: W4D7-02
  name: 创建Week 4总结
  duration: 1h
  output: docs/WEEKLY_SUMMARY/week-04.md

- id: W4D7-03
  name: 准备Week 5计划
  duration: 1h
  output: Week 5任务确认
  notes: |
    Week 5继续Agent开发:
    - A1运行时完善
    - A4数据采集Agent
    - A2清洁调度Agent启动

- id: W4D7-04
  name: 更新PROGRESS.md
  duration: 0.5h
```

---

## Week 4 完成标准

| 检查项 | 标准 | 状态 |
|-------|------|------|
| D1 采集器 | 可采集机器人和任务状态 | ⬜ |
| D2 存储 | 可持久化和查询 | ⬜ |
| D1+D2 集成 | 测试通过 | ⬜ |
| A1 基类 | 实现完成 | ⬜ |
| A1 MCP客户端 | 可调用Tool | ⬜ |
| 回归测试 | 无回归 | ⬜ |
| 周报 | 完成 | ⬜ |

---

## 架构检查点

Week 4结束时，系统架构应该是:

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent层 (A1框架)                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  AgentBase + MCPClient + EscalationManager          │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────┐
│                    数据平台 (D1+D2)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Collector    │  │ Storage      │  │ Aggregator   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────┐
│                    MCP Server层                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ M1 空间管理  │  │ M2 任务管理  │  │ M3 高仙机器人│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────────────────────────────────────────┘
```

---

## Claude Code 快速参考

### 开始数据平台开发
```
开始D1数据采集引擎开发。

背景:
- MCP Server层(M1/M2/M3)已完成
- 需要定期采集机器人状态和任务状态

请参考:
- interfaces/events.py (事件定义)
- interfaces/data_models.py (数据模型)

先设计架构，然后实现基础框架。
```

### 开始Agent运行时开发
```
开始A1 Agent运行时框架开发。

背景:
- MCP Server层已完成
- 数据平台基础已完成
- Agent需要能调用MCP Tools

请参考:
- interfaces/agent_protocols.py (Agent协议)
- 5级自治定义

先设计架构，然后实现AgentBase和MCPClient。
```
