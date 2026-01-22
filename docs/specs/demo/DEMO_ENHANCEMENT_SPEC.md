# LinkC Platform 演示增强功能规格书

> **实现状态**: ✅ 已完成 (2026-01-22)
> **测试数量**: 129个测试全部通过

> 本文档定义演示增强功能的详细规格，用于向客户和投资人展示人机协同时代的系统架构和交互模式。

**文档版本**: 1.0
**创建日期**: 2026-01-22
**目标**: 打造令人印象深刻的产品演示体验

---

## 目录

1. [演示目标与受众](#演示目标与受众)
2. [演示场景设计](#演示场景设计)
3. [模块规格](#模块规格)
4. [数据规格](#数据规格)
5. [技术实现](#技术实现)
6. [验收标准](#验收标准)

---

## 演示目标与受众

### 核心演示目标

| 目标 | 说明 | 关键指标 |
|------|------|----------|
| **效率提升** | 展示机器人协同带来的效率提升 | 清洁面积+40% |
| **成本节约** | 展示相比传统人工的成本优势 | 成本-35% |
| **智能决策** | 展示AI Agent的智能调度能力 | 决策响应<3秒 |
| **人机协作** | 展示不同角色的人机交互模式 | 3种角色视角 |

### 目标受众

| 受众 | 关注点 | 演示重点 |
|------|--------|----------|
| **投资人** | ROI、市场规模、技术壁垒 | 战略驾驶舱、数据故事 |
| **物业高管** | 成本、效率、可靠性 | 运营总览、成本分析 |
| **运营经理** | 易用性、实时监控、告警 | 运营控制台、移动端 |
| **技术决策者** | 架构、扩展性、集成能力 | API文档、架构图 |

---

## 演示场景设计

### 场景总览

```
┌─────────────────────────────────────────────────────────────────┐
│                      LinkC 演示剧本                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  场景1: 高管视角 (3分钟)                                         │
│  ├── 战略总览仪表盘                                              │
│  ├── 核心KPI展示 (效率↑40%, 成本↓35%)                           │
│  └── 多楼宇状态一览                                              │
│                                                                 │
│  场景2: 运营视角 (5分钟)                                         │
│  ├── 实时机器人地图 (8台机器人动态移动)                          │
│  ├── 任务调度演示 (一键派发)                                     │
│  ├── 告警处理演示 (从告警到解决)                                 │
│  └── 机器人远程控制                                              │
│                                                                 │
│  场景3: AI协作 (5分钟) ⭐ 核心亮点                                │
│  ├── 自然语言下达任务                                            │
│  ├── Agent智能决策展示                                           │
│  ├── 人机协作审批流程                                            │
│  └── Agent学习与优化                                             │
│                                                                 │
│  场景4: 移动端 (2分钟)                                           │
│  ├── 告警推送接收                                                │
│  ├── 现场快速响应                                                │
│  └── 扫码查看详情                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 场景1: 高管视角 (战略驾驶舱)

**目标**: 30秒内让高管理解业务价值

**展示内容**:

```yaml
页面: /executive
展示元素:
  健康度评分:
    值: 92分
    颜色: 绿色
    趋势: ↑3% vs 上周

  核心KPI:
    - 任务完成率: 96.8%
    - 机器人利用率: 87.2%
    - 成本节约: ¥428,600/月
    - 客户满意度: 4.8/5.0

  今日概览:
    - 完成任务: 127个
    - 清洁面积: 45,800㎡
    - 工作时长: 186小时
    - 节约人工: 23人/天

  楼宇状态:
    - 环球贸易广场: 健康 (3台机器人)
    - 国际金融中心: 健康 (3台机器人)
    - 太古广场: 注意 (2台机器人, 1台维护中)

交互演示:
  - 点击楼宇卡片 → 下钻到楼宇详情
  - 点击KPI → 跳转到详细分析
  - 时间范围切换 → 数据动态刷新
```

### 场景2: 运营视角 (运营控制台)

**目标**: 展示实时监控和操作能力

**展示内容**:

```yaml
页面: /operations, /robots, /tasks, /alerts

2.1 运营总览:
  实时统计:
    - 在线机器人: 7/8
    - 执行中任务: 12个
    - 待处理告警: 2个
    - 今日完成: 89个

  快速操作:
    - 一键派发紧急任务
    - 批量调度机器人
    - 查看告警详情

2.2 机器人地图 (核心演示):
  地图展示:
    - 楼层平面图背景
    - 8个机器人图标 (实时位置)
    - 清洁轨迹显示 (渐变淡出)
    - 充电站位置标记

  动态效果:
    - 机器人平滑移动动画
    - 状态变化颜色提示
    - 点击机器人弹出详情卡片

  演示操作:
    - 选择机器人 → 查看详情
    - 发送"回充电站"指令
    - 观察机器人路径规划动画

2.3 告警处理演示:
  模拟告警:
    - 类型: 机器人电量低 (15%)
    - 位置: 环球贸易广场 28F
    - 时间: 实时触发

  处理流程:
    - 收到告警 → 查看详情
    - 选择处理方案 (召回充电/忽略)
    - 确认执行 → 观察机器人响应
    - 告警状态更新为"已解决"
```

### 场景3: AI协作 (训练工作台) ⭐

**目标**: 展示人机协同的核心价值

**展示内容**:

```yaml
页面: /trainer

3.1 自然语言任务下达:
  演示对话:
    用户: "明天早上8点安排大堂深度清洁"

    Agent思考过程 (可视化展示):
      ├── 解析意图: 创建清洁任务
      ├── 识别区域: 大堂 (zone_lobby_001)
      ├── 确定时间: 2026-01-23 08:00
      ├── 选择类型: 深度清洁
      ├── 评估资源: 需要2台机器人, 预计90分钟
      └── 生成计划: 分配 Robot-01, Robot-02

    Agent回复:
      "好的，我已为您安排明天08:00的大堂深度清洁任务。
       将派出2台机器人（清洁机器人A-01、A-02），
       预计清洁面积800㎡，用时约90分钟。
       是否确认执行？"

  用户确认: [确认] [修改] [取消]

3.2 智能决策展示:
  决策可视化:
    - 候选机器人列表 (带评分)
    - 路径规划预览
    - 时间冲突检测
    - 资源优化建议

  Agent推理过程:
    "选择Robot-01的原因:
     1. 当前电量85%, 足够完成任务
     2. 距离目标区域最近 (预计3分钟到达)
     3. 今日工作时长较低, 负载均衡
     4. 历史完成率98.5%"

3.3 人机协作审批:
  待审批队列:
    - 紧急任务自动派发 (需确认)
    - 异常情况处理建议 (需审批)
    - 调度计划变更 (需审批)

  审批操作:
    - 批准 → Agent执行
    - 拒绝 + 反馈 → Agent学习
    - 修改 → 人工调整后执行

3.4 学习反馈演示:
  场景: Agent选择了Robot-03, 但用户改为Robot-05

  反馈录入:
    用户: "Robot-05更适合这个区域，它有拖地功能"

  Agent学习:
    "已记录: 该区域优先选择带拖地功能的机器人。
     已更新区域偏好设置。
     下次将优先考虑此因素。"
```

### 场景4: 移动端体验

**目标**: 展示现场人员的使用场景

**展示内容**:

```yaml
页面: /mobile, /mobile/tasks, /mobile/alerts

4.1 告警推送:
  模拟推送通知:
    标题: "⚠️ 机器人需要关注"
    内容: "Robot-03 在28F遇到障碍物"
    时间: 刚刚

  点击推送 → 打开告警详情

4.2 快速响应:
  告警详情页:
    - 机器人位置 (小地图)
    - 问题描述
    - 建议操作
    - 快捷按钮: [远程恢复] [派人处理] [忽略]

  操作演示:
    点击"远程恢复" → 机器人尝试绕行 → 成功 → 告警关闭

4.3 扫码功能 (可选):
  扫描机器人二维码 → 显示机器人实时状态
```

---

## 模块规格

### DM1: 演示数据服务

**模块ID**: DM1
**名称**: Demo Data Service
**职责**: 管理演示数据的加载、重置、场景切换

```typescript
// 接口定义
interface DemoDataService {
  // 初始化演示数据
  initDemoData(scenario: DemoScenario): Promise<void>;

  // 重置到初始状态
  resetDemo(): Promise<void>;

  // 切换演示场景
  switchScenario(scenario: DemoScenario): Promise<void>;

  // 触发演示事件
  triggerEvent(event: DemoEvent): Promise<void>;

  // 获取当前演示状态
  getDemoStatus(): DemoStatus;
}

// 演示场景
enum DemoScenario {
  EXECUTIVE_OVERVIEW = 'executive',    // 高管视角
  OPERATIONS_NORMAL = 'ops_normal',    // 正常运营
  OPERATIONS_ALERT = 'ops_alert',      // 告警场景
  AGENT_CONVERSATION = 'agent_chat',   // Agent对话
  FULL_DEMO = 'full'                   // 完整演示
}

// 演示事件
enum DemoEvent {
  ROBOT_LOW_BATTERY = 'low_battery',
  ROBOT_OBSTACLE = 'obstacle',
  TASK_COMPLETED = 'task_done',
  NEW_URGENT_TASK = 'urgent_task'
}
```

**API端点**:

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/demo/init` | 初始化演示数据 |
| POST | `/api/v1/demo/reset` | 重置演示 |
| POST | `/api/v1/demo/scenario` | 切换场景 |
| POST | `/api/v1/demo/trigger` | 触发事件 |
| GET | `/api/v1/demo/status` | 获取状态 |

### DM2: 实时模拟引擎

**模块ID**: DM2
**名称**: Real-time Simulation Engine
**职责**: 模拟机器人实时移动、状态变化

```python
class SimulationEngine:
    """实时模拟引擎"""

    def __init__(self):
        self.robots: Dict[str, RobotSimState] = {}
        self.tick_interval = 1.0  # 秒

    async def start(self):
        """启动模拟循环"""
        while self.running:
            await self.tick()
            await asyncio.sleep(self.tick_interval)

    async def tick(self):
        """每秒更新"""
        for robot_id, state in self.robots.items():
            # 更新位置 (沿路径移动)
            state.position = self.calculate_next_position(state)
            # 更新电量
            state.battery -= 0.02  # 每秒消耗0.02%
            # 更新清洁进度
            if state.status == 'working':
                state.task_progress += 0.5
            # 广播状态
            await self.broadcast_state(robot_id, state)

    async def broadcast_state(self, robot_id: str, state: RobotSimState):
        """通过WebSocket广播状态"""
        await websocket_manager.broadcast({
            'type': 'robot_update',
            'robot_id': robot_id,
            'position': state.position,
            'battery': state.battery,
            'status': state.status
        })
```

### DM3: 演示控制面板

**模块ID**: DM3
**名称**: Demo Control Panel
**职责**: 提供演示控制界面

```typescript
// 演示控制面板组件
interface DemoControlPanelProps {
  visible: boolean;
  onClose: () => void;
}

// 功能
- 场景快速切换按钮
- 事件触发按钮 (低电量、障碍物、紧急任务)
- 模拟速度控制 (1x, 2x, 5x)
- 重置按钮
- 当前状态显示
```

**UI设计**:

```
┌─────────────────────────────────────┐
│  🎬 演示控制面板              [×]   │
├─────────────────────────────────────┤
│                                     │
│  场景切换:                          │
│  [高管视角] [运营视角] [AI协作]     │
│                                     │
│  触发事件:                          │
│  [⚡低电量] [🚧障碍物] [🆘紧急任务]  │
│                                     │
│  模拟速度: [1x] [2x] [5x]           │
│                                     │
│  状态: ● 运行中 (场景: 运营视角)    │
│                                     │
│  [🔄 重置演示]                      │
│                                     │
└─────────────────────────────────────┘
```

### DM4: Agent对话演示增强

**模块ID**: DM4
**名称**: Agent Demo Conversations
**职责**: 预设精彩对话场景，展示AI能力

```yaml
预设对话场景:

场景A - 任务调度:
  用户输入: "安排明天大堂深度清洁"
  Agent响应: 展示完整推理过程和计划

场景B - 状态查询:
  用户输入: "现在有哪些机器人空闲"
  Agent响应: 列表展示 + 推荐最优选择

场景C - 问题处理:
  用户输入: "28楼的机器人怎么停了"
  Agent响应: 诊断问题 + 提供解决方案

场景D - 数据分析:
  用户输入: "这周的清洁效率怎么样"
  Agent响应: 数据摘要 + 趋势分析 + 优化建议

场景E - 复杂指令:
  用户输入: "把所有电量低于30%的机器人召回充电"
  Agent响应: 识别目标 + 批量操作 + 确认执行
```

### DM5: 地图动态可视化

**模块ID**: DM5
**名称**: Dynamic Map Visualization
**职责**: 增强机器人地图展示效果

```typescript
// 地图增强功能
interface MapEnhancements {
  // 机器人平滑移动动画
  robotAnimation: {
    duration: 1000,  // ms
    easing: 'ease-in-out'
  };

  // 清洁轨迹
  cleaningTrail: {
    enabled: true,
    color: '#4CAF50',
    fadeTime: 30000,  // 30秒渐隐
    width: 3
  };

  // 状态颜色
  statusColors: {
    idle: '#9E9E9E',
    working: '#4CAF50',
    charging: '#2196F3',
    error: '#F44336',
    paused: '#FF9800'
  };

  // 交互效果
  interactions: {
    hoverHighlight: true,
    clickPopup: true,
    dragToMove: false  // 演示模式禁用
  };
}
```

---

## 数据规格

### 演示数据集

```yaml
楼宇数据:
  - id: building_001
    name: 环球贸易广场
    address: 香港九龙柯士甸道西1号
    floors: 10
    total_area: 125000
    robots: 3

  - id: building_002
    name: 国际金融中心
    address: 香港中环金融街8号
    floors: 8
    total_area: 98000
    robots: 3

  - id: building_003
    name: 太古广场
    address: 香港金钟道88号
    floors: 6
    total_area: 76000
    robots: 2

机器人数据:
  - robot_id: robot_001
    name: 清洁机器人 A-01
    model: GS-50 Pro
    building: 环球贸易广场
    status: working
    battery: 78%
    current_task: 28F走廊清洁

  - robot_id: robot_002
    name: 清洁机器人 A-02
    model: GS-50 Pro
    building: 环球贸易广场
    status: idle
    battery: 92%

  # ... 共8台机器人

任务数据:
  历史任务: 500+ (过去30天)
  今日任务: 45个
  进行中: 12个
  待执行: 18个
  已完成: 15个

KPI数据:
  任务完成率: 96.8%
  机器人利用率: 87.2%
  平均清洁效率: 125㎡/小时
  月度成本节约: ¥428,600
  客户满意度: 4.8/5.0
```

### 数据故事线

```yaml
演示数据故事:

核心信息:
  "使用LinkC平台后，相同数量的机器人，清洁面积提升40%，
   运营成本降低35%，客户满意度从4.2提升到4.8"

数据支撑:
  传统模式 (对比基准):
    - 8台机器人
    - 日均清洁: 32,000㎡
    - 月度成本: ¥660,000
    - 满意度: 4.2

  LinkC模式 (演示数据):
    - 8台机器人 (相同)
    - 日均清洁: 45,800㎡ (+43%)
    - 月度成本: ¥428,600 (-35%)
    - 满意度: 4.8 (+14%)

  效率提升原因:
    - 智能路径规划: 减少重复清洁
    - 动态调度: 按需分配，减少空闲
    - 预测性维护: 减少故障停机
    - 协同作业: 多机配合，无冲突
```

---

## 技术实现

### 文件结构

```
src/
├── demo/                          # 演示模块 (新增)
│   ├── __init__.py
│   ├── data_service.py           # DM1: 演示数据服务
│   ├── simulation_engine.py      # DM2: 实时模拟引擎
│   ├── seed_data.py              # 演示种子数据
│   └── scenarios/                # 预设场景
│       ├── executive.py
│       ├── operations.py
│       └── agent_chat.py

frontend/src/
├── components/demo/              # 演示组件 (新增)
│   ├── DemoControlPanel.tsx     # DM3: 控制面板
│   ├── DemoModeIndicator.tsx    # 演示模式指示器
│   └── GuidedTour.tsx           # 引导教程

├── pages/
│   └── (existing pages)         # 现有页面增强
│       ├── RobotMonitoring.tsx  # + DM5 地图增强
│       └── TrainerWorkbench.tsx # + DM4 对话增强
```

### 环境变量

```bash
# .env
DEMO_MODE=true                    # 启用演示模式
DEMO_SCENARIO=full               # 默认场景
SIMULATION_SPEED=1               # 模拟速度倍率
DEMO_AUTO_EVENTS=true            # 自动触发演示事件
```

### WebSocket消息格式

```typescript
// 机器人状态更新
{
  type: 'robot_update',
  robot_id: 'robot_001',
  position: { x: 125.5, y: 78.3, floor_id: 'floor_028' },
  battery: 77.8,
  status: 'working',
  task_progress: 45.5
}

// 告警通知
{
  type: 'alert',
  alert_id: 'alert_001',
  severity: 'warning',
  robot_id: 'robot_003',
  message: '电量低于20%',
  timestamp: '2026-01-22T10:30:00Z'
}

// 任务状态变化
{
  type: 'task_update',
  task_id: 'task_001',
  status: 'completed',
  robot_id: 'robot_001',
  completion_time: '2026-01-22T10:25:00Z'
}
```

---

## 验收标准

### 功能验收

| 功能 | 验收标准 |
|------|----------|
| 演示数据初始化 | 一键加载完整演示数据，<3秒完成 |
| 场景切换 | 切换场景后数据立即刷新，无空白 |
| 机器人动画 | 地图上机器人平滑移动，帧率>30fps |
| 告警触发 | 触发后<1秒在UI显示 |
| Agent对话 | 预设场景响应<2秒，展示推理过程 |
| 演示重置 | 一键重置到初始状态 |

### 演示效果验收

| 场景 | 时长 | 效果标准 |
|------|------|----------|
| 高管视角 | 3分钟 | 30秒内理解核心价值 |
| 运营视角 | 5分钟 | 能完成一次完整任务派发 |
| AI协作 | 5分钟 | 展示3轮以上智能对话 |
| 移动端 | 2分钟 | 完成一次告警处理 |

### 性能要求

| 指标 | 要求 |
|------|------|
| 页面加载 | <2秒 |
| 数据刷新 | <500ms |
| 动画帧率 | >30fps |
| WebSocket延迟 | <100ms |

---

## 开发计划

| 阶段 | 模块 | 工作内容 | 预计工时 |
|------|------|----------|----------|
| Phase 1 | DM1 | 演示数据服务 + 种子数据 | 1天 |
| Phase 2 | DM2 | 实时模拟引擎 | 1天 |
| Phase 3 | DM3 | 演示控制面板 | 0.5天 |
| Phase 4 | DM4 | Agent对话增强 | 1天 |
| Phase 5 | DM5 | 地图动态可视化 | 1天 |
| Phase 6 | - | 集成测试 + 演示彩排 | 0.5天 |
| **总计** | | | **5天** |

---

## 附录

### A. 演示脚本模板

```markdown
# LinkC 产品演示脚本

## 开场 (30秒)
"欢迎了解LinkC智能清洁机器人协同平台。
 我们的目标是让清洁机器人从各自为战变成协同作战。"

## 场景1: 高管视角 (3分钟)
"首先，让我们从管理者视角看看整体运营状况..."
[展示战略驾驶舱]

## 场景2: 运营视角 (5分钟)
"现在让我们看看运营团队如何实时管理机器人车队..."
[展示运营控制台，演示任务派发]

## 场景3: AI协作 (5分钟)
"接下来是我们的核心亮点——人机协作..."
[展示Agent对话，演示智能调度]

## 收尾 (1分钟)
"总结: 效率提升40%，成本降低35%，
 这就是LinkC带来的价值。"
```

### B. 常见演示问题处理

| 问题 | 处理方式 |
|------|----------|
| 数据加载慢 | 使用演示控制面板重置 |
| 动画卡顿 | 降低模拟速度到1x |
| 网络断开 | 系统自动使用本地缓存 |
| 意外错误 | 刷新页面重新开始 |

---

*文档版本: 1.0*
*创建日期: 2026-01-22*
