"""Schema模块"""
from app.schemas.response import (
    ErrorDetail,
    APIResponse,
    PaginationInfo,
    PaginatedResponse,
    ErrorCodes,
    ERROR_MESSAGES,
    success_response,
    error_response,
)
from app.schemas.energy import (
    EnergyReadingItem,
    EnergyConsumptionResponse,
    EnergyTrendPoint,
    EnergyTrendResponse,
    EnergyPeriod,
    EnergyComparisonResponse,
    EnergyRankItem,
    EnergyRankingResponse,
    EnergyAnomalyItem,
    EnergyAnomalyResponse,
)
from app.schemas.alarm import (
    AlarmResponse,
    AlarmListResponse,
    AlarmAcknowledgeRequest,
    AlarmResolveRequest,
    AlarmStatsResponse,
    AlarmSuggestionResponse,
    AlarmDetailResponse,
)

__all__ = [
    # Response schemas
    "ErrorDetail",
    "APIResponse",
    "PaginationInfo",
    "PaginatedResponse",
    "ErrorCodes",
    "ERROR_MESSAGES",
    "success_response",
    "error_response",
    # Energy schemas
    "EnergyReadingItem",
    "EnergyConsumptionResponse",
    "EnergyTrendPoint",
    "EnergyTrendResponse",
    "EnergyPeriod",
    "EnergyComparisonResponse",
    "EnergyRankItem",
    "EnergyRankingResponse",
    "EnergyAnomalyItem",
    "EnergyAnomalyResponse",
    # Alarm schemas
    "AlarmResponse",
    "AlarmListResponse",
    "AlarmAcknowledgeRequest",
    "AlarmResolveRequest",
    "AlarmStatsResponse",
    "AlarmSuggestionResponse",
    "AlarmDetailResponse",
]
