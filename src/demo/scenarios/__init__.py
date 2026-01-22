"""
演示场景定义
"""

from enum import Enum
from typing import Dict, Any, List

class DemoScenario(str, Enum):
    """演示场景枚举"""
    EXECUTIVE_OVERVIEW = "executive"      # 高管视角
    OPERATIONS_NORMAL = "ops_normal"      # 正常运营
    OPERATIONS_ALERT = "ops_alert"        # 告警场景
    AGENT_CONVERSATION = "agent_chat"     # Agent对话
    FULL_DEMO = "full"                    # 完整演示

    @classmethod
    def get_description(cls, scenario: "DemoScenario") -> str:
        """获取场景描述"""
        descriptions = {
            cls.EXECUTIVE_OVERVIEW: "高管视角 - 展示战略驾驶舱、KPI和业务价值",
            cls.OPERATIONS_NORMAL: "运营视角(正常) - 展示实时监控和任务调度",
            cls.OPERATIONS_ALERT: "运营视角(告警) - 展示告警处理流程",
            cls.AGENT_CONVERSATION: "AI协作 - 展示智能对话和决策能力",
            cls.FULL_DEMO: "完整演示 - 15分钟全流程展示"
        }
        return descriptions.get(scenario, "未知场景")


class DemoEvent(str, Enum):
    """演示事件枚举"""
    ROBOT_LOW_BATTERY = "low_battery"     # 机器人电量低
    ROBOT_OBSTACLE = "obstacle"            # 遇到障碍物
    TASK_COMPLETED = "task_done"           # 任务完成
    NEW_URGENT_TASK = "urgent_task"        # 紧急任务
    ROBOT_ERROR = "robot_error"            # 机器人故障
    CHARGING_COMPLETE = "charging_done"    # 充电完成

    @classmethod
    def get_event_config(cls, event: "DemoEvent") -> Dict[str, Any]:
        """获取事件配置"""
        configs = {
            cls.ROBOT_LOW_BATTERY: {
                "default_robot": "robot_001",
                "battery_level": 15,
                "severity": "warning",
                "auto_action": "return_to_charge"
            },
            cls.ROBOT_OBSTACLE: {
                "default_robot": "robot_004",
                "obstacle_type": "unexpected_object",
                "severity": "warning",
                "auto_action": "wait_for_resolution"
            },
            cls.TASK_COMPLETED: {
                "default_robot": "robot_001",
                "completion_rate": 100,
                "severity": "info"
            },
            cls.NEW_URGENT_TASK: {
                "task_type": "emergency",
                "priority": "urgent",
                "severity": "high",
                "zone": "zone_001"  # 大堂
            },
            cls.ROBOT_ERROR: {
                "default_robot": "robot_006",
                "error_type": "sensor_malfunction",
                "severity": "critical",
                "auto_action": "stop_and_alert"
            },
            cls.CHARGING_COMPLETE: {
                "default_robot": "robot_003",
                "battery_level": 100,
                "severity": "info",
                "auto_action": "ready_for_task"
            }
        }
        return configs.get(event, {})


# 场景配置
SCENARIO_CONFIGS: Dict[DemoScenario, Dict[str, Any]] = {
    DemoScenario.EXECUTIVE_OVERVIEW: {
        "name": "高管视角",
        "duration_minutes": 3,
        "start_page": "/executive",
        "highlights": [
            "健康度评分 92分",
            "任务完成率 96.8%",
            "月度成本节约 ¥428,600",
            "多楼宇状态概览"
        ],
        "robot_states": {
            "working": 4,
            "idle": 2,
            "charging": 1,
            "maintenance": 1
        },
        "auto_events": []
    },
    DemoScenario.OPERATIONS_NORMAL: {
        "name": "运营视角(正常)",
        "duration_minutes": 5,
        "start_page": "/operations",
        "highlights": [
            "实时机器人地图",
            "任务调度演示",
            "机器人远程控制"
        ],
        "robot_states": {
            "working": 5,
            "idle": 2,
            "charging": 1,
            "maintenance": 0
        },
        "auto_events": [
            {"event": DemoEvent.TASK_COMPLETED, "delay_seconds": 60}
        ]
    },
    DemoScenario.OPERATIONS_ALERT: {
        "name": "运营视角(告警)",
        "duration_minutes": 5,
        "start_page": "/operations",
        "highlights": [
            "告警推送",
            "问题诊断",
            "快速响应"
        ],
        "robot_states": {
            "working": 4,
            "idle": 2,
            "charging": 1,
            "maintenance": 1
        },
        "auto_events": [
            {"event": DemoEvent.ROBOT_LOW_BATTERY, "delay_seconds": 30},
            {"event": DemoEvent.ROBOT_OBSTACLE, "delay_seconds": 90}
        ]
    },
    DemoScenario.AGENT_CONVERSATION: {
        "name": "AI协作",
        "duration_minutes": 5,
        "start_page": "/trainer",
        "highlights": [
            "自然语言任务下达",
            "智能决策展示",
            "人机协作审批",
            "学习反馈演示"
        ],
        "robot_states": {
            "working": 4,
            "idle": 3,
            "charging": 1,
            "maintenance": 0
        },
        "auto_events": [],
        "preset_conversations": [
            "task_scheduling",
            "status_query",
            "problem_diagnosis",
            "data_analysis",
            "batch_operation"
        ]
    },
    DemoScenario.FULL_DEMO: {
        "name": "完整演示",
        "duration_minutes": 15,
        "start_page": "/executive",
        "sequence": [
            {"scenario": DemoScenario.EXECUTIVE_OVERVIEW, "duration": 180},
            {"scenario": DemoScenario.OPERATIONS_NORMAL, "duration": 300},
            {"scenario": DemoScenario.AGENT_CONVERSATION, "duration": 300},
            {"page": "/mobile", "duration": 120}
        ],
        "robot_states": {
            "working": 4,
            "idle": 2,
            "charging": 1,
            "maintenance": 1
        },
        "auto_events": [
            {"event": DemoEvent.TASK_COMPLETED, "delay_seconds": 180},
            {"event": DemoEvent.ROBOT_LOW_BATTERY, "delay_seconds": 360},
            {"event": DemoEvent.CHARGING_COMPLETE, "delay_seconds": 600}
        ]
    }
}


def get_scenario_config(scenario: DemoScenario) -> Dict[str, Any]:
    """获取场景配置"""
    return SCENARIO_CONFIGS.get(scenario, {})


__all__ = [
    "DemoScenario",
    "DemoEvent",
    "SCENARIO_CONFIGS",
    "get_scenario_config"
]
