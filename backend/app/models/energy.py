"""能耗模型"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, Integer, String, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EnergyType(str, Enum):
    """能源类型枚举"""

    ELECTRICITY = "electricity"  # 电力
    WATER = "water"  # 水
    GAS = "gas"  # 燃气
    STEAM = "steam"  # 蒸汽
    COOLING = "cooling"  # 冷量
    HEATING = "heating"  # 热量


class EnergyReading(Base):
    """能耗读数模型

    存储各类能源计量表的读数。
    """

    __tablename__ = "energy_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meter_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )

    # 读数信息
    energy_type: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)

    # 位置信息
    building: Mapped[str | None] = mapped_column(String(50))
    floor: Mapped[str | None] = mapped_column(String(20))
    system_type: Mapped[str | None] = mapped_column(String(50))

    # 数据质量
    quality: Mapped[int] = mapped_column(Integer, default=100)

    __table_args__ = (
        Index("ix_energy_readings_meter_time", "meter_id", "timestamp"),
        Index("ix_energy_readings_type_time", "energy_type", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<EnergyReading(meter_id={self.meter_id}, type={self.energy_type}, value={self.value})>"
