"""
DM1: 演示数据服务单元测试

测试范围:
- 演示数据初始化
- 场景切换
- 事件触发
- 数据查询
- 状态管理
"""

import pytest
import pytest_asyncio
from datetime import datetime
from copy import deepcopy

# 测试用的演示服务类
from src.demo.data_service import DemoDataService, DemoStatus
from src.demo.seed_data import DemoSeedData
from src.demo.scenarios import DemoScenario, DemoEvent, get_scenario_config


class TestDemoSeedData:
    """测试种子数据生成"""

    def test_get_buildings(self):
        """测试楼宇数据"""
        buildings = DemoSeedData.get_buildings()
        assert len(buildings) == 3
        assert "building_001" in buildings
        assert "building_002" in buildings
        assert "building_003" in buildings

        # 验证楼宇属性
        b1 = buildings["building_001"]
        assert b1["name"] == "环球贸易广场"
        assert b1["total_floors"] == 10
        assert b1["robot_count"] == 3

    def test_get_floors(self):
        """测试楼层数据"""
        floors = DemoSeedData.get_floors()
        # 3楼宇共 10 + 8 + 6 = 24 层
        assert len(floors) == 24

        # 验证楼层属性
        floor_1 = floors["floor_001"]
        assert floor_1["building_id"] == "building_001"
        assert floor_1["floor_number"] == 1

    def test_get_zones(self):
        """测试区域数据"""
        zones = DemoSeedData.get_zones()
        # 每层5个区域, 24层 = 120个区域
        assert len(zones) == 120

        # 验证区域类型
        zone_types = set(z["zone_type"] for z in zones.values())
        assert "lobby" in zone_types
        assert "corridor" in zone_types
        assert "office" in zone_types

    def test_get_robots(self):
        """测试机器人数据"""
        robots = DemoSeedData.get_robots()
        assert len(robots) == 8

        # 验证机器人分布
        building_001_robots = [r for r in robots.values() if r["building_id"] == "building_001"]
        building_002_robots = [r for r in robots.values() if r["building_id"] == "building_002"]
        building_003_robots = [r for r in robots.values() if r["building_id"] == "building_003"]

        assert len(building_001_robots) == 3
        assert len(building_002_robots) == 3
        assert len(building_003_robots) == 2

        # 验证机器人属性
        robot_001 = robots["robot_001"]
        assert robot_001["name"] == "清洁机器人 A-01"
        assert robot_001["model"] == "GS-50 Pro"
        assert "battery" in robot_001
        assert "status" in robot_001

    def test_get_tasks(self):
        """测试任务数据"""
        tasks = DemoSeedData.get_tasks(days=7)

        # 应该有较多任务 (7天 * 15-20个 + 今日任务)
        assert len(tasks) > 100

        # 验证任务状态分布
        statuses = [t["status"] for t in tasks]
        assert "completed" in statuses
        assert "in_progress" in statuses
        assert "pending" in statuses

    def test_get_kpi_data(self):
        """测试KPI数据"""
        kpi = DemoSeedData.get_kpi_data()

        assert kpi["task_completion_rate"] == 96.8
        assert kpi["robot_utilization"] == 87.2
        assert kpi["monthly_cost_savings"] == 428600
        assert kpi["customer_satisfaction"] == 4.8

        # 验证健康度评分
        assert kpi["health_score"]["overall"] == 92

        # 验证趋势数据
        assert len(kpi["trends"]["dates"]) == 7
        assert len(kpi["trends"]["task_completion"]) == 7

    def test_get_all_demo_data(self):
        """测试完整数据集"""
        data = DemoSeedData.get_all_demo_data()

        assert "buildings" in data
        assert "floors" in data
        assert "zones" in data
        assert "robots" in data
        assert "tasks" in data
        assert "alerts" in data
        assert "kpi" in data
        assert "tenant_id" in data


class TestDemoScenarios:
    """测试演示场景"""

    def test_scenario_enum(self):
        """测试场景枚举"""
        assert DemoScenario.EXECUTIVE_OVERVIEW.value == "executive"
        assert DemoScenario.OPERATIONS_NORMAL.value == "ops_normal"
        assert DemoScenario.FULL_DEMO.value == "full"

    def test_scenario_descriptions(self):
        """测试场景描述"""
        desc = DemoScenario.get_description(DemoScenario.EXECUTIVE_OVERVIEW)
        assert "高管视角" in desc

    def test_event_enum(self):
        """测试事件枚举"""
        assert DemoEvent.ROBOT_LOW_BATTERY.value == "low_battery"
        assert DemoEvent.ROBOT_OBSTACLE.value == "obstacle"

    def test_event_config(self):
        """测试事件配置"""
        config = DemoEvent.get_event_config(DemoEvent.ROBOT_LOW_BATTERY)
        assert config["battery_level"] == 15
        assert config["severity"] == "warning"

    def test_scenario_config(self):
        """测试场景配置"""
        config = get_scenario_config(DemoScenario.EXECUTIVE_OVERVIEW)
        assert config["name"] == "高管视角"
        assert config["duration_minutes"] == 3
        assert config["start_page"] == "/executive"


class TestDemoDataService:
    """测试演示数据服务"""

    @pytest_asyncio.fixture
    async def service(self):
        """创建测试用服务实例"""
        # 重置单例
        DemoDataService._instance = None
        svc = DemoDataService()
        yield svc
        # 清理
        DemoDataService._instance = None

    @pytest.mark.asyncio
    async def test_init_demo_data(self, service):
        """测试初始化演示数据"""
        result = await service.init_demo_data(DemoScenario.FULL_DEMO)

        assert result["success"] is True
        assert result["scenario"] == "full"
        assert result["stats"]["buildings"] == 3
        assert result["stats"]["robots"] == 8
        assert result["stats"]["tasks"] > 0

        # 验证状态
        assert service.status.is_active is True
        assert service.status.current_scenario == DemoScenario.FULL_DEMO

    @pytest.mark.asyncio
    async def test_reset_demo(self, service):
        """测试重置演示"""
        # 先初始化
        await service.init_demo_data()

        # 修改一些数据
        robots = service.get_robots()
        robot_id = list(robots.keys())[0]
        service.update_robot(robot_id, {"battery": 10})

        # 重置
        result = await service.reset_demo()
        assert result["success"] is True

        # 验证数据已恢复
        robot = service.get_robot(robot_id)
        assert robot["battery"] != 10

    @pytest.mark.asyncio
    async def test_switch_scenario(self, service):
        """测试切换场景"""
        await service.init_demo_data(DemoScenario.FULL_DEMO)

        result = await service.switch_scenario(DemoScenario.EXECUTIVE_OVERVIEW)

        assert result["success"] is True
        assert result["scenario"] == "executive"
        assert service.status.current_scenario == DemoScenario.EXECUTIVE_OVERVIEW

    @pytest.mark.asyncio
    async def test_trigger_low_battery_event(self, service):
        """测试触发低电量事件"""
        await service.init_demo_data()

        result = await service.trigger_event(DemoEvent.ROBOT_LOW_BATTERY, "robot_001")

        assert result["success"] is True
        assert result["battery_level"] == 15

        # 验证机器人状态已更新
        robot = service.get_robot("robot_001")
        assert robot["battery"] == 15
        assert robot["status"] == "returning"

        # 验证告警已创建
        alerts = service.get_alerts(status="active")
        assert len(alerts) > 0
        alert = [a for a in alerts if a["robot_id"] == "robot_001"]
        assert len(alert) > 0

    @pytest.mark.asyncio
    async def test_trigger_obstacle_event(self, service):
        """测试触发障碍物事件"""
        await service.init_demo_data()

        result = await service.trigger_event(DemoEvent.ROBOT_OBSTACLE, "robot_004")

        assert result["success"] is True
        assert result["robot_status"] == "paused"

        robot = service.get_robot("robot_004")
        assert robot["status"] == "paused"

    @pytest.mark.asyncio
    async def test_trigger_urgent_task_event(self, service):
        """测试触发紧急任务事件"""
        await service.init_demo_data()

        result = await service.trigger_event(DemoEvent.NEW_URGENT_TASK)

        assert result["success"] is True
        assert "task_id" in result
        assert "robot_id" in result

        # 验证任务已创建
        tasks = service.get_tasks(status="in_progress")
        urgent_tasks = [t for t in tasks if t["priority"] == "urgent"]
        assert len(urgent_tasks) > 0

    @pytest.mark.asyncio
    async def test_trigger_charging_complete_event(self, service):
        """测试触发充电完成事件"""
        await service.init_demo_data()

        # 先让机器人充电
        service.update_robot("robot_003", {"status": "charging", "battery": 35})

        result = await service.trigger_event(DemoEvent.CHARGING_COMPLETE, "robot_003")

        assert result["success"] is True
        assert result["battery_level"] == 100

        robot = service.get_robot("robot_003")
        assert robot["battery"] == 100
        assert robot["status"] == "idle"

    @pytest.mark.asyncio
    async def test_get_buildings(self, service):
        """测试获取楼宇"""
        await service.init_demo_data()

        buildings = service.get_buildings()
        assert len(buildings) == 3

    @pytest.mark.asyncio
    async def test_get_floors_by_building(self, service):
        """测试按楼宇获取楼层"""
        await service.init_demo_data()

        floors = service.get_floors("building_001")
        assert len(floors) == 10  # 环球贸易广场10层

    @pytest.mark.asyncio
    async def test_get_robots_by_status(self, service):
        """测试按状态获取机器人"""
        await service.init_demo_data()

        working_robots = service.get_robots(status="working")
        assert len(working_robots) > 0

        all_robots = service.get_robots()
        assert len(all_robots) == 8

    @pytest.mark.asyncio
    async def test_get_tasks_by_status(self, service):
        """测试按状态获取任务"""
        await service.init_demo_data()

        pending_tasks = service.get_tasks(status="pending")
        in_progress_tasks = service.get_tasks(status="in_progress")
        completed_tasks = service.get_tasks(status="completed")

        assert len(pending_tasks) > 0
        assert len(in_progress_tasks) > 0
        assert len(completed_tasks) > 0

    @pytest.mark.asyncio
    async def test_get_kpi(self, service):
        """测试获取KPI"""
        await service.init_demo_data()

        kpi = service.get_kpi()
        assert kpi["task_completion_rate"] == 96.8
        assert "health_score" in kpi
        assert "trends" in kpi

    @pytest.mark.asyncio
    async def test_simulation_speed(self, service):
        """测试模拟速度设置"""
        service.set_simulation_speed(2.0)
        assert service.status.simulation_speed == 2.0

        service.set_simulation_speed(0.5)
        assert service.status.simulation_speed == 0.5

    @pytest.mark.asyncio
    async def test_auto_events_toggle(self, service):
        """测试自动事件开关"""
        service.set_auto_events(False)
        assert service.status.auto_events_enabled is False

        service.set_auto_events(True)
        assert service.status.auto_events_enabled is True

    @pytest.mark.asyncio
    async def test_update_robot(self, service):
        """测试更新机器人状态"""
        await service.init_demo_data()

        success = service.update_robot("robot_001", {
            "battery": 50,
            "status": "idle"
        })
        assert success is True

        robot = service.get_robot("robot_001")
        assert robot["battery"] == 50
        assert robot["status"] == "idle"

    @pytest.mark.asyncio
    async def test_status_tracking(self, service):
        """测试状态追踪"""
        await service.init_demo_data()

        # 触发一些事件
        await service.trigger_event(DemoEvent.ROBOT_LOW_BATTERY)
        await service.trigger_event(DemoEvent.TASK_COMPLETED)

        status = service.get_status()
        assert status["is_active"] is True
        assert status["triggered_events_count"] == 2

    @pytest.mark.asyncio
    async def test_event_callback(self, service):
        """测试事件回调"""
        await service.init_demo_data()

        callback_received = []

        async def test_callback(event, result):
            callback_received.append({"event": event, "result": result})

        service.register_event_callback(test_callback)

        await service.trigger_event(DemoEvent.ROBOT_LOW_BATTERY)

        assert len(callback_received) == 1
        assert callback_received[0]["event"] == DemoEvent.ROBOT_LOW_BATTERY


class TestDemoStatus:
    """测试演示状态"""

    def test_status_to_dict(self):
        """测试状态转字典"""
        status = DemoStatus()
        status.is_active = True
        status.current_scenario = DemoScenario.FULL_DEMO
        status.started_at = datetime.now()

        result = status.to_dict()

        assert result["is_active"] is True
        assert result["current_scenario"] == "full"
        assert result["scenario_name"] is not None
        assert result["uptime_seconds"] >= 0


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
