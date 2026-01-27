"""
Capabilities Models - 能力模型定义
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Capability:
    """能力定义"""
    id: str
    name: str
    category: str  # cleaning, delivery, patrol
    action: str  # vacuum, mop, deliver
    parameters: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class AgentCapabilityInfo:
    """Agent 能力信息"""
    agent_id: str
    agent_type: str  # cleaning, delivery, patrol
    capabilities: List[str]  # 能力 ID 列表
    status: str = "ready"  # ready, busy, offline
    current_task: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CapabilityMatch:
    """能力匹配结果"""
    agent_id: str
    capability_id: str
    match_score: float  # 0-1
    estimated_duration: int  # 分钟
    agent_status: str
