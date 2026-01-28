"""知识库模型"""

from enum import Enum

from sqlalchemy import Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from .base import TimestampMixin


class KnowledgeCategory(str, Enum):
    """知识分类枚举"""

    TROUBLESHOOTING = "troubleshooting"  # 故障排除
    MAINTENANCE = "maintenance"  # 维护保养
    OPERATION = "operation"  # 操作规程
    SPECIFICATION = "specification"  # 技术规格
    SAFETY = "safety"  # 安全规范
    FAQ = "faq"  # 常见问题


class KnowledgeArticle(Base, TimestampMixin):
    """知识文章模型

    存储MEP设备相关的知识库文章。
    """

    __tablename__ = "knowledge_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    knowledge_id: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )

    # 文章内容
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 分类信息
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    device_types: Mapped[list | None] = mapped_column(JSON, default=list)
    tags: Mapped[list | None] = mapped_column(JSON, default=list)

    # 向量嵌入 (用于RAG检索)
    embedding: Mapped[list | None] = mapped_column(JSON)

    # 元数据
    author: Mapped[str | None] = mapped_column(String(50))
    version: Mapped[str | None] = mapped_column(String(20), default="1.0")
    view_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return (
            f"<KnowledgeArticle(knowledge_id={self.knowledge_id}, title={self.title})>"
        )
