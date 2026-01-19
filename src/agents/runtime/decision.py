"""
A1: 决策模型
============
Agent 决策的数据结构。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import uuid


@dataclass
class Decision:
    """Agent 决策"""
    decision_id: str = field(default_factory=lambda: f"dec_{uuid.uuid4().hex[:8]}")
    decision_type: str = ""
    description: str = ""
    
    # 决策内容
    actions: list[dict] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    
    # 置信度和边界
    confidence: float = 0.0  # 0-1
    exceeds_boundary: bool = False
    auto_approve: bool = False
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.utcnow)
    reasoning: str = ""  # 决策推理过程
    
    def add_action(self, action_type: str, params: dict):
        """添加动作"""
        self.actions.append({
            "type": action_type,
            "params": params,
            "order": len(self.actions)
        })
    
    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type,
            "description": self.description,
            "actions": self.actions,
            "confidence": self.confidence,
            "exceeds_boundary": self.exceeds_boundary,
            "auto_approve": self.auto_approve,
            "reasoning": self.reasoning,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class DecisionResult:
    """决策执行结果"""
    success: bool = False
    decision: Optional[Decision] = None
    
    # 执行详情
    actions_executed: list[dict] = field(default_factory=list)
    actions_failed: list[dict] = field(default_factory=list)
    
    # 状态
    requires_approval: bool = False
    error: Optional[str] = None
    message: Optional[str] = None
    
    # 元数据
    executed_at: datetime = field(default_factory=datetime.utcnow)
    duration_ms: int = 0
    
    def add_executed_action(self, action: dict, result: Any):
        """记录已执行的动作"""
        self.actions_executed.append({
            **action,
            "result": result,
            "executed_at": datetime.utcnow().isoformat()
        })
    
    def add_failed_action(self, action: dict, error: str):
        """记录失败的动作"""
        self.actions_failed.append({
            **action,
            "error": error,
            "failed_at": datetime.utcnow().isoformat()
        })
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "decision_id": self.decision.decision_id if self.decision else None,
            "actions_executed": len(self.actions_executed),
            "actions_failed": len(self.actions_failed),
            "requires_approval": self.requires_approval,
            "error": self.error,
            "message": self.message,
            "executed_at": self.executed_at.isoformat(),
            "duration_ms": self.duration_ms,
        }
