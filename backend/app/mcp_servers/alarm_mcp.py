"""告警管理MCP Server模块"""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp_servers.base_mcp_server import (
    BaseMCPServer,
    MCPServerType,
    MCPTool,
    ToolParameter,
)
from app.models.alarm import Alarm, AlarmStatus, AlarmSeverity, AlarmCategory
from app.models.device import Device


class AlarmMCPServer(BaseMCPServer):
    """告警管理MCP Server

    提供告警查询、确认、解决等功能。
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        super().__init__(MCPServerType.ALARM)

    def _register_tools(self) -> None:
        """注册告警管理工具"""

        # 1. 获取告警列表
        self.register_tool(
            MCPTool(
                name="get_alarm_list",
                description="获取告警列表，支持按状态、级别、设备、时间筛选",
                parameters=[
                    ToolParameter(
                        name="status",
                        type="string",
                        description="告警状态: active/acknowledged/resolved/closed",
                        required=False,
                        enum=["active", "acknowledged", "resolved", "closed"],
                    ),
                    ToolParameter(
                        name="severity",
                        type="string",
                        description="告警级别: critical/major/minor/warning",
                        required=False,
                        enum=["critical", "major", "minor", "warning"],
                    ),
                    ToolParameter(
                        name="device_id",
                        type="string",
                        description="设备ID，筛选特定设备的告警",
                        required=False,
                    ),
                    ToolParameter(
                        name="hours",
                        type="integer",
                        description="查询最近多少小时的告警，默认24",
                        required=False,
                        default=24,
                    ),
                    ToolParameter(
                        name="limit",
                        type="integer",
                        description="返回数量限制，默认20",
                        required=False,
                        default=20,
                    ),
                ],
                handler=self._get_alarm_list,
            )
        )

        # 2. 获取告警详情
        self.register_tool(
            MCPTool(
                name="get_alarm_detail",
                description="获取告警的详细信息，包括关联设备、触发值、处理记录等",
                parameters=[
                    ToolParameter(
                        name="alarm_id",
                        type="string",
                        description="告警唯一标识",
                        required=True,
                    )
                ],
                handler=self._get_alarm_detail,
            )
        )

        # 3. 获取告警统计
        self.register_tool(
            MCPTool(
                name="get_alarm_stats",
                description="获取告警统计信息，如各级别数量、各状态数量等",
                parameters=[
                    ToolParameter(
                        name="group_by",
                        type="string",
                        description="分组维度: severity/status/category",
                        required=False,
                        enum=["severity", "status", "category"],
                        default="severity",
                    ),
                    ToolParameter(
                        name="hours",
                        type="integer",
                        description="统计最近多少小时，默认24",
                        required=False,
                        default=24,
                    ),
                ],
                handler=self._get_alarm_stats,
            )
        )

        # 4. 确认告警
        self.register_tool(
            MCPTool(
                name="acknowledge_alarm",
                description="确认告警，表示已知晓该告警",
                parameters=[
                    ToolParameter(
                        name="alarm_id",
                        type="string",
                        description="告警唯一标识",
                        required=True,
                    ),
                    ToolParameter(
                        name="comment",
                        type="string",
                        description="确认备注",
                        required=False,
                    ),
                ],
                handler=self._acknowledge_alarm,
            )
        )

        # 5. 解决告警
        self.register_tool(
            MCPTool(
                name="resolve_alarm",
                description="解决告警，记录解决方案",
                parameters=[
                    ToolParameter(
                        name="alarm_id",
                        type="string",
                        description="告警唯一标识",
                        required=True,
                    ),
                    ToolParameter(
                        name="resolution",
                        type="string",
                        description="解决方案描述",
                        required=True,
                    ),
                    ToolParameter(
                        name="comment",
                        type="string",
                        description="额外备注",
                        required=False,
                    ),
                ],
                handler=self._resolve_alarm,
            )
        )

        # 6. 获取处理建议
        self.register_tool(
            MCPTool(
                name="get_alarm_suggestions",
                description="根据告警类型和历史处理记录，获取处理建议",
                parameters=[
                    ToolParameter(
                        name="alarm_id",
                        type="string",
                        description="告警唯一标识",
                        required=True,
                    )
                ],
                handler=self._get_alarm_suggestions,
            )
        )

    async def _get_alarm_list(self, args: dict[str, Any]) -> dict[str, Any]:
        """获取告警列表"""
        status = args.get("status")
        severity = args.get("severity")
        device_id = args.get("device_id")
        hours = args.get("hours", 24)
        limit = args.get("limit", 20)

        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = select(Alarm).where(Alarm.triggered_at >= since)

        if status:
            query = query.where(Alarm.status == status)
        if severity:
            query = query.where(Alarm.severity == severity)
        if device_id:
            query = query.where(Alarm.device_id == device_id)

        query = query.order_by(Alarm.triggered_at.desc()).limit(limit)

        result = await self.db.execute(query)
        alarms = result.scalars().all()

        return {
            "total": len(alarms),
            "period_hours": hours,
            "alarms": [
                {
                    "alarm_id": a.alarm_id,
                    "title": a.title,
                    "severity": a.severity,
                    "status": a.status,
                    "device_id": a.device_id,
                    "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
                    "category": a.category,
                }
                for a in alarms
            ],
        }

    async def _get_alarm_detail(self, args: dict[str, Any]) -> dict[str, Any]:
        """获取告警详情"""
        alarm_id = args["alarm_id"]

        result = await self.db.execute(
            select(Alarm).where(Alarm.alarm_id == alarm_id)
        )
        alarm = result.scalar_one_or_none()

        if not alarm:
            return {"error": f"告警 {alarm_id} 不存在"}

        # 获取关联设备信息
        device_info = None
        if alarm.device_id:
            device_result = await self.db.execute(
                select(Device).where(Device.device_id == alarm.device_id)
            )
            device = device_result.scalar_one_or_none()
            if device:
                device_info = {
                    "device_id": device.device_id,
                    "name": device.name,
                    "device_type": device.device_type,
                    "location": device.location,
                }

        return {
            "alarm_id": alarm.alarm_id,
            "title": alarm.title,
            "description": alarm.description,
            "severity": alarm.severity,
            "status": alarm.status,
            "category": alarm.category,
            "device": device_info,
            "trigger_value": alarm.trigger_value,
            "threshold_value": alarm.threshold_value,
            "trigger_parameter": alarm.trigger_parameter,
            "triggered_at": alarm.triggered_at.isoformat() if alarm.triggered_at else None,
            "acknowledged_at": alarm.acknowledged_at.isoformat() if alarm.acknowledged_at else None,
            "acknowledged_by": alarm.acknowledged_by,
            "resolved_at": alarm.resolved_at.isoformat() if alarm.resolved_at else None,
            "resolved_by": alarm.resolved_by,
            "resolution_notes": alarm.resolution_notes,
        }

    async def _get_alarm_stats(self, args: dict[str, Any]) -> dict[str, Any]:
        """获取告警统计"""
        group_by = args.get("group_by", "severity")
        hours = args.get("hours", 24)

        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        result = await self.db.execute(
            select(Alarm).where(Alarm.triggered_at >= since)
        )
        alarms = result.scalars().all()

        stats: dict[str, int] = {}
        for alarm in alarms:
            key = getattr(alarm, group_by, "unknown")
            if key is None:
                key = "unknown"
            stats[key] = stats.get(key, 0) + 1

        # 额外统计
        active_count = sum(1 for a in alarms if a.status == AlarmStatus.ACTIVE.value)
        critical_count = sum(1 for a in alarms if a.severity == AlarmSeverity.CRITICAL.value)

        return {
            "group_by": group_by,
            "period_hours": hours,
            "total": len(alarms),
            "active_count": active_count,
            "critical_count": critical_count,
            "statistics": stats,
        }

    async def _acknowledge_alarm(self, args: dict[str, Any]) -> dict[str, Any]:
        """确认告警"""
        alarm_id = args["alarm_id"]
        comment = args.get("comment", "")

        result = await self.db.execute(
            select(Alarm).where(Alarm.alarm_id == alarm_id)
        )
        alarm = result.scalar_one_or_none()

        if not alarm:
            return {"error": f"告警 {alarm_id} 不存在"}

        if alarm.status != AlarmStatus.ACTIVE.value:
            return {"error": f"告警状态为 {alarm.status}，无法确认"}

        alarm.status = AlarmStatus.ACKNOWLEDGED.value
        alarm.acknowledged_at = datetime.now(timezone.utc)
        alarm.acknowledged_by = "system"  # MVP阶段

        await self.db.flush()

        return {
            "alarm_id": alarm_id,
            "status": "acknowledged",
            "message": f"告警已确认" + (f"，备注：{comment}" if comment else ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _resolve_alarm(self, args: dict[str, Any]) -> dict[str, Any]:
        """解决告警"""
        alarm_id = args["alarm_id"]
        resolution = args["resolution"]
        comment = args.get("comment", "")

        result = await self.db.execute(
            select(Alarm).where(Alarm.alarm_id == alarm_id)
        )
        alarm = result.scalar_one_or_none()

        if not alarm:
            return {"error": f"告警 {alarm_id} 不存在"}

        if alarm.status == AlarmStatus.RESOLVED.value:
            return {"error": "告警已解决"}

        alarm.status = AlarmStatus.RESOLVED.value
        alarm.resolved_at = datetime.now(timezone.utc)
        alarm.resolved_by = "system"
        alarm.resolution_notes = resolution + (f"\n备注：{comment}" if comment else "")

        await self.db.flush()

        return {
            "alarm_id": alarm_id,
            "status": "resolved",
            "resolution": resolution,
            "message": "告警已解决",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _get_alarm_suggestions(self, args: dict[str, Any]) -> dict[str, Any]:
        """获取处理建议"""
        alarm_id = args["alarm_id"]

        result = await self.db.execute(
            select(Alarm).where(Alarm.alarm_id == alarm_id)
        )
        alarm = result.scalar_one_or_none()

        if not alarm:
            return {"error": f"告警 {alarm_id} 不存在"}

        # MVP阶段：基于告警类型返回预设建议
        suggestions = self._get_preset_suggestions(alarm.category)

        return {
            "alarm_id": alarm_id,
            "alarm_title": alarm.title,
            "category": alarm.category,
            "suggestions": suggestions,
            "related_knowledge": [],  # 可扩展：关联知识库
        }

    def _get_preset_suggestions(self, category: str | None) -> list[dict[str, Any]]:
        """获取预设处理建议"""
        suggestions_map = {
            AlarmCategory.THRESHOLD.value: [
                {"step": 1, "action": "检查当前参数值是否持续超限"},
                {"step": 2, "action": "确认阈值设置是否合理"},
                {"step": 3, "action": "检查相关设备运行状态"},
                {"step": 4, "action": "如持续异常，考虑调整设备参数或报修"},
            ],
            AlarmCategory.FAULT.value: [
                {"step": 1, "action": "确认设备当前状态"},
                {"step": 2, "action": "查看设备故障码或报警信息"},
                {"step": 3, "action": "尝试复位操作"},
                {"step": 4, "action": "如无法恢复，联系维修人员"},
            ],
            AlarmCategory.OFFLINE.value: [
                {"step": 1, "action": "检查设备网络连接"},
                {"step": 2, "action": "检查通信线路"},
                {"step": 3, "action": "尝试重启通信模块"},
                {"step": 4, "action": "联系网络管理员"},
            ],
            AlarmCategory.MAINTENANCE.value: [
                {"step": 1, "action": "查看设备维护记录"},
                {"step": 2, "action": "确认维护周期是否到期"},
                {"step": 3, "action": "安排维护人员"},
                {"step": 4, "action": "完成维护后更新记录"},
            ],
            AlarmCategory.EFFICIENCY.value: [
                {"step": 1, "action": "分析设备运行效率数据"},
                {"step": 2, "action": "检查设备是否需要清洁或维护"},
                {"step": 3, "action": "对比历史数据找出异常原因"},
                {"step": 4, "action": "优化运行参数或安排维修"},
            ],
            AlarmCategory.SECURITY.value: [
                {"step": 1, "action": "立即确认现场安全状况"},
                {"step": 2, "action": "通知相关安全人员"},
                {"step": 3, "action": "采取必要的安全措施"},
                {"step": 4, "action": "记录事件详情并上报"},
            ],
        }

        return suggestions_map.get(
            category or "",
            [{"step": 1, "action": "请根据告警描述进行排查"}],
        )
