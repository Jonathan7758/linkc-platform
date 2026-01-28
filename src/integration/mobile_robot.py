"""
Mobile Robot Integration - 移动机器人集成模块

将无人机和机器狗 Agent 集成到 ECIS 系统
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..federation.client import FederationClient
from ..capabilities.registry import CapabilityRegistry
from ..capabilities.drone import DRONE_CAPABILITIES, get_drone_capability_ids
from ..capabilities.robot_dog import ROBOT_DOG_CAPABILITIES, get_robot_dog_capability_ids
from ..agents.drone_agent import DroneAgent
from ..agents.robot_dog_agent import RobotDogAgent

logger = logging.getLogger("ecis_robot.integration.mobile_robot")


@dataclass
class MobileRobotConfig:
    """移动机器人配置"""
    drone_count: int = 1
    robot_dog_count: int = 1
    auto_register: bool = True
    enable_federation: bool = True


class MobileRobotIntegration:
    """
    移动机器人集成管理器

    负责:
    - 初始化无人机和机器狗 Agent
    - 注册能力到 CapabilityRegistry
    - 注册到 Federation Gateway
    - 管理 Agent 生命周期
    """

    def __init__(
        self,
        config: MobileRobotConfig = None,
        federation_client: FederationClient = None,
        capability_registry: CapabilityRegistry = None
    ):
        self.config = config or MobileRobotConfig()
        self._federation_client = federation_client
        self._capability_registry = capability_registry or CapabilityRegistry()

        self._drone_agents: Dict[str, DroneAgent] = {}
        self._robot_dog_agents: Dict[str, RobotDogAgent] = {}
        self._initialized = False

    @property
    def drone_agents(self) -> Dict[str, DroneAgent]:
        """获取所有无人机 Agent"""
        return self._drone_agents

    @property
    def robot_dog_agents(self) -> Dict[str, RobotDogAgent]:
        """获取所有机器狗 Agent"""
        return self._robot_dog_agents

    @property
    def all_agents(self) -> Dict[str, Any]:
        """获取所有 Agent"""
        return {**self._drone_agents, **self._robot_dog_agents}

    async def initialize(self) -> bool:
        """初始化移动机器人系统"""
        try:
            logger.info("Initializing Mobile Robot Integration...")

            # 注册能力定义
            self._register_capabilities()

            # 创建无人机 Agent
            for i in range(self.config.drone_count):
                agent_id = f"drone-{i+1:03d}"
                agent = DroneAgent(agent_id=agent_id)
                if await agent.start():
                    self._drone_agents[agent_id] = agent
                    logger.info(f"Drone agent {agent_id} started")

                    # 注册到能力注册表
                    self._capability_registry.register_agent_capabilities(
                        agent_id=agent_id,
                        agent_type="drone",
                        capability_ids=get_drone_capability_ids()
                    )

                    # 注册到 Federation
                    if self.config.enable_federation and self._federation_client:
                        await self._register_to_federation(agent_id, "drone", get_drone_capability_ids())
                else:
                    logger.error(f"Failed to start drone agent {agent_id}")

            # 创建机器狗 Agent
            for i in range(self.config.robot_dog_count):
                agent_id = f"robotdog-{i+1:03d}"
                agent = RobotDogAgent(agent_id=agent_id)
                if await agent.start():
                    self._robot_dog_agents[agent_id] = agent
                    logger.info(f"Robot dog agent {agent_id} started")

                    # 注册到能力注册表
                    self._capability_registry.register_agent_capabilities(
                        agent_id=agent_id,
                        agent_type="robot_dog",
                        capability_ids=get_robot_dog_capability_ids()
                    )

                    # 注册到 Federation
                    if self.config.enable_federation and self._federation_client:
                        await self._register_to_federation(agent_id, "robot_dog", get_robot_dog_capability_ids())
                else:
                    logger.error(f"Failed to start robot dog agent {agent_id}")

            self._initialized = True
            logger.info(f"Mobile Robot Integration initialized: {len(self._drone_agents)} drones, {len(self._robot_dog_agents)} robot dogs")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Mobile Robot Integration: {e}")
            return False

    async def shutdown(self) -> None:
        """关闭移动机器人系统"""
        logger.info("Shutting down Mobile Robot Integration...")

        # 停止所有无人机 Agent
        for agent_id, agent in self._drone_agents.items():
            try:
                await agent.stop()
                self._capability_registry.unregister_agent(agent_id)
                logger.info(f"Drone agent {agent_id} stopped")
            except Exception as e:
                logger.error(f"Error stopping drone agent {agent_id}: {e}")

        # 停止所有机器狗 Agent
        for agent_id, agent in self._robot_dog_agents.items():
            try:
                await agent.stop()
                self._capability_registry.unregister_agent(agent_id)
                logger.info(f"Robot dog agent {agent_id} stopped")
            except Exception as e:
                logger.error(f"Error stopping robot dog agent {agent_id}: {e}")

        self._drone_agents.clear()
        self._robot_dog_agents.clear()
        self._initialized = False
        logger.info("Mobile Robot Integration shutdown complete")

    def _register_capabilities(self) -> None:
        """注册能力定义"""
        # 注册无人机能力
        for cap in DRONE_CAPABILITIES:
            self._capability_registry.register_capability(cap)
            logger.debug(f"Registered capability: {cap.id}")

        # 注册机器狗能力
        for cap in ROBOT_DOG_CAPABILITIES:
            self._capability_registry.register_capability(cap)
            logger.debug(f"Registered capability: {cap.id}")

    async def _register_to_federation(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[str]
    ) -> Optional[str]:
        """注册 Agent 到 Federation"""
        if not self._federation_client or not self._federation_client.is_connected:
            logger.debug("Federation client not available, skipping registration")
            return None

        try:
            token = await self._federation_client.register_agent(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=capabilities
            )
            if token:
                logger.info(f"Agent {agent_id} registered to Federation")
            return token
        except Exception as e:
            logger.warning(f"Failed to register agent {agent_id} to Federation: {e}")
            return None

    def get_agent(self, agent_id: str) -> Optional[Any]:
        """获取指定 Agent"""
        if agent_id in self._drone_agents:
            return self._drone_agents[agent_id]
        if agent_id in self._robot_dog_agents:
            return self._robot_dog_agents[agent_id]
        return None

    def get_agents_by_capability(self, capability_id: str) -> List[Any]:
        """按能力获取 Agent 列表"""
        agents = []

        # 检查无人机
        if capability_id.startswith("drone.") or capability_id == "drone.*":
            for agent in self._drone_agents.values():
                if agent._has_capability(capability_id):
                    agents.append(agent)

        # 检查机器狗
        if capability_id.startswith("robotdog.") or capability_id == "robotdog.*":
            for agent in self._robot_dog_agents.values():
                if agent._has_capability(capability_id):
                    agents.append(agent)

        return agents

    def get_available_agents(self, agent_type: str = None) -> List[Any]:
        """获取可用的 Agent 列表"""
        agents = []

        if agent_type is None or agent_type == "drone":
            for agent in self._drone_agents.values():
                if agent.status == "ready":
                    agents.append(agent)

        if agent_type is None or agent_type == "robot_dog":
            for agent in self._robot_dog_agents.values():
                if agent.status == "ready":
                    agents.append(agent)

        return agents

    async def dispatch_task(
        self,
        capability_id: str,
        parameters: Dict[str, Any],
        priority: int = 3
    ) -> Optional[str]:
        """
        分派任务到合适的 Agent

        Returns:
            任务 ID 如果成功，否则 None
        """
        # 查找具备能力的可用 Agent
        agents = self.get_agents_by_capability(capability_id)
        available_agents = [a for a in agents if a.status == "ready"]

        if not available_agents:
            logger.warning(f"No available agent for capability: {capability_id}")
            return None

        # 选择第一个可用的 Agent（可以扩展为更复杂的调度逻辑）
        agent = available_agents[0]

        # 构建任务
        from dataclasses import dataclass

        @dataclass
        class Task:
            task_id: str
            required_capability: str
            parameters: Dict[str, Any]
            priority: int

        import uuid
        task = Task(
            task_id=f"task-{uuid.uuid4().hex[:8]}",
            required_capability=capability_id,
            parameters={**parameters, "capability": capability_id},
            priority=priority
        )

        # 发送任务
        response = await agent.receive_orchestration_task(task)

        if response.status == "accepted":
            logger.info(f"Task {task.task_id} dispatched to {agent.agent_id}")
            return task.task_id
        else:
            logger.warning(f"Task rejected by {agent.agent_id}: {response.reason}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        drone_status = {}
        for agent_id, agent in self._drone_agents.items():
            drone_status[agent_id] = {
                "status": agent.status,
                "capabilities": agent.capabilities,
            }

        robot_dog_status = {}
        for agent_id, agent in self._robot_dog_agents.items():
            robot_dog_status[agent_id] = {
                "status": agent.status,
                "capabilities": agent.capabilities,
            }

        return {
            "initialized": self._initialized,
            "drone_count": len(self._drone_agents),
            "robot_dog_count": len(self._robot_dog_agents),
            "drones": drone_status,
            "robot_dogs": robot_dog_status,
        }


# 全局实例
_mobile_robot_integration: Optional[MobileRobotIntegration] = None


def get_mobile_robot_integration() -> MobileRobotIntegration:
    """获取移动机器人集成实例"""
    global _mobile_robot_integration
    if _mobile_robot_integration is None:
        _mobile_robot_integration = MobileRobotIntegration()
    return _mobile_robot_integration


async def init_mobile_robot_integration(
    config: MobileRobotConfig = None,
    federation_client: FederationClient = None
) -> MobileRobotIntegration:
    """初始化移动机器人集成"""
    global _mobile_robot_integration
    _mobile_robot_integration = MobileRobotIntegration(
        config=config,
        federation_client=federation_client
    )
    await _mobile_robot_integration.initialize()
    return _mobile_robot_integration
