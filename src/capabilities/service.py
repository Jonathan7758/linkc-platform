"""
Capabilities Service - 能力服务
"""

from typing import List, Optional

from .models import AgentCapabilityInfo, Capability
from .registry import (
    CapabilityRegistry,
    CLEANING_CAPABILITIES,
    DELIVERY_CAPABILITIES,
    PATROL_CAPABILITIES
)


class CapabilityService:
    """能力服务 - 提供 API 层使用的方法"""

    def __init__(self, registry: CapabilityRegistry = None):
        self._registry = registry or CapabilityRegistry()
        self._init_default_capabilities()

    def _init_default_capabilities(self) -> None:
        """初始化默认能力"""
        for cap in CLEANING_CAPABILITIES:
            self._registry.register_capability(cap)
        for cap in DELIVERY_CAPABILITIES:
            self._registry.register_capability(cap)
        for cap in PATROL_CAPABILITIES:
            self._registry.register_capability(cap)

    def list_all_capabilities(self) -> List[Capability]:
        """获取所有能力定义"""
        return self._registry.list_all_capabilities()

    def get_capability(self, capability_id: str) -> Optional[Capability]:
        """获取单个能力定义"""
        return self._registry.get_capability(capability_id)

    def get_agent_capabilities(self, agent_id: str) -> Optional[AgentCapabilityInfo]:
        """获取 Agent 的能力信息"""
        return self._registry.get_agent_capabilities(agent_id)

    def find_agents_by_capability(
        self,
        capability_id: str,
        status: str = "ready"
    ) -> List[AgentCapabilityInfo]:
        """按能力搜索 Agent"""
        return self._registry.find_agents_by_capability(capability_id, status)

    def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        capability_ids: List[str]
    ) -> None:
        """注册 Agent 的能力"""
        self._registry.register_agent_capabilities(agent_id, agent_type, capability_ids)

    def update_agent_status(
        self,
        agent_id: str,
        status: str,
        current_task: Optional[str] = None
    ) -> None:
        """更新 Agent 状态"""
        self._registry.update_agent_status(agent_id, status, current_task)

    def unregister_agent(self, agent_id: str) -> None:
        """注销 Agent"""
        self._registry.unregister_agent(agent_id)
