"""
ECIS Autonomy Package -- B5 Human-Agent Autonomy Boundaries.

Provides autonomy-level management for human-robot task collaboration,
including context-aware escalation, approval workflows, and Tower C defaults.
"""

from .human_agent_boundary import (
    AutoExecuteResult,
    AutonomyLevel,
    HumanAgentBoundary,
    TaskAutonomyConfig,
)

__all__ = [
    "AutonomyLevel",
    "TaskAutonomyConfig",
    "AutoExecuteResult",
    "HumanAgentBoundary",
]
