"""
Robot Dog Capabilities - 机器狗能力定义
"""

from .models import Capability


# ===== 机器狗能力定义 =====

ROBOT_DOG_CAPABILITIES = [
    Capability(
        id="robotdog.patrol.rough",
        name="复杂地形巡逻",
        category="robotdog",
        action="patrol",
        parameters={
            "route_id": {"type": "string", "required": True},
            "terrain_type": {"type": "string", "enum": ["stairs", "gravel", "grass", "slope", "mixed"], "default": "mixed"},
            "checkpoints": {"type": "array", "items": "string"},
            "camera_mode": {"type": "string", "enum": ["visible", "thermal", "both"], "default": "visible"},
            "speed_mode": {"type": "string", "enum": ["slow", "normal", "fast"], "default": "normal"},
        },
        constraints={
            "min_battery": 40,
            "max_slope_degree": 35,
            "max_stair_height_cm": 25,
            "weather_conditions": ["clear", "cloudy", "light_rain"],
        },
        description="在复杂地形环境下进行安防巡逻，支持楼梯、斜坡等"
    ),
    Capability(
        id="robotdog.inspection.underground",
        name="地下空间检查",
        category="robotdog",
        action="inspect",
        parameters={
            "area_id": {"type": "string", "required": True},
            "inspection_type": {"type": "string", "enum": ["pipe", "cable", "structural", "general"], "default": "general"},
            "depth_level": {"type": "integer", "min": -5, "max": 0, "default": -1},
            "camera_mode": {"type": "string", "enum": ["visible", "thermal", "night_vision"], "default": "night_vision"},
            "gas_detection": {"type": "boolean", "default": True},
        },
        constraints={
            "min_battery": 50,
            "requires_gas_sensor": True,
            "max_tunnel_width_m": 2,
        },
        description="在地下管廊、地下室等空间进行检查，支持气体检测"
    ),
    Capability(
        id="robotdog.escort.security",
        name="安保护送",
        category="robotdog",
        action="escort",
        parameters={
            "person_id": {"type": "string", "required": True},
            "start_location": {"type": "string", "required": True},
            "end_location": {"type": "string", "required": True},
            "alert_mode": {"type": "string", "enum": ["silent", "warning", "active"], "default": "warning"},
            "follow_distance_m": {"type": "float", "min": 1, "max": 5, "default": 2},
        },
        constraints={
            "min_battery": 50,
            "max_escort_duration_min": 60,
        },
        description="为重要人员提供安保护送服务"
    ),
    Capability(
        id="robotdog.care.companion",
        name="陪伴服务",
        category="robotdog",
        action="companion",
        parameters={
            "person_id": {"type": "string", "required": True},
            "location": {"type": "string", "required": True},
            "duration_min": {"type": "integer", "min": 5, "max": 120, "default": 30},
            "interaction_mode": {"type": "string", "enum": ["passive", "interactive", "playful"], "default": "interactive"},
            "monitor_health": {"type": "boolean", "default": True},
            "alert_on_fall": {"type": "boolean", "default": True},
        },
        constraints={
            "min_battery": 30,
            "requires_health_sensor": True,
        },
        description="为老人或需要关怀的人员提供陪伴服务，支持健康监测"
    ),
]


def get_robot_dog_capabilities():
    """获取所有机器狗能力"""
    return ROBOT_DOG_CAPABILITIES


def get_robot_dog_capability_ids():
    """获取机器狗能力 ID 列表"""
    return [cap.id for cap in ROBOT_DOG_CAPABILITIES]
