"""RAG服务单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.services.rag_service import (
    RAGService,
    RetrievedDocument,
    RAGContext,
    create_rag_service,
)


class TestRetrievedDocument:
    """RetrievedDocument测试"""

    def test_create_document(self):
        """测试创建文档"""
        doc = RetrievedDocument(
            doc_id="doc-001",
            title="空调维护指南",
            content="空调日常维护步骤...",
            category="maintenance",
            relevance_score=0.85,
        )
        assert doc.doc_id == "doc-001"
        assert doc.title == "空调维护指南"
        assert doc.relevance_score == 0.85

    def test_default_values(self):
        """测试默认值"""
        doc = RetrievedDocument(
            doc_id="doc-001",
            title="测试",
            content="内容",
            category="test",
        )
        assert doc.relevance_score == 0.0
        assert doc.metadata == {}


class TestRAGContext:
    """RAGContext测试"""

    def test_create_context(self):
        """测试创建上下文"""
        docs = [
            RetrievedDocument(
                doc_id="doc-001",
                title="文档1",
                content="内容1",
                category="test",
            )
        ]
        context = RAGContext(
            query="测试查询",
            documents=docs,
            augmented_prompt="增强后的提示",
        )
        assert context.query == "测试查询"
        assert len(context.documents) == 1
        assert context.augmented_prompt == "增强后的提示"


class TestRAGService:
    """RAGService测试"""

    @pytest.fixture
    def mock_db(self):
        """创建mock数据库会话"""
        return MagicMock()

    @pytest.fixture
    def rag_service(self, mock_db):
        """创建RAG服务"""
        return RAGService(mock_db)

    def test_init(self, rag_service):
        """测试初始化"""
        assert rag_service.max_documents == 5
        assert rag_service.context_template is not None

    @pytest.mark.asyncio
    async def test_retrieve_with_results(self, rag_service, mock_db):
        """测试检索有结果"""
        # Mock知识条目
        mock_item = MagicMock()
        mock_item.knowledge_id = "kb-001"
        mock_item.title = "空调故障排查"
        mock_item.content = "空调不制冷的常见原因..."
        mock_item.category = "troubleshooting"
        mock_item.tags = ["空调", "故障", "维修"]
        mock_item.created_at = datetime.now(timezone.utc)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_item]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        docs = await rag_service.retrieve("空调故障")

        assert len(docs) == 1
        assert docs[0].doc_id == "kb-001"
        assert docs[0].title == "空调故障排查"

    @pytest.mark.asyncio
    async def test_retrieve_empty_results(self, rag_service, mock_db):
        """测试检索无结果"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        docs = await rag_service.retrieve("不存在的内容")

        assert len(docs) == 0

    @pytest.mark.asyncio
    async def test_retrieve_with_category_filter(self, rag_service, mock_db):
        """测试带分类过滤的检索"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        await rag_service.retrieve("查询", category="maintenance")

        # 验证execute被调用
        mock_db.execute.assert_called_once()

    def test_calculate_relevance(self, rag_service):
        """测试相关性计算"""
        mock_item = MagicMock()
        mock_item.title = "空调维护"
        mock_item.content = "空调日常维护步骤"
        mock_item.tags = ["空调", "维护"]

        score = rag_service._calculate_relevance("空调", mock_item)

        assert score > 0
        assert score <= 1.0

    def test_calculate_relevance_no_match(self, rag_service):
        """测试无匹配的相关性"""
        mock_item = MagicMock()
        mock_item.title = "电梯维护"
        mock_item.content = "电梯维护步骤"
        mock_item.tags = ["电梯"]

        score = rag_service._calculate_relevance("空调", mock_item)

        assert score == 0.0

    def test_build_context(self, rag_service):
        """测试构建上下文"""
        docs = [
            RetrievedDocument(
                doc_id="doc-001",
                title="空调维护指南",
                content="空调日常维护步骤包括清洗滤网...",
                category="maintenance",
                relevance_score=0.9,
            ),
            RetrievedDocument(
                doc_id="doc-002",
                title="空调故障排查",
                content="空调不制冷可能的原因...",
                category="troubleshooting",
                relevance_score=0.7,
            ),
        ]

        context = rag_service.build_context("空调如何维护", docs)

        assert context.query == "空调如何维护"
        assert len(context.documents) == 2
        assert "空调维护指南" in context.augmented_prompt
        assert "空调故障排查" in context.augmented_prompt
        assert context.metadata["document_count"] == 2
        assert context.metadata["has_relevant_docs"] is True

    def test_build_context_no_docs(self, rag_service):
        """测试无文档时构建上下文"""
        context = rag_service.build_context("测试查询", [])

        assert context.query == "测试查询"
        assert len(context.documents) == 0
        assert "未找到相关文档" in context.augmented_prompt
        assert context.metadata["has_relevant_docs"] is False

    @pytest.mark.asyncio
    async def test_retrieve_and_build_context(self, rag_service, mock_db):
        """测试检索并构建上下文"""
        mock_item = MagicMock()
        mock_item.knowledge_id = "kb-001"
        mock_item.title = "测试文档"
        mock_item.content = "测试内容"
        mock_item.category = "test"
        mock_item.tags = ["测试"]
        mock_item.created_at = datetime.now(timezone.utc)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_item]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        context = await rag_service.retrieve_and_build_context("测试")

        assert isinstance(context, RAGContext)
        assert context.query == "测试"
        assert len(context.documents) >= 0


class TestCreateRAGService:
    """create_rag_service测试"""

    def test_create_service(self):
        """测试创建服务"""
        mock_db = MagicMock()
        service = create_rag_service(mock_db)

        assert isinstance(service, RAGService)
        assert service.db_session == mock_db
