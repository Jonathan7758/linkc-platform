# 模块开发规格书：A1 Agent运行时框架

## 文档信息

| 项目 | 内容 |
|-----|------|
| 模块ID | A1 |
| 模块名称 | Agent运行时框架 |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | F1数据模型、MCP SDK |

---

## 1. 模块概述

### 1.1 职责描述

Agent运行时框架提供Agent执行的基础能力，包括：
- **生命周期管理**：Agent的启动、停止、重启
- **MCP客户端封装**：统一的MCP Tool调用接口
- **消息路由**：Agent间的消息传递
- **异常升级**：自动检测异常并升级处理
- **可观测性**：日志、指标、追踪
- **状态管理**：Agent状态持久化和恢复

### 1.2 在系统中的位置

```
┌─────────────────────────────────────────────────────────────┐
│                       Agent层                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            【A1 Agent运行时框架】 ◄── 本模块         │   │
│  │                                                     │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │              Agent基类                        │  │   │
│  │  │  lifecycle / state / tools / escalation      │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │                       │                            │   │
│  │       ┌───────────────┼───────────────┐            │   │
│  │       ▼               ▼               ▼            │   │
│  │  ┌─────────┐   ┌─────────┐   ┌─────────┐          │   │
│  │  │A2清洁调度│   │A3对话助手│   │A4数据采集│          │   │
│  │  └─────────┘   └─────────┘   └─────────┘          │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│                         ▼                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   MCP Client                         │   │
│  │       调用 M1/M2/M3/M4 等MCP Server                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 输入/输出概述

| 类型 | 内容 |
|-----|------|
| **输入** | Agent配置、触发事件、用户指令 |
| **输出** | Agent执行日志、状态变更、升级事件 |

---

## 2. 核心组件

### 2.1 Agent基类

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

class AgentState(str, Enum):
    """Agent状态"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

class AgentConfig(BaseModel):
    """Agent配置"""
    agent_id: str
    agent_type: str
    tenant_id: str
    enabled: bool = True
    settings: Dict[str, Any] = {}
    
class BaseAgent(ABC):
    """Agent基类 - 所有Agent必须继承此类"""
    
    def __init__(self, config: AgentConfig, runtime: 'AgentRuntime'):
        self.config = config
        self.runtime = runtime
        self.state = AgentState.INITIALIZING
        self.mcp_client = runtime.mcp_client
        self.logger = runtime.get_logger(config.agent_id)
        self._task: Optional[asyncio.Task] = None
        
    @property
    def agent_id(self) -> str:
        return self.config.agent_id
    
    @property
    def tenant_id(self) -> str:
        return self.config.tenant_id
    
    # === 生命周期方法 ===
    
    async def start(self) -> None:
        """启动Agent"""
        self.logger.info(f"Starting agent {self.agent_id}")
        await self.on_start()
        self.state = AgentState.RUNNING
        self._task = asyncio.create_task(self._run_loop())
        
    async def stop(self) -> None:
        """停止Agent"""
        self.logger.info(f"Stopping agent {self.agent_id}")
        self.state = AgentState.STOPPED
        if self._task:
            self._task.cancel()
        await self.on_stop()
        
    async def pause(self) -> None:
        """暂停Agent"""
        self.state = AgentState.PAUSED
        
    async def resume(self) -> None:
        """恢复Agent"""
        self.state = AgentState.RUNNING
        
    # === 子类必须实现的方法 ===
    
    @abstractmethod
    async def on_start(self) -> None:
        """启动时的初始化逻辑"""
        pass
    
    @abstractmethod
    async def on_stop(self) -> None:
        """停止时的清理逻辑"""
        pass
    
    @abstractmethod
    async def run(self) -> None:
        """Agent主逻辑（循环执行）"""
        pass
    
    # === 工具方法 ===
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """调用MCP Tool"""
        self.logger.debug(f"Calling tool: {tool_name}")
        result = await self.mcp_client.call_tool(tool_name, arguments)
        self._log_tool_call(tool_name, arguments, result)
        return result
    
    async def escalate(
        self,
        level: 'EscalationLevel',
        reason: str,
        context: Dict[str, Any]
    ) -> str:
        """触发异常升级"""
        return await self.runtime.escalate(
            agent_id=self.agent_id,
            level=level,
            reason=reason,
            context=context
        )
    
    async def emit_event(
        self,
        event_type: str,
        data: Dict[str, Any]
    ) -> None:
        """发送事件"""
        await self.runtime.emit_event(
            source=self.agent_id,
            event_type=event_type,
            data=data
        )
    
    # === 私有方法 ===
    
    async def _run_loop(self):
        """Agent运行循环"""
        while self.state == AgentState.RUNNING:
            try:
                await self.run()
            except Exception as e:
                self.logger.error(f"Agent error: {e}")
                await self._handle_error(e)
            await asyncio.sleep(1)  # 避免空转
            
    async def _handle_error(self, error: Exception):
        """处理Agent错误"""
        self.state = AgentState.ERROR
        await self.escalate(
            level=EscalationLevel.ERROR,
            reason=str(error),
            context={"exception": type(error).__name__}
        )
    
    def _log_tool_call(self, tool_name: str, args: dict, result: ToolResult):
        """记录工具调用日志"""
        self.runtime.log_activity(AgentActivity(
            agent_id=self.agent_id,
            activity_type="tool_call",
            tool_name=tool_name,
            arguments=args,
            result_success=result.success,
            timestamp=datetime.utcnow()
        ))
```

### 2.2 Agent运行时

```python
class AgentRuntime:
    """Agent运行时环境"""
    
    def __init__(
        self,
        mcp_servers: Dict[str, str],    # MCP Server地址配置
        redis_url: str,
        storage_service: StorageService
    ):
        self.mcp_client = MCPClient(mcp_servers)
        self.redis = redis.from_url(redis_url)
        self.storage = storage_service
        self.agents: Dict[str, BaseAgent] = {}
        self.escalation_handler = EscalationHandler(self)
        self.activity_logger = ActivityLogger(storage_service)
        
    async def start(self):
        """启动运行时"""
        await self.mcp_client.connect()
        await self._load_agents()
        
    async def stop(self):
        """停止运行时"""
        for agent in self.agents.values():
            await agent.stop()
        await self.mcp_client.disconnect()
        
    async def register_agent(self, agent: BaseAgent) -> None:
        """注册Agent"""
        self.agents[agent.agent_id] = agent
        
    async def start_agent(self, agent_id: str) -> None:
        """启动指定Agent"""
        if agent_id in self.agents:
            await self.agents[agent_id].start()
            
    async def stop_agent(self, agent_id: str) -> None:
        """停止指定Agent"""
        if agent_id in self.agents:
            await self.agents[agent_id].stop()
            
    async def get_agent_status(self, agent_id: str) -> Optional[AgentStatus]:
        """获取Agent状态"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            return AgentStatus(
                agent_id=agent_id,
                state=agent.state,
                config=agent.config
            )
        return None
    
    def get_logger(self, agent_id: str) -> logging.Logger:
        """获取Agent专用Logger"""
        return logging.getLogger(f"agent.{agent_id}")
    
    async def escalate(
        self,
        agent_id: str,
        level: 'EscalationLevel',
        reason: str,
        context: Dict[str, Any]
    ) -> str:
        """处理异常升级"""
        return await self.escalation_handler.handle(
            agent_id, level, reason, context
        )
    
    async def emit_event(
        self,
        source: str,
        event_type: str,
        data: Dict[str, Any]
    ) -> None:
        """发送事件到事件总线"""
        event = AgentEvent(
            source=source,
            event_type=event_type,
            data=data,
            timestamp=datetime.utcnow()
        )
        await self.redis.publish(
            f"events:{event_type}",
            event.json()
        )
        
    def log_activity(self, activity: AgentActivity) -> None:
        """记录Agent活动"""
        self.activity_logger.log(activity)
```

### 2.3 异常升级系统

```python
class EscalationLevel(str, Enum):
    """升级级别"""
    INFO = "info"           # 信息通知
    WARNING = "warning"     # 警告，需关注
    ERROR = "error"         # 错误，需处理
    CRITICAL = "critical"   # 严重，需立即处理

class EscalationRule(BaseModel):
    """升级规则"""
    rule_id: str
    trigger_type: str       # error_type/threshold/pattern
    trigger_config: dict
    level: EscalationLevel
    actions: List[str]      # notify/pause_agent/human_approval

class EscalationEvent(BaseModel):
    """升级事件"""
    event_id: str
    agent_id: str
    tenant_id: str
    level: EscalationLevel
    reason: str
    context: dict
    status: str             # pending/acknowledged/resolved
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

class EscalationHandler:
    """升级处理器"""
    
    def __init__(self, runtime: AgentRuntime):
        self.runtime = runtime
        self.rules: List[EscalationRule] = []
        
    async def handle(
        self,
        agent_id: str,
        level: EscalationLevel,
        reason: str,
        context: dict
    ) -> str:
        """处理升级事件"""
        # 创建升级事件
        event = EscalationEvent(
            event_id=str(uuid4()),
            agent_id=agent_id,
            tenant_id=self.runtime.agents[agent_id].tenant_id,
            level=level,
            reason=reason,
            context=context,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        # 保存事件
        await self._save_event(event)
        
        # 根据级别执行动作
        await self._execute_actions(event)
        
        return event.event_id
    
    async def _execute_actions(self, event: EscalationEvent):
        """执行升级动作"""
        if event.level == EscalationLevel.CRITICAL:
            # 暂停Agent
            await self.runtime.pause_agent(event.agent_id)
            # 发送紧急通知
            await self._send_notification(event, urgent=True)
        elif event.level == EscalationLevel.ERROR:
            # 发送通知
            await self._send_notification(event)
        elif event.level == EscalationLevel.WARNING:
            # 记录并定期汇总通知
            pass
            
    async def acknowledge(self, event_id: str, user_id: str) -> bool:
        """确认升级事件"""
        pass
    
    async def resolve(
        self,
        event_id: str,
        user_id: str,
        resolution: str
    ) -> bool:
        """解决升级事件"""
        pass
```

### 2.4 MCP客户端封装

```python
class MCPClient:
    """MCP客户端封装"""
    
    def __init__(self, servers: Dict[str, str]):
        """
        Args:
            servers: {"gaoxian": "localhost:8001", "ecovacs": "localhost:8002", ...}
        """
        self.servers = servers
        self.connections: Dict[str, MCPConnection] = {}
        
    async def connect(self):
        """连接所有MCP Server"""
        for name, url in self.servers.items():
            self.connections[name] = await MCPConnection.create(url)
            
    async def disconnect(self):
        """断开所有连接"""
        for conn in self.connections.values():
            await conn.close()
            
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict
    ) -> ToolResult:
        """
        调用MCP Tool
        
        自动路由到正确的MCP Server
        """
        # 根据tool_name前缀确定Server
        server_name = self._get_server_for_tool(tool_name)
        
        if server_name not in self.connections:
            return ToolResult(
                success=False,
                error=f"Unknown MCP server for tool: {tool_name}",
                error_code="UNKNOWN_SERVER"
            )
        
        try:
            conn = self.connections[server_name]
            result = await conn.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                error_code="MCP_ERROR"
            )
    
    def _get_server_for_tool(self, tool_name: str) -> str:
        """根据tool名称确定MCP Server"""
        # tool命名规则: {server}_{action}
        # 例如: gaoxian_list_robots, task_create_schedule
        prefix = tool_name.split('_')[0]
        
        TOOL_SERVER_MAPPING = {
            "gaoxian": "gaoxian",
            "ecovacs": "ecovacs",
            "space": "space",
            "task": "task"
        }
        
        return TOOL_SERVER_MAPPING.get(prefix, "default")
```

### 2.5 活动日志系统

```python
class AgentActivity(BaseModel):
    """Agent活动记录"""
    activity_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    tenant_id: str
    activity_type: str      # tool_call/decision/escalation/state_change
    timestamp: datetime
    
    # 工具调用相关
    tool_name: Optional[str] = None
    arguments: Optional[dict] = None
    result_success: Optional[bool] = None
    result_data: Optional[dict] = None
    
    # 决策相关
    decision_type: Optional[str] = None
    decision_reason: Optional[str] = None
    decision_confidence: Optional[float] = None
    
    # 其他
    metadata: Optional[dict] = None

class ActivityLogger:
    """活动日志记录器"""
    
    def __init__(self, storage: StorageService):
        self.storage = storage
        self.buffer: List[AgentActivity] = []
        self.buffer_size = 100
        
    def log(self, activity: AgentActivity):
        """记录活动（带缓冲）"""
        self.buffer.append(activity)
        if len(self.buffer) >= self.buffer_size:
            asyncio.create_task(self._flush())
            
    async def _flush(self):
        """刷新缓冲区到存储"""
        if self.buffer:
            activities = self.buffer.copy()
            self.buffer.clear()
            await self.storage.save_activities(activities)
            
    async def query(
        self,
        agent_id: str = None,
        activity_type: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100
    ) -> List[AgentActivity]:
        """查询活动日志"""
        pass
```

---

## 3. 接口定义汇总

### 3.1 Agent生命周期API

```python
# Agent管理接口（供API网关调用）
class AgentManagementAPI:
    
    async def list_agents(self, tenant_id: str) -> List[AgentStatus]:
        """列出所有Agent"""
        pass
    
    async def get_agent(self, agent_id: str) -> AgentStatus:
        """获取Agent详情"""
        pass
    
    async def start_agent(self, agent_id: str) -> bool:
        """启动Agent"""
        pass
    
    async def stop_agent(self, agent_id: str) -> bool:
        """停止Agent"""
        pass
    
    async def pause_agent(self, agent_id: str) -> bool:
        """暂停Agent"""
        pass
    
    async def resume_agent(self, agent_id: str) -> bool:
        """恢复Agent"""
        pass
    
    async def get_activities(
        self,
        agent_id: str,
        limit: int = 50
    ) -> List[AgentActivity]:
        """获取Agent活动日志"""
        pass
```

### 3.2 升级事件API

```python
class EscalationAPI:
    
    async def list_escalations(
        self,
        tenant_id: str,
        status: str = None,
        level: str = None
    ) -> List[EscalationEvent]:
        """列出升级事件"""
        pass
    
    async def acknowledge_escalation(
        self,
        event_id: str,
        user_id: str
    ) -> bool:
        """确认升级事件"""
        pass
    
    async def resolve_escalation(
        self,
        event_id: str,
        user_id: str,
        resolution: str
    ) -> bool:
        """解决升级事件"""
        pass
```

---

## 4. 实现要求

### 4.1 技术栈

```
语言: Python 3.11+
异步: asyncio
MCP: mcp-sdk
消息: Redis Pub/Sub
日志: structlog
```

### 4.2 代码规范

```python
# Agent实现示例骨架
class MyAgent(BaseAgent):
    """自定义Agent示例"""
    
    async def on_start(self):
        # 初始化逻辑
        self.logger.info("MyAgent started")
        
    async def on_stop(self):
        # 清理逻辑
        self.logger.info("MyAgent stopped")
        
    async def run(self):
        # 主循环逻辑
        # 1. 获取数据
        # 2. 做出决策
        # 3. 执行动作
        # 4. 记录结果
        await asyncio.sleep(60)  # 控制执行频率
```

---

## 5. 测试要求

### 5.1 单元测试用例

```python
class TestAgentRuntime:
    async def test_register_agent(self):
        """测试注册Agent"""
        pass
    
    async def test_start_stop_agent(self):
        """测试启动停止Agent"""
        pass
    
    async def test_tool_call(self):
        """测试工具调用"""
        pass
    
    async def test_escalation(self):
        """测试异常升级"""
        pass
    
    async def test_activity_logging(self):
        """测试活动日志"""
        pass
```

---

## 6. 验收标准

### 6.1 功能验收

- [ ] Agent基类可正常继承使用
- [ ] 生命周期管理正常
- [ ] MCP Tool调用正常
- [ ] 异常升级机制工作
- [ ] 活动日志完整记录

### 6.2 性能要求

- Agent启动时间 < 1s
- Tool调用额外延迟 < 50ms
- 支持100+ Agent并行运行

### 6.3 代码质量

- 单元测试覆盖率 > 80%
- 异步代码正确
- 日志完整
