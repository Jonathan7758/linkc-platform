"""
DM2: 模拟引擎API路由 (Simulation Engine API Router)

提供实时模拟控制的API端点:
- POST /api/v1/simulation/start - 启动模拟
- POST /api/v1/simulation/stop - 停止模拟
- POST /api/v1/simulation/pause - 暂停模拟
- POST /api/v1/simulation/resume - 恢复模拟
- POST /api/v1/simulation/speed - 设置速度
- GET /api/v1/simulation/status - 获取状态
- GET /api/v1/simulation/robots - 获取机器人状态
- POST /api/v1/simulation/robots/{robot_id}/task - 分配任务
- POST /api/v1/simulation/robots/{robot_id}/recall - 召回机器人
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

router = APIRouter(prefix="/simulation", tags=["simulation"])


# ==================== Pydantic 模型 ====================

class SetSpeedRequest(BaseModel):
    """设置模拟速度请求"""
    speed: float = Field(..., ge=0.1, le=10, description="模拟速度倍率 (0.1-10)")


class AssignTaskRequest(BaseModel):
    """分配任务请求"""
    task_id: str = Field(..., description="任务ID")
    target_x: Optional[float] = Field(None, description="目标X坐标")
    target_y: Optional[float] = Field(None, description="目标Y坐标")


class SetStatusRequest(BaseModel):
    """设置状态请求"""
    status: str = Field(..., description="状态: idle, working, charging, returning, paused, error, maintenance")


# ==================== 模拟引擎实例 ====================

_simulation_engine = None
_demo_service = None
_ws_manager = None


def get_simulation_engine():
    """获取模拟引擎实例"""
    global _simulation_engine, _demo_service, _ws_manager

    if _simulation_engine is None:
        from src.demo.simulation_engine import simulation_engine
        from src.demo.data_service import demo_service
        from app.api.v1.routers.websocket import manager

        _simulation_engine = simulation_engine
        _demo_service = demo_service
        _ws_manager = manager

        # 设置广播回调
        async def broadcast_callback(data: dict):
            await manager.broadcast(data)

        _simulation_engine.set_broadcast_callback(broadcast_callback)

    return _simulation_engine


# ==================== 控制端点 ====================

@router.post("/start")
async def start_simulation():
    """
    启动模拟引擎

    启动后，机器人将开始实时移动，状态通过WebSocket广播
    """
    engine = get_simulation_engine()

    # 如果尚未初始化机器人，从demo服务初始化
    if len(engine.get_all_states()) == 0:
        from src.demo.data_service import demo_service
        if not demo_service.status.is_active:
            # 先初始化演示数据
            from src.demo.scenarios import DemoScenario
            await demo_service.init_demo_data(DemoScenario.FULL_DEMO)

        engine.setup_from_demo_service(demo_service)

    result = await engine.start()

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.post("/stop")
async def stop_simulation():
    """
    停止模拟引擎
    """
    engine = get_simulation_engine()
    result = await engine.stop()

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.post("/pause")
async def pause_simulation():
    """
    暂停模拟
    """
    engine = get_simulation_engine()
    result = engine.pause()

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.post("/resume")
async def resume_simulation():
    """
    恢复模拟
    """
    engine = get_simulation_engine()
    result = engine.resume()

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.post("/speed")
async def set_simulation_speed(request: SetSpeedRequest):
    """
    设置模拟速度

    速度范围: 0.1x - 10x
    """
    engine = get_simulation_engine()
    result = engine.set_speed(request.speed)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.get("/status")
async def get_simulation_status():
    """
    获取模拟引擎状态
    """
    engine = get_simulation_engine()
    return {
        "success": True,
        "status": engine.get_status()
    }


# ==================== 机器人状态端点 ====================

@router.get("/robots")
async def get_simulation_robots(
    status: Optional[str] = Query(None, description="按状态筛选")
):
    """
    获取所有机器人的模拟状态

    包含实时位置、电量、任务进度等
    """
    engine = get_simulation_engine()
    states = engine.get_all_states()

    if status:
        states = [s for s in states if s["status"] == status]

    return {
        "success": True,
        "robots": states,
        "total": len(states),
        "simulation_running": engine.is_running
    }


@router.get("/robots/{robot_id}")
async def get_simulation_robot(robot_id: str):
    """
    获取单个机器人的模拟状态
    """
    engine = get_simulation_engine()
    state = engine.get_robot_state(robot_id)

    if not state:
        raise HTTPException(status_code=404, detail=f"Robot {robot_id} not found")

    return {
        "success": True,
        "robot": state
    }


@router.post("/robots/{robot_id}/task")
async def assign_robot_task(robot_id: str, request: AssignTaskRequest):
    """
    分配任务给机器人

    机器人将开始向目标位置移动并执行清洁任务
    """
    engine = get_simulation_engine()

    target = None
    if request.target_x is not None and request.target_y is not None:
        target = {"x": request.target_x, "y": request.target_y}

    result = engine.assign_task(robot_id, request.task_id, target)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/robots/{robot_id}/recall")
async def recall_robot(robot_id: str):
    """
    召回机器人到充电站

    机器人将停止当前任务并返回充电站
    """
    engine = get_simulation_engine()
    result = engine.recall_robot(robot_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/robots/{robot_id}/status")
async def set_robot_status(robot_id: str, request: SetStatusRequest):
    """
    设置机器人状态

    可用状态: idle, working, charging, returning, paused, error, maintenance
    """
    engine = get_simulation_engine()
    result = engine.set_robot_status(robot_id, request.status)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


# ==================== 配置端点 ====================

@router.get("/config")
async def get_simulation_config():
    """
    获取模拟配置
    """
    engine = get_simulation_engine()
    config = engine.config

    return {
        "success": True,
        "config": {
            "tick_interval": config.tick_interval,
            "speed_multiplier": config.speed_multiplier,
            "battery_drain_rate": config.battery_drain_rate,
            "battery_charge_rate": config.battery_charge_rate,
            "task_progress_rate": config.task_progress_rate,
            "map_bounds": config.map_bounds
        }
    }
