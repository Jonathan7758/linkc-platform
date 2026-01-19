"""
A2: 清洁调度 Agent 实现
======================
"""

from typing import Optional
import structlog

from src.agents.runtime.base import BaseAgent, AgentConfig, AutonomyLevel
from src.agents.runtime.decision import Decision, DecisionResult

logger = structlog.get_logger(__name__)


class CleaningSchedulerAgent(BaseAgent):
    """清洁调度 Agent"""
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        task_manager=None,
        robot_control=None,
        space_manager=None
    ):
        if config is None:
            config = AgentConfig(
                name="清洁调度Agent",
                description="智能调度清洁任务到合适的机器人",
                autonomy_level=AutonomyLevel.L2_LIMITED
            )
        super().__init__(config)
        
        self.task_manager = task_manager
        self.robot_control = robot_control
        self.space_manager = space_manager
    
    async def think(self, context: dict) -> Decision:
        """分析当前情况，决定如何调度任务"""
        decision = Decision(
            decision_type="task_scheduling",
            description="分析待处理任务并分配给合适的机器人"
        )
        
        tenant_id = context.get("tenant_id", self.config.tenant_id)
        
        try:
            pending_tasks = await self._get_pending_tasks(tenant_id)
            if not pending_tasks:
                decision.description = "没有待分配的任务"
                decision.confidence = 1.0
                return decision
            
            available_robots = await self._get_available_robots(tenant_id)
            if not available_robots:
                decision.description = "没有可用的机器人"
                decision.confidence = 1.0
                return decision
            
            assignments = self._generate_assignments(pending_tasks, available_robots)
            
            for task_id, robot_id, reason in assignments:
                decision.add_action(
                    action_type="assign_task",
                    params={"task_id": task_id, "robot_id": robot_id, "reason": reason}
                )
            
            decision.confidence = self._calculate_confidence(assignments)
            decision.reasoning = f"找到 {len(pending_tasks)} 个待分配任务，{len(available_robots)} 个可用机器人"
            
            if len(assignments) > self.config.max_tasks_per_decision:
                decision.exceeds_boundary = True
            else:
                decision.auto_approve = True
                
        except Exception as e:
            decision.confidence = 0.0
            decision.reasoning = f"决策过程出错: {str(e)}"
        
        return decision
    
    async def execute(self, decision: Decision) -> DecisionResult:
        """执行任务分配决策"""
        result = DecisionResult(decision=decision)
        
        if not decision.actions:
            result.success = True
            result.message = "没有需要执行的动作"
            return result
        
        for action in decision.actions:
            try:
                if action["type"] == "assign_task":
                    params = action["params"]
                    assign_result = await self._assign_task(
                        task_id=params["task_id"],
                        robot_id=params["robot_id"],
                        reason=params.get("reason", "")
                    )
                    
                    if assign_result.get("success"):
                        result.add_executed_action(action, assign_result)
                    else:
                        result.add_failed_action(action, assign_result.get("error", "Unknown"))
            except Exception as e:
                result.add_failed_action(action, str(e))
        
        result.success = len(result.actions_failed) == 0
        return result
    
    async def _get_pending_tasks(self, tenant_id: str) -> list[dict]:
        if self.task_manager:
            result = await self.task_manager.get_pending_tasks(tenant_id)
            return result.get("tasks", [])
        return []
    
    async def _get_available_robots(self, tenant_id: str) -> list[dict]:
        if self.robot_control:
            result = await self.robot_control.get_available_robots(
                tenant_id=tenant_id,
                min_battery=self.config.max_battery_threshold
            )
            return result.get("robots", [])
        return []
    
    def _generate_assignments(self, tasks: list, robots: list) -> list[tuple]:
        assignments = []
        priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        sorted_tasks = sorted(tasks, key=lambda t: priority_order.get(t.get("priority", "normal"), 99))
        available = list(robots)
        
        for task in sorted_tasks:
            if not available:
                break
            robot = max(available, key=lambda r: r.get("battery_level", 0))
            available.remove(robot)
            reason = f"自动分配: 优先级={task.get('priority')}, 电量={robot.get('battery_level')}%"
            assignments.append((task["id"], robot["id"], reason))
        
        return assignments
    
    def _calculate_confidence(self, assignments: list) -> float:
        if not assignments:
            return 1.0
        return max(0.5, 1.0 - len(assignments) * 0.05)
    
    async def _assign_task(self, task_id: str, robot_id: str, reason: str) -> dict:
        if self.task_manager:
            return await self.task_manager.assign_task(
                task_id=task_id, robot_id=robot_id, assigned_by=self.agent_id
            )
        return {"success": False, "error": "Task manager not connected"}
