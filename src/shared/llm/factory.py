"""
LLM 客户端工厂
"""

from .base import LLMClient, LLMConfig, LLMProvider
from .claude import ClaudeLLMClient


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
    elif config.provider == LLMProvider.DEEPSEEK:
        # TODO: 实现DeepSeek客户端
        raise NotImplementedError("DeepSeek client not implemented yet")
    elif config.provider == LLMProvider.QWEN:
        # TODO: 实现Qwen客户端
        raise NotImplementedError("Qwen client not implemented yet")
    elif config.provider == LLMProvider.OPENAI:
        # TODO: 实现OpenAI兼容客户端 (DeepSeek/Qwen可能用这个)
        raise NotImplementedError("OpenAI client not implemented yet")
    else:
        raise ValueError(f"Unknown LLM provider: {config.provider}")


def create_llm_from_env() -> LLMClient:
    """从环境变量创建LLM客户端"""
    import os
    
    provider = os.getenv("LLM_PROVIDER", "claude")
    api_key = os.getenv("LLM_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")
    base_url = os.getenv("LLM_BASE_URL")
    
    if not api_key:
        raise ValueError("LLM_API_KEY or ANTHROPIC_API_KEY environment variable required")
    
    config = LLMConfig(
        provider=LLMProvider(provider),
        api_key=api_key,
        model=model,
        base_url=base_url,
    )
    
    return create_llm_client(config)
