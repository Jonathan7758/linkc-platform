"""
DM1: 演示数据API路由 (Demo Data API Router)

提供演示数据管理的API端点:
- POST /api/v1/demo/init - 初始化演示数据
- POST /api/v1/demo/reset - 重置演示
- POST /api/v1/demo/scenario - 切换场景
- POST /api/v1/demo/trigger - 触发事件
- GET /api/v1/demo/status - 获取状态
- GET /api/v1/demo/buildings - 获取楼宇
- GET /api/v1/demo/robots - 获取机器人
- GET /api/v1/demo/tasks - 获取任务
- GET /api/v1/demo/kpi - 获取KPI数据
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from enum import Enum
from datetime import datetime

router = APIRouter(prefix="/demo", tags=["demo"])


# ==================== Pydantic 模型 ====================

class DemoScenarioEnum(str, Enum):
    """演示场景"""
    executive = "executive"
    ops_normal = "ops_normal"
    ops_alert = "ops_alert"
    agent_chat = "agent_chat"
    full = "full"


class DemoEventEnum(str, Enum):
    """演示事件"""
    low_battery = "low_battery"
    obstacle = "obstacle"
    task_done = "task_done"
    urgent_task = "urgent_task"
    robot_error = "robot_error"
    charging_done = "charging_done"


class InitDemoRequest(BaseModel):
    """初始化演示请求"""
    scenario: DemoScenarioEnum = Field(default=DemoScenarioEnum.full, description="演示场景")


class SwitchScenarioRequest(BaseModel):
    """切换场景请求"""
    scenario: DemoScenarioEnum = Field(..., description="目标场景")


class TriggerEventRequest(BaseModel):
    """触发事件请求"""
    event: DemoEventEnum = Field(..., description="事件类型")
    robot_id: Optional[str] = Field(None, description="目标机器人ID")


class SetSpeedRequest(BaseModel):
    """设置模拟速度请求"""
    speed: float = Field(..., ge=0.1, le=10, description="模拟速度倍率 (0.1-10)")


class SetAutoEventsRequest(BaseModel):
    """设置自动事件请求"""
    enabled: bool = Field(..., description="是否启用自动事件")


# ==================== 演示数据存储 (内存) ====================

# 导入演示服务 (延迟导入避免循环依赖)
_demo_service = None

def get_demo_service():
    """获取演示服务实例"""
    global _demo_service
    if _demo_service is None:
        from src.demo.data_service import demo_service
        _demo_service = demo_service
    return _demo_service


# ==================== API 端点 ====================

@router.post("/init")
async def init_demo(request: InitDemoRequest):
    """
    初始化演示数据

    加载指定场景的演示数据，包括:
    - 3个楼宇
    - 8台机器人
    - 500+历史任务
    - KPI数据
    """
    service = get_demo_service()
    from src.demo.scenarios import DemoScenario

    # 转换枚举
    scenario_map = {
        DemoScenarioEnum.executive: DemoScenario.EXECUTIVE_OVERVIEW,
        DemoScenarioEnum.ops_normal: DemoScenario.OPERATIONS_NORMAL,
        DemoScenarioEnum.ops_alert: DemoScenario.OPERATIONS_ALERT,
        DemoScenarioEnum.agent_chat: DemoScenario.AGENT_CONVERSATION,
        DemoScenarioEnum.full: DemoScenario.FULL_DEMO
    }

    result = await service.init_demo_data(scenario_map[request.scenario])

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

    return result


@router.post("/reset")
async def reset_demo():
    """
    重置演示数据

    将演示数据重置到初始状态
    """
    service = get_demo_service()
    result = await service.reset_demo()

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

    return result


@router.post("/scenario")
async def switch_scenario(request: SwitchScenarioRequest):
    """
    切换演示场景

    可用场景:
    - executive: 高管视角
    - ops_normal: 运营视角(正常)
    - ops_alert: 运营视角(告警)
    - agent_chat: AI协作
    - full: 完整演示
    """
    service = get_demo_service()
    from src.demo.scenarios import DemoScenario

    scenario_map = {
        DemoScenarioEnum.executive: DemoScenario.EXECUTIVE_OVERVIEW,
        DemoScenarioEnum.ops_normal: DemoScenario.OPERATIONS_NORMAL,
        DemoScenarioEnum.ops_alert: DemoScenario.OPERATIONS_ALERT,
        DemoScenarioEnum.agent_chat: DemoScenario.AGENT_CONVERSATION,
        DemoScenarioEnum.full: DemoScenario.FULL_DEMO
    }

    result = await service.switch_scenario(scenario_map[request.scenario])

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

    return result


@router.post("/trigger")
async def trigger_event(request: TriggerEventRequest):
    """
    触发演示事件

    可用事件:
    - low_battery: 机器人电量低
    - obstacle: 遇到障碍物
    - task_done: 任务完成
    - urgent_task: 紧急任务
    - robot_error: 机器人故障
    - charging_done: 充电完成
    """
    service = get_demo_service()
    from src.demo.scenarios import DemoEvent

    event_map = {
        DemoEventEnum.low_battery: DemoEvent.ROBOT_LOW_BATTERY,
        DemoEventEnum.obstacle: DemoEvent.ROBOT_OBSTACLE,
        DemoEventEnum.task_done: DemoEvent.TASK_COMPLETED,
        DemoEventEnum.urgent_task: DemoEvent.NEW_URGENT_TASK,
        DemoEventEnum.robot_error: DemoEvent.ROBOT_ERROR,
        DemoEventEnum.charging_done: DemoEvent.CHARGING_COMPLETE
    }

    result = await service.trigger_event(event_map[request.event], request.robot_id)

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

    return result


@router.get("/status")
async def get_demo_status():
    """
    获取演示状态

    返回当前演示的运行状态，包括:
    - 是否激活
    - 当前场景
    - 模拟速度
    - 触发的事件数量
    """
    service = get_demo_service()
    return {
        "success": True,
        "status": service.get_status()
    }


@router.post("/speed")
async def set_simulation_speed(request: SetSpeedRequest):
    """
    设置模拟速度

    速度范围: 0.1x - 10x
    """
    service = get_demo_service()
    service.set_simulation_speed(request.speed)
    return {
        "success": True,
        "speed": request.speed,
        "message": f"Simulation speed set to {request.speed}x"
    }


@router.post("/auto-events")
async def set_auto_events(request: SetAutoEventsRequest):
    """
    设置自动事件开关
    """
    service = get_demo_service()
    service.set_auto_events(request.enabled)
    return {
        "success": True,
        "enabled": request.enabled,
        "message": f"Auto events {'enabled' if request.enabled else 'disabled'}"
    }


# ==================== 数据查询端点 ====================

@router.get("/buildings")
async def get_buildings():
    """
    获取演示楼宇数据

    返回3个香港知名商业楼宇
    """
    service = get_demo_service()
    buildings = service.get_buildings()
    return {
        "success": True,
        "buildings": list(buildings.values()),
        "total": len(buildings)
    }


@router.get("/buildings/{building_id}")
async def get_building(building_id: str):
    """获取单个楼宇详情"""
    service = get_demo_service()
    buildings = service.get_buildings()
    if building_id not in buildings:
        raise HTTPException(status_code=404, detail="Building not found")
    return {
        "success": True,
        "building": buildings[building_id]
    }


@router.get("/floors")
async def get_floors(building_id: Optional[str] = Query(None, description="楼宇ID")):
    """获取楼层数据"""
    service = get_demo_service()
    floors = service.get_floors(building_id)
    return {
        "success": True,
        "floors": list(floors.values()),
        "total": len(floors)
    }


@router.get("/zones")
async def get_zones(floor_id: Optional[str] = Query(None, description="楼层ID")):
    """获取区域数据"""
    service = get_demo_service()
    zones = service.get_zones(floor_id)
    return {
        "success": True,
        "zones": list(zones.values()),
        "total": len(zones)
    }


@router.get("/robots")
async def get_robots(
    building_id: Optional[str] = Query(None, description="楼宇ID"),
    status: Optional[str] = Query(None, description="状态: working, idle, charging, maintenance, error")
):
    """
    获取机器人数据

    返回8台机器人的实时状态
    """
    service = get_demo_service()
    robots = service.get_robots(building_id, status)
    return {
        "success": True,
        "robots": list(robots.values()),
        "total": len(robots)
    }


@router.get("/robots/{robot_id}")
async def get_robot(robot_id: str):
    """获取单个机器人详情"""
    service = get_demo_service()
    robot = service.get_robot(robot_id)
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    return {
        "success": True,
        "robot": robot
    }


@router.get("/tasks")
async def get_tasks(
    status: Optional[str] = Query(None, description="状态: pending, in_progress, completed, failed"),
    robot_id: Optional[str] = Query(None, description="机器人ID"),
    limit: int = Query(100, ge=1, le=500, description="返回数量限制")
):
    """
    获取任务数据

    支持按状态和机器人筛选
    """
    service = get_demo_service()
    tasks = service.get_tasks(status, robot_id, limit)
    return {
        "success": True,
        "tasks": tasks,
        "total": len(tasks)
    }


@router.get("/alerts")
async def get_alerts(
    status: Optional[str] = Query(None, description="状态: active, resolved"),
    severity: Optional[str] = Query(None, description="严重程度: info, warning, critical")
):
    """获取告警数据"""
    service = get_demo_service()
    alerts = service.get_alerts(status, severity)
    return {
        "success": True,
        "alerts": alerts,
        "total": len(alerts)
    }


@router.get("/kpi")
async def get_kpi():
    """
    获取KPI数据

    返回完整的KPI数据，包括:
    - 核心指标 (任务完成率、机器人利用率等)
    - 今日概览
    - 效率对比 (使用LinkC前后)
    - 健康度评分
    - 楼宇状态
    - 趋势数据
    """
    service = get_demo_service()
    kpi = service.get_kpi()
    return {
        "success": True,
        "kpi": kpi
    }


@router.get("/summary")
async def get_demo_summary():
    """
    获取演示数据摘要

    一次性返回所有关键数据的概要
    """
    service = get_demo_service()

    buildings = service.get_buildings()
    robots = service.get_robots()
    tasks = service.get_tasks(limit=50)
    alerts = service.get_alerts()
    kpi = service.get_kpi()
    status = service.get_status()

    # 统计
    working_robots = len([r for r in robots.values() if r["status"] == "working"])
    idle_robots = len([r for r in robots.values() if r["status"] == "idle"])
    in_progress_tasks = len([t for t in tasks if t["status"] == "in_progress"])
    pending_tasks = len([t for t in tasks if t["status"] == "pending"])
    active_alerts = len([a for a in alerts if a["status"] == "active"])

    return {
        "success": True,
        "demo_status": status,
        "summary": {
            "buildings": len(buildings),
            "robots": {
                "total": len(robots),
                "working": working_robots,
                "idle": idle_robots,
                "other": len(robots) - working_robots - idle_robots
            },
            "tasks": {
                "in_progress": in_progress_tasks,
                "pending": pending_tasks,
                "recent_completed": len([t for t in tasks if t["status"] == "completed"])
            },
            "alerts": {
                "active": active_alerts,
                "total": len(alerts)
            },
            "kpi": {
                "task_completion_rate": kpi.get("task_completion_rate", 0),
                "robot_utilization": kpi.get("robot_utilization", 0),
                "health_score": kpi.get("health_score", {}).get("overall", 0)
            }
        }
    }
