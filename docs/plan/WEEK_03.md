# Week 3 详细任务计划

**周期**: 2026-01-29 ~ 2026-02-04  
**主题**: M3高仙机器人MCP完成 + 三模块联调  
**目标**: 完成M3，三个MCP Server联调成功，达成MS1里程碑

---

## 周目标

| 目标 | 验收标准 | 优先级 |
|------|---------|-------|
| M3高仙MCP完成 | 12个Tools全部可用 | P0 |
| Mock模拟器稳定 | 可运行24小时 | P0 |
| 三模块联调通过 | 完整任务流程可走通 | P0 |
| MS1里程碑达成 | 里程碑验收通过 | P0 |

---

## Day 15 (01-29, 周三) - M3 Tools实现(上)

### 任务列表

```yaml
- id: W3D1-01
  name: 实现M3 tools.py (状态查询4个Tool)
  duration: 3h
  depends_on: W2D6-02 (mock_client)
  output: src/mcp_servers/robot_gaoxian/tools.py (部分)
  test: pytest tests/mcp_servers/robot_gaoxian/test_tools.py -k "status or list"
  spec_ref: docs/specs/M3-gaoxian-mcp.md
  claude_prompt: |
    实现M3高仙机器人MCP的状态查询Tools:
    1. robot_list_robots - 获取机器人列表
    2. robot_get_robot - 获取单个机器人详情
    3. robot_get_status - 获取实时状态
    4. robot_batch_get_status - 批量获取状态
    
    参考规格书: docs/specs/M3-gaoxian-mcp.md
    使用mock_client作为后端

- id: W3D1-02
  name: 实现M3 tools.py (任务控制4个Tool)
  duration: 3h
  output: src/mcp_servers/robot_gaoxian/tools.py (部分)
  test: pytest tests/mcp_servers/robot_gaoxian/test_tools.py -k "task"
  claude_prompt: |
    实现M3高仙机器人MCP的任务控制Tools:
    5. robot_start_task - 启动清洁任务
    6. robot_pause_task - 暂停任务
    7. robot_resume_task - 恢复任务
    8. robot_cancel_task - 取消任务
    
    业务规则:
    - 启动前检查: 状态(idle/charging)、电量(>=20%)、无故障
    - 状态流转验证
```

### 验收检查
```bash
pytest tests/mcp_servers/robot_gaoxian/test_tools.py -v
# 预期: 状态查询和任务控制测试通过
```

---

## Day 16 (01-30, 周四) - M3完成

### 任务列表

```yaml
- id: W3D2-01
  name: 实现M3 tools.py (导航+故障4个Tool)
  duration: 3h
  output: src/mcp_servers/robot_gaoxian/tools.py (完整)
  test: pytest tests/mcp_servers/robot_gaoxian/test_tools.py
  claude_prompt: |
    实现M3高仙机器人MCP的剩余Tools:
    9. robot_go_to_location - 导航到指定位置
    10. robot_go_to_charge - 返回充电桩
    11. robot_get_errors - 获取故障列表
    12. robot_clear_error - 清除故障
    
    业务规则:
    - go_to_charge的force参数处理
    - 只能清除warning级别故障

- id: W3D2-02
  name: 实现M3 server.py
  duration: 1h
  output: src/mcp_servers/robot_gaoxian/server.py
  test: python -m src.mcp_servers.robot_gaoxian.server --help

- id: W3D2-03
  name: M3单元测试完善
  duration: 2h
  output: 完整测试用例
  test: pytest tests/mcp_servers/robot_gaoxian/ -v --cov
  claude_prompt: |
    完善M3的测试用例:
    1. 所有12个Tools的正常路径
    2. 电量检查边界测试
    3. 状态流转测试
    4. 故障处理测试
    5. Mock模拟器行为测试
```

### 验收检查
```bash
pytest tests/mcp_servers/robot_gaoxian/ -v --cov=src/mcp_servers/robot_gaoxian
# 预期: 覆盖率>85%
```

---

## Day 17 (01-31, 周五) - 三模块联调

### 任务列表

```yaml
- id: W3D3-01
  name: 创建三模块集成测试框架
  duration: 2h
  output: tests/integration/test_mcp_servers.py
  claude_prompt: |
    创建M1+M2+M3的集成测试框架。
    
    设计测试场景:
    1. 完整任务生命周期
    2. 机器人状态同步
    3. 异常处理流程

- id: W3D3-02
  name: 实现端到端场景测试
  duration: 4h
  output: 端到端测试用例
  test: pytest tests/integration/test_mcp_servers.py -v
  claude_prompt: |
    实现完整的端到端场景测试:
    
    场景1: 正常任务流程
    1. M1: 创建楼宇、楼层、区域
    2. M2: 为区域创建排程
    3. M2: 生成今日任务
    4. M2: 获取待执行任务
    5. M3: 获取可用机器人
    6. M2: 分配任务给机器人
    7. M3: 启动机器人任务
    8. M3: (等待模拟完成)
    9. M2: 更新任务状态为完成
    
    场景2: 异常处理
    1. 机器人电量不足时拒绝任务
    2. 机器人故障时任务失败
    3. 任务取消流程
```

### 验收检查
```bash
pytest tests/integration/ -v
# 预期: 所有集成测试通过
```

---

## Day 18 (02-01, 周六) - 稳定化

### 任务列表

```yaml
- id: W3D4-01
  name: 修复集成测试发现的问题
  duration: 3h
  output: Bug修复
  claude_prompt: |
    分析并修复昨天集成测试中发现的问题。
    优先处理阻塞性问题。

- id: W3D4-02
  name: Mock模拟器稳定性测试
  duration: 2h
  output: 稳定性测试报告
  claude_prompt: |
    测试Mock模拟器的稳定性:
    1. 运行持续10分钟的模拟
    2. 验证状态一致性
    3. 检查内存使用
    4. 验证随机故障触发

- id: W3D4-03
  name: 性能基准测试
  duration: 1h
  output: 性能基准数据
  claude_prompt: |
    为MCP Server建立性能基准:
    1. 单Tool响应时间
    2. 批量查询性能
    3. 并发调用测试
```

---

## Day 19 (02-02, 周日) - MS1验收准备

### 任务列表

```yaml
- id: W3D5-01
  name: MS1验收检查清单执行
  duration: 3h
  output: 验收检查报告
  checklist:
    功能:
      - M1: 8个Tools全部可用
      - M2: 10个Tools全部可用
      - M3: 12个Tools全部可用
      - Mock模拟器稳定
    测试:
      - 单元测试覆盖率>85%
      - 集成测试全部通过
      - 完整任务流程可走通
    文档:
      - README文件完整
      - LESSONS_LEARNED更新
    代码:
      - 无import错误
      - 类型注解完整

- id: W3D5-02
  name: 补充缺失项
  duration: 3h
  output: 补充完成
  claude_prompt: |
    根据验收检查结果，补充缺失项:
    1. 补充缺失的测试用例
    2. 补充缺失的文档
    3. 修复发现的问题
```

---

## Day 20 (02-03, 周一) - 文档和Review

### 任务列表

```yaml
- id: W3D6-01
  name: 编写MCP Server文档
  duration: 2h
  output: 
    - src/mcp_servers/space_manager/README.md
    - src/mcp_servers/task_manager/README.md
    - src/mcp_servers/robot_gaoxian/README.md
  claude_prompt: |
    为每个MCP Server编写README文档:
    1. 模块说明
    2. Tools列表和说明
    3. 使用示例
    4. 测试运行方法

- id: W3D6-02
  name: 代码Review和重构
  duration: 3h
  output: 重构后的代码
  claude_prompt: |
    对三个MCP Server进行代码Review:
    1. 检查是否有重复代码可提取
    2. 检查错误处理是否一致
    3. 检查日志记录是否完整
    4. 进行必要的小规模重构

- id: W3D6-03
  name: 更新LESSONS_LEARNED
  duration: 1h
  output: 问题知识库更新
```

---

## Day 21 (02-04, 周二) - Week 3总结 + MS1里程碑

### 任务列表

```yaml
- id: W3D7-01
  name: MS1里程碑正式验收
  duration: 2h
  output: 里程碑验收报告
  claude_prompt: |
    执行MS1里程碑正式验收:
    
    运行完整测试套件:
    pytest tests/ -v --cov=src --cov-report=html
    
    验收标准:
    1. 所有测试通过
    2. 覆盖率>85%
    3. 三模块联调成功
    4. 文档完整

- id: W3D7-02
  name: 创建Week 3总结
  duration: 1h
  output: docs/WEEKLY_SUMMARY/week-03.md

- id: W3D7-03
  name: 准备Week 4计划
  duration: 1h
  output: Week 4任务确认
  notes: |
    Week 4开始数据平台开发:
    - D1数据采集引擎
    - D2数据存储服务

- id: W3D7-04
  name: 更新PROGRESS.md
  duration: 0.5h
```

### MS1里程碑验收检查

```bash
# 完整测试
pytest tests/ -v --cov=src --cov-report=html

# 检查清单
echo "=== MS1 验收检查 ==="
echo "1. M1 Tools: 8/8"
echo "2. M2 Tools: 10/10"
echo "3. M3 Tools: 12/12"
echo "4. 单元测试覆盖率: XX%"
echo "5. 集成测试: PASS/FAIL"
echo "6. 端到端测试: PASS/FAIL"
```

---

## Week 3 完成标准

| 检查项 | 标准 | 状态 |
|-------|------|------|
| M3 Tools | 12/12 实现 | ⬜ |
| M3 测试覆盖 | >85% | ⬜ |
| Mock模拟器 | 稳定运行 | ⬜ |
| 三模块联调 | 通过 | ⬜ |
| 端到端测试 | 通过 | ⬜ |
| **MS1里程碑** | **达成** | ⬜ |
| 周报 | 完成 | ⬜ |

---

## 风险和应对

| 风险 | 应对措施 |
|-----|---------|
| Mock模拟器不稳定 | 简化模拟逻辑，优先保证核心功能 |
| 三模块集成困难 | 预留Day 18作为Buffer |
| 测试覆盖不足 | Day 19专门补充测试 |
