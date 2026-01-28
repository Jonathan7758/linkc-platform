"""告警相关Schema"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AlarmResponse(BaseModel):
    """告警响应"""

    alarm_id: str
    title: str
    description: str | None = None
    severity: str
    status: str
    category: str | None = None
    device_id: str | None = None
    triggered_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None

    class Config:
        from_attributes = True


class AlarmListResponse(BaseModel):
    """告警列表响应"""

    alarms: list[AlarmResponse]
    total: int


class AlarmAcknowledgeRequest(BaseModel):
    """确认告警请求"""

    comment: str | None = None


class AlarmResolveRequest(BaseModel):
    """解决告警请求"""

    resolution: str = Field(..., min_length=1, max_length=1000)
    comment: str | None = None


class AlarmStatsResponse(BaseModel):
    """告警统计响应"""

    group_by: str
    period_hours: int
    total: int
    active_count: int
    critical_count: int
    statistics: dict[str, int]


class AlarmSuggestion(BaseModel):
    """处理建议"""

    step: int
    action: str


class AlarmSuggestionResponse(BaseModel):
    """处理建议响应"""

    alarm_id: str
    alarm_title: str
    category: str | None
    suggestions: list[AlarmSuggestion]
    related_knowledge: list[Any] = []


class AlarmDetailResponse(BaseModel):
    """告警详情响应"""

    alarm_id: str
    title: str
    description: str | None = None
    severity: str
    status: str
    category: str | None = None
    device: dict[str, Any] | None = None
    trigger_value: float | None = None
    threshold_value: float | None = None
    trigger_parameter: str | None = None
    triggered_at: str | None = None
    acknowledged_at: str | None = None
    acknowledged_by: str | None = None
    resolved_at: str | None = None
    resolved_by: str | None = None
    resolution_notes: str | None = None
