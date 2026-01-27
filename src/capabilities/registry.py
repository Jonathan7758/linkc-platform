"""
Capabilities Registry - 能力注册表
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime

from .models import Capability, AgentCapabilityInfo

logger = logging.getLogger("ecis_robot.capabilities")


# ===== 预定义能力 =====

CLEANING_CAPABILITIES = [
    Capability(
        id="cleaning.floor.vacuum",
        name="地面吸尘",
        category="cleaning",
        action="vacuum",
        parameters={"area_sqm": {"type": "float", "max": 500}},
        constraints={"min_battery": 20},
        description="使用吸尘功能清洁地面"
    ),
    Capability(
        id="cleaning.floor.mop",
        name="地面拖洗",
        category="cleaning",
        action="mop",
        parameters={"area_sqm": {"type": "float", "max": 300}},
        constraints={"min_battery": 30, "min_water": 20},
        description="使用拖洗功能清洁地面"
    ),
    Capability(
        id="cleaning.floor.scrub",
        name="地面洗地",
        category="cleaning",
        action="scrub",
        parameters={"area_sqm": {"type": "float", "max": 200}},
        constraints={"min_battery": 40},
        description="使用洗地机功能深度清洁"
    )
]

DELIVERY_CAPABILITIES = [
    Capability(
        id="delivery.package.small",
        name="小包裹配送",
        category="delivery",
        action="deliver",
        parameters={"destination": {"type": "string", "required": True}},
        constraints={"max_weight_kg": 5},
        description="配送5kg以下的小包裹"
    ),
    Capability(
        id="delivery.package.medium",
        name="中包裹配送",
        category="delivery",
        action="deliver",
        parameters={"destination": {"type": "string", "required": True}},
        constraints={"max_weight_kg": 20},
        description="配送20kg以下的中型包裹"
    )
]

PATROL_CAPABILITIES = [
    Capability(
        id="patrol.security.routine",
        name="常规巡逻",
        category="patrol",
        action="patrol",
        parameters={"route_id": {"type": "string", "required": True}},
        constraints={},
        description="按预设路线进行安全巡逻"
    )
]


class CapabilityRegistry:
    """
    能力注册表

    管理系统中所有能力定义和 Agent 能力映射
    """

    def __init__(self, federation_client=None):
        self._federation_client = federation_client
        self._capabilities: Dict[str, Capability] = {}
        self._agent_capabilities: Dict[str, AgentCapabilityInfo] = {}

    def register_capability(self, capability: Capability) -> None:
        """注册能力定义"""
        self._capabilities[capability.id] = capability
        logger.debug(f"Registered capability: {capability.id}")

    def register_agent_capabilities(
        self,
        agent_id: str,
        agent_type: str,
        capability_ids: List[str]
    ) -> None:
        """注册 Agent 的能力"""
        self._agent_capabilities[agent_id] = AgentCapabilityInfo(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capability_ids,
            status="ready",
            last_updated=datetime.utcnow()
        )
        logger.info(f"Registered agent capabilities: {agent_id} -> {capability_ids}")

    def unregister_agent(self, agent_id: str) -> None:
        """注销 Agent"""
        if agent_id in self._agent_capabilities:
            del self._agent_capabilities[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")

    def update_agent_status(
        self,
        agent_id: str,
        status: str,
        current_task: Optional[str] = None
    ) -> None:
        """更新 Agent 状态"""
        if agent_id in self._agent_capabilities:
            info = self._agent_capabilities[agent_id]
            info.status = status
            info.current_task = current_task
            info.last_updated = datetime.utcnow()

    def get_capability(self, capability_id: str) -> Optional[Capability]:
        """获取能力定义"""
        return self._capabilities.get(capability_id)

    def get_agent_capabilities(self, agent_id: str) -> Optional[AgentCapabilityInfo]:
        """获取 Agent 的能力信息"""
        return self._agent_capabilities.get(agent_id)

    def find_agents_by_capability(
        self,
        capability_id: str,
        status: str = "ready"
    ) -> List[AgentCapabilityInfo]:
        """
        按能力查找 Agent

        Args:
            capability_id: 能力 ID，支持通配符如 "cleaning.*"
            status: Agent 状态过滤

        Returns:
            匹配的 Agent 列表
        """
        result = []

        for agent_info in self._agent_capabilities.values():
            if status and agent_info.status != status:
                continue

            for cap_id in agent_info.capabilities:
                if self._match_capability(capability_id, cap_id):
                    result.append(agent_info)
                    break

        return result

    def _match_capability(self, pattern: str, capability_id: str) -> bool:
        """匹配能力 ID"""
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return capability_id.startswith(prefix)
        return pattern == capability_id

    def list_all_capabilities(self) -> List[Capability]:
        """列出所有能力"""
        return list(self._capabilities.values())

    def list_all_agents(self) -> List[AgentCapabilityInfo]:
        """列出所有 Agent"""
        return list(self._agent_capabilities.values())
