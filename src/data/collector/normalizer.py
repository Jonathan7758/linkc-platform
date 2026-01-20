"""
D1: 数据采集引擎 - 数据标准化
==============================
将不同MCP的数据格式标准化
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .models import RobotStatusData, RobotPositionData, TaskProgressData


# 状态映射规则
STATUS_MAPPING = {
    "gaoxian": {
        "idle": "idle",
        "working": "working",
        "charging": "charging",
        "paused": "paused",
        "error": "error",
        "offline": "offline",
        "navigating": "navigating",
    },
    "ecovacs": {
        "idle": "idle",
        "cleaning": "working",
        "charging": "charging",
        "pause": "paused",
        "error": "error",
        "offline": "offline",
    }
}


class DataNormalizer:
    """数据标准化器"""

    def normalize_robot_status(
        self,
        raw_data: Dict[str, Any],
        source: str,
        tenant_id: str
    ) -> RobotStatusData:
        """
        标准化机器人状态数据

        Args:
            raw_data: MCP返回的原始数据
            source: 数据来源 (gaoxian/ecovacs)
            tenant_id: 租户ID

        Returns:
            标准化的机器人状态数据
        """
        # 获取状态映射
        status_map = STATUS_MAPPING.get(source, {})
        raw_status = raw_data.get("status", "unknown")
        if isinstance(raw_status, str):
            normalized_status = status_map.get(raw_status.lower(), raw_status)
        else:
            normalized_status = status_map.get(raw_status.value, str(raw_status))

        # 提取位置信息
        location = raw_data.get("location", {})
        position_x = None
        position_y = None
        floor_id = None

        if isinstance(location, dict):
            position_x = location.get("x")
            position_y = location.get("y")
            floor_id = location.get("floor_id")

        return RobotStatusData(
            robot_id=raw_data.get("robot_id", ""),
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            status=normalized_status,
            battery_level=raw_data.get("battery_level", 0),
            position_x=position_x,
            position_y=position_y,
            floor_id=floor_id,
            zone_id=raw_data.get("zone_id"),
            current_task_id=raw_data.get("current_task_id"),
            error_code=raw_data.get("error_code"),
        )

    def normalize_robot_position(
        self,
        raw_data: Dict[str, Any],
        source: str,
        tenant_id: str
    ) -> Optional[RobotPositionData]:
        """
        标准化机器人位置数据

        Args:
            raw_data: MCP返回的原始数据
            source: 数据来源
            tenant_id: 租户ID

        Returns:
            标准化的位置数据，如果没有位置信息则返回None
        """
        location = raw_data.get("location", {})
        if not isinstance(location, dict):
            return None

        x = location.get("x")
        y = location.get("y")

        if x is None or y is None:
            return None

        return RobotPositionData(
            robot_id=raw_data.get("robot_id", ""),
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            x=float(x),
            y=float(y),
            floor_id=location.get("floor_id"),
            heading=location.get("heading"),
            speed=raw_data.get("speed"),
        )

    def normalize_task_progress(
        self,
        raw_data: Dict[str, Any],
        source: str,
        tenant_id: str
    ) -> TaskProgressData:
        """
        标准化任务进度数据

        Args:
            raw_data: MCP返回的原始数据
            source: 数据来源
            tenant_id: 租户ID

        Returns:
            标准化的任务进度数据
        """
        return TaskProgressData(
            task_id=raw_data.get("task_id", ""),
            robot_id=raw_data.get("robot_id", ""),
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            status=raw_data.get("status", "unknown"),
            progress=raw_data.get("progress", 0.0),
            zone_id=raw_data.get("zone_id"),
            started_at=raw_data.get("started_at"),
            estimated_completion=raw_data.get("estimated_completion"),
        )
