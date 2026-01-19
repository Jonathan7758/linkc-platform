"""
A1: Agent 管理器
================
管理 Agent 的生命周期和调度。
"""

from datetime import datetime
from typing import Optional, Type
import asyncio
import structlog

from src.agents.runtime.base import BaseAgent, AgentConfig, AgentState
from src.agents.runtime.decision import Decision, DecisionResult

logger = structlog.get_logger(__name__)


class AgentManager:
    """Agent 管理器"""
    
    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._pending_approvals: dict[str, dict] = {}
    
    def register_agent(self, agent: BaseAgent) -> str:
        """注册 Agent"""
        agent_id = agent.agent_id
        
        if agent_id in self._agents:
            raise ValueError(f"Agent {agent_id} already registered")
        
        self._agents[agent_id] = agent
        
        logger.info(
            "agent_registered",
            agent_id=agent_id,
            agent_name=agent.name,
            autonomy_level=agent.autonomy_level.name
        )
        
        return agent_id
    
    def unregister_agent(self, agent_id: str):
        """注销 Agent"""
        if agent_id in self._running_tasks:
            self._running_tasks[agent_id].cancel()
            del self._running_tasks[agent_id]
        
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info("agent_unregistered", agent_id=agent_id)
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取 Agent"""
        return self._agents.get(agent_id)
    
    def list_agents(self) -> list[dict]:
        """列出所有 Agent"""
        return [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "state": agent.state.value,
                "autonomy_level": agent.autonomy_level.name,
                "last_activity": agent.last_activity.isoformat(),
            }
            for agent in self._agents.values()
        ]
    
    async def run_agent_once(self, agent_id: str, context: dict) -> DecisionResult:
        """运行 Agent 一次"""
        agent = self._agents.get(agent_id)
        if not agent:
            return DecisionResult(
                success=False,
                error=f"Agent {agent_id} not found"
            )
        
        result = await agent.run_cycle(context)
        
        # 如果需要审批，保存到待审批列表
        if result.requires_approval and result.decision:
            self._pending_approvals[result.decision.decision_id] = {
                "agent_id": agent_id,
                "decision": result.decision,
                "created_at": datetime.utcnow().isoformat()
            }
        
        return result
    
    async def start_agent_loop(
        self,
        agent_id: str,
        context_provider: callable,
        interval_seconds: int = 60
    ):
        """启动 Agent 循环"""
        agent = self._agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        async def _loop():
            while True:
                try:
                    context = await context_provider()
                    await agent.run_cycle(context)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(
                        "agent_loop_error",
                        agent_id=agent_id,
                        error=str(e)
                    )
                await asyncio.sleep(interval_seconds)
        
        task = asyncio.create_task(_loop())
        self._running_tasks[agent_id] = task
        
        logger.info(
            "agent_loop_started",
            agent_id=agent_id,
            interval=interval_seconds
        )
    
    def stop_agent_loop(self, agent_id: str):
        """停止 Agent 循环"""
        if agent_id in self._running_tasks:
            self._running_tasks[agent_id].cancel()
            del self._running_tasks[agent_id]
            logger.info("agent_loop_stopped", agent_id=agent_id)
    
    async def approve_decision(
        self,
        decision_id: str,
        approved: bool,
        approver: str
    ) -> DecisionResult:
        """审批决策"""
        pending = self._pending_approvals.get(decision_id)
        if not pending:
            return DecisionResult(
                success=False,
                error=f"Decision {decision_id} not found in pending approvals"
            )
        
        agent_id = pending["agent_id"]
        decision = pending["decision"]
        agent = self._agents.get(agent_id)
        
        if not agent:
            return DecisionResult(
                success=False,
                error=f"Agent {agent_id} not found"
            )
        
        # 通知 Agent 审批结果
        await agent.handle_approval(decision_id, approved, approver)
        
        # 如果批准，执行决策
        if approved:
            result = await agent.execute(decision)
        else:
            result = DecisionResult(
                success=False,
                decision=decision,
                message=f"Decision rejected by {approver}"
            )
        
        # 从待审批列表移除
        del self._pending_approvals[decision_id]
        
        logger.info(
            "decision_approved",
            decision_id=decision_id,
            approved=approved,
            approver=approver
        )
        
        return result
    
    def get_pending_approvals(self) -> list[dict]:
        """获取待审批的决策"""
        return [
            {
                "decision_id": decision_id,
                "agent_id": data["agent_id"],
                "decision_type": data["decision"].decision_type,
                "description": data["decision"].description,
                "created_at": data["created_at"],
            }
            for decision_id, data in self._pending_approvals.items()
        ]
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "total_agents": len(self._agents),
            "running_loops": len(self._running_tasks),
            "pending_approvals": len(self._pending_approvals),
            "agents_by_state": {
                state.value: sum(1 for a in self._agents.values() if a.state == state)
                for state in AgentState
            }
        }
