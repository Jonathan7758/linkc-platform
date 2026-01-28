"""设备模型"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, Integer, JSON, String, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from .base import TimestampMixin


class DeviceType(str, Enum):
    """设备类型枚举"""

    CHILLER = "chiller"  # 冷水机组
    AHU = "ahu"  # 空调机组
    FCU = "fcu"  # 风机盘管
    PUMP = "pump"  # 水泵
    COOLING_TOWER = "cooling_tower"  # 冷却塔
    VAV = "vav"  # 变风量末端
    TRANSFORMER = "transformer"  # 变压器
    METER = "meter"  # 电表
    ELEVATOR = "elevator"  # 电梯
    SENSOR = "sensor"  # 传感器
    OTHER = "other"  # 其他


class SystemType(str, Enum):
    """系统类型枚举"""

    HVAC = "hvac"  # 暖通空调
    ELECTRICAL = "electrical"  # 电气
    PLUMBING = "plumbing"  # 给排水
    FIRE_PROTECTION = "fire_protection"  # 消防
    SECURITY = "security"  # 安防
    ELEVATOR = "elevator"  # 电梯
    BMS = "bms"  # 楼宇自控


class DeviceStatus(str, Enum):
    """设备状态枚举"""

    RUNNING = "running"  # 运行中
    STOPPED = "stopped"  # 已停止
    FAULT = "fault"  # 故障
    MAINTENANCE = "maintenance"  # 维护中
    OFFLINE = "offline"  # 离线


class Device(Base, TimestampMixin):
    """设备模型

    存储MEP设备的基础信息和配置。
    """

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    system: Mapped[str] = mapped_column(String(50), nullable=False)

    # 位置信息
    building: Mapped[str | None] = mapped_column(String(50))
    floor: Mapped[str | None] = mapped_column(String(20))
    zone: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(200))

    # 状态信息
    status: Mapped[str] = mapped_column(String(20), default=DeviceStatus.STOPPED.value)
    health_score: Mapped[int] = mapped_column(Integer, default=100)

    # 设备规格
    manufacturer: Mapped[str | None] = mapped_column(String(100))
    model_number: Mapped[str | None] = mapped_column(String(100))

    # JSON字段
    parameters: Mapped[dict | None] = mapped_column(JSON, default=dict)
    thresholds: Mapped[dict | None] = mapped_column(JSON, default=dict)

    __table_args__ = (
        Index("ix_devices_type_status", "type", "status"),
        Index("ix_devices_system_building", "system", "building"),
    )

    def __repr__(self) -> str:
        return f"<Device(device_id={self.device_id}, name={self.name})>"


class DeviceReading(Base):
    """设备读数模型

    存储设备的实时参数读数。
    """

    __tablename__ = "device_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    parameter: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20))
    quality: Mapped[int] = mapped_column(Integer, default=100)

    __table_args__ = (
        Index("ix_device_readings_device_time", "device_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<DeviceReading(device_id={self.device_id}, parameter={self.parameter}, value={self.value})>"
