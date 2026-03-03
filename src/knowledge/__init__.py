"""
K1/K2/K3 知识层

知识层位于数据平台和Agent层之间，为Agent决策提供可配置的知识基础:
- K1 ScenarioKnowledgeBase: 场景知识库 — "应该知道什么"
- K2 GovernanceRuleEngine:  治理规则库 — "不能做什么"
- K3 DecisionLogger:        决策日志库 — "做过什么"
"""

from .scenario_kb import (
    ScenarioKnowledge,
    ScenarioKnowledgeBase,
    PromptTemplate,
)
from .rule_engine import (
    GovernanceRule,
    GovernanceRuleEngine,
    RuleEvalResult,
    CompiledCondition,
)
from .decision_logger import (
    DecisionContext,
    DecisionOutcome,
    DecisionRecord,
    DecisionLogger,
)

__all__ = [
    # K1
    "ScenarioKnowledge",
    "ScenarioKnowledgeBase",
    "PromptTemplate",
    # K2
    "GovernanceRule",
    "GovernanceRuleEngine",
    "RuleEvalResult",
    "CompiledCondition",
    # K3
    "DecisionContext",
    "DecisionOutcome",
    "DecisionRecord",
    "DecisionLogger",
]
