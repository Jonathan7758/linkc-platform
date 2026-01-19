"""
A1: Agent 运行时框架
====================
管理 Agent 生命周期、决策执行、人机协作。
"""

from src.agents.runtime.base import BaseAgent, AgentConfig
from src.agents.runtime.manager import AgentManager
from src.agents.runtime.decision import Decision, DecisionResult

__all__ = [
    "BaseAgent",
    "AgentConfig",
    "AgentManager",
    "Decision",
    "DecisionResult",
]
