"""
DM1: 演示种子数据 (Demo Seed Data)

包含完整的演示数据集:
- 3个楼宇
- 8台机器人
- 500+历史任务
- KPI数据
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import random
import uuid

class DemoSeedData:
    """演示种子数据生成器"""

    # 租户ID
    DEMO_TENANT_ID = "demo_tenant_001"

    @classmethod
    def get_buildings(cls) -> Dict[str, Dict[str, Any]]:
        """获取楼宇数据"""
        return {
            "building_001": {
                "id": "building_001",
                "tenant_id": cls.DEMO_TENANT_ID,
                "name": "环球贸易广场",
                "address": "香港九龙柯士甸道西1号",
                "total_floors": 10,
                "total_area": 125000.0,
                "robot_count": 3,
                "status": "healthy",
                "created_at": "2025-06-01T00:00:00Z"
            },
            "building_002": {
                "id": "building_002",
                "tenant_id": cls.DEMO_TENANT_ID,
                "name": "国际金融中心",
                "address": "香港中环金融街8号",
                "total_floors": 8,
                "total_area": 98000.0,
                "robot_count": 3,
                "status": "healthy",
                "created_at": "2025-06-15T00:00:00Z"
            },
            "building_003": {
                "id": "building_003",
                "tenant_id": cls.DEMO_TENANT_ID,
                "name": "太古广场",
                "address": "香港金钟道88号",
                "total_floors": 6,
                "total_area": 76000.0,
                "robot_count": 2,
                "status": "attention",  # 有一台机器人维护中
                "created_at": "2025-07-01T00:00:00Z"
            }
        }

    @classmethod
    def get_floors(cls) -> Dict[str, Dict[str, Any]]:
        """获取楼层数据"""
        floors = {}
        floor_idx = 1

        # 环球贸易广场 - 10层
        for i in range(1, 11):
            floor_id = f"floor_{floor_idx:03d}"
            floors[floor_id] = {
                "id": floor_id,
                "building_id": "building_001",
                "floor_number": i,
                "name": f"{i}F",
                "area": 12500.0
            }
            floor_idx += 1

        # 国际金融中心 - 8层
        for i in range(1, 9):
            floor_id = f"floor_{floor_idx:03d}"
            floors[floor_id] = {
                "id": floor_id,
                "building_id": "building_002",
                "floor_number": i,
                "name": f"{i}F",
                "area": 12250.0
            }
            floor_idx += 1

        # 太古广场 - 6层
        for i in range(1, 7):
            floor_id = f"floor_{floor_idx:03d}"
            floors[floor_id] = {
                "id": floor_id,
                "building_id": "building_003",
                "floor_number": i,
                "name": f"{i}F",
                "area": 12666.7
            }
            floor_idx += 1

        return floors

    @classmethod
    def get_zones(cls) -> Dict[str, Dict[str, Any]]:
        """获取区域数据"""
        zones = {}
        zone_idx = 1
        floors = cls.get_floors()

        zone_types = [
            ("lobby", "大堂", 500.0),
            ("corridor", "走廊", 200.0),
            ("office", "办公区", 800.0),
            ("restroom", "洗手间", 50.0),
            ("elevator", "电梯厅", 100.0)
        ]

        for floor_id, floor in floors.items():
            # 每层创建5个区域
            for zone_type, zone_name_base, base_area in zone_types:
                zone_id = f"zone_{zone_idx:03d}"
                zones[zone_id] = {
                    "id": zone_id,
                    "floor_id": floor_id,
                    "name": f"{floor['name']}{zone_name_base}",
                    "zone_type": zone_type,
                    "area": base_area + random.uniform(-50, 100),
                    "priority": random.randint(1, 5)
                }
                zone_idx += 1

        return zones

    @classmethod
    def get_robots(cls) -> Dict[str, Dict[str, Any]]:
        """获取机器人数据"""
        robots = {
            # 环球贸易广场 - 3台
            "robot_001": {
                "id": "robot_001",
                "tenant_id": cls.DEMO_TENANT_ID,
                "name": "清洁机器人 A-01",
                "model": "GS-50 Pro",
                "serial_number": "GS50P2024001",
                "building_id": "building_001",
                "building_name": "环球贸易广场",
                "current_floor": "floor_003",  # 3F
                "status": "working",
                "battery": 78,
                "position": {"x": 125.5, "y": 78.3},
                "current_task_id": "task_current_001",
                "current_task": "3F走廊清洁",
                "work_hours_today": 6.5,
                "tasks_completed_today": 8,
                "cleaning_area_today": 2400.0,
                "last_maintenance": "2026-01-15T10:00:00Z",
                "capabilities": ["sweeping", "mopping", "vacuuming"]
            },
            "robot_002": {
                "id": "robot_002",
                "tenant_id": cls.DEMO_TENANT_ID,
                "name": "清洁机器人 A-02",
                "model": "GS-50 Pro",
                "serial_number": "GS50P2024002",
                "building_id": "building_001",
                "building_name": "环球贸易广场",
                "current_floor": "floor_001",  # 1F
                "status": "idle",
                "battery": 92,
                "position": {"x": 50.0, "y": 120.0},
                "current_task_id": None,
                "current_task": None,
                "work_hours_today": 4.2,
                "tasks_completed_today": 5,
                "cleaning_area_today": 1800.0,
                "last_maintenance": "2026-01-18T14:00:00Z",
                "capabilities": ["sweeping", "mopping", "vacuuming"]
            },
            "robot_003": {
                "id": "robot_003",
                "tenant_id": cls.DEMO_TENANT_ID,
                "name": "清洁机器人 A-03",
                "model": "GS-50",
                "serial_number": "GS502024003",
                "building_id": "building_001",
                "building_name": "环球贸易广场",
                "current_floor": "floor_005",  # 5F
                "status": "charging",
                "battery": 35,
                "position": {"x": 10.0, "y": 10.0},  # 充电站位置
                "current_task_id": None,
                "current_task": None,
                "work_hours_today": 7.8,
                "tasks_completed_today": 10,
                "cleaning_area_today": 3200.0,
                "last_maintenance": "2026-01-10T09:00:00Z",
                "capabilities": ["sweeping", "vacuuming"]
            },
            # 国际金融中心 - 3台
            "robot_004": {
                "id": "robot_004",
                "tenant_id": cls.DEMO_TENANT_ID,
                "name": "清洁机器人 B-01",
                "model": "GS-50 Pro",
                "serial_number": "GS50P2024004",
                "building_id": "building_002",
                "building_name": "国际金融中心",
                "current_floor": "floor_011",  # 1F
                "status": "working",
                "battery": 65,
                "position": {"x": 200.0, "y": 150.0},
                "current_task_id": "task_current_002",
                "current_task": "1F大堂清洁",
                "work_hours_today": 5.5,
                "tasks_completed_today": 7,
                "cleaning_area_today": 2100.0,
                "last_maintenance": "2026-01-16T11:00:00Z",
                "capabilities": ["sweeping", "mopping", "vacuuming"]
            },
            "robot_005": {
                "id": "robot_005",
                "tenant_id": cls.DEMO_TENANT_ID,
                "name": "清洁机器人 B-02",
                "model": "GS-50 Pro",
                "serial_number": "GS50P2024005",
                "building_id": "building_002",
                "building_name": "国际金融中心",
                "current_floor": "floor_014",  # 4F
                "status": "working",
                "battery": 54,
                "position": {"x": 180.0, "y": 90.0},
                "current_task_id": "task_current_003",
                "current_task": "4F办公区清洁",
                "work_hours_today": 6.0,
                "tasks_completed_today": 6,
                "cleaning_area_today": 2500.0,
                "last_maintenance": "2026-01-14T15:00:00Z",
                "capabilities": ["sweeping", "mopping", "vacuuming"]
            },
            "robot_006": {
                "id": "robot_006",
                "tenant_id": cls.DEMO_TENANT_ID,
                "name": "清洁机器人 B-03",
                "model": "GS-50",
                "serial_number": "GS502024006",
                "building_id": "building_002",
                "building_name": "国际金融中心",
                "current_floor": "floor_016",  # 6F
                "status": "idle",
                "battery": 88,
                "position": {"x": 100.0, "y": 200.0},
                "current_task_id": None,
                "current_task": None,
                "work_hours_today": 3.5,
                "tasks_completed_today": 4,
                "cleaning_area_today": 1400.0,
                "last_maintenance": "2026-01-19T08:00:00Z",
                "capabilities": ["sweeping", "vacuuming"]
            },
            # 太古广场 - 2台
            "robot_007": {
                "id": "robot_007",
                "tenant_id": cls.DEMO_TENANT_ID,
                "name": "清洁机器人 C-01",
                "model": "GS-50 Pro",
                "serial_number": "GS50P2024007",
                "building_id": "building_003",
                "building_name": "太古广场",
                "current_floor": "floor_019",  # 1F
                "status": "working",
                "battery": 71,
                "position": {"x": 150.0, "y": 80.0},
                "current_task_id": "task_current_004",
                "current_task": "1F大堂清洁",
                "work_hours_today": 5.0,
                "tasks_completed_today": 6,
                "cleaning_area_today": 1900.0,
                "last_maintenance": "2026-01-17T10:00:00Z",
                "capabilities": ["sweeping", "mopping", "vacuuming"]
            },
            "robot_008": {
                "id": "robot_008",
                "tenant_id": cls.DEMO_TENANT_ID,
                "name": "清洁机器人 C-02",
                "model": "GS-50",
                "serial_number": "GS502024008",
                "building_id": "building_003",
                "building_name": "太古广场",
                "current_floor": "floor_021",  # 3F
                "status": "maintenance",
                "battery": 100,
                "position": {"x": 0.0, "y": 0.0},  # 维护区域
                "current_task_id": None,
                "current_task": None,
                "work_hours_today": 0.0,
                "tasks_completed_today": 0,
                "cleaning_area_today": 0.0,
                "last_maintenance": "2026-01-22T08:00:00Z",
                "maintenance_reason": "定期保养",
                "capabilities": ["sweeping", "vacuuming"]
            }
        }
        return robots

    @classmethod
    def get_tasks(cls, days: int = 30) -> List[Dict[str, Any]]:
        """生成历史任务数据

        Args:
            days: 生成多少天的历史数据

        Returns:
            任务列表 (500+任务)
        """
        tasks = []
        robots = cls.get_robots()
        zones = cls.get_zones()
        zone_list = list(zones.values())
        robot_list = list(robots.values())

        task_types = ["routine", "deep_clean", "spot_clean", "emergency"]
        task_priorities = ["low", "normal", "high", "urgent"]
        task_statuses = ["completed", "completed", "completed", "completed", "failed"]  # 80% 成功率

        base_time = datetime.now()
        task_idx = 1

        # 生成历史任务 (过去30天)
        for day_offset in range(days, 0, -1):
            day = base_time - timedelta(days=day_offset)
            # 每天15-20个任务
            daily_tasks = random.randint(15, 20)

            for _ in range(daily_tasks):
                task_id = f"task_hist_{task_idx:04d}"
                robot = random.choice(robot_list)
                zone = random.choice(zone_list)
                task_type = random.choice(task_types)

                # 任务时间
                hour = random.randint(6, 22)
                minute = random.randint(0, 59)
                start_time = day.replace(hour=hour, minute=minute)
                duration = random.randint(30, 120)  # 30-120分钟
                end_time = start_time + timedelta(minutes=duration)

                status = random.choice(task_statuses)

                tasks.append({
                    "id": task_id,
                    "tenant_id": cls.DEMO_TENANT_ID,
                    "robot_id": robot["id"],
                    "robot_name": robot["name"],
                    "zone_id": zone["id"],
                    "zone_name": zone["name"],
                    "building_id": robot["building_id"],
                    "task_type": task_type,
                    "priority": random.choice(task_priorities),
                    "status": status,
                    "scheduled_start": start_time.isoformat() + "Z",
                    "actual_start": start_time.isoformat() + "Z" if status != "pending" else None,
                    "completed_at": end_time.isoformat() + "Z" if status == "completed" else None,
                    "estimated_duration": duration,
                    "actual_duration": duration + random.randint(-10, 20) if status == "completed" else None,
                    "cleaning_area": zone["area"] if status == "completed" else 0,
                    "created_at": (start_time - timedelta(hours=1)).isoformat() + "Z"
                })
                task_idx += 1

        # 今日任务
        today = base_time.date()

        # 已完成任务 (15个)
        for i in range(15):
            task_id = f"task_today_{i+1:03d}"
            robot = random.choice(robot_list[:7])  # 排除维护中的机器人
            zone = random.choice(zone_list)

            hour = random.randint(6, base_time.hour - 1) if base_time.hour > 6 else 6
            start_time = datetime.combine(today, datetime.min.time()).replace(hour=hour, minute=random.randint(0, 59))
            duration = random.randint(30, 90)

            tasks.append({
                "id": task_id,
                "tenant_id": cls.DEMO_TENANT_ID,
                "robot_id": robot["id"],
                "robot_name": robot["name"],
                "zone_id": zone["id"],
                "zone_name": zone["name"],
                "building_id": robot["building_id"],
                "task_type": random.choice(task_types[:3]),
                "priority": "normal",
                "status": "completed",
                "scheduled_start": start_time.isoformat() + "Z",
                "actual_start": start_time.isoformat() + "Z",
                "completed_at": (start_time + timedelta(minutes=duration)).isoformat() + "Z",
                "estimated_duration": duration,
                "actual_duration": duration + random.randint(-5, 10),
                "cleaning_area": zone["area"],
                "created_at": (start_time - timedelta(minutes=30)).isoformat() + "Z"
            })

        # 进行中任务 (12个) - 对应当前工作中的机器人
        working_robots = [r for r in robot_list if r["status"] == "working"]
        for i, robot in enumerate(working_robots * 3):  # 复制以确保12个任务
            if i >= 12:
                break
            task_id = f"task_current_{i+1:03d}"
            # 随机选择一个区域 (简化逻辑)
            zone = random.choice(zone_list)

            start_time = datetime.now() - timedelta(minutes=random.randint(10, 45))

            tasks.append({
                "id": task_id,
                "tenant_id": cls.DEMO_TENANT_ID,
                "robot_id": robot["id"],
                "robot_name": robot["name"],
                "zone_id": zone["id"],
                "zone_name": zone["name"],
                "building_id": robot["building_id"],
                "task_type": "routine",
                "priority": "normal",
                "status": "in_progress",
                "scheduled_start": start_time.isoformat() + "Z",
                "actual_start": start_time.isoformat() + "Z",
                "completed_at": None,
                "estimated_duration": 60,
                "actual_duration": None,
                "cleaning_area": 0,
                "progress": random.randint(20, 80),
                "created_at": (start_time - timedelta(minutes=15)).isoformat() + "Z"
            })

        # 待执行任务 (18个)
        for i in range(18):
            task_id = f"task_pending_{i+1:03d}"
            robot = random.choice(robot_list[:7])
            zone = random.choice(zone_list)

            # 未来1-4小时
            start_time = datetime.now() + timedelta(hours=random.randint(1, 4), minutes=random.randint(0, 59))

            tasks.append({
                "id": task_id,
                "tenant_id": cls.DEMO_TENANT_ID,
                "robot_id": robot["id"],
                "robot_name": robot["name"],
                "zone_id": zone["id"],
                "zone_name": zone["name"],
                "building_id": robot["building_id"],
                "task_type": random.choice(task_types[:3]),
                "priority": random.choice(["normal", "high"]),
                "status": "pending",
                "scheduled_start": start_time.isoformat() + "Z",
                "actual_start": None,
                "completed_at": None,
                "estimated_duration": random.randint(30, 90),
                "actual_duration": None,
                "cleaning_area": 0,
                "created_at": datetime.now().isoformat() + "Z"
            })

        return tasks

    @classmethod
    def get_alerts(cls) -> List[Dict[str, Any]]:
        """获取告警数据"""
        return [
            {
                "id": "alert_001",
                "tenant_id": cls.DEMO_TENANT_ID,
                "robot_id": "robot_003",
                "robot_name": "清洁机器人 A-03",
                "building_id": "building_001",
                "building_name": "环球贸易广场",
                "alert_type": "low_battery",
                "severity": "warning",
                "title": "电量低",
                "message": "机器人电量低于40%，已自动返回充电",
                "status": "resolved",
                "created_at": (datetime.now() - timedelta(hours=1)).isoformat() + "Z",
                "resolved_at": (datetime.now() - timedelta(minutes=30)).isoformat() + "Z",
                "resolved_by": "system"
            },
            {
                "id": "alert_002",
                "tenant_id": cls.DEMO_TENANT_ID,
                "robot_id": "robot_008",
                "robot_name": "清洁机器人 C-02",
                "building_id": "building_003",
                "building_name": "太古广场",
                "alert_type": "maintenance",
                "severity": "info",
                "title": "定期保养",
                "message": "机器人正在进行定期保养，预计2小时后恢复",
                "status": "active",
                "created_at": (datetime.now() - timedelta(hours=2)).isoformat() + "Z",
                "resolved_at": None,
                "resolved_by": None
            }
        ]

    @classmethod
    def get_kpi_data(cls) -> Dict[str, Any]:
        """获取KPI数据"""
        return {
            "tenant_id": cls.DEMO_TENANT_ID,
            "period": "today",
            "generated_at": datetime.now().isoformat() + "Z",

            # 核心KPI
            "task_completion_rate": 96.8,
            "robot_utilization": 87.2,
            "monthly_cost_savings": 428600,
            "customer_satisfaction": 4.8,

            # 今日概览
            "today": {
                "completed_tasks": 127,
                "cleaning_area": 45800,
                "work_hours": 186,
                "labor_saved": 23  # 节约人工数
            },

            # 效率对比
            "efficiency": {
                "before_linkc": {
                    "daily_area": 32000,
                    "monthly_cost": 660000,
                    "satisfaction": 4.2
                },
                "after_linkc": {
                    "daily_area": 45800,
                    "monthly_cost": 428600,
                    "satisfaction": 4.8
                },
                "improvement": {
                    "area_increase": 43,  # 百分比
                    "cost_decrease": 35,
                    "satisfaction_increase": 14
                }
            },

            # 健康度评分
            "health_score": {
                "overall": 92,
                "trend": "+3%",
                "components": {
                    "robot_health": 95,
                    "task_efficiency": 91,
                    "alert_response": 89,
                    "resource_utilization": 93
                }
            },

            # 楼宇状态
            "buildings_status": [
                {
                    "building_id": "building_001",
                    "name": "环球贸易广场",
                    "status": "healthy",
                    "robot_count": 3,
                    "online_count": 3,
                    "tasks_today": 48,
                    "completion_rate": 97.2
                },
                {
                    "building_id": "building_002",
                    "name": "国际金融中心",
                    "status": "healthy",
                    "robot_count": 3,
                    "online_count": 3,
                    "tasks_today": 42,
                    "completion_rate": 96.5
                },
                {
                    "building_id": "building_003",
                    "name": "太古广场",
                    "status": "attention",
                    "robot_count": 2,
                    "online_count": 1,
                    "tasks_today": 37,
                    "completion_rate": 96.2,
                    "attention_reason": "1台机器人维护中"
                }
            ],

            # 趋势数据 (过去7天)
            "trends": {
                "dates": [
                    (datetime.now() - timedelta(days=i)).strftime("%m-%d")
                    for i in range(6, -1, -1)
                ],
                "task_completion": [95.2, 96.1, 95.8, 97.0, 96.5, 96.8, 96.8],
                "robot_utilization": [85.5, 86.2, 87.0, 86.8, 87.5, 87.0, 87.2],
                "cleaning_area": [43200, 44100, 44800, 45200, 45000, 45500, 45800]
            }
        }

    @classmethod
    def get_all_demo_data(cls) -> Dict[str, Any]:
        """获取完整的演示数据集"""
        return {
            "tenant_id": cls.DEMO_TENANT_ID,
            "buildings": cls.get_buildings(),
            "floors": cls.get_floors(),
            "zones": cls.get_zones(),
            "robots": cls.get_robots(),
            "tasks": cls.get_tasks(30),  # 30天历史
            "alerts": cls.get_alerts(),
            "kpi": cls.get_kpi_data(),
            "generated_at": datetime.now().isoformat() + "Z"
        }
