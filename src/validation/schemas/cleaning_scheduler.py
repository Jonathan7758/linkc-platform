"""
清洁调度 Agent 决策 JSON Schema
"""

CLEANING_SCHEDULE_DECISION_SCHEMA = {
    "type": "object",
    "required": ["action", "assignments"],
    "properties": {
        "action": {
            "type": "string",
            "enum": ["schedule", "reschedule", "cancel", "pause"],
        },
        "assignments": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["robot_id", "zone_id", "task_type"],
                "properties": {
                    "robot_id": {"type": "string"},
                    "zone_id": {"type": "string"},
                    "floor_id": {"type": "string"},
                    "task_type": {
                        "type": "string",
                        "enum": ["standard", "deep", "quick", "spot"],
                    },
                    "priority": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                    },
                    "scheduled_start": {
                        "type": "string",
                        "format": "date-time",
                    },
                    "estimated_duration_minutes": {
                        "type": "integer",
                        "minimum": 5,
                        "maximum": 480,
                    },
                },
            },
        },
        "reasoning": {"type": "string"},
    },
}
