"""
LLM 抽象基类
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from dataclasses import dataclass, field


class LLMProvider(str, Enum):
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    OPENAI = "openai"
    VOLCENGINE = "volcengine"


class LLMConfig(BaseModel):
    """LLM配置"""
    provider: LLMProvider = LLMProvider.CLAUDE
    api_key: str
    model: str = "claude-sonnet-4-20250514"
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 60


class Message(BaseModel):
    """对话消息"""
    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None  # for tool messages
    tool_call_id: Optional[str] = None  # for tool results


class Tool(BaseModel):
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema


class ToolCall(BaseModel):
    """工具调用"""
    id: str
    name: str
    arguments: Dict[str, Any]


class LLMResponse(BaseModel):
    """LLM响应"""
    content: Optional[str] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    finish_reason: str = "stop"  # stop, tool_calls, length
    usage: Dict[str, int] = Field(default_factory=dict)


class LLMClient(ABC):
    """LLM客户端抽象基类"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        tool_choice: Optional[str] = None,  # auto, none, required
    ) -> LLMResponse:
        """发送对话请求"""
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
    ):
        """流式对话"""
        pass
    
    def format_tool_result(
        self,
        tool_call_id: str,
        result: Any,
    ) -> Message:
        """格式化工具结果为消息"""
        import json
        content = json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result
        return Message(
            role="tool",
            content=content,
            tool_call_id=tool_call_id,
        )
