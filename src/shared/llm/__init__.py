"""
LLM 抽象层
==========
支持多种LLM提供商: Claude, DeepSeek, Qwen, OpenAI
"""
from .base import LLMClient, LLMConfig, LLMResponse, Message, ToolCall, Tool, LLMProvider
from .claude import ClaudeLLMClient
from .openai_compat import OpenAICompatibleClient
from .factory import create_llm_client, create_llm_from_env

__all__ = [
    'LLMClient',
    'LLMConfig', 
    'LLMProvider',
    'LLMResponse',
    'Message',
    'ToolCall',
    'Tool',
    'ClaudeLLMClient',
    'OpenAICompatibleClient',
    'create_llm_client',
    'create_llm_from_env',
]
