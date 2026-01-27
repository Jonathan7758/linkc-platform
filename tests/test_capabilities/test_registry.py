"""
Capabilities Registry Tests
"""

import pytest
from datetime import datetime


class TestCapabilityRegistry:
    """CapabilityRegistry 测试"""

    def test_register_capability(self):
        """注册能力测试"""
        from src.capabilities.registry import CapabilityRegistry, CLEANING_CAPABILITIES

        registry = CapabilityRegistry()
        cap = CLEANING_CAPABILITIES[0]
        registry.register_capability(cap)

        result = registry.get_capability(cap.id)
        assert result is not None
        assert result.id == cap.id
        assert result.name == cap.name

    def test_register_agent_capabilities(self):
        """注册 Agent 能力测试"""
        from src.capabilities.registry import CapabilityRegistry

        registry = CapabilityRegistry()
        registry.register_agent_capabilities(
            agent_id="robot-001",
            agent_type="cleaning",
            capability_ids=["cleaning.floor.vacuum", "cleaning.floor.mop"]
        )

        info = registry.get_agent_capabilities("robot-001")
        assert info is not None
        assert info.agent_id == "robot-001"
        assert info.agent_type == "cleaning"
        assert len(info.capabilities) == 2

    def test_find_agents_by_capability(self):
        """按能力查找 Agent 测试"""
        from src.capabilities.registry import CapabilityRegistry, CLEANING_CAPABILITIES

        registry = CapabilityRegistry()

        # 注册能力
        for cap in CLEANING_CAPABILITIES:
            registry.register_capability(cap)

        # 注册 Agent
        registry.register_agent_capabilities(
            agent_id="robot-001",
            agent_type="cleaning",
            capability_ids=["cleaning.floor.vacuum"]
        )
        registry.register_agent_capabilities(
            agent_id="robot-002",
            agent_type="cleaning",
            capability_ids=["cleaning.floor.mop"]
        )

        # 查找具有 vacuum 能力的 Agent
        agents = registry.find_agents_by_capability("cleaning.floor.vacuum")
        assert len(agents) == 1
        assert agents[0].agent_id == "robot-001"

    def test_find_agents_by_capability_wildcard(self):
        """通配符查找 Agent 测试"""
        from src.capabilities.registry import CapabilityRegistry

        registry = CapabilityRegistry()
        registry.register_agent_capabilities(
            agent_id="robot-001",
            agent_type="cleaning",
            capability_ids=["cleaning.floor.vacuum"]
        )
        registry.register_agent_capabilities(
            agent_id="robot-002",
            agent_type="delivery",
            capability_ids=["delivery.package.small"]
        )

        # 使用通配符查找所有清洁能力的 Agent
        agents = registry.find_agents_by_capability("cleaning.*")
        assert len(agents) == 1
        assert agents[0].agent_id == "robot-001"

    def test_update_agent_status(self):
        """更新 Agent 状态测试"""
        from src.capabilities.registry import CapabilityRegistry

        registry = CapabilityRegistry()
        registry.register_agent_capabilities(
            agent_id="robot-001",
            agent_type="cleaning",
            capability_ids=["cleaning.floor.vacuum"]
        )

        # 初始状态
        info = registry.get_agent_capabilities("robot-001")
        assert info.status == "ready"

        # 更新状态
        registry.update_agent_status("robot-001", "busy", "task-123")

        info = registry.get_agent_capabilities("robot-001")
        assert info.status == "busy"
        assert info.current_task == "task-123"

    def test_unregister_agent(self):
        """注销 Agent 测试"""
        from src.capabilities.registry import CapabilityRegistry

        registry = CapabilityRegistry()
        registry.register_agent_capabilities(
            agent_id="robot-001",
            agent_type="cleaning",
            capability_ids=["cleaning.floor.vacuum"]
        )

        # 注销
        registry.unregister_agent("robot-001")

        info = registry.get_agent_capabilities("robot-001")
        assert info is None

    def test_list_all_capabilities(self):
        """列出所有能力测试"""
        from src.capabilities.registry import CapabilityRegistry, CLEANING_CAPABILITIES

        registry = CapabilityRegistry()
        for cap in CLEANING_CAPABILITIES:
            registry.register_capability(cap)

        caps = registry.list_all_capabilities()
        assert len(caps) == len(CLEANING_CAPABILITIES)


class TestCapabilityService:
    """CapabilityService 测试"""

    def test_init_default_capabilities(self):
        """初始化默认能力测试"""
        from src.capabilities.service import CapabilityService

        service = CapabilityService()
        caps = service.list_all_capabilities()

        # 应该有预定义的清洁、配送和巡逻能力
        assert len(caps) > 0

        # 验证能力 ID 格式
        cap_ids = [c.id for c in caps]
        assert any(c.startswith("cleaning.") for c in cap_ids)
        assert any(c.startswith("delivery.") for c in cap_ids)
