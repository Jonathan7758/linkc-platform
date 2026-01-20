# 模块开发规格书：A3 对话助手 Agent

## 文档信息

| 项目 | 内容 |
|-----|------|
| 模块ID | A3 |
| 模块名称 | 对话助手 Agent |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | A1运行时框架、LLM API、所有MCP Server |

---

## 1. 模块概述

### 1.1 职责描述

对话助手Agent提供自然语言交互能力，包括：
- **自然语言理解**：理解用户意图和参数
- **任务执行**：调用MCP Tools执行用户请求
- **信息查询**：回答关于系统状态的问题
- **多轮对话**：维护对话上下文
- **结果展示**：将执行结果转换为自然语言

### 1.2 在系统中的位置

```
┌─────────────────────────────────────────────────────────────┐
│                       用户交互层                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          API网关 (G5 Agent交互API)                   │   │
│  └─────────────────────────┬───────────────────────────┘   │
│                            │                               │
│                            ▼                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         【A3 对话助手Agent】 ◄── 本模块              │   │
│  │                                                     │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │              LLM决策引擎                     │   │   │
│  │  │  意图识别 / 参数提取 / 工具调用 / 回复生成  │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│         ┌───────────────┼───────────────┐                  │
│         ▼               ▼               ▼                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ M1空间MCP  │ │ M2任务MCP   │ │ M3/M4机器人 │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 支持的对话场景

| 场景 | 示例 | 涉及MCP |
|-----|------|--------|
| 状态查询 | "1号机器人在哪里？" | M3/M4 |
| 任务创建 | "给大堂安排一次深度清洁" | M2 |
| 任务查询 | "今天还有哪些任务没完成？" | M2 |
| 机器人控制 | "让2号机器人回去充电" | M3/M4 |
| 数据统计 | "本周的清洁完成率是多少？" | D3 |
| 异常处理 | "3号机器人好像卡住了" | M3/M4 |

---

## 2. 接口定义

### 2.1 对话接口

```python
class ConversationRequest(BaseModel):
    """对话请求"""
    session_id: str                     # 会话ID
    tenant_id: str
    user_id: str
    message: str                        # 用户消息
    context: Optional[dict] = None      # 额外上下文

class ConversationResponse(BaseModel):
    """对话响应"""
    session_id: str
    message: str                        # 助手回复
    intent: Optional[str] = None        # 识别的意图
    actions_taken: List[dict] = []      # 执行的动作
    suggestions: List[str] = []         # 建议的后续操作
    data: Optional[dict] = None         # 附带数据（如图表数据）

class ConversationAgent:
    """对话助手Agent接口"""
    
    async def chat(
        self,
        request: ConversationRequest
    ) -> ConversationResponse:
        """处理对话"""
        pass
    
    async def get_history(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[dict]:
        """获取对话历史"""
        pass
    
    async def clear_session(
        self,
        session_id: str
    ) -> bool:
        """清除会话"""
        pass
```

### 2.2 意图定义

```python
class Intent(str, Enum):
    """对话意图"""
    # 查询类
    QUERY_ROBOT_STATUS = "query_robot_status"       # 查询机器人状态
    QUERY_TASK_STATUS = "query_task_status"         # 查询任务状态
    QUERY_STATISTICS = "query_statistics"           # 查询统计数据
    QUERY_SCHEDULE = "query_schedule"               # 查询排程
    
    # 操作类
    CREATE_TASK = "create_task"                     # 创建任务
    CANCEL_TASK = "cancel_task"                     # 取消任务
    CONTROL_ROBOT = "control_robot"                 # 控制机器人
    UPDATE_SCHEDULE = "update_schedule"             # 更新排程
    
    # 其他
    GREETING = "greeting"                           # 问候
    HELP = "help"                                   # 帮助
    UNKNOWN = "unknown"                             # 未知意图

class IntentSlots(BaseModel):
    """意图槽位"""
    robot_id: Optional[str] = None
    robot_name: Optional[str] = None
    zone_id: Optional[str] = None
    zone_name: Optional[str] = None
    task_type: Optional[str] = None
    time_range: Optional[str] = None
    date: Optional[str] = None
    action: Optional[str] = None
```

---

## 3. 核心实现

### 3.1 LLM集成

```python
class LLMClient:
    """LLM客户端"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet"):
        self.api_key = api_key
        self.model = model
        
    async def chat(
        self,
        messages: List[dict],
        tools: List[dict] = None,
        system_prompt: str = None
    ) -> dict:
        """调用LLM"""
        pass

# 系统提示词
SYSTEM_PROMPT = """你是LinkC智能物业管理平台的对话助手。

你可以帮助用户：
1. 查询机器人状态（位置、电量、工作状态）
2. 查询清洁任务（今日任务、完成情况）
3. 创建清洁任务（指定区域、类型、时间）
4. 控制机器人（开始清洁、停止、回充电站）
5. 查看统计数据（完成率、效率、趋势）

当需要执行操作时，调用相应的工具。
回复要简洁友好，使用中文。
如果信息不足，请询问用户补充。

当前租户ID: {tenant_id}
"""

# 工具定义（给LLM）
TOOLS_DEFINITION = [
    {
        "name": "get_robot_status",
        "description": "获取机器人当前状态",
        "parameters": {
            "type": "object",
            "properties": {
                "robot_id": {"type": "string", "description": "机器人ID"},
                "robot_name": {"type": "string", "description": "机器人名称"}
            }
        }
    },
    {
        "name": "list_robots",
        "description": "列出所有机器人",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "状态筛选", "enum": ["all", "idle", "working", "charging"]}
            }
        }
    },
    {
        "name": "get_pending_tasks",
        "description": "获取待执行任务",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "日期，默认今天"}
            }
        }
    },
    {
        "name": "create_cleaning_task",
        "description": "创建清洁任务",
        "parameters": {
            "type": "object",
            "properties": {
                "zone_name": {"type": "string", "description": "区域名称"},
                "task_type": {"type": "string", "description": "任务类型", "enum": ["routine", "deep", "spot"]},
                "priority": {"type": "integer", "description": "优先级1-10"}
            },
            "required": ["zone_name"]
        }
    },
    {
        "name": "control_robot",
        "description": "控制机器人",
        "parameters": {
            "type": "object",
            "properties": {
                "robot_id": {"type": "string", "description": "机器人ID"},
                "robot_name": {"type": "string", "description": "机器人名称"},
                "action": {"type": "string", "description": "动作", "enum": ["start", "stop", "pause", "resume", "return_dock"]}
            },
            "required": ["action"]
        }
    },
    {
        "name": "get_task_statistics",
        "description": "获取任务统计",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "统计周期", "enum": ["today", "week", "month"]}
            }
        }
    }
]
```

### 3.2 ConversationAgent实现

```python
class ConversationAgent(BaseAgent):
    """对话助手Agent"""
    
    def __init__(self, config: AgentConfig, runtime: AgentRuntime):
        super().__init__(config, runtime)
        self.llm = LLMClient(config.settings.get("llm_api_key"))
        self.sessions: Dict[str, ConversationSession] = {}
        
    async def on_start(self):
        self.logger.info("ConversationAgent starting")
        
    async def on_stop(self):
        self.logger.info("ConversationAgent stopping")
        
    async def run(self):
        # 对话Agent不需要主动循环，只响应请求
        await asyncio.sleep(60)
        
    async def chat(
        self,
        request: ConversationRequest
    ) -> ConversationResponse:
        """处理对话请求"""
        
        # 获取或创建会话
        session = self._get_or_create_session(request.session_id, request.tenant_id)
        
        # 添加用户消息到历史
        session.add_message("user", request.message)
        
        # 构建LLM请求
        messages = self._build_messages(session, request)
        
        # 调用LLM
        llm_response = await self.llm.chat(
            messages=messages,
            tools=TOOLS_DEFINITION,
            system_prompt=SYSTEM_PROMPT.format(tenant_id=request.tenant_id)
        )
        
        # 处理LLM响应
        actions_taken = []
        
        # 如果LLM请求调用工具
        while llm_response.get("tool_calls"):
            for tool_call in llm_response["tool_calls"]:
                # 执行工具调用
                result = await self._execute_tool(
                    tool_call["name"],
                    tool_call["arguments"],
                    request.tenant_id
                )
                actions_taken.append({
                    "tool": tool_call["name"],
                    "arguments": tool_call["arguments"],
                    "result": result
                })
                
                # 将结果告诉LLM
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result)
                })
            
            # 继续对话
            llm_response = await self.llm.chat(
                messages=messages,
                tools=TOOLS_DEFINITION
            )
        
        # 获取最终回复
        assistant_message = llm_response.get("content", "抱歉，我没有理解您的问题。")
        
        # 保存助手回复
        session.add_message("assistant", assistant_message)
        
        return ConversationResponse(
            session_id=request.session_id,
            message=assistant_message,
            actions_taken=actions_taken,
            suggestions=self._generate_suggestions(actions_taken)
        )
    
    async def _execute_tool(
        self,
        tool_name: str,
        arguments: dict,
        tenant_id: str
    ) -> dict:
        """执行工具调用"""
        
        if tool_name == "get_robot_status":
            return await self._get_robot_status(tenant_id, arguments)
        elif tool_name == "list_robots":
            return await self._list_robots(tenant_id, arguments)
        elif tool_name == "get_pending_tasks":
            return await self._get_pending_tasks(tenant_id, arguments)
        elif tool_name == "create_cleaning_task":
            return await self._create_task(tenant_id, arguments)
        elif tool_name == "control_robot":
            return await self._control_robot(tenant_id, arguments)
        elif tool_name == "get_task_statistics":
            return await self._get_statistics(tenant_id, arguments)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    async def _get_robot_status(self, tenant_id: str, args: dict) -> dict:
        """获取机器人状态"""
        # 通过名称查找ID
        robot_id = args.get("robot_id")
        if not robot_id and args.get("robot_name"):
            robot_id = await self._find_robot_by_name(tenant_id, args["robot_name"])
        
        if not robot_id:
            return {"error": "未找到指定的机器人"}
        
        # 调用MCP
        result = await self.call_tool(
            "gaoxian_get_robot_status",  # 或根据品牌选择
            {"robot_id": robot_id}
        )
        
        return result.data if result.success else {"error": result.error}
    
    async def _create_task(self, tenant_id: str, args: dict) -> dict:
        """创建清洁任务"""
        # 通过区域名称查找ID
        zone_id = await self._find_zone_by_name(tenant_id, args["zone_name"])
        if not zone_id:
            return {"error": f"未找到区域: {args['zone_name']}"}
        
        # 创建任务
        result = await self.call_tool(
            "task_create_task",
            {
                "tenant_id": tenant_id,
                "zone_id": zone_id,
                "task_type": args.get("task_type", "routine"),
                "priority": args.get("priority", 5)
            }
        )
        
        return result.data if result.success else {"error": result.error}
    
    async def _control_robot(self, tenant_id: str, args: dict) -> dict:
        """控制机器人"""
        robot_id = args.get("robot_id")
        if not robot_id and args.get("robot_name"):
            robot_id = await self._find_robot_by_name(tenant_id, args["robot_name"])
        
        if not robot_id:
            return {"error": "未找到指定的机器人"}
        
        action = args["action"]
        
        # 根据动作调用不同的MCP
        tool_mapping = {
            "stop": "gaoxian_stop_cleaning",
            "pause": "gaoxian_pause_cleaning",
            "resume": "gaoxian_resume_cleaning",
            "return_dock": "gaoxian_return_to_dock"
        }
        
        tool_name = tool_mapping.get(action)
        if not tool_name:
            return {"error": f"不支持的操作: {action}"}
        
        result = await self.call_tool(tool_name, {"robot_id": robot_id})
        
        return result.data if result.success else {"error": result.error}
```

---

## 4. 会话管理

### 4.1 会话数据结构

```python
class ConversationSession:
    """对话会话"""
    
    def __init__(self, session_id: str, tenant_id: str):
        self.session_id = session_id
        self.tenant_id = tenant_id
        self.messages: List[dict] = []
        self.context: dict = {}
        self.created_at = datetime.utcnow()
        self.last_active = datetime.utcnow()
        
    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.last_active = datetime.utcnow()
        
        # 限制历史长度
        if len(self.messages) > 50:
            self.messages = self.messages[-50:]
```

---

## 5. 测试要求

### 5.1 测试用例

```python
class TestConversationAgent:
    
    async def test_query_robot_status(self):
        """测试查询机器人状态"""
        response = await agent.chat(ConversationRequest(
            session_id="test",
            tenant_id="test_tenant",
            user_id="test_user",
            message="1号机器人在哪里？"
        ))
        assert "机器人" in response.message
        
    async def test_create_task(self):
        """测试创建任务"""
        response = await agent.chat(ConversationRequest(
            session_id="test",
            tenant_id="test_tenant",
            user_id="test_user",
            message="给大堂安排一次深度清洁"
        ))
        assert len(response.actions_taken) > 0
        
    async def test_multi_turn(self):
        """测试多轮对话"""
        # 第一轮
        response1 = await agent.chat(ConversationRequest(
            session_id="test",
            tenant_id="test_tenant",
            user_id="test_user",
            message="查看1号机器人状态"
        ))
        # 第二轮（应理解上下文）
        response2 = await agent.chat(ConversationRequest(
            session_id="test",
            tenant_id="test_tenant",
            user_id="test_user",
            message="让它去充电"
        ))
        assert "充电" in response2.message or len(response2.actions_taken) > 0
```

---

## 6. 验收标准

### 6.1 功能验收

- [ ] 能理解常见查询意图
- [ ] 能正确调用MCP执行操作
- [ ] 支持多轮对话
- [ ] 回复自然友好
- [ ] 异常情况处理得当

### 6.2 性能要求

- 响应时间 < 3s（LLM调用时间）
- 支持100+并发会话

### 6.3 用户体验

- 意图识别准确率 > 90%
- 用户满意度 > 85%
