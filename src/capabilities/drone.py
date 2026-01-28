"""
Drone Capabilities - 无人机能力定义
"""

from .models import Capability


# ===== 无人机能力定义 =====

DRONE_CAPABILITIES = [
    Capability(
        id="drone.patrol.aerial",
        name="空中巡逻",
        category="drone",
        action="patrol",
        parameters={
            "route_id": {"type": "string", "required": True},
            "altitude_m": {"type": "float", "min": 10, "max": 120, "default": 50},
            "speed_ms": {"type": "float", "min": 1, "max": 15, "default": 5},
            "checkpoints": {"type": "array", "items": "string"},
            "camera_mode": {"type": "string", "enum": ["visible", "thermal", "both"], "default": "visible"},
        },
        constraints={
            "min_battery": 40,
            "max_wind_speed_ms": 10,
            "weather_conditions": ["clear", "cloudy", "light_rain"],
            "daylight_required": False,
        },
        description="使用无人机进行空中安防巡逻，支持可见光和热成像"
    ),
    Capability(
        id="drone.inspection.facade",
        name="外墙检查",
        category="drone",
        action="inspect",
        parameters={
            "building_id": {"type": "string", "required": True},
            "facade_side": {"type": "string", "enum": ["north", "south", "east", "west", "all"], "default": "all"},
            "floor_range": {"type": "object", "properties": {"start": "int", "end": "int"}},
            "camera_mode": {"type": "string", "enum": ["visible", "thermal"], "default": "visible"},
            "detail_level": {"type": "string", "enum": ["quick", "standard", "detailed"], "default": "standard"},
        },
        constraints={
            "min_battery": 50,
            "max_wind_speed_ms": 8,
            "daylight_required": True,
        },
        description="使用无人机检查建筑外墙，检测裂缝、渗水等问题"
    ),
    Capability(
        id="drone.inspection.roof",
        name="屋顶检查",
        category="drone",
        action="inspect",
        parameters={
            "building_id": {"type": "string", "required": True},
            "scan_pattern": {"type": "string", "enum": ["grid", "spiral", "perimeter"], "default": "grid"},
            "camera_mode": {"type": "string", "enum": ["visible", "thermal", "both"], "default": "both"},
            "focus_areas": {"type": "array", "items": "string"},
        },
        constraints={
            "min_battery": 40,
            "max_wind_speed_ms": 8,
            "daylight_required": True,
        },
        description="使用无人机检查屋顶状况，包括防水层、设备等"
    ),
    Capability(
        id="drone.delivery.aerial",
        name="空中配送",
        category="drone",
        action="deliver",
        parameters={
            "pickup_location": {"type": "string", "required": True},
            "delivery_location": {"type": "string", "required": True},
            "package_weight_kg": {"type": "float", "max": 2.5},
            "recipient": {"type": "string", "required": True},
            "urgent": {"type": "boolean", "default": False},
        },
        constraints={
            "min_battery": 60,
            "max_payload_kg": 2.5,
            "max_distance_km": 5,
            "weather_conditions": ["clear", "cloudy"],
        },
        description="使用无人机进行小件快速配送"
    ),
    Capability(
        id="drone.photography.aerial",
        name="航拍",
        category="drone",
        action="photograph",
        parameters={
            "target_area": {"type": "string", "required": True},
            "shot_type": {"type": "string", "enum": ["photo", "video", "panorama", "timelapse"], "default": "photo"},
            "altitude_m": {"type": "float", "min": 10, "max": 120, "default": 50},
            "resolution": {"type": "string", "enum": ["720p", "1080p", "4k"], "default": "1080p"},
            "duration_sec": {"type": "integer", "max": 600},
        },
        constraints={
            "min_battery": 50,
            "max_wind_speed_ms": 8,
            "daylight_required": True,
        },
        description="使用无人机进行航拍摄影"
    ),
]


def get_drone_capabilities():
    """获取所有无人机能力"""
    return DRONE_CAPABILITIES


def get_drone_capability_ids():
    """获取无人机能力 ID 列表"""
    return [cap.id for cap in DRONE_CAPABILITIES]
