"""
A1: Agent 运行时
================
Agent 执行的完整运行时环境
"""

from typing import Dict, List, Optional, Any, Type
from datetime import datetime
import asyncio
import logging

from .base import BaseAgent, AgentConfig, AgentState
from .decision import Decision, DecisionResult
from .mcp_client import MCPClient, ToolResult
from .escalation import EscalationHandler, EscalationLevel, EscalationEvent
from .activity import ActivityLogger, AgentActivity

logger = logging.getLogger(__name__)


class AgentRuntime:
    """
    Agent 运行时环境

    提供 Agent 执行的完整基础设施：
    - 生命周期管理
    - MCP 客户端
    - 异常升级
    - 活动日志
    - 事件总线
    """

    def __init__(
        self,
        mcp_servers: Optional[Dict[str, str]] = None,
        redis_url: Optional[str] = None,
        storage=None
    ):
        """
        初始化运行时

        Args:
            mcp_servers: MCP Server 配置
            redis_url: Redis URL (用于事件总线)
            storage: 存储服务
        """
        # 核心组件
        self.mcp_client = MCPClient(mcp_servers or {})
        self.escalation_handler = EscalationHandler(self)
        self.activity_logger = ActivityLogger(storage)

        # Agent 管理
        self._agents: Dict[str, BaseAgent] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._pending_approvals: Dict[str, dict] = {}

        # 事件总线
        self._redis = None
        self._redis_url = redis_url
        self._event_handlers: Dict[str, List[callable]] = {}

        # 状态
        self._running = False

    async def start(self) -> None:
        """启动运行时"""
        if self._running:
            logger.warning("Runtime already running")
            return

        logger.info("Starting Agent Runtime...")

        # 连接 MCP
        await self.mcp_client.connect()

        # 启动活动日志
        await self.activity_logger.start()

        # 连接 Redis (如果配置了)
        if self._redis_url:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(self._redis_url)
                logger.info("Connected to Redis")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")

        self._running = True
        logger.info("Agent Runtime started")

    async def stop(self) -> None:
        """停止运行时"""
        if not self._running:
            return

        logger.info("Stopping Agent Runtime...")

        # 停止所有 Agent
        for agent_id in list(self._agents.keys()):
            await self.stop_agent(agent_id)

        # 停止活动日志
        await self.activity_logger.stop()

        # 断开 MCP
        await self.mcp_client.disconnect()

        # 关闭 Redis
        if self._redis:
            await self._redis.close()

        self._running = False
        logger.info("Agent Runtime stopped")

    # ==================== Agent 管理 ====================

    def register_agent(self, agent: BaseAgent) -> str:
        """注册 Agent"""
        agent_id = agent.agent_id

        if agent_id in self._agents:
            raise ValueError(f"Agent {agent_id} already registered")

        self._agents[agent_id] = agent

        # 注入运行时引用
        if hasattr(agent, 'runtime'):
            agent.runtime = self
        if hasattr(agent, 'mcp_client'):
            agent.mcp_client = self.mcp_client

        logger.info(
            f"Agent registered: {agent_id} ({agent.name})",
            extra={"agent_id": agent_id}
        )

        return agent_id

    def unregister_agent(self, agent_id: str) -> bool:
        """注销 Agent"""
        if agent_id not in self._agents:
            return False

        # 停止运行中的任务
        if agent_id in self._running_tasks:
            self._running_tasks[agent_id].cancel()
            del self._running_tasks[agent_id]

        del self._agents[agent_id]
        logger.info(f"Agent unregistered: {agent_id}")
        return True

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取 Agent"""
        return self._agents.get(agent_id)

    def list_agents(self, tenant_id: Optional[str] = None) -> List[dict]:
        """列出所有 Agent"""
        agents = []
        for agent in self._agents.values():
            if tenant_id and agent.config.tenant_id != tenant_id:
                continue
            agents.append({
                "agent_id": agent.agent_id,
                "name": agent.name,
                "state": agent.state.value,
                "autonomy_level": agent.autonomy_level.name,
                "tenant_id": agent.config.tenant_id,
                "last_activity": agent.last_activity.isoformat(),
            })
        return agents

    # ==================== Agent 生命周期 ====================

    async def start_agent(self, agent_id: str) -> bool:
        """启动 Agent"""
        agent = self._agents.get(agent_id)
        if not agent:
            return False

        if agent_id in self._running_tasks:
            logger.warning(f"Agent {agent_id} already running")
            return False

        old_state = agent.state
        agent.state = AgentState.IDLE

        # 记录状态变更
        self.activity_logger.log_state_change(
            agent_id=agent_id,
            tenant_id=agent.config.tenant_id,
            old_state=old_state.value,
            new_state=agent.state.value
        )

        logger.info(f"Agent started: {agent_id}")
        return True

    async def stop_agent(self, agent_id: str) -> bool:
        """停止 Agent"""
        agent = self._agents.get(agent_id)
        if not agent:
            return False

        # 取消运行任务
        if agent_id in self._running_tasks:
            self._running_tasks[agent_id].cancel()
            try:
                await self._running_tasks[agent_id]
            except asyncio.CancelledError:
                pass
            del self._running_tasks[agent_id]

        old_state = agent.state
        agent.state = AgentState.STOPPED

        # 记录状态变更
        self.activity_logger.log_state_change(
            agent_id=agent_id,
            tenant_id=agent.config.tenant_id,
            old_state=old_state.value,
            new_state=agent.state.value
        )

        logger.info(f"Agent stopped: {agent_id}")
        return True

    async def pause_agent(self, agent_id: str) -> bool:
        """暂停 Agent"""
        agent = self._agents.get(agent_id)
        if not agent:
            return False

        # 取消运行任务
        if agent_id in self._running_tasks:
            self._running_tasks[agent_id].cancel()
            del self._running_tasks[agent_id]

        old_state = agent.state
        agent.state = AgentState.WAITING_APPROVAL  # 用作暂停状态

        self.activity_logger.log_state_change(
            agent_id=agent_id,
            tenant_id=agent.config.tenant_id,
            old_state=old_state.value,
            new_state=agent.state.value
        )

        logger.info(f"Agent paused: {agent_id}")
        return True

    async def resume_agent(self, agent_id: str) -> bool:
        """恢复 Agent"""
        agent = self._agents.get(agent_id)
        if not agent:
            return False

        old_state = agent.state
        agent.state = AgentState.IDLE

        self.activity_logger.log_state_change(
            agent_id=agent_id,
            tenant_id=agent.config.tenant_id,
            old_state=old_state.value,
            new_state=agent.state.value
        )

        logger.info(f"Agent resumed: {agent_id}")
        return True

    # ==================== Agent 执行 ====================

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
    ) -> bool:
        """启动 Agent 循环"""
        agent = self._agents.get(agent_id)
        if not agent:
            return False

        if agent_id in self._running_tasks:
            return False

        async def _loop():
            while True:
                try:
                    context = await context_provider()
                    await agent.run_cycle(context)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Agent loop error: {agent_id} - {e}")
                    await self.escalate(
                        agent_id=agent_id,
                        level=EscalationLevel.ERROR,
                        reason=str(e),
                        context={"exception": type(e).__name__}
                    )
                await asyncio.sleep(interval_seconds)

        task = asyncio.create_task(_loop())
        self._running_tasks[agent_id] = task

        logger.info(f"Agent loop started: {agent_id}, interval={interval_seconds}s")
        return True

    def stop_agent_loop(self, agent_id: str) -> bool:
        """停止 Agent 循环"""
        if agent_id not in self._running_tasks:
            return False

        self._running_tasks[agent_id].cancel()
        del self._running_tasks[agent_id]

        logger.info(f"Agent loop stopped: {agent_id}")
        return True

    # ==================== 工具调用 ====================

    async def call_tool(
        self,
        agent_id: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """代理调用 MCP 工具"""
        agent = self._agents.get(agent_id)
        tenant_id = agent.config.tenant_id if agent else ""

        result = await self.mcp_client.call_tool(tool_name, arguments)

        # 记录活动
        self.activity_logger.log_tool_call(
            agent_id=agent_id,
            tenant_id=tenant_id,
            tool_name=tool_name,
            arguments=arguments,
            success=result.success,
            result_data=result.data
        )

        return result

    # ==================== 异常升级 ====================

    async def escalate(
        self,
        agent_id: str,
        level: EscalationLevel,
        reason: str,
        context: Dict[str, Any]
    ) -> str:
        """触发异常升级"""
        return await self.escalation_handler.handle(
            agent_id=agent_id,
            level=level,
            reason=reason,
            context=context
        )

    # ==================== 事件系统 ====================

    async def emit_event(
        self,
        source: str,
        event_type: str,
        data: Dict[str, Any]
    ) -> None:
        """发送事件"""
        event = {
            "source": source,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # 发布到 Redis (如果可用)
        if self._redis:
            try:
                import json
                await self._redis.publish(
                    f"events:{event_type}",
                    json.dumps(event)
                )
            except Exception as e:
                logger.error(f"Failed to publish event: {e}")

        # 调用本地处理器
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    def on_event(self, event_type: str, handler: callable) -> None:
        """注册事件处理器"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    # ==================== 审批系统 ====================

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
                error=f"Decision {decision_id} not found"
            )

        agent_id = pending["agent_id"]
        decision = pending["decision"]
        agent = self._agents.get(agent_id)

        if not agent:
            return DecisionResult(
                success=False,
                error=f"Agent {agent_id} not found"
            )

        # 通知 Agent
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

        return result

    def get_pending_approvals(self, tenant_id: Optional[str] = None) -> List[dict]:
        """获取待审批的决策"""
        approvals = []
        for decision_id, data in self._pending_approvals.items():
            agent = self._agents.get(data["agent_id"])
            if tenant_id and agent and agent.config.tenant_id != tenant_id:
                continue
            approvals.append({
                "decision_id": decision_id,
                "agent_id": data["agent_id"],
                "decision_type": data["decision"].decision_type,
                "description": data["decision"].description,
                "created_at": data["created_at"],
            })
        return approvals

    # ==================== 日志和统计 ====================

    def get_logger(self, agent_id: str) -> logging.Logger:
        """获取 Agent 专用 Logger"""
        return logging.getLogger(f"agent.{agent_id}")

    async def get_activities(
        self,
        agent_id: Optional[str] = None,
        limit: int = 50
    ) -> List[AgentActivity]:
        """获取 Agent 活动日志"""
        return await self.activity_logger.query(agent_id=agent_id, limit=limit)

    def get_stats(self) -> Dict[str, Any]:
        """获取运行时统计"""
        return {
            "running": self._running,
            "agents": {
                "total": len(self._agents),
                "running_loops": len(self._running_tasks),
                "by_state": {
                    state.value: sum(1 for a in self._agents.values() if a.state == state)
                    for state in AgentState
                }
            },
            "pending_approvals": len(self._pending_approvals),
            "mcp": {
                "connected": self.mcp_client.is_connected,
                "available_tools": list(self.mcp_client.get_available_tools().keys())
            },
            "escalations": self.escalation_handler.get_stats(),
            "activities": self.activity_logger.get_stats(),
        }
