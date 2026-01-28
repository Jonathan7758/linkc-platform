"""知识库MCP单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.mcp_servers.knowledge_mcp import KnowledgeMCPServer
from app.mcp_servers.base_mcp_server import MCPServerType, MCPToolCall


class TestKnowledgeMCPServer:
    """KnowledgeMCPServer测试"""

    def test_server_type(self):
        """测试服务器类型"""
        mock_session = MagicMock()
        server = KnowledgeMCPServer(mock_session)
        assert server.server_type == MCPServerType.KNOWLEDGE

    def test_tools_registered(self):
        """测试工具注册"""
        mock_session = MagicMock()
        server = KnowledgeMCPServer(mock_session)
        tools = server.get_tools()
        tool_names = [t.name for t in tools]

        assert "search_knowledge" in tool_names
        assert "get_knowledge_detail" in tool_names
        assert "get_related_knowledge" in tool_names
        assert len(tools) == 3


class TestSearchKnowledge:
    """search_knowledge工具测试"""

    @pytest.mark.asyncio
    async def test_search_with_results(self):
        """测试搜索有结果"""
        mock_session = MagicMock()
        mock_article = MagicMock()
        mock_article.knowledge_id = "KB-001"
        mock_article.title = "冷水机组故障排除指南"
        mock_article.summary = "冷水机组常见故障及处理方法"
        mock_article.content = "冷水机组故障处理步骤..."
        mock_article.category = "troubleshooting"

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_article]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        server = KnowledgeMCPServer(mock_session)
        result = await server.call_tool(
            MCPToolCall(
                call_id="123",
                tool_name="search_knowledge",
                arguments={"query": "冷水机组故障"},
            )
        )

        assert result.success is True
        assert result.result["total"] == 1
        assert result.result["results"][0]["knowledge_id"] == "KB-001"

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """测试搜索无结果"""
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        server = KnowledgeMCPServer(mock_session)
        result = await server.call_tool(
            MCPToolCall(
                call_id="123",
                tool_name="search_knowledge",
                arguments={"query": "不存在的内容"},
            )
        )

        assert result.success is True
        assert result.result["total"] == 0


class TestGetKnowledgeDetail:
    """get_knowledge_detail工具测试"""

    @pytest.mark.asyncio
    async def test_article_found(self):
        """测试文章存在"""
        mock_session = MagicMock()
        mock_article = MagicMock()
        mock_article.knowledge_id = "KB-001"
        mock_article.title = "冷水机组故障排除指南"
        mock_article.category = "troubleshooting"
        mock_article.content = "详细内容..."
        mock_article.tags = ["冷水机", "故障"]
        mock_article.device_types = ["chiller"]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_article
        mock_session.execute = AsyncMock(return_value=mock_result)

        server = KnowledgeMCPServer(mock_session)
        result = await server.call_tool(
            MCPToolCall(
                call_id="123",
                tool_name="get_knowledge_detail",
                arguments={"knowledge_id": "KB-001"},
            )
        )

        assert result.success is True
        assert result.result["knowledge_id"] == "KB-001"
        assert result.result["title"] == "冷水机组故障排除指南"

    @pytest.mark.asyncio
    async def test_article_not_found(self):
        """测试文章不存在"""
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        server = KnowledgeMCPServer(mock_session)
        result = await server.call_tool(
            MCPToolCall(
                call_id="123",
                tool_name="get_knowledge_detail",
                arguments={"knowledge_id": "INVALID"},
            )
        )

        assert result.success is True
        assert "error" in result.result
