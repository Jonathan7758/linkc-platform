"""告警模型"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from .base import TimestampMixin


class AlarmSeverity(str, Enum):
    """告警级别枚举"""

    CRITICAL = "critical"  # 紧急
    MAJOR = "major"  # 重要
    MINOR = "minor"  # 次要
    WARNING = "warning"  # 警告


class AlarmStatus(str, Enum):
    """告警状态枚举"""

    ACTIVE = "active"  # 活动
    ACKNOWLEDGED = "acknowledged"  # 已确认
    RESOLVED = "resolved"  # 已解决
    CLOSED = "closed"  # 已关闭


class AlarmCategory(str, Enum):
    """告警分类枚举"""

    FAULT = "fault"  # 故障
    THRESHOLD = "threshold"  # 阈值超限
    OFFLINE = "offline"  # 离线
    MAINTENANCE = "maintenance"  # 维护
    EFFICIENCY = "efficiency"  # 效率异常
    SECURITY = "security"  # 安全


class Alarm(Base, TimestampMixin):
    """告警模型

    存储设备告警信息。
    """

    __tablename__ = "alarms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alarm_id: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    device_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)

    # 告警内容
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # 告警分类
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=AlarmStatus.ACTIVE.value)
    category: Mapped[str | None] = mapped_column(String(20))

    # 时间信息
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_by: Mapped[str | None] = mapped_column(String(50))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[str | None] = mapped_column(String(50))

    # 触发条件
    trigger_value: Mapped[float | None] = mapped_column(Float)
    threshold_value: Mapped[float | None] = mapped_column(Float)
    trigger_parameter: Mapped[str | None] = mapped_column(String(50))

    # 处理信息
    resolution_notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("ix_alarms_status_severity", "status", "severity"),
        Index("ix_alarms_triggered_at", "triggered_at"),
    )

    def __repr__(self) -> str:
        return f"<Alarm(alarm_id={self.alarm_id}, title={self.title}, severity={self.severity})>"
