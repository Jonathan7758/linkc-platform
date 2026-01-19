"""
A1: Agent 基类
==============
所有 Agent 的抽象基类。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid
import structlog

logger = structlog.get_logger(__name__)


class AutonomyLevel(Enum):
    """Agent 自主性级别"""
    L0_PASSIVE = 0      # 被动响应 - 只响应人类请求
    L1_SUGGEST = 1      # 建议执行 - 提出建议，人类确认后执行
    L2_LIMITED = 2      # 有限自主 - 在预设边界内自主执行
    L3_AUTONOMOUS = 3   # 完全自主 - 自主决策和执行


@dataclass
class AgentConfig:
    """Agent 配置"""
    agent_id: str = field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:8]}")
    name: str = "Unnamed Agent"
    description: str = ""
    autonomy_level: AutonomyLevel = AutonomyLevel.L1_SUGGEST
    tenant_id: str = ""
    
    # 自主执行边界
    max_tasks_per_decision: int = 5
    max_battery_threshold: int = 20  # 最低电量要求
    allowed_zones: list[str] = field(default_factory=list)  # 空则允许所有
    
    # 升级规则
    escalation_on_error: bool = True
    escalation_on_conflict: bool = True
    escalation_timeout_seconds: int = 300


class AgentState(Enum):
    """Agent 状态"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING_APPROVAL = "waiting_approval"
    ERROR = "error"
    STOPPED = "stopped"


class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = AgentState.IDLE
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self._decision_history: list[dict] = []
    
    @property
    def agent_id(self) -> str:
        return self.config.agent_id
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def autonomy_level(self) -> AutonomyLevel:
        return self.config.autonomy_level
    
    @abstractmethod
    async def think(self, context: dict) -> "Decision":
        """
        分析上下文，生成决策。
        
        Args:
            context: 当前环境上下文
            
        Returns:
            Decision 对象
        """
        pass
    
    @abstractmethod
    async def execute(self, decision: "Decision") -> "DecisionResult":
        """
        执行决策。
        
        Args:
            decision: 要执行的决策
            
        Returns:
            执行结果
        """
        pass
    
    async def run_cycle(self, context: dict) -> "DecisionResult":
        """
        运行一个完整的决策-执行周期。
        """
        logger.info(
            "agent_cycle_start",
            agent_id=self.agent_id,
            agent_name=self.name
        )
        
        try:
            # 思考阶段
            self.state = AgentState.THINKING
            decision = await self.think(context)
            
            # 检查是否需要人工审批
            if self._requires_approval(decision):
                self.state = AgentState.WAITING_APPROVAL
                logger.info(
                    "agent_waiting_approval",
                    agent_id=self.agent_id,
                    decision_type=decision.decision_type
                )
                return DecisionResult(
                    success=False,
                    requires_approval=True,
                    decision=decision,
                    message="Decision requires human approval"
                )
            
            # 执行阶段
            self.state = AgentState.EXECUTING
            result = await self.execute(decision)
            
            # 记录决策历史
            self._record_decision(decision, result)
            
            self.state = AgentState.IDLE
            self.last_activity = datetime.utcnow()
            
            logger.info(
                "agent_cycle_complete",
                agent_id=self.agent_id,
                success=result.success
            )
            
            return result
            
        except Exception as e:
            self.state = AgentState.ERROR
            logger.error(
                "agent_cycle_error",
                agent_id=self.agent_id,
                error=str(e)
            )
            return DecisionResult(
                success=False,
                error=str(e)
            )
    
    def _requires_approval(self, decision: "Decision") -> bool:
        """判断决策是否需要人工审批"""
        # L0: 总是需要审批
        if self.autonomy_level == AutonomyLevel.L0_PASSIVE:
            return True
        
        # L1: 默认需要审批，除非明确标记
        if self.autonomy_level == AutonomyLevel.L1_SUGGEST:
            return not decision.auto_approve
        
        # L2: 只有超出边界时需要审批
        if self.autonomy_level == AutonomyLevel.L2_LIMITED:
            return decision.exceeds_boundary
        
        # L3: 不需要审批
        return False
    
    def _record_decision(self, decision: "Decision", result: "DecisionResult"):
        """记录决策历史"""
        self._decision_history.append({
            "decision_id": decision.decision_id,
            "decision_type": decision.decision_type,
            "timestamp": datetime.utcnow().isoformat(),
            "success": result.success,
            "actions": decision.actions,
        })
        
        # 只保留最近100条记录
        if len(self._decision_history) > 100:
            self._decision_history = self._decision_history[-100:]
    
    async def handle_approval(self, decision_id: str, approved: bool, approver: str):
        """处理人工审批结果"""
        logger.info(
            "agent_approval_received",
            agent_id=self.agent_id,
            decision_id=decision_id,
            approved=approved,
            approver=approver
        )
        # 子类实现具体逻辑


# 前向声明的类型在文件末尾定义
from src.agents.runtime.decision import Decision, DecisionResult
