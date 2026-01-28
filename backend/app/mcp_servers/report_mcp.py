"""报表生成MCP Server模块"""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp_servers.base_mcp_server import (
    BaseMCPServer,
    MCPServerType,
    MCPTool,
    ToolParameter,
)
from app.models.energy import EnergyReading
from app.models.alarm import Alarm
from app.models.ticket import Ticket, TicketStatus


class ReportMCPServer(BaseMCPServer):
    """报表生成MCP Server

    提供各类报表生成功能，包括能耗报表、告警报表、工单报表等。
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        super().__init__(MCPServerType.REPORT)

    def _register_tools(self) -> None:
        """注册报表生成工具"""

        # 1. 生成能耗报表
        self.register_tool(
            MCPTool(
                name="generate_energy_report",
                description="生成能耗报表，包含用量统计、趋势分析、对比数据",
                parameters=[
                    ToolParameter(
                        name="report_type",
                        type="string",
                        description="报表类型: daily/weekly/monthly",
                        required=False,
                        enum=["daily", "weekly", "monthly"],
                        default="daily",
                    ),
                    ToolParameter(
                        name="energy_type",
                        type="string",
                        description="能源类型: electricity/water/gas/all",
                        required=False,
                        enum=["electricity", "water", "gas", "all"],
                        default="all",
                    ),
                    ToolParameter(
                        name="building",
                        type="string",
                        description="建筑名称，不填则统计所有建筑",
                        required=False,
                    ),
                    ToolParameter(
                        name="date",
                        type="string",
                        description="报表日期，格式YYYY-MM-DD，默认今天",
                        required=False,
                    ),
                ],
                handler=self._generate_energy_report,
            )
        )

        # 2. 生成告警报表
        self.register_tool(
            MCPTool(
                name="generate_alarm_report",
                description="生成告警报表，包含告警统计、处理情况、趋势分析",
                parameters=[
                    ToolParameter(
                        name="report_type",
                        type="string",
                        description="报表类型: daily/weekly/monthly",
                        required=False,
                        enum=["daily", "weekly", "monthly"],
                        default="daily",
                    ),
                    ToolParameter(
                        name="building",
                        type="string",
                        description="建筑名称",
                        required=False,
                    ),
                    ToolParameter(
                        name="date",
                        type="string",
                        description="报表日期，格式YYYY-MM-DD",
                        required=False,
                    ),
                ],
                handler=self._generate_alarm_report,
            )
        )

        # 3. 生成工单报表
        self.register_tool(
            MCPTool(
                name="generate_ticket_report",
                description="生成工单报表，包含工单统计、完成率、处理时长分析",
                parameters=[
                    ToolParameter(
                        name="report_type",
                        type="string",
                        description="报表类型: daily/weekly/monthly",
                        required=False,
                        enum=["daily", "weekly", "monthly"],
                        default="weekly",
                    ),
                    ToolParameter(
                        name="date",
                        type="string",
                        description="报表日期，格式YYYY-MM-DD",
                        required=False,
                    ),
                ],
                handler=self._generate_ticket_report,
            )
        )

        # 4. 生成综合运营报表
        self.register_tool(
            MCPTool(
                name="generate_operations_report",
                description="生成综合运营报表，汇总能耗、告警、工单等关键指标",
                parameters=[
                    ToolParameter(
                        name="report_type",
                        type="string",
                        description="报表类型: daily/weekly/monthly",
                        required=False,
                        enum=["daily", "weekly", "monthly"],
                        default="daily",
                    ),
                    ToolParameter(
                        name="date",
                        type="string",
                        description="报表日期，格式YYYY-MM-DD",
                        required=False,
                    ),
                ],
                handler=self._generate_operations_report,
            )
        )

        # 5. 获取报表列表
        self.register_tool(
            MCPTool(
                name="get_report_list",
                description="获取可用的报表类型列表",
                parameters=[],
                handler=self._get_report_list,
            )
        )

    def _get_report_period(self, report_type: str, date_str: str | None) -> tuple[datetime, datetime]:
        """计算报表周期"""
        if date_str:
            base_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        else:
            base_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        if report_type == "daily":
            start = base_date
            end = start + timedelta(days=1)
        elif report_type == "weekly":
            # 本周一开始
            start = base_date - timedelta(days=base_date.weekday())
            end = start + timedelta(days=7)
        else:  # monthly
            # 本月1号开始
            start = base_date.replace(day=1)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)

        return start, end

    async def _generate_energy_report(self, args: dict[str, Any]) -> dict[str, Any]:
        """生成能耗报表"""
        report_type = args.get("report_type", "daily")
        energy_type = args.get("energy_type", "all")
        building = args.get("building")
        date_str = args.get("date")

        start, end = self._get_report_period(report_type, date_str)

        # 构建查询
        query = select(EnergyReading).where(
            and_(
                EnergyReading.timestamp >= start,
                EnergyReading.timestamp < end,
            )
        )

        if energy_type != "all":
            query = query.where(EnergyReading.energy_type == energy_type)
        if building:
            query = query.where(EnergyReading.building == building)

        result = await self.db.execute(query)
        readings = result.scalars().all()

        # 统计数据
        total_consumption = sum(r.value for r in readings)

        # 按能源类型分组
        by_type: dict[str, float] = {}
        for r in readings:
            by_type[r.energy_type] = by_type.get(r.energy_type, 0) + r.value

        # 按建筑分组
        by_building: dict[str, float] = {}
        for r in readings:
            if r.building:
                by_building[r.building] = by_building.get(r.building, 0) + r.value

        # 计算同比（去年同期）
        prev_year_start = start.replace(year=start.year - 1)
        prev_year_end = end.replace(year=end.year - 1)

        prev_query = select(func.sum(EnergyReading.value)).where(
            and_(
                EnergyReading.timestamp >= prev_year_start,
                EnergyReading.timestamp < prev_year_end,
            )
        )
        if energy_type != "all":
            prev_query = prev_query.where(EnergyReading.energy_type == energy_type)
        if building:
            prev_query = prev_query.where(EnergyReading.building == building)

        prev_result = await self.db.execute(prev_query)
        prev_total = prev_result.scalar() or 0

        yoy_change = 0.0
        if prev_total > 0:
            yoy_change = round((total_consumption - prev_total) / prev_total * 100, 2)

        type_names = {"daily": "日", "weekly": "周", "monthly": "月"}
        return {
            "report_type": report_type,
            "report_title": f"能耗{type_names[report_type]}报",
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
            "filters": {
                "energy_type": energy_type,
                "building": building,
            },
            "summary": {
                "total_consumption": round(total_consumption, 2),
                "reading_count": len(readings),
                "yoy_change": yoy_change,
            },
            "breakdown": {
                "by_type": {k: round(v, 2) for k, v in by_type.items()},
                "by_building": {k: round(v, 2) for k, v in by_building.items()},
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _generate_alarm_report(self, args: dict[str, Any]) -> dict[str, Any]:
        """生成告警报表"""
        report_type = args.get("report_type", "daily")
        building = args.get("building")
        date_str = args.get("date")

        start, end = self._get_report_period(report_type, date_str)

        # 构建查询
        query = select(Alarm).where(
            and_(
                Alarm.created_at >= start,
                Alarm.created_at < end,
            )
        )

        if building:
            query = query.where(Alarm.building == building)

        result = await self.db.execute(query)
        alarms = result.scalars().all()

        # 统计数据
        total_alarms = len(alarms)
        resolved_alarms = sum(1 for a in alarms if a.status == "resolved")
        acknowledged_alarms = sum(1 for a in alarms if a.status == "acknowledged")

        # 按严重级别分组
        by_severity: dict[str, int] = {}
        for a in alarms:
            by_severity[a.severity] = by_severity.get(a.severity, 0) + 1

        # 按设备类型分组
        by_device_type: dict[str, int] = {}
        for a in alarms:
            if a.device_type:
                by_device_type[a.device_type] = by_device_type.get(a.device_type, 0) + 1

        # 计算平均响应时间
        response_times = []
        for a in alarms:
            if a.acknowledged_at and a.created_at:
                delta = (a.acknowledged_at - a.created_at).total_seconds() / 60  # 分钟
                response_times.append(delta)

        avg_response_time = round(sum(response_times) / len(response_times), 1) if response_times else 0

        resolution_rate = round(resolved_alarms / total_alarms * 100, 1) if total_alarms > 0 else 0

        type_names = {"daily": "日", "weekly": "周", "monthly": "月"}
        return {
            "report_type": report_type,
            "report_title": f"告警{type_names[report_type]}报",
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
            "filters": {
                "building": building,
            },
            "summary": {
                "total_alarms": total_alarms,
                "resolved_alarms": resolved_alarms,
                "acknowledged_alarms": acknowledged_alarms,
                "pending_alarms": total_alarms - resolved_alarms - acknowledged_alarms,
                "resolution_rate": resolution_rate,
                "avg_response_time_minutes": avg_response_time,
            },
            "breakdown": {
                "by_severity": by_severity,
                "by_device_type": by_device_type,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _generate_ticket_report(self, args: dict[str, Any]) -> dict[str, Any]:
        """生成工单报表"""
        report_type = args.get("report_type", "weekly")
        date_str = args.get("date")

        start, end = self._get_report_period(report_type, date_str)

        # 构建查询
        query = select(Ticket).where(
            and_(
                Ticket.created_at >= start,
                Ticket.created_at < end,
            )
        )

        result = await self.db.execute(query)
        tickets = result.scalars().all()

        # 统计数据
        total_tickets = len(tickets)
        completed_tickets = sum(1 for t in tickets if t.status == TicketStatus.COMPLETED.value)
        in_progress_tickets = sum(1 for t in tickets if t.status == TicketStatus.IN_PROGRESS.value)
        pending_tickets = sum(1 for t in tickets if t.status in [TicketStatus.PENDING.value, TicketStatus.ASSIGNED.value])

        # 按类型分组
        by_type: dict[str, int] = {}
        for t in tickets:
            by_type[t.type] = by_type.get(t.type, 0) + 1

        # 按优先级分组
        by_priority: dict[str, int] = {}
        for t in tickets:
            by_priority[t.priority] = by_priority.get(t.priority, 0) + 1

        # 按负责人分组
        by_assignee: dict[str, int] = {}
        for t in tickets:
            assignee = t.assigned_to or "未分配"
            by_assignee[assignee] = by_assignee.get(assignee, 0) + 1

        # 计算平均处理时长
        processing_times = []
        for t in tickets:
            if t.completed_at and t.started_at:
                delta = (t.completed_at - t.started_at).total_seconds() / 3600  # 小时
                processing_times.append(delta)

        avg_processing_time = round(sum(processing_times) / len(processing_times), 1) if processing_times else 0

        completion_rate = round(completed_tickets / total_tickets * 100, 1) if total_tickets > 0 else 0

        # 逾期工单统计
        now = datetime.now(timezone.utc)
        overdue_tickets = sum(
            1 for t in tickets
            if t.due_date and t.due_date < now and t.status not in [TicketStatus.COMPLETED.value, TicketStatus.CANCELLED.value]
        )

        type_names = {"daily": "日", "weekly": "周", "monthly": "月"}
        return {
            "report_type": report_type,
            "report_title": f"工单{type_names[report_type]}报",
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
            "summary": {
                "total_tickets": total_tickets,
                "completed_tickets": completed_tickets,
                "in_progress_tickets": in_progress_tickets,
                "pending_tickets": pending_tickets,
                "overdue_tickets": overdue_tickets,
                "completion_rate": completion_rate,
                "avg_processing_time_hours": avg_processing_time,
            },
            "breakdown": {
                "by_type": by_type,
                "by_priority": by_priority,
                "by_assignee": by_assignee,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _generate_operations_report(self, args: dict[str, Any]) -> dict[str, Any]:
        """生成综合运营报表"""
        report_type = args.get("report_type", "daily")
        date_str = args.get("date")

        # 获取各项报表数据
        energy_report = await self._generate_energy_report({
            "report_type": report_type,
            "energy_type": "all",
            "date": date_str,
        })

        alarm_report = await self._generate_alarm_report({
            "report_type": report_type,
            "date": date_str,
        })

        ticket_report = await self._generate_ticket_report({
            "report_type": report_type,
            "date": date_str,
        })

        # 汇总关键指标
        type_names = {"daily": "日", "weekly": "周", "monthly": "月"}
        return {
            "report_type": report_type,
            "report_title": f"运营综合{type_names[report_type]}报",
            "period": energy_report["period"],
            "key_metrics": {
                "energy": {
                    "total_consumption": energy_report["summary"]["total_consumption"],
                    "yoy_change": energy_report["summary"]["yoy_change"],
                },
                "alarms": {
                    "total": alarm_report["summary"]["total_alarms"],
                    "resolution_rate": alarm_report["summary"]["resolution_rate"],
                    "avg_response_time": alarm_report["summary"]["avg_response_time_minutes"],
                },
                "tickets": {
                    "total": ticket_report["summary"]["total_tickets"],
                    "completion_rate": ticket_report["summary"]["completion_rate"],
                    "overdue": ticket_report["summary"]["overdue_tickets"],
                },
            },
            "details": {
                "energy": energy_report["breakdown"],
                "alarms": alarm_report["breakdown"],
                "tickets": ticket_report["breakdown"],
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _get_report_list(self, args: dict[str, Any]) -> dict[str, Any]:
        """获取报表列表"""
        return {
            "reports": [
                {
                    "name": "generate_energy_report",
                    "title": "能耗报表",
                    "description": "包含用量统计、趋势分析、对比数据",
                    "types": ["daily", "weekly", "monthly"],
                },
                {
                    "name": "generate_alarm_report",
                    "title": "告警报表",
                    "description": "包含告警统计、处理情况、趋势分析",
                    "types": ["daily", "weekly", "monthly"],
                },
                {
                    "name": "generate_ticket_report",
                    "title": "工单报表",
                    "description": "包含工单统计、完成率、处理时长分析",
                    "types": ["daily", "weekly", "monthly"],
                },
                {
                    "name": "generate_operations_report",
                    "title": "运营综合报表",
                    "description": "汇总能耗、告警、工单等关键指标",
                    "types": ["daily", "weekly", "monthly"],
                },
            ],
        }
