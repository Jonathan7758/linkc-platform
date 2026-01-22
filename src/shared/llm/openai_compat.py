"""
OpenAI兼容客户端 - 支持DeepSeek, Qwen等
"""

import httpx
import json
import logging
from typing import List, Optional, AsyncIterator
from .base import LLMClient, LLMConfig, Message, Tool, ToolCall, LLMResponse

logger = logging.getLogger(__name__)

# Provider配置
PROVIDER_CONFIGS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
    },
    "volcengine": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "default_model": "doubao-1-5-pro-32k-250115",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
    },
}


class OpenAICompatibleClient(LLMClient):
    """OpenAI兼容API客户端 (DeepSeek, Qwen, etc.)"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        provider = config.provider.value
        provider_config = PROVIDER_CONFIGS.get(provider, {})
        
        self.base_url = config.base_url or provider_config.get("base_url", "https://api.openai.com/v1")
        self.model = config.model or provider_config.get("default_model", "gpt-4o")
        
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        """发送对话请求"""
        
        # 转换消息格式
        openai_messages = self._convert_messages(messages)
        
        # 构建请求
        payload = {
            "model": self.model,
            "messages": openai_messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }
        
        # 添加工具
        if tools:
            payload["tools"] = self._convert_tools(tools)
            if tool_choice:
                payload["tool_choice"] = tool_choice if tool_choice in ["auto", "none"] else {"type": "function", "function": {"name": tool_choice}}
        
        # 发送请求
        url = f"{self.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return self._parse_response(data)
            except httpx.HTTPStatusError as e:
                logger.error(f"API error: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"API error: {e}")
                raise
    
    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
    ) -> AsyncIterator[str]:
        """流式对话"""
        openai_messages = self._convert_messages(messages)
        
        payload = {
            "model": self.model,
            "messages": openai_messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": True,
        }
        
        if tools:
            payload["tools"] = self._convert_tools(tools)
        
        url = f"{self.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            async with client.stream("POST", url, headers=self.headers, json=payload) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            data = json.loads(line[6:])
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            pass
    
    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """转换消息格式"""
        result = []
        for msg in messages:
            if msg.role == "tool":
                result.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": msg.tool_call_id,
                })
            else:
                result.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        return result
    
    def _convert_tools(self, tools: List[Tool]) -> List[dict]:
        """转换工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            }
            for tool in tools
        ]
    
    def _parse_response(self, data: dict) -> LLMResponse:
        """解析响应"""
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        content = message.get("content")
        tool_calls = []
        
        if message.get("tool_calls"):
            for tc in message["tool_calls"]:
                func = tc.get("function", {})
                args = func.get("arguments", "{}")
                try:
                    arguments = json.loads(args) if isinstance(args, str) else args
                except json.JSONDecodeError:
                    arguments = {}
                tool_calls.append(ToolCall(
                    id=tc.get("id", ""),
                    name=func.get("name", ""),
                    arguments=arguments,
                ))
        
        finish_reason = choice.get("finish_reason", "stop")
        if finish_reason == "tool_calls":
            finish_reason = "tool_calls"
        
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            }
        )
