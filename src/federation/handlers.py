"""
Federation Event Handlers - 事件处理器
"""

import logging
import re
from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger("ecis_robot.federation.handlers")


@dataclass
class OrchestrationTask:
    """编排任务"""
    task_id: str
    task_type: str
    required_capability: str
    parameters: Dict[str, Any]
    priority: int = 0
    timeout: int = 3600


class EventHandler:
    """
    事件处理器

    接收并处理来自 Federation Gateway 的事件
    """

    def __init__(self, capability_registry=None, agent_manager=None):
        self._capability_registry = capability_registry
        self._agent_manager = agent_manager
        self._handlers: Dict[str, Callable] = {}

        # 注册默认处理器
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """注册默认处理器"""
        self.register("ecis.orchestration.task.assign", self._handle_task_assign)
        self.register("ecis.robot.command.*", self._handle_robot_command)

    def register(self, pattern: str, handler: Callable) -> None:
        """
        注册事件处理器

        Args:
            pattern: 事件类型模式，支持通配符
            handler: 处理函数
        """
        self._handlers[pattern] = handler
        logger.info(f"Registered handler for pattern: {pattern}")

    async def handle(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理事件

        Args:
            event: CloudEvents 格式事件

        Returns:
            处理结果
        """
        event_type = event.get("type", "")

        for pattern, handler in self._handlers.items():
            if self._match_pattern(pattern, event_type):
                try:
                    return await handler(event)
                except Exception as e:
                    logger.error(f"Handler error for {event_type}: {e}")
                    return {"status": "error", "message": str(e)}

        logger.warning(f"No handler found for event type: {event_type}")
        return None

    def _match_pattern(self, pattern: str, event_type: str) -> bool:
        """匹配事件类型模式"""
        if "*" in pattern:
            regex = pattern.replace(".", r"\.").replace("*", ".*")
            return bool(re.match(f"^{regex}$", event_type))
        return pattern == event_type

    async def _handle_task_assign(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务分配事件"""
        data = event.get("data", {})

        task = OrchestrationTask(
            task_id=data.get("task_id"),
            task_type=data.get("task_type"),
            required_capability=data.get("required_capability"),
            parameters=data.get("parameters", {}),
            priority=data.get("priority", 0),
            timeout=data.get("timeout", 3600)
        )

        # 查找可用 Agent
        if self._capability_registry:
            agents = self._capability_registry.find_agents_by_capability(
                task.required_capability,
                status="ready"
            )

            if not agents:
                return {
                    "status": "rejected",
                    "reason": "no_available_agent",
                    "task_id": task.task_id
                }

            # 选择最佳 Agent
            selected_agent = self._select_best_agent(agents)

            # 获取 Agent 实例并分配任务
            if self._agent_manager:
                agent = self._agent_manager.get_agent(selected_agent.agent_id)
                if agent and hasattr(agent, "receive_orchestration_task"):
                    response = await agent.receive_orchestration_task(task)
                    return {
                        "status": response.status,
                        "reason": response.reason,
                        "task_id": task.task_id,
                        "agent_id": selected_agent.agent_id
                    }

        return {
            "status": "rejected",
            "reason": "capability_registry_unavailable",
            "task_id": task.task_id
        }

    async def _handle_robot_command(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """处理机器人命令事件"""
        event_type = event.get("type", "")
        data = event.get("data", {})
        agent_id = data.get("agent_id")

        # 解析命令
        command = event_type.split(".")[-1]  # e.g., "pause", "resume", "cancel"

        if self._agent_manager:
            agent = self._agent_manager.get_agent(agent_id)
            if agent:
                if command == "pause" and hasattr(agent, "pause"):
                    await agent.pause()
                    return {"status": "success", "command": command}
                elif command == "resume" and hasattr(agent, "resume"):
                    await agent.resume()
                    return {"status": "success", "command": command}
                elif command == "cancel" and hasattr(agent, "cancel"):
                    await agent.cancel()
                    return {"status": "success", "command": command}
                elif command == "return_home" and hasattr(agent, "return_home"):
                    await agent.return_home()
                    return {"status": "success", "command": command}

        return {
            "status": "failed",
            "reason": "agent_not_found",
            "agent_id": agent_id
        }

    def _select_best_agent(self, agents: List) -> Any:
        """
        选择最佳 Agent（简单负载均衡）

        策略：选择第一个状态为 ready 的 Agent
        """
        for agent in agents:
            if agent.status == "ready":
                return agent
        return agents[0] if agents else None
