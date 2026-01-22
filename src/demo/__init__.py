"""
演示模块 (Demo Module)

DM1: 演示数据服务 - 管理演示数据
DM2: 实时模拟引擎 - 模拟机器人实时移动
DM4: Agent对话增强 - 预设对话场景和推理展示
"""

from .data_service import DemoDataService, demo_service
from .seed_data import DemoSeedData
from .scenarios import DemoScenario, DemoEvent
from .simulation_engine import SimulationEngine, simulation_engine
from .agent_conversations import AgentConversationService, agent_conversation_service

__all__ = [
    "DemoDataService",
    "demo_service",
    "DemoSeedData",
    "DemoScenario",
    "DemoEvent",
    "SimulationEngine",
    "simulation_engine",
    "AgentConversationService",
    "agent_conversation_service",
]
