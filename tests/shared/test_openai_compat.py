"""
OpenAI兼容客户端测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.shared.llm import (
    OpenAICompatibleClient,
    LLMConfig,
    LLMProvider,
    Message,
    Tool,
)


class TestOpenAICompatibleClient:
    """OpenAI兼容客户端测试"""

    @pytest.fixture
    def deepseek_config(self):
        return LLMConfig(
            provider=LLMProvider.DEEPSEEK,
            api_key="test-api-key",
            model="deepseek-chat",
        )

    @pytest.fixture
    def qwen_config(self):
        return LLMConfig(
            provider=LLMProvider.QWEN,
            api_key="test-api-key",
            model="qwen-plus",
        )

    @pytest.fixture
    def client(self, deepseek_config):
        return OpenAICompatibleClient(deepseek_config)

    def test_deepseek_config(self, deepseek_config):
        """测试DeepSeek配置"""
        client = OpenAICompatibleClient(deepseek_config)
        assert client.base_url == "https://api.deepseek.com/v1"
        assert client.model == "deepseek-chat"
        assert "Bearer test-api-key" in client.headers["Authorization"]

    def test_qwen_config(self, qwen_config):
        """测试Qwen配置"""
        client = OpenAICompatibleClient(qwen_config)
        assert client.base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
        assert client.model == "qwen-plus"

    def test_custom_base_url(self, deepseek_config):
        """测试自定义base_url"""
        deepseek_config.base_url = "https://custom.api.com/v1"
        client = OpenAICompatibleClient(deepseek_config)
        assert client.base_url == "https://custom.api.com/v1"

    def test_convert_messages(self, client):
        """测试消息转换"""
        messages = [
            Message(role="system", content="You are helpful"),
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!"),
        ]
        converted = client._convert_messages(messages)

        assert len(converted) == 3
        assert converted[0] == {"role": "system", "content": "You are helpful"}
        assert converted[1] == {"role": "user", "content": "Hello"}
        assert converted[2] == {"role": "assistant", "content": "Hi there!"}

    def test_convert_tool_messages(self, client):
        """测试工具消息转换"""
        messages = [
            Message(role="tool", content='{"result": "ok"}', tool_call_id="call_123"),
        ]
        converted = client._convert_messages(messages)

        assert len(converted) == 1
        assert converted[0]["role"] == "tool"
        assert converted[0]["tool_call_id"] == "call_123"

    def test_convert_tools(self, client):
        """测试工具定义转换"""
        tools = [
            Tool(
                name="get_weather",
                description="Get weather info",
                parameters={
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"}
                    }
                }
            )
        ]
        converted = client._convert_tools(tools)

        assert len(converted) == 1
        assert converted[0]["type"] == "function"
        assert converted[0]["function"]["name"] == "get_weather"
        assert converted[0]["function"]["description"] == "Get weather info"

    def test_parse_response_simple(self, client):
        """测试简单响应解析"""
        data = {
            "choices": [{
                "message": {
                    "content": "Hello!"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5
            }
        }
        response = client._parse_response(data)

        assert response.content == "Hello!"
        assert response.finish_reason == "stop"
        assert response.tool_calls == []
        assert response.usage["prompt_tokens"] == 10

    def test_parse_response_with_tool_calls(self, client):
        """测试工具调用响应解析"""
        data = {
            "choices": [{
                "message": {
                    "content": None,
                    "tool_calls": [{
                        "id": "call_abc123",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"city": "Beijing"}'
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }],
            "usage": {"prompt_tokens": 20, "completion_tokens": 10}
        }
        response = client._parse_response(data)

        assert response.content is None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].id == "call_abc123"
        assert response.tool_calls[0].name == "get_weather"
        assert response.tool_calls[0].arguments == {"city": "Beijing"}
        assert response.finish_reason == "tool_calls"

    @pytest.mark.asyncio
    async def test_chat_success(self, client):
        """测试chat方法成功"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "Test response"},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            messages = [Message(role="user", content="Hello")]
            response = await client.chat(messages)

            assert response.content == "Test response"
            assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_chat_with_tools(self, client):
        """测试带工具的chat"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "function": {
                            "name": "test_tool",
                            "arguments": "{}"
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            messages = [Message(role="user", content="Test")]
            tools = [Tool(name="test_tool", description="Test", parameters={})]
            response = await client.chat(messages, tools=tools)

            assert len(response.tool_calls) == 1
            assert response.tool_calls[0].name == "test_tool"


class TestLLMFactory:
    """测试LLM工厂"""

    def test_create_deepseek_client(self):
        """测试创建DeepSeek客户端"""
        from src.shared.llm import create_llm_client, LLMConfig, LLMProvider

        config = LLMConfig(
            provider=LLMProvider.DEEPSEEK,
            api_key="test-key",
        )
        client = create_llm_client(config)

        assert isinstance(client, OpenAICompatibleClient)
        assert client.base_url == "https://api.deepseek.com/v1"

    def test_create_qwen_client(self):
        """测试创建Qwen客户端"""
        from src.shared.llm import create_llm_client, LLMConfig, LLMProvider

        config = LLMConfig(
            provider=LLMProvider.QWEN,
            api_key="test-key",
        )
        client = create_llm_client(config)

        assert isinstance(client, OpenAICompatibleClient)
        assert "dashscope" in client.base_url
