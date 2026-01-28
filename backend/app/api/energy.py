"""能耗API"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.mcp_servers.energy_mcp import EnergyMCPServer
from app.schemas.energy import (
    EnergyConsumptionResponse,
    EnergyTrendResponse,
    EnergyComparisonResponse,
    EnergyRankingResponse,
    EnergyAnomalyResponse,
)
from app.schemas.response import APIResponse, success_response

router = APIRouter(prefix="/api/v1/energy", tags=["energy"])


@router.get("/consumption", response_model=APIResponse[EnergyConsumptionResponse])
async def get_energy_consumption(
    energy_type: str | None = None,
    building: str | None = None,
    system_type: str | None = None,
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_async_session),
):
    """获取能耗数据"""
    mcp = EnergyMCPServer(db)
    result = await mcp._get_energy_consumption({
        "energy_type": energy_type,
        "building": building,
        "system_type": system_type,
        "hours": hours,
    })

    return success_response(data=EnergyConsumptionResponse(**result))


@router.get("/trend", response_model=APIResponse[EnergyTrendResponse])
async def get_energy_trend(
    energy_type: str = Query("electricity", pattern="^(electricity|water|gas)$"),
    building: str | None = None,
    period: str = Query("day", pattern="^(hour|day|week)$"),
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_async_session),
):
    """获取能耗趋势"""
    mcp = EnergyMCPServer(db)
    result = await mcp._get_energy_trend({
        "energy_type": energy_type,
        "building": building,
        "period": period,
        "days": days,
    })

    return success_response(data=EnergyTrendResponse(**result))


@router.get("/comparison", response_model=APIResponse[EnergyComparisonResponse])
async def get_energy_comparison(
    energy_type: str = Query("electricity", pattern="^(electricity|water|gas)$"),
    building: str | None = None,
    compare_type: str = Query("mom", pattern="^(yoy|mom|wow)$"),
    db: AsyncSession = Depends(get_async_session),
):
    """获取能耗同比环比"""
    mcp = EnergyMCPServer(db)
    result = await mcp._get_energy_comparison({
        "energy_type": energy_type,
        "building": building,
        "compare_type": compare_type,
    })

    return success_response(data=EnergyComparisonResponse(**result))


@router.get("/ranking", response_model=APIResponse[EnergyRankingResponse])
async def get_energy_ranking(
    energy_type: str = Query("electricity", pattern="^(electricity|water|gas)$"),
    group_by: str = Query("building", pattern="^(building|floor|system_type)$"),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_async_session),
):
    """获取能耗排名"""
    mcp = EnergyMCPServer(db)
    result = await mcp._get_energy_ranking({
        "energy_type": energy_type,
        "group_by": group_by,
        "days": days,
        "limit": limit,
    })

    return success_response(data=EnergyRankingResponse(**result))


@router.get("/anomaly", response_model=APIResponse[EnergyAnomalyResponse])
async def get_energy_anomaly(
    building: str | None = None,
    threshold: float = Query(1.5, ge=1.0, le=5.0),
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_async_session),
):
    """检测能耗异常"""
    mcp = EnergyMCPServer(db)
    result = await mcp._get_energy_anomaly({
        "building": building,
        "threshold": threshold,
        "hours": hours,
    })

    return success_response(data=EnergyAnomalyResponse(**result))
