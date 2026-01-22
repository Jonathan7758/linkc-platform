"""
G6: 数据查询API - 路由层
============================
"""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status

from .models import (
    Granularity, ComparisonRequest, ExportRequest,
    KPIOverviewResponse, EfficiencyTrendResponse, UtilizationResponse,
    CoverageAnalysisResponse, TaskStatisticsResponse, AlertStatisticsResponse,
    ComparisonResponse, ExportCreateResponse, ExportStatusResponse,
    DashboardRealtimeResponse
)
from .service import DataService

router = APIRouter(prefix="/api/v1/data", tags=["data"])

# 单例服务实例
_data_service: DataService = None


def get_data_service() -> DataService:
    """获取数据服务实例（单例）"""
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service


def get_tenant_id() -> str:
    """获取租户ID"""
    return "tenant_001"


# ============================================================
# KPI概览
# ============================================================

@router.get("/kpi/overview", response_model=KPIOverviewResponse)
async def get_kpi_overview(
    building_id: Optional[str] = Query(None, description="楼宇ID"),
    query_date: Optional[date] = Query(None, alias="date", description="统计日期"),
    tenant_id: str = Depends(get_tenant_id),
    service: DataService = Depends(get_data_service)
):
    """
    获取关键KPI指标概览

    返回清洁、机器人、告警、Agent等维度的KPI数据
    """
    return await service.get_kpi_overview(tenant_id, building_id, query_date)


# ============================================================
# 效率趋势
# ============================================================

@router.get("/efficiency/trend", response_model=EfficiencyTrendResponse)
async def get_efficiency_trend(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    building_id: Optional[str] = Query(None, description="楼宇ID"),
    granularity: Granularity = Query(Granularity.DAY, description="时间粒度"),
    robot_id: Optional[str] = Query(None, description="机器人ID"),
    tenant_id: str = Depends(get_tenant_id),
    service: DataService = Depends(get_data_service)
):
    """
    获取清洁效率趋势数据

    支持按天、周、月等粒度查询
    """
    return await service.get_efficiency_trend(
        tenant_id, start_date, end_date, building_id, granularity, robot_id
    )


# ============================================================
# 机器人利用率
# ============================================================

@router.get("/robots/utilization", response_model=UtilizationResponse)
async def get_robot_utilization(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    building_id: Optional[str] = Query(None, description="楼宇ID"),
    granularity: Granularity = Query(Granularity.DAY, description="时间粒度"),
    tenant_id: str = Depends(get_tenant_id),
    service: DataService = Depends(get_data_service)
):
    """
    获取机器人利用率数据

    包括各机器人利用率和小时分布
    """
    return await service.get_utilization(
        tenant_id, start_date, end_date, building_id, granularity
    )


# ============================================================
# 区域覆盖分析
# ============================================================

@router.get("/coverage/analysis", response_model=CoverageAnalysisResponse)
async def get_coverage_analysis(
    building_id: str = Query(..., description="楼宇ID"),
    floor_id: Optional[str] = Query(None, description="楼层ID"),
    query_date: Optional[date] = Query(None, alias="date", description="统计日期"),
    tenant_id: str = Depends(get_tenant_id),
    service: DataService = Depends(get_data_service)
):
    """
    获取区域清洁覆盖分析

    按楼层和区域展示覆盖率
    """
    return await service.get_coverage_analysis(
        tenant_id, building_id, floor_id, query_date
    )


# ============================================================
# 任务统计
# ============================================================

@router.get("/tasks/statistics", response_model=TaskStatisticsResponse)
async def get_task_statistics(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    building_id: Optional[str] = Query(None, description="楼宇ID"),
    tenant_id: str = Depends(get_tenant_id),
    service: DataService = Depends(get_data_service)
):
    """
    获取任务执行统计

    包括完成率、失败原因分布等
    """
    return await service.get_task_statistics(
        tenant_id, start_date, end_date, building_id
    )


# ============================================================
# 告警统计
# ============================================================

@router.get("/alerts/statistics", response_model=AlertStatisticsResponse)
async def get_alert_statistics(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    tenant_id: str = Depends(get_tenant_id),
    service: DataService = Depends(get_data_service)
):
    """
    获取告警统计数据

    包括告警趋势和Top机器人
    """
    return await service.get_alert_statistics(tenant_id, start_date, end_date)


# ============================================================
# 对比分析
# ============================================================

@router.post("/comparison", response_model=ComparisonResponse)
async def compare_data(
    request: ComparisonRequest,
    service: DataService = Depends(get_data_service)
):
    """
    多维度对比分析

    支持机器人、楼层、时间段对比
    """
    return await service.compare_data(request)


# ============================================================
# 导出
# ============================================================

@router.post("/export", response_model=ExportCreateResponse)
async def create_export(
    request: ExportRequest,
    service: DataService = Depends(get_data_service)
):
    """
    导出数据报表

    支持Excel、CSV、PDF格式
    """
    return await service.create_export(request)


@router.get("/export/{export_id}", response_model=ExportStatusResponse)
async def get_export_status(
    export_id: str,
    service: DataService = Depends(get_data_service)
):
    """
    获取导出任务状态

    返回下载链接（如果已完成）
    """
    result = await service.get_export_status(export_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export {export_id} not found"
        )
    return result


# ============================================================
# 实时仪表板
# ============================================================

@router.get("/dashboard/realtime", response_model=DashboardRealtimeResponse)
async def get_realtime_dashboard(
    building_id: Optional[str] = Query(None, description="楼宇ID"),
    tenant_id: str = Depends(get_tenant_id),
    service: DataService = Depends(get_data_service)
):
    """
    获取实时仪表板数据

    用于自动刷新的仪表板
    """
    return await service.get_realtime_dashboard(tenant_id, building_id)
