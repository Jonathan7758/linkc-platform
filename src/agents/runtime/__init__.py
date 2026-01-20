"""
A1: Agent 运行时框架
====================
管理 Agent 生命周期、决策执行、人机协作、MCP调用、异常升级。
"""

from src.agents.runtime.base import (
    BaseAgent,
    AgentConfig,
    AgentState,
    AutonomyLevel,
)
from src.agents.runtime.manager import AgentManager
from src.agents.runtime.decision import Decision, DecisionResult
from src.agents.runtime.mcp_client import MCPClient, ToolResult
from src.agents.runtime.escalation import (
    EscalationHandler,
    EscalationLevel,
    EscalationEvent,
    EscalationRule,
)
from src.agents.runtime.activity import ActivityLogger, AgentActivity
from src.agents.runtime.runtime import AgentRuntime

__all__ = [
    # Base
    "BaseAgent",
    "AgentConfig",
    "AgentState",
    "AutonomyLevel",
    # Manager
    "AgentManager",
    # Decision
    "Decision",
    "DecisionResult",
    # MCP Client
    "MCPClient",
    "ToolResult",
    # Escalation
    "EscalationHandler",
    "EscalationLevel",
    "EscalationEvent",
    "EscalationRule",
    # Activity
    "ActivityLogger",
    "AgentActivity",
    # Runtime
    "AgentRuntime",
]
