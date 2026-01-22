"""
A3: 对话助手Agent - 配置和数据模型
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class Intent(str, Enum):
    """对话意图"""
    QUERY_ROBOT_STATUS = "query_robot_status"
    QUERY_TASK_STATUS = "query_task_status"
    QUERY_STATISTICS = "query_statistics"
    CREATE_TASK = "create_task"
    CANCEL_TASK = "cancel_task"
    CONTROL_ROBOT = "control_robot"
    GREETING = "greeting"
    HELP = "help"
    UNKNOWN = "unknown"


class ConversationRequest(BaseModel):
    """对话请求"""
    session_id: str
    tenant_id: str
    user_id: str
    message: str
    context: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """对话响应"""
    session_id: str
    message: str
    intent: Optional[str] = None
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    data: Optional[Dict[str, Any]] = None


class ConversationTurn(BaseModel):
    """对话轮次"""
    role: str  # user, assistant
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None


class ConversationSession(BaseModel):
    """对话会话"""
    session_id: str
    tenant_id: str
    user_id: str
    turns: List[ConversationTurn] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationAgentConfig(BaseModel):
    """对话助手Agent配置"""
    agent_id: str = "conversation-agent"
    tenant_id: str
    
    # LLM配置
    llm_provider: str = "volcengine"
    llm_api_key: str = ""
    llm_model: str = "doubao-1-5-pro-32k-250115"
    llm_base_url: Optional[str] = None
    
    # 对话配置
    max_history_turns: int = 20
    max_tool_iterations: int = 5
    
    # 系统提示词
    system_prompt: str = """你是LinkC物业机器人管理平台的智能助手。

你可以帮助用户:
1. 查询机器人状态 - 了解机器人位置、电量、工作状态
2. 管理清洁任务 - 创建、查询、取消清洁任务
3. 控制机器人 - 让机器人回充电桩、前往指定位置
4. 查看数据统计 - 清洁完成率、工作时长等

请用简洁友好的中文回复用户。当需要执行操作时，使用提供的工具函数。"""
