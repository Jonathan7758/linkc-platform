"""
MS8 Demo Enhancement - Integration Tests
演示模块集成测试

测试范围:
- DM1 + DM2: 数据服务与模拟引擎协同
- DM2 + DM4: 模拟引擎与Agent对话协同
- 完整演示流程端到端测试
- API端点集成测试
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime

# Import all demo modules
from src.demo.data_service import DemoDataService
from src.demo.simulation_engine import SimulationEngine
from src.demo.agent_conversations import (
    AgentConversationService,
    ConversationScenario,
    AgentResponse
)
from src.demo.scenarios import DemoScenario, DemoEvent


class TestDM1DM2Integration:
    """DM1数据服务 + DM2模拟引擎 集成测试"""

    @pytest_asyncio.fixture
    async def services(self):
        """创建测试用服务实例"""
        # Reset singletons
        DemoDataService._instance = None
        SimulationEngine._instance = None

        data_service = DemoDataService()
        sim_engine = SimulationEngine()

        yield data_service, sim_engine

        # Cleanup
        if sim_engine.is_running:
            await sim_engine.stop()
        DemoDataService._instance = None
        SimulationEngine._instance = None

    @pytest.mark.asyncio
    async def test_simulation_uses_demo_data(self, services):
        """测试模拟引擎使用演示数据"""
        data_service, sim_engine = services

        # Initialize demo data (async)
        await data_service.init_demo_data()

        # Get robots from data service (sync)
        robots = data_service.get_robots()
        robot_list = list(robots.values())
        assert len(robot_list) > 0

        # Setup simulation with demo service
        sim_engine.setup_from_demo_service(data_service)

        # Verify simulation has the robots
        states = sim_engine.get_all_states()
        assert len(states) == len(robot_list)

    @pytest.mark.asyncio
    async def test_scenario_switch_affects_simulation(self, services):
        """测试场景切换影响模拟状态"""
        data_service, sim_engine = services

        # Initialize with default scenario
        await data_service.init_demo_data()
        sim_engine.setup_from_demo_service(data_service)

        # Switch to ops_alert scenario
        await data_service.switch_scenario(DemoScenario.OPERATIONS_ALERT)

        # Verify data service reflects scenario
        status = data_service.get_status()
        assert status['current_scenario'] == DemoScenario.OPERATIONS_ALERT.value

    @pytest.mark.asyncio
    async def test_event_propagation(self, services):
        """测试事件从数据服务传播"""
        data_service, sim_engine = services

        await data_service.init_demo_data()
        sim_engine.setup_from_demo_service(data_service)

        # Get a robot
        robots = data_service.get_robots()
        robot_id = list(robots.keys())[0]

        # Trigger low battery event in data service
        result = await data_service.trigger_event(DemoEvent.ROBOT_LOW_BATTERY, robot_id=robot_id)
        assert result['success'] is True

        # Verify robot battery is updated in data service
        updated_robots = data_service.get_robots()
        assert updated_robots[robot_id]['battery'] <= 20

    @pytest.mark.asyncio
    async def test_simulation_state_sync(self, services):
        """测试模拟状态运行"""
        data_service, sim_engine = services

        await data_service.init_demo_data()
        sim_engine.setup_from_demo_service(data_service)

        # Start simulation briefly
        await sim_engine.start()
        await asyncio.sleep(0.2)
        await sim_engine.stop()

        # Get simulation states (returns a list)
        sim_states = sim_engine.get_all_states()

        # All robots should have valid states
        for state in sim_states:
            assert state['position']['x'] >= 0
            assert state['position']['y'] >= 0
            assert 0 <= state['battery'] <= 100


class TestDM2DM4Integration:
    """DM2模拟引擎 + DM4 Agent对话 集成测试"""

    @pytest_asyncio.fixture
    async def services(self):
        """创建测试用服务实例"""
        DemoDataService._instance = None
        SimulationEngine._instance = None
        AgentConversationService._instance = None

        data_service = DemoDataService()
        sim_engine = SimulationEngine()
        agent_service = AgentConversationService()

        # Initialize demo data
        await data_service.init_demo_data()
        sim_engine.setup_from_demo_service(data_service)

        yield sim_engine, agent_service

        if sim_engine.is_running:
            await sim_engine.stop()
        DemoDataService._instance = None
        SimulationEngine._instance = None
        AgentConversationService._instance = None

    @pytest.mark.asyncio
    async def test_agent_can_query_robot_status(self, services):
        """测试Agent可以查询机器人状态"""
        sim_engine, agent_service = services

        # Query through agent
        response = await agent_service.process_message(
            session_id="test_integration_1",
            user_message="现在有哪些机器人空闲",
            scenario=ConversationScenario.STATUS_QUERY
        )

        assert isinstance(response, AgentResponse)
        assert len(response.reasoning_steps) > 0

    @pytest.mark.asyncio
    async def test_agent_task_scheduling_with_simulation(self, services):
        """测试Agent任务调度与模拟引擎交互"""
        sim_engine, agent_service = services

        # Schedule task through agent
        response = await agent_service.process_message(
            session_id="test_integration_2",
            user_message="安排大堂清洁任务",
            scenario=ConversationScenario.TASK_SCHEDULING
        )

        assert response.requires_confirmation is True
        assert len(response.actions) > 0

    @pytest.mark.asyncio
    async def test_agent_batch_operation(self, services):
        """测试Agent批量操作"""
        sim_engine, agent_service = services

        # Batch operation through agent
        response = await agent_service.process_message(
            session_id="test_integration_3",
            user_message="把所有电量低于50%的机器人召回充电",
            scenario=ConversationScenario.BATCH_OPERATION
        )

        assert response.requires_confirmation is True


class TestFullDemoFlow:
    """完整演示流程端到端测试"""

    @pytest_asyncio.fixture
    async def all_services(self):
        """创建所有服务实例"""
        DemoDataService._instance = None
        SimulationEngine._instance = None
        AgentConversationService._instance = None

        data_service = DemoDataService()
        sim_engine = SimulationEngine()
        agent_service = AgentConversationService()

        yield data_service, sim_engine, agent_service

        if sim_engine.is_running:
            await sim_engine.stop()
        DemoDataService._instance = None
        SimulationEngine._instance = None
        AgentConversationService._instance = None

    @pytest.mark.asyncio
    async def test_complete_demo_initialization(self, all_services):
        """测试完整演示初始化流程"""
        data_service, sim_engine, agent_service = all_services

        # Step 1: Initialize demo data
        await data_service.init_demo_data()
        status = data_service.get_status()
        assert status['is_active'] is True

        # Step 2: Get demo data
        buildings = data_service.get_buildings()
        robots = data_service.get_robots()
        tasks = data_service.get_tasks()

        assert len(buildings) >= 3
        assert len(robots) >= 8
        assert len(tasks) > 0

        # Step 3: Setup simulation
        sim_engine.setup_from_demo_service(data_service)
        states = sim_engine.get_all_states()
        assert len(states) == len(robots)

        # Step 4: Get agent scenarios
        scenarios = agent_service.get_preset_scenarios()
        assert len(scenarios) == 5

    @pytest.mark.asyncio
    async def test_executive_demo_scenario(self, all_services):
        """测试高管演示场景完整流程"""
        data_service, sim_engine, agent_service = all_services

        # Initialize for executive demo
        await data_service.init_demo_data()
        await data_service.switch_scenario(DemoScenario.EXECUTIVE_OVERVIEW)

        sim_engine.setup_from_demo_service(data_service)

        # Start simulation
        await sim_engine.start()

        # Run for a short time
        await asyncio.sleep(0.3)

        # Query KPI through data service
        kpi = data_service.get_kpi()
        assert 'task_completion_rate' in kpi
        assert 'robot_utilization' in kpi

        # Stop simulation
        await sim_engine.stop()

    @pytest.mark.asyncio
    async def test_ops_demo_with_agent_interaction(self, all_services):
        """测试运营演示场景含Agent交互"""
        data_service, sim_engine, agent_service = all_services

        # Initialize
        await data_service.init_demo_data()
        await data_service.switch_scenario(DemoScenario.OPERATIONS_NORMAL)

        sim_engine.setup_from_demo_service(data_service)
        await sim_engine.start()

        # Agent interaction - query status
        response1 = await agent_service.process_message(
            session_id="ops_demo_1",
            user_message="现在机器人状态怎么样",
            scenario=ConversationScenario.STATUS_QUERY
        )
        assert response1 is not None

        # Agent interaction - schedule task
        response2 = await agent_service.process_message(
            session_id="ops_demo_1",
            user_message="安排会议室清洁",
            scenario=ConversationScenario.TASK_SCHEDULING
        )
        assert response2.requires_confirmation is True

        await sim_engine.stop()

    @pytest.mark.asyncio
    async def test_alert_scenario_handling(self, all_services):
        """测试告警场景处理流程"""
        data_service, sim_engine, agent_service = all_services

        # Initialize with alert scenario
        await data_service.init_demo_data()
        await data_service.switch_scenario(DemoScenario.OPERATIONS_ALERT)

        robots = data_service.get_robots()
        robot_id = list(robots.keys())[0]
        robot_name = robots[robot_id]['name']

        # Trigger an error event
        await data_service.trigger_event(DemoEvent.ROBOT_ERROR, robot_id=robot_id)

        # Agent diagnoses the problem
        response = await agent_service.process_message(
            session_id="alert_demo_1",
            user_message=f"机器人{robot_name}怎么了",
            scenario=ConversationScenario.PROBLEM_DIAGNOSIS
        )

        assert len(response.reasoning_steps) > 0
        # Should have diagnostic steps
        actions = [s.action for s in response.reasoning_steps]
        assert any('diagnose' in a or 'analyze' in a for a in actions)

    @pytest.mark.asyncio
    async def test_demo_reset_and_restart(self, all_services):
        """测试演示重置和重启"""
        data_service, sim_engine, agent_service = all_services

        # First initialization
        await data_service.init_demo_data()
        robots1 = data_service.get_robots()
        sim_engine.setup_from_demo_service(data_service)
        await sim_engine.start()
        await asyncio.sleep(0.1)
        await sim_engine.stop()

        # Reset
        await data_service.reset_demo()

        # Second initialization
        await data_service.init_demo_data()
        robots2 = data_service.get_robots()
        sim_engine.setup_from_demo_service(data_service)

        # Should have fresh data
        assert len(robots2) == len(robots1)


class TestAPIEndpointsIntegration:
    """API端点集成测试 (模拟FastAPI请求)"""

    @pytest_asyncio.fixture
    async def services(self):
        """创建服务实例"""
        DemoDataService._instance = None
        SimulationEngine._instance = None
        AgentConversationService._instance = None

        data_service = DemoDataService()
        sim_engine = SimulationEngine()
        agent_service = AgentConversationService()

        # Initialize
        await data_service.init_demo_data()
        sim_engine.setup_from_demo_service(data_service)

        yield {
            'data': data_service,
            'sim': sim_engine,
            'agent': agent_service
        }

        if sim_engine.is_running:
            await sim_engine.stop()
        DemoDataService._instance = None
        SimulationEngine._instance = None
        AgentConversationService._instance = None

    @pytest.mark.asyncio
    async def test_demo_status_endpoint(self, services):
        """测试 GET /api/v1/demo/status"""
        data_service = services['data']

        status = data_service.get_status()

        assert 'is_active' in status
        assert 'current_scenario' in status
        assert status['is_active'] is True

    @pytest.mark.asyncio
    async def test_demo_buildings_endpoint(self, services):
        """测试 GET /api/v1/demo/buildings"""
        data_service = services['data']

        buildings = data_service.get_buildings()

        assert len(buildings) >= 3
        for building_id, building in buildings.items():
            assert 'name' in building

    @pytest.mark.asyncio
    async def test_demo_robots_endpoint(self, services):
        """测试 GET /api/v1/demo/robots"""
        data_service = services['data']

        robots = data_service.get_robots()

        assert len(robots) >= 8
        for robot_id, robot in robots.items():
            assert 'status' in robot
            assert 'battery' in robot

    @pytest.mark.asyncio
    async def test_simulation_status_endpoint(self, services):
        """测试 GET /api/v1/simulation/status"""
        sim_engine = services['sim']

        status = sim_engine.get_status()

        assert 'running' in status
        assert 'robots_count' in status
        assert 'speed' in status

    @pytest.mark.asyncio
    async def test_simulation_start_stop_endpoints(self, services):
        """测试 POST /api/v1/simulation/start 和 stop"""
        sim_engine = services['sim']

        # Start
        await sim_engine.start()
        assert sim_engine.is_running is True

        # Stop
        await sim_engine.stop()
        assert sim_engine.is_running is False

    @pytest.mark.asyncio
    async def test_agent_scenarios_endpoint(self, services):
        """测试 GET /api/v1/agent-demo/scenarios"""
        agent_service = services['agent']

        scenarios = agent_service.get_preset_scenarios()

        assert len(scenarios) == 5
        scenario_ids = [s['id'] for s in scenarios]
        assert 'task_scheduling' in scenario_ids
        assert 'status_query' in scenario_ids

    @pytest.mark.asyncio
    async def test_agent_chat_endpoint(self, services):
        """测试 POST /api/v1/agent-demo/chat"""
        agent_service = services['agent']

        response = await agent_service.process_message(
            session_id="api_test_1",
            user_message="查询机器人状态",
            scenario=ConversationScenario.STATUS_QUERY
        )

        response_dict = response.to_dict()

        assert 'message' in response_dict
        assert 'reasoning_steps' in response_dict
        assert len(response_dict['reasoning_steps']) > 0

    @pytest.mark.asyncio
    async def test_agent_confirm_endpoint(self, services):
        """测试 POST /api/v1/agent-demo/confirm"""
        agent_service = services['agent']

        # First create a pending action
        await agent_service.process_message(
            session_id="api_test_2",
            user_message="安排清洁任务",
            scenario=ConversationScenario.TASK_SCHEDULING
        )

        # Confirm
        result = await agent_service.confirm_action(
            session_id="api_test_2",
            confirmed=True
        )

        assert result['confirmed'] is True

    @pytest.mark.asyncio
    async def test_agent_feedback_endpoint(self, services):
        """测试 POST /api/v1/agent-demo/feedback"""
        agent_service = services['agent']

        result = await agent_service.record_learning(
            session_id="api_test_3",
            feedback="这个区域应该用拖地机器人"
        )

        assert result['success'] is True
        assert 'learning_id' in result


class TestConcurrentOperations:
    """并发操作测试"""

    @pytest_asyncio.fixture
    async def services(self):
        """创建服务实例"""
        DemoDataService._instance = None
        SimulationEngine._instance = None
        AgentConversationService._instance = None

        data_service = DemoDataService()
        sim_engine = SimulationEngine()
        agent_service = AgentConversationService()

        await data_service.init_demo_data()
        sim_engine.setup_from_demo_service(data_service)

        yield data_service, sim_engine, agent_service

        if sim_engine.is_running:
            await sim_engine.stop()
        DemoDataService._instance = None
        SimulationEngine._instance = None
        AgentConversationService._instance = None

    @pytest.mark.asyncio
    async def test_concurrent_agent_sessions(self, services):
        """测试并发Agent会话"""
        _, _, agent_service = services

        # Create multiple concurrent sessions
        tasks = [
            agent_service.process_message(
                session_id=f"concurrent_{i}",
                user_message="查询状态",
                scenario=ConversationScenario.STATUS_QUERY
            )
            for i in range(5)
        ]

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 5
        for response in responses:
            assert isinstance(response, AgentResponse)

    @pytest.mark.asyncio
    async def test_simulation_with_concurrent_queries(self, services):
        """测试模拟运行时的并发查询"""
        data_service, sim_engine, agent_service = services

        # Start simulation
        await sim_engine.start()

        # Concurrent queries while simulation runs
        async def query_status():
            return sim_engine.get_all_states()

        async def query_agent():
            return await agent_service.process_message(
                session_id=f"concurrent_sim_{datetime.now().timestamp()}",
                user_message="状态如何",
                scenario=ConversationScenario.STATUS_QUERY
            )

        tasks = [query_status() for _ in range(3)] + [query_agent() for _ in range(3)]
        results = await asyncio.gather(*tasks)

        await sim_engine.stop()

        assert len(results) == 6


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
