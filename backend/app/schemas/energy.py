"""能耗相关Schema"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class EnergyReadingItem(BaseModel):
    """能耗读数项"""
    meter_id: str
    energy_type: str
    value: float
    unit: str
    building: str | None = None
    timestamp: str | None = None


class EnergyConsumptionResponse(BaseModel):
    """能耗消耗响应"""
    period_hours: int
    total_readings: int
    total_consumption: float
    average_consumption: float
    by_type: dict[str, float]
    readings: list[EnergyReadingItem]


class EnergyTrendPoint(BaseModel):
    """趋势数据点"""
    period: str
    value: float


class EnergyTrendResponse(BaseModel):
    """能耗趋势响应"""
    energy_type: str
    building: str | None = None
    period: str
    days: int
    data_points: int
    trend: list[EnergyTrendPoint]


class EnergyPeriod(BaseModel):
    """能耗周期"""
    start: str
    end: str
    value: float


class EnergyComparisonResponse(BaseModel):
    """能耗对比响应"""
    energy_type: str
    building: str | None = None
    compare_type: str
    current_period: EnergyPeriod
    previous_period: EnergyPeriod
    change_rate: float
    trend: str


class EnergyRankItem(BaseModel):
    """能耗排名项"""
    rank: int
    name: str
    consumption: float


class EnergyRankingResponse(BaseModel):
    """能耗排名响应"""
    energy_type: str
    group_by: str
    period_days: int
    ranking: list[EnergyRankItem]


class EnergyAnomalyItem(BaseModel):
    """异常项"""
    meter_id: str
    energy_type: str
    value: float
    average: float
    ratio: float
    building: str | None = None
    timestamp: str | None = None


class EnergyAnomalyResponse(BaseModel):
    """能耗异常响应"""
    period_hours: int
    threshold: float
    total_readings: int
    anomaly_count: int
    anomalies: list[EnergyAnomalyItem]
    averages: dict[str, float]
    message: str | None = None
