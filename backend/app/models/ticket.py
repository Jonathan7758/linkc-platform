"""工单模型"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from .base import TimestampMixin


class TicketType(str, Enum):
    """工单类型枚举"""

    REPAIR = "repair"  # 维修
    MAINTENANCE = "maintenance"  # 保养
    INSPECTION = "inspection"  # 巡检
    INSTALLATION = "installation"  # 安装
    UPGRADE = "upgrade"  # 升级


class TicketPriority(str, Enum):
    """工单优先级枚举"""

    URGENT = "urgent"  # 紧急
    HIGH = "high"  # 高
    MEDIUM = "medium"  # 中
    LOW = "low"  # 低


class TicketStatus(str, Enum):
    """工单状态枚举"""

    PENDING = "pending"  # 待处理
    ASSIGNED = "assigned"  # 已分配
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class Ticket(Base, TimestampMixin):
    """工单模型

    存储维护工单信息。
    """

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )

    # 工单内容
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # 分类信息
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    priority: Mapped[str] = mapped_column(
        String(20), default=TicketPriority.MEDIUM.value
    )
    status: Mapped[str] = mapped_column(String(20), default=TicketStatus.PENDING.value)

    # 关联信息
    device_id: Mapped[str | None] = mapped_column(String(50), index=True)
    alarm_id: Mapped[str | None] = mapped_column(String(50), index=True)

    # 负责人信息
    created_by: Mapped[str | None] = mapped_column(String(50))
    assigned_to: Mapped[str | None] = mapped_column(String(50))

    # 时间信息
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # 工作记录
    work_notes: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<Ticket(ticket_id={self.ticket_id}, title={self.title})>"
