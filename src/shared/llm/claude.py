"""
Claude LLM 客户端实现
"""

import httpx
import json
import logging
from typing import List, Optional, Any, AsyncIterator
from .base import LLMClient, LLMConfig, Message, Tool, ToolCall, LLMResponse

logger = logging.getLogger(__name__)

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"


class ClaudeLLMClient(LLMClient):
    """Claude API 客户端"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_url = config.base_url or CLAUDE_API_URL
        self.headers = {
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        """发送对话请求到Claude API"""
        
        # 转换消息格式
        claude_messages = self._convert_messages(messages)
        
        # 构建请求
        payload = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "messages": claude_messages,
        }
        
        # 提取system message
        system_content = self._extract_system(messages)
        if system_content:
            payload["system"] = system_content
        
        # 添加工具
        if tools:
            payload["tools"] = self._convert_tools(tools)
            if tool_choice:
                payload["tool_choice"] = self._convert_tool_choice(tool_choice)
        
        # 发送请求
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return self._parse_response(data)
            except httpx.HTTPStatusError as e:
                logger.error(f"Claude API error: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Claude API error: {e}")
                raise
    
    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
    ) -> AsyncIterator[str]:
        """流式对话"""
        claude_messages = self._convert_messages(messages)
        
        payload = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "messages": claude_messages,
            "stream": True,
        }
        
        system_content = self._extract_system(messages)
        if system_content:
            payload["system"] = system_content
        
        if tools:
            payload["tools"] = self._convert_tools(tools)
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            async with client.stream(
                "POST",
                self.api_url,
                headers=self.headers,
                json=payload,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if data.get("type") == "content_block_delta":
                            delta = data.get("delta", {})
                            if "text" in delta:
                                yield delta["text"]
    
    def _extract_system(self, messages: List[Message]) -> Optional[str]:
        """提取system消息"""
        for msg in messages:
            if msg.role == "system":
                return msg.content
        return None
    
    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """转换消息格式为Claude格式"""
        claude_messages = []
        
        for msg in messages:
            if msg.role == "system":
                continue  # system消息单独处理
            
            if msg.role == "tool":
                # Claude使用tool_result格式
                claude_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.content,
                    }]
                })
            elif msg.role == "assistant" and hasattr(msg, "tool_calls") and msg.tool_calls:
                # 助手调用工具
                content = []
                if msg.content:
                    content.append({"type": "text", "text": msg.content})
                for tc in msg.tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    })
                claude_messages.append({"role": "assistant", "content": content})
            else:
                claude_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        
        return claude_messages
    
    def _convert_tools(self, tools: List[Tool]) -> List[dict]:
        """转换工具定义为Claude格式"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            }
            for tool in tools
        ]
    
    def _convert_tool_choice(self, choice: str) -> dict:
        """转换tool_choice"""
        if choice == "auto":
            return {"type": "auto"}
        elif choice == "none":
            return {"type": "none"}
        elif choice == "required":
            return {"type": "any"}
        else:
            return {"type": "tool", "name": choice}
    
    def _parse_response(self, data: dict) -> LLMResponse:
        """解析Claude响应"""
        content = None
        tool_calls = []
        
        for block in data.get("content", []):
            if block.get("type") == "text":
                content = block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.get("id"),
                    name=block.get("name"),
                    arguments=block.get("input", {}),
                ))
        
        stop_reason = data.get("stop_reason", "end_turn")
        finish_reason = "tool_calls" if stop_reason == "tool_use" else "stop"
        
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
            }
        )
