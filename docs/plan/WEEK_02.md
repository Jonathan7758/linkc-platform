# Week 2 详细任务计划

**周期**: 2026-01-22 ~ 2026-01-28  
**主题**: M1空间MCP + M2任务MCP开发  
**目标**: 完成M1和M2两个MCP Server

---

## 周目标

| 目标 | 验收标准 | 优先级 |
|------|---------|-------|
| M1空间MCP完成 | 8个Tools全部可用，测试通过 | P0 |
| M2任务MCP完成 | 10个Tools全部可用，测试通过 | P0 |
| M1+M2联调通过 | 可创建区域→创建排程→生成任务 | P0 |
| M3开发启动 | Mock模拟器完成 | P1 |

---

## Day 8 (01-22, 周三) - M1开发启动

### 任务列表

```yaml
- id: W2D1-01
  name: 创建M1目录结构
  duration: 0.5h
  output: 
    - src/mcp_servers/space_manager/__init__.py
    - src/mcp_servers/space_manager/server.py (空)
    - src/mcp_servers/space_manager/tools.py (空)
    - src/mcp_servers/space_manager/storage.py (空)
    - tests/mcp_servers/space_manager/__init__.py
  test: 目录和文件存在
  claude_prompt: |
    创建M1空间管理MCP Server的目录结构:
    src/mcp_servers/space_manager/
    ├── __init__.py
    ├── server.py
    ├── tools.py
    └── storage.py
    以及对应的tests目录

- id: W2D1-02
  name: 实现M1 storage.py
  duration: 3h
  depends_on: W2D1-01
  output: src/mcp_servers/space_manager/storage.py
  test: pytest tests/mcp_servers/space_manager/test_storage.py
  spec_ref: docs/specs/M1-space-mcp.md
  claude_prompt: |
    实现M1空间管理MCP Server的存储层。
    
    参考规格书: docs/specs/M1-space-mcp.md 第7.3节
    参考接口: interfaces/data_models.py (Building, Floor, Zone, Point)
    
    要求:
    1. 使用InMemoryStorage类
    2. 实现Building/Floor/Zone/Point的CRUD
    3. 支持层级关系查询
    4. 完整类型注解
    
    同时创建对应的单元测试文件。

- id: W2D1-03
  name: 实现M1 tools.py (前4个Tool)
  duration: 3h
  depends_on: W2D1-02
  output: src/mcp_servers/space_manager/tools.py (部分)
  test: pytest tests/mcp_servers/space_manager/test_tools.py -k "building or floor"
  spec_ref: docs/specs/M1-space-mcp.md
  claude_prompt: |
    实现M1空间管理MCP Server的前4个Tools:
    1. space_list_buildings
    2. space_get_building
    3. space_list_floors
    4. space_get_floor
    
    参考规格书: docs/specs/M1-space-mcp.md 第2.1节
    参考接口: interfaces/mcp_tools.py
    
    要求:
    1. 使用刚创建的storage层
    2. 返回格式统一使用ToolResult
    3. 错误处理完善
    4. 同时写单元测试
```

### 验收检查

```bash
# Day 8 结束时运行
pytest tests/mcp_servers/space_manager/ -v
# 预期: 至少10个测试用例通过
```

### Daily Review要点
- [ ] storage层CRUD是否正常
- [ ] 前4个Tool是否符合接口定义
- [ ] 测试覆盖率检查

---

## Day 9 (01-23, 周四) - M1完成

### 任务列表

```yaml
- id: W2D2-01
  name: 实现M1 tools.py (后4个Tool)
  duration: 3h
  depends_on: W2D1-03
  output: src/mcp_servers/space_manager/tools.py (完整)
  test: pytest tests/mcp_servers/space_manager/test_tools.py
  claude_prompt: |
    实现M1空间管理MCP Server的后4个Tools:
    5. space_list_zones
    6. space_get_zone
    7. space_update_zone
    8. space_query_points
    
    延续昨天的代码风格，补充完整tools.py

- id: W2D2-02
  name: 实现M1 server.py
  duration: 2h
  depends_on: W2D2-01
  output: src/mcp_servers/space_manager/server.py
  test: python -m src.mcp_servers.space_manager.server --help
  claude_prompt: |
    实现M1空间管理MCP Server的主入口。
    
    参考规格书: docs/specs/M1-space-mcp.md 第7.1节
    
    要求:
    1. 使用mcp.server.Server
    2. 实现@app.list_tools()和@app.call_tool()
    3. 返回list[TextContent]格式
    4. 可独立启动

- id: W2D2-03
  name: M1集成测试
  duration: 2h
  depends_on: W2D2-02
  output: tests/mcp_servers/space_manager/test_integration.py
  test: pytest tests/mcp_servers/space_manager/test_integration.py -v
  claude_prompt: |
    为M1空间管理MCP Server编写集成测试。
    
    测试场景:
    1. 创建楼宇→添加楼层→添加区域→添加点位
    2. 查询楼宇包含的所有区域
    3. 更新区域信息
    4. 按条件筛选区域
```

### 验收检查

```bash
# Day 9 结束时运行
pytest tests/mcp_servers/space_manager/ -v --cov=src/mcp_servers/space_manager
# 预期: 覆盖率>85%, 所有测试通过
```

### Daily Review要点
- [ ] 8个Tools全部实现
- [ ] MCP Server可启动
- [ ] 所有测试通过
- [ ] 覆盖率达标

---

## Day 10 (01-24, 周五) - M2开发启动

### 任务列表

```yaml
- id: W2D3-01
  name: 创建M2目录结构
  duration: 0.5h
  output: src/mcp_servers/task_manager/
  claude_prompt: |
    创建M2任务管理MCP Server的目录结构，参考M1

- id: W2D3-02
  name: 实现M2 storage.py
  duration: 3h
  output: src/mcp_servers/task_manager/storage.py
  test: pytest tests/mcp_servers/task_manager/test_storage.py
  spec_ref: docs/specs/M2-task-mcp.md
  claude_prompt: |
    实现M2任务管理MCP Server的存储层。
    
    参考规格书: docs/specs/M2-task-mcp.md 第7.3节
    参考接口: interfaces/data_models.py (CleaningSchedule, CleaningTask)
    
    要求:
    1. 排程(Schedule)CRUD
    2. 任务(Task)CRUD
    3. 待执行任务查询（按优先级排序）
    4. 幂等性检查（同一排程同一天不重复生成）

- id: W2D3-03
  name: 实现M2 tools.py (排程相关4个Tool)
  duration: 3h
  output: src/mcp_servers/task_manager/tools.py (部分)
  test: pytest tests/mcp_servers/task_manager/test_tools.py -k "schedule"
  claude_prompt: |
    实现M2任务管理的排程相关Tools:
    1. task_list_schedules
    2. task_get_schedule
    3. task_create_schedule
    4. task_update_schedule
    
    参考规格书: docs/specs/M2-task-mcp.md
```

### 验收检查

```bash
pytest tests/mcp_servers/task_manager/ -v
```

---

## Day 11 (01-25, 周六) - M2完成

### 任务列表

```yaml
- id: W2D4-01
  name: 实现M2 tools.py (任务相关6个Tool)
  duration: 4h
  output: src/mcp_servers/task_manager/tools.py (完整)
  claude_prompt: |
    实现M2任务管理的任务相关Tools:
    5. task_list_tasks
    6. task_get_task
    7. task_create_task
    8. task_update_status (含状态机验证)
    9. task_get_pending_tasks
    10. task_generate_daily_tasks
    
    重点: task_update_status必须实现状态机验证
    状态流转: pending → assigned → in_progress → completed/failed

- id: W2D4-02
  name: 状态机测试
  duration: 2h
  output: 状态机测试用例
  test: pytest tests/mcp_servers/task_manager/test_tools.py -k "status"
  claude_prompt: |
    为任务状态机编写完整测试:
    1. 合法流转测试 (pending→assigned→in_progress→completed)
    2. 非法流转测试 (pending→completed应失败)
    3. 边界条件 (completed必须有completion_rate)
    4. 错误处理 (failed必须有failure_reason)

- id: W2D4-03
  name: 实现M2 server.py
  duration: 1h
  output: src/mcp_servers/task_manager/server.py
  test: python -m src.mcp_servers.task_manager.server --help
```

### 验收检查

```bash
pytest tests/mcp_servers/task_manager/ -v --cov=src/mcp_servers/task_manager
# 预期: 覆盖率>85%
```

---

## Day 12 (01-26, 周日) - M1+M2联调

### 任务列表

```yaml
- id: W2D5-01
  name: M1+M2集成测试
  duration: 3h
  output: tests/integration/test_m1_m2.py
  test: pytest tests/integration/test_m1_m2.py -v
  claude_prompt: |
    编写M1+M2的集成测试。
    
    测试场景:
    1. 用M1创建楼宇和区域
    2. 用M2为区域创建排程
    3. 用M2生成每日任务
    4. 验证任务的zone信息正确
    
    这个测试验证两个MCP Server可以协同工作。

- id: W2D5-02
  name: 修复集成问题
  duration: 2h
  output: Bug修复
  claude_prompt: |
    修复集成测试中发现的问题。
    分析错误原因，修复代码，确保测试通过。

- id: W2D5-03
  name: 更新LESSONS_LEARNED.md
  duration: 1h
  output: 问题记录
  claude_prompt: |
    总结本周开发中遇到的问题和解决方案。
    更新docs/LESSONS_LEARNED.md
```

### 验收检查

```bash
# 完整回归测试
pytest tests/mcp_servers/ -v
pytest tests/integration/ -v
```

---

## Day 13 (01-27, 周一) - M3开发启动

### 任务列表

```yaml
- id: W2D6-01
  name: 创建M3目录结构
  duration: 0.5h
  output: src/mcp_servers/robot_gaoxian/

- id: W2D6-02
  name: 实现M3 mock_client.py
  duration: 4h
  output: src/mcp_servers/robot_gaoxian/mock_client.py
  test: pytest tests/mcp_servers/robot_gaoxian/test_mock.py
  spec_ref: docs/specs/M3-gaoxian-mcp.md
  claude_prompt: |
    实现高仙机器人Mock模拟器。
    
    参考规格书: docs/specs/M3-gaoxian-mcp.md 第7.3节
    
    Mock模拟器要求:
    1. 初始化3个模拟机器人
    2. 模拟电量消耗（工作时每秒-0.1%）
    3. 模拟充电（每秒+0.5%）
    4. 模拟任务进度（每秒+1-3%）
    5. 模拟随机故障（1%概率）
    
    这是MVP阶段的关键依赖！

- id: W2D6-03
  name: 实现M3 storage.py
  duration: 2h
  output: src/mcp_servers/robot_gaoxian/storage.py
  test: pytest tests/mcp_servers/robot_gaoxian/test_storage.py
```

### 验收检查

```bash
pytest tests/mcp_servers/robot_gaoxian/ -v
```

---

## Day 14 (01-28, 周二) - Week 2总结

### 任务列表

```yaml
- id: W2D7-01
  name: Week 2代码Review
  duration: 2h
  output: Review记录
  claude_prompt: |
    进行Week 2代码Review。
    
    检查:
    1. M1代码是否符合规格书
    2. M2代码是否符合规格书
    3. 测试覆盖率是否达标
    4. 是否有需要重构的地方
    
    输出Review报告。

- id: W2D7-02
  name: 创建Week 2总结
  duration: 1h
  output: docs/WEEKLY_SUMMARY/week-02.md
  template: |
    # Week 2 总结
    
    ## 完成情况
    - 计划任务: X个
    - 完成任务: X个
    - 完成率: X%
    
    ## 产出
    - M1: [状态]
    - M2: [状态]
    - M3: [状态]
    
    ## 遇到的问题
    ...
    
    ## 下周计划
    ...

- id: W2D7-03
  name: 更新PROGRESS.md
  duration: 0.5h
  output: PROGRESS.md更新

- id: W2D7-04
  name: 准备Week 3任务
  duration: 0.5h
  output: Week 3计划确认
```

### 周末验收检查

```bash
# Week 2 完整测试
pytest tests/ -v --cov=src --cov-report=html

# 检查覆盖率
# 预期: M1 >85%, M2 >85%
```

---

## Week 2 完成标准

| 检查项 | 标准 | 状态 |
|-------|------|------|
| M1 Tools | 8/8 实现 | ⬜ |
| M1 测试覆盖 | >85% | ⬜ |
| M2 Tools | 10/10 实现 | ⬜ |
| M2 测试覆盖 | >85% | ⬜ |
| M1+M2 联调 | 通过 | ⬜ |
| M3 Mock | 完成 | ⬜ |
| 周报 | 完成 | ⬜ |

---

## Claude Code 快速参考

### 开始某天工作
```
今天是Week 2 Day [X]。
请查看docs/plan/WEEK_02.md中Day [X]的任务列表。
我准备开始第一个任务。
```

### 结束某天工作
```
今天的任务完成了。请帮我:
1. 运行今日相关测试
2. 更新PROGRESS.md
3. 创建Daily Review
```

### 遇到问题
```
遇到问题:
[错误信息]

请分析原因并修复。
如果是通用问题，请建议添加到LESSONS_LEARNED.md
```
