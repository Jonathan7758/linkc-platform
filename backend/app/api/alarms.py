"""告警API"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.alarm import Alarm, AlarmStatus, AlarmSeverity
from app.mcp_servers.alarm_mcp import AlarmMCPServer
from app.schemas.alarm import (
    AlarmResponse,
    AlarmListResponse,
    AlarmAcknowledgeRequest,
    AlarmResolveRequest,
    AlarmStatsResponse,
    AlarmSuggestionResponse,
    AlarmDetailResponse,
)
from app.schemas.response import APIResponse, success_response, error_response, ErrorCodes

router = APIRouter(prefix="/api/v1/alarms", tags=["alarms"])


@router.get("", response_model=APIResponse[AlarmListResponse])
async def get_alarms(
    status: str | None = None,
    severity: str | None = None,
    device_id: str | None = None,
    hours: int = Query(24, ge=1, le=720),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session),
):
    """获取告警列表"""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = select(Alarm).where(Alarm.triggered_at >= since)

    if status:
        query = query.where(Alarm.status == status)
    if severity:
        query = query.where(Alarm.severity == severity)
    if device_id:
        query = query.where(Alarm.device_id == device_id)

    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # 分页
    query = query.order_by(Alarm.triggered_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    alarms = result.scalars().all()

    return success_response(
        data=AlarmListResponse(
            alarms=[
                AlarmResponse(
                    alarm_id=a.alarm_id,
                    title=a.title,
                    description=a.description,
                    severity=a.severity,
                    status=a.status,
                    category=a.category,
                    device_id=a.device_id,
                    triggered_at=a.triggered_at,
                    acknowledged_at=a.acknowledged_at,
                    resolved_at=a.resolved_at,
                )
                for a in alarms
            ],
            total=total,
        )
    )


@router.get("/stats", response_model=APIResponse[AlarmStatsResponse])
async def get_alarm_stats(
    group_by: str = Query("severity", pattern="^(severity|status|category)$"),
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_async_session),
):
    """获取告警统计"""
    mcp = AlarmMCPServer(db)
    result = await mcp._get_alarm_stats({"group_by": group_by, "hours": hours})

    return success_response(
        data=AlarmStatsResponse(
            group_by=result["group_by"],
            period_hours=result["period_hours"],
            total=result["total"],
            active_count=result["active_count"],
            critical_count=result["critical_count"],
            statistics=result["statistics"],
        )
    )


@router.get("/{alarm_id}", response_model=APIResponse[AlarmDetailResponse])
async def get_alarm_detail(
    alarm_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    """获取告警详情"""
    mcp = AlarmMCPServer(db)
    result = await mcp._get_alarm_detail({"alarm_id": alarm_id})

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return success_response(data=AlarmDetailResponse(**result))


@router.post("/{alarm_id}/acknowledge", response_model=APIResponse[dict])
async def acknowledge_alarm(
    alarm_id: str,
    request: AlarmAcknowledgeRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """确认告警"""
    mcp = AlarmMCPServer(db)
    result = await mcp._acknowledge_alarm({
        "alarm_id": alarm_id,
        "comment": request.comment,
    })

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return success_response(data=result)


@router.post("/{alarm_id}/resolve", response_model=APIResponse[dict])
async def resolve_alarm(
    alarm_id: str,
    request: AlarmResolveRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """解决告警"""
    mcp = AlarmMCPServer(db)
    result = await mcp._resolve_alarm({
        "alarm_id": alarm_id,
        "resolution": request.resolution,
        "comment": request.comment,
    })

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return success_response(data=result)


@router.get("/{alarm_id}/suggestions", response_model=APIResponse[AlarmSuggestionResponse])
async def get_alarm_suggestions(
    alarm_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    """获取处理建议"""
    mcp = AlarmMCPServer(db)
    result = await mcp._get_alarm_suggestions({"alarm_id": alarm_id})

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return success_response(
        data=AlarmSuggestionResponse(
            alarm_id=result["alarm_id"],
            alarm_title=result["alarm_title"],
            category=result["category"],
            suggestions=[
                {"step": s["step"], "action": s["action"]}
                for s in result["suggestions"]
            ],
            related_knowledge=result.get("related_knowledge", []),
        )
    )
