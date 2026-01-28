"""知识库MCP Server"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeArticle
from .base_mcp_server import (
    BaseMCPServer,
    MCPServerType,
    MCPTool,
    ToolParameter,
)


class KnowledgeMCPServer(BaseMCPServer):
    """知识库MCP Server"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        super().__init__(MCPServerType.KNOWLEDGE)

    def _register_tools(self) -> None:
        """注册知识库工具"""

        # 1. 搜索知识
        self.register_tool(
            MCPTool(
                name="search_knowledge",
                description="搜索知识库，查找相关的故障处理、维护保养、操作规程等知识",
                parameters=[
                    ToolParameter(
                        name="query",
                        type="string",
                        description="搜索关键词，如 '冷水机组故障'、'空调维护'",
                        required=True,
                    ),
                    ToolParameter(
                        name="category",
                        type="string",
                        description="知识分类",
                        required=False,
                        enum=[
                            "troubleshooting",
                            "maintenance",
                            "operation",
                            "specification",
                            "safety",
                            "faq",
                        ],
                    ),
                    ToolParameter(
                        name="limit",
                        type="integer",
                        description="返回数量，默认5",
                        required=False,
                        default=5,
                    ),
                ],
                handler=self._search_knowledge,
            )
        )

        # 2. 获取知识详情
        self.register_tool(
            MCPTool(
                name="get_knowledge_detail",
                description="获取知识文章的详细内容",
                parameters=[
                    ToolParameter(
                        name="knowledge_id",
                        type="string",
                        description="知识文章ID",
                        required=True,
                    )
                ],
                handler=self._get_knowledge_detail,
            )
        )

        # 3. 获取相关知识
        self.register_tool(
            MCPTool(
                name="get_related_knowledge",
                description="获取与指定知识相关的其他知识文章",
                parameters=[
                    ToolParameter(
                        name="knowledge_id",
                        type="string",
                        description="知识文章ID",
                        required=True,
                    ),
                    ToolParameter(
                        name="limit",
                        type="integer",
                        description="返回数量，默认3",
                        required=False,
                        default=3,
                    ),
                ],
                handler=self._get_related_knowledge,
            )
        )

    async def _search_knowledge(self, args: dict) -> dict:
        """搜索知识库（MVP：关键词匹配）"""
        query = args["query"]
        category = args.get("category")
        limit = args.get("limit", 5)

        # MVP阶段：简单关键词匹配
        keywords = query.split()

        stmt = select(KnowledgeArticle)

        if category:
            stmt = stmt.where(KnowledgeArticle.category == category)

        result = await self.db.execute(stmt)
        articles = result.scalars().all()

        # 简单匹配评分
        scored = []
        for article in articles:
            score = 0
            text = f"{article.title} {article.summary or ''} {article.content}".lower()
            for kw in keywords:
                if kw.lower() in text:
                    score += 1
            if score > 0:
                scored.append((score, article))

        # 排序取前N
        scored.sort(key=lambda x: x[0], reverse=True)
        top_articles = scored[:limit]

        return {
            "query": query,
            "total": len(top_articles),
            "results": [
                {
                    "knowledge_id": a.knowledge_id,
                    "title": a.title,
                    "summary": a.summary,
                    "category": a.category if isinstance(a.category, str) else a.category,
                    "relevance": "high" if s > 2 else "medium",
                }
                for s, a in top_articles
            ],
        }

    async def _get_knowledge_detail(self, args: dict) -> dict:
        """获取知识详情"""
        knowledge_id = args["knowledge_id"]

        result = await self.db.execute(
            select(KnowledgeArticle).where(
                KnowledgeArticle.knowledge_id == knowledge_id
            )
        )
        article = result.scalar_one_or_none()

        if not article:
            return {"error": f"知识文章 {knowledge_id} 不存在"}

        return {
            "knowledge_id": article.knowledge_id,
            "title": article.title,
            "category": article.category if isinstance(article.category, str) else article.category,
            "content": article.content,
            "tags": article.tags,
            "device_types": article.device_types,
        }

    async def _get_related_knowledge(self, args: dict) -> dict:
        """获取相关知识（MVP：同分类）"""
        knowledge_id = args["knowledge_id"]
        limit = args.get("limit", 3)

        # 先获取当前文章
        result = await self.db.execute(
            select(KnowledgeArticle).where(
                KnowledgeArticle.knowledge_id == knowledge_id
            )
        )
        article = result.scalar_one_or_none()

        if not article:
            return {"error": f"知识文章 {knowledge_id} 不存在"}

        # 获取同分类的其他文章
        result = await self.db.execute(
            select(KnowledgeArticle)
            .where(
                KnowledgeArticle.category == article.category,
                KnowledgeArticle.knowledge_id != knowledge_id,
            )
            .limit(limit)
        )
        related = result.scalars().all()

        return {
            "knowledge_id": knowledge_id,
            "related": [
                {
                    "knowledge_id": a.knowledge_id,
                    "title": a.title,
                    "summary": a.summary,
                }
                for a in related
            ],
        }
