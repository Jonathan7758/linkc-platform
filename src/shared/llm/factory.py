"""
LLM 客户端工厂
"""

from .base import LLMClient, LLMConfig, LLMProvider
from .claude import ClaudeLLMClient
from .openai_compat import OpenAICompatibleClient


def create_llm_client(config: LLMConfig) -> LLMClient:
    """
    根据配置创建LLM客户端
    
    Args:
        config: LLM配置
        
    Returns:
        LLM客户端实例
    """
    if config.provider == LLMProvider.CLAUDE:
        return ClaudeLLMClient(config)
    elif config.provider in (LLMProvider.DEEPSEEK, LLMProvider.QWEN, LLMProvider.OPENAI, LLMProvider.VOLCENGINE):
        # DeepSeek, Qwen, OpenAI都使用OpenAI兼容API
        return OpenAICompatibleClient(config)
    else:
        raise ValueError(f"Unknown LLM provider: {config.provider}")


def create_llm_from_env() -> LLMClient:
    """从环境变量创建LLM客户端"""
    import os
    
    provider = os.getenv("LLM_PROVIDER", "claude")
    api_key = os.getenv("LLM_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    model = os.getenv("LLM_MODEL")
    base_url = os.getenv("LLM_BASE_URL")
    
    if not api_key:
        raise ValueError("LLM_API_KEY, ANTHROPIC_API_KEY, or DEEPSEEK_API_KEY environment variable required")
    
    config = LLMConfig(
        provider=LLMProvider(provider),
        api_key=api_key,
        model=model if model else None,
        base_url=base_url,
    )
    
    return create_llm_client(config)
