"""对话模型"""

from enum import Enum

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from .base import TimestampMixin


class MessageRole(str, Enum):
    """消息角色枚举"""

    USER = "user"  # 用户
    ASSISTANT = "assistant"  # 助手
    TOOL = "tool"  # 工具
    SYSTEM = "system"  # 系统


class Conversation(Base, TimestampMixin):
    """对话模型

    存储对话会话信息。
    """

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )

    # 会话信息
    user_id: Mapped[str | None] = mapped_column(String(50), index=True)
    title: Mapped[str | None] = mapped_column(String(200))

    # 统计信息
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    # 上下文数据
    context: Mapped[dict | None] = mapped_column(JSON, default=dict)

    # 关联消息
    messages: Mapped[list["ConversationMessage"]] = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Conversation(conversation_id={self.conversation_id}, title={self.title})>"


class ConversationMessage(Base, TimestampMixin):
    """对话消息模型

    存储对话中的单条消息。
    """

    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )

    # 关联会话
    conversation_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # 消息内容
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)

    # 工具调用记录
    tool_calls: Mapped[list | None] = mapped_column(JSON)
    tool_call_id: Mapped[str | None] = mapped_column(String(50))

    # 关联会话
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return f"<ConversationMessage(message_id={self.message_id}, role={self.role})>"
