# Demo API 文档

**版本**: 1.0
**更新日期**: 2026-01-22

本文档描述演示增强模块的API端点。

---

## 目录

1. [Demo数据服务API](#demo数据服务api)
2. [模拟引擎API](#模拟引擎api)
3. [Agent对话API](#agent对话api)
4. [WebSocket实时推送](#websocket实时推送)

---

## Demo数据服务API

### GET /api/v1/demo/status

获取演示模式状态。

**响应示例**:
```json
{
  "is_active": true,
  "current_scenario": "executive_overview",
  "simulation_speed": 1.0,
  "auto_events_enabled": true,
  "started_at": "2026-01-22T08:00:00Z"
}
```

### POST /api/v1/demo/init

初始化演示数据。

**响应示例**:
```json
{
  "success": true,
  "message": "Demo data initialized successfully",
  "data": {
    "buildings": 3,
    "robots": 8,
    "tasks": 15
  }
}
```

### POST /api/v1/demo/scenario

切换演示场景。

**请求体**:
```json
{
  "scenario": "operations_normal"
}
```

**可用场景**:
- `executive_overview` - 高管总览
- `operations_normal` - 运营常态
- `operations_alert` - 运营告警
- `agent_conversation` - Agent对话
- `full_demo` - 完整演示

### POST /api/v1/demo/event

触发演示事件。

**请求体**:
```json
{
  "event": "low_battery",
  "robot_id": "robot_001"
}
```

**可用事件**:
- `low_battery` - 低电量告警
- `obstacle` - 遇到障碍物
- `task_done` - 任务完成
- `urgent_task` - 紧急任务
- `robot_error` - 机器人故障
- `charging_done` - 充电完成

### POST /api/v1/demo/reset

重置演示数据。

### GET /api/v1/demo/buildings

获取演示楼宇列表。

### GET /api/v1/demo/robots

获取演示机器人列表。

### GET /api/v1/demo/tasks

获取演示任务列表。

### GET /api/v1/demo/kpi

获取演示KPI数据。

---

## 模拟引擎API

### GET /api/v1/simulation/status

获取模拟引擎状态。

**响应示例**:
```json
{
  "running": true,
  "paused": false,
  "speed": 1.0,
  "tick_interval": 0.1,
  "robots_count": 8,
  "robots_by_status": {
    "working": 4,
    "idle": 2,
    "charging": 1,
    "error": 1
  }
}
```

### POST /api/v1/simulation/start

启动模拟引擎。

### POST /api/v1/simulation/stop

停止模拟引擎。

### POST /api/v1/simulation/pause

暂停模拟引擎。

### POST /api/v1/simulation/resume

恢复模拟引擎。

### POST /api/v1/simulation/speed

设置模拟速度。

**请求体**:
```json
{
  "speed": 2.0
}
```

### GET /api/v1/simulation/robots

获取所有机器人的实时状态。

**响应示例**:
```json
{
  "robots": [
    {
      "robot_id": "robot_001",
      "name": "清洁机器人 A-01",
      "status": "working",
      "position": {"x": 25.5, "y": 30.2, "orientation": 45},
      "battery": 85,
      "speed": 0.5,
      "current_task_id": "task_001"
    }
  ]
}
```

### GET /api/v1/simulation/robot/{robot_id}

获取单个机器人详情。

---

## Agent对话API

### GET /api/v1/agent-demo/scenarios

获取预设对话场景列表。

**响应示例**:
```json
{
  "scenarios": [
    {
      "id": "task_scheduling",
      "name": "任务调度",
      "description": "通过对话下达清洁任务",
      "sample_messages": ["安排大堂清洁", "调度3号机器人去会议室"]
    },
    {
      "id": "status_query",
      "name": "状态查询",
      "description": "询问系统状态",
      "sample_messages": ["现在有多少机器人在工作", "今天清洁面积是多少"]
    }
  ]
}
```

### POST /api/v1/agent-demo/chat

与Agent对话。

**请求体**:
```json
{
  "session_id": "demo_session_001",
  "message": "安排大堂清洁",
  "scenario": "task_scheduling"
}
```

**响应示例**:
```json
{
  "message": "好的，我来为您安排大堂清洁任务。",
  "reasoning_steps": [
    {
      "step": 1,
      "action": "analyze_request",
      "result": "用户请求清洁大堂区域",
      "duration": 0.2
    },
    {
      "step": 2,
      "action": "check_robots",
      "result": "发现2台空闲机器人：A-02, A-05",
      "duration": 0.3
    },
    {
      "step": 3,
      "action": "select_robot",
      "result": "选择A-02（距离最近，电量92%）",
      "duration": 0.1
    }
  ],
  "actions": [
    {
      "type": "create_task",
      "params": {
        "zone": "大堂",
        "robot": "A-02",
        "priority": "normal"
      }
    }
  ],
  "requires_confirmation": true
}
```

### POST /api/v1/agent-demo/confirm

确认Agent建议的操作。

**请求体**:
```json
{
  "session_id": "demo_session_001",
  "confirmed": true
}
```

### POST /api/v1/agent-demo/feedback

记录学习反馈。

**请求体**:
```json
{
  "session_id": "demo_session_001",
  "feedback": "这个区域应该用拖地机器人"
}
```

---

## WebSocket实时推送

### 连接地址

```
ws://localhost:8000/ws/simulation
```

### 消息格式

**机器人状态更新**:
```json
{
  "type": "robot_update",
  "data": {
    "robot_id": "robot_001",
    "position": {"x": 25.5, "y": 30.2},
    "status": "working",
    "battery": 84
  }
}
```

**任务状态更新**:
```json
{
  "type": "task_update",
  "data": {
    "task_id": "task_001",
    "status": "completed",
    "progress": 100
  }
}
```

**告警事件**:
```json
{
  "type": "alert",
  "data": {
    "alert_id": "alert_001",
    "type": "low_battery",
    "robot_id": "robot_003",
    "message": "机器人A-03电量低于20%"
  }
}
```

---

## 错误响应

所有API在发生错误时返回统一格式：

```json
{
  "error": {
    "code": "DEMO_NOT_INITIALIZED",
    "message": "Demo data has not been initialized",
    "details": {}
  }
}
```

**常见错误码**:
- `DEMO_NOT_INITIALIZED` - 演示数据未初始化
- `INVALID_SCENARIO` - 无效的场景名称
- `INVALID_EVENT` - 无效的事件类型
- `ROBOT_NOT_FOUND` - 机器人不存在
- `SIMULATION_NOT_RUNNING` - 模拟引擎未运行

---

*文档版本: 1.0*
*最后更新: 2026-01-22*
