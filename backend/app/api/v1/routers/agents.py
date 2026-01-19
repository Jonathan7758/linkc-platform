"""
G5: Agent 交互 API
==================
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from src.agents.runtime.manager import AgentManager
from src.agents.runtime.base import AgentConfig, AutonomyLevel
from src.agents.cleaning_scheduler.agent import CleaningSchedulerAgent
from src.mcp_servers.task_manager.tools import TaskManagerTools
from src.mcp_servers.task_manager.storage import TaskStorage
from src.mcp_servers.robot_control.tools import RobotControlTools
from src.mcp_servers.robot_control.storage import RobotStorage

router = APIRouter(prefix="/agents", tags=["agents"])

# 初始化 Agent 管理器
agent_manager = AgentManager()

# 初始化 MCP 工具
task_storage = TaskStorage()
task_tools = TaskManagerTools(task_storage)
robot_storage = RobotStorage()
robot_tools = RobotControlTools(robot_storage)

# 创建并注册默认的清洁调度 Agent
default_scheduler = CleaningSchedulerAgent(
    config=AgentConfig(
        agent_id="scheduler_default",
        name="默认清洁调度Agent",
        tenant_id="tenant_001",
        autonomy_level=AutonomyLevel.L2_LIMITED
    ),
    task_manager=task_tools,
    robot_control=robot_tools
)
agent_manager.register_agent(default_scheduler)


class AgentCommand(BaseModel):
    """Agent 命令"""
    command: str
    context: Optional[dict] = None


class ApprovalRequest(BaseModel):
    """审批请求"""
    approved: bool
    approver: str


@router.get("")
async def list_agents():
    """列出所有 Agent"""
    return {
        "success": True,
        "agents": agent_manager.list_agents(),
        "stats": agent_manager.get_stats()
    }


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """获取 Agent 详情"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return {
        "success": True,
        "agent": {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "state": agent.state.value,
            "autonomy_level": agent.autonomy_level.name,
            "last_activity": agent.last_activity.isoformat(),
            "config": {
                "max_tasks_per_decision": agent.config.max_tasks_per_decision,
                "max_battery_threshold": agent.config.max_battery_threshold,
            }
        }
    }


@router.post("/{agent_id}/run")
async def run_agent(
    agent_id: str,
    tenant_id: str = Query("tenant_001")
):
    """运行 Agent 一次"""
    context = {
        "tenant_id": tenant_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    result = await agent_manager.run_agent_once(agent_id, context)
    
    return {
        "success": result.success,
        "result": result.to_dict(),
        "message": result.message or ("执行成功" if result.success else "执行失败"),
        "requires_approval": result.requires_approval
    }


@router.get("/approvals/pending")
async def get_pending_approvals():
    """获取待审批的决策"""
    return {
        "success": True,
        "approvals": agent_manager.get_pending_approvals()
    }


@router.post("/approvals/{decision_id}")
async def approve_decision(
    decision_id: str,
    request: ApprovalRequest = Body(...)
):
    """审批决策"""
    result = await agent_manager.approve_decision(
        decision_id=decision_id,
        approved=request.approved,
        approver=request.approver
    )
    
    if not result.success and result.error:
        raise HTTPException(status_code=400, detail=result.error)
    
    return {
        "success": result.success,
        "result": result.to_dict(),
        "message": "审批完成"
    }


@router.get("/stats")
async def get_agent_stats():
    """获取 Agent 统计信息"""
    return {
        "success": True,
        "stats": agent_manager.get_stats()
    }
