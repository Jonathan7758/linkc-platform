"""工单管理MCP Server模块"""

from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp_servers.base_mcp_server import (
    BaseMCPServer,
    MCPServerType,
    MCPTool,
    ToolParameter,
)
from app.models.ticket import Ticket, TicketType, TicketPriority, TicketStatus


class TicketMCPServer(BaseMCPServer):
    """工单管理MCP Server

    提供工单查询、创建、分配、更新等功能。
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        super().__init__(MCPServerType.TICKET)

    def _register_tools(self) -> None:
        """注册工单管理工具"""

        # 1. 获取工单列表
        self.register_tool(
            MCPTool(
                name="get_ticket_list",
                description="获取工单列表，支持按状态、类型、优先级、负责人等条件筛选",
                parameters=[
                    ToolParameter(
                        name="status",
                        type="string",
                        description="工单状态: pending/assigned/in_progress/completed/cancelled",
                        required=False,
                        enum=["pending", "assigned", "in_progress", "completed", "cancelled"],
                    ),
                    ToolParameter(
                        name="type",
                        type="string",
                        description="工单类型: repair/maintenance/inspection/installation/upgrade",
                        required=False,
                        enum=["repair", "maintenance", "inspection", "installation", "upgrade"],
                    ),
                    ToolParameter(
                        name="priority",
                        type="string",
                        description="优先级: urgent/high/medium/low",
                        required=False,
                        enum=["urgent", "high", "medium", "low"],
                    ),
                    ToolParameter(
                        name="assigned_to",
                        type="string",
                        description="负责人",
                        required=False,
                    ),
                    ToolParameter(
                        name="days",
                        type="integer",
                        description="查询最近多少天的工单，默认7",
                        required=False,
                        default=7,
                    ),
                    ToolParameter(
                        name="limit",
                        type="integer",
                        description="返回数量限制，默认20",
                        required=False,
                        default=20,
                    ),
                ],
                handler=self._get_ticket_list,
            )
        )

        # 2. 获取工单详情
        self.register_tool(
            MCPTool(
                name="get_ticket_detail",
                description="根据工单ID获取详细信息",
                parameters=[
                    ToolParameter(
                        name="ticket_id",
                        type="string",
                        description="工单ID",
                        required=True,
                    ),
                ],
                handler=self._get_ticket_detail,
            )
        )

        # 3. 创建工单
        self.register_tool(
            MCPTool(
                name="create_ticket",
                description="创建新工单",
                parameters=[
                    ToolParameter(
                        name="title",
                        type="string",
                        description="工单标题",
                        required=True,
                    ),
                    ToolParameter(
                        name="description",
                        type="string",
                        description="工单描述",
                        required=False,
                    ),
                    ToolParameter(
                        name="type",
                        type="string",
                        description="工单类型: repair/maintenance/inspection/installation/upgrade",
                        required=True,
                        enum=["repair", "maintenance", "inspection", "installation", "upgrade"],
                    ),
                    ToolParameter(
                        name="priority",
                        type="string",
                        description="优先级: urgent/high/medium/low",
                        required=False,
                        enum=["urgent", "high", "medium", "low"],
                        default="medium",
                    ),
                    ToolParameter(
                        name="device_id",
                        type="string",
                        description="关联设备ID",
                        required=False,
                    ),
                    ToolParameter(
                        name="alarm_id",
                        type="string",
                        description="关联告警ID",
                        required=False,
                    ),
                    ToolParameter(
                        name="created_by",
                        type="string",
                        description="创建人",
                        required=False,
                    ),
                ],
                handler=self._create_ticket,
            )
        )

        # 4. 分配工单
        self.register_tool(
            MCPTool(
                name="assign_ticket",
                description="分配工单给指定负责人",
                parameters=[
                    ToolParameter(
                        name="ticket_id",
                        type="string",
                        description="工单ID",
                        required=True,
                    ),
                    ToolParameter(
                        name="assigned_to",
                        type="string",
                        description="负责人",
                        required=True,
                    ),
                ],
                handler=self._assign_ticket,
            )
        )

        # 5. 更新工单状态
        self.register_tool(
            MCPTool(
                name="update_ticket_status",
                description="更新工单状态",
                parameters=[
                    ToolParameter(
                        name="ticket_id",
                        type="string",
                        description="工单ID",
                        required=True,
                    ),
                    ToolParameter(
                        name="status",
                        type="string",
                        description="新状态: pending/assigned/in_progress/completed/cancelled",
                        required=True,
                        enum=["pending", "assigned", "in_progress", "completed", "cancelled"],
                    ),
                    ToolParameter(
                        name="work_notes",
                        type="string",
                        description="工作备注",
                        required=False,
                    ),
                ],
                handler=self._update_ticket_status,
            )
        )

        # 6. 获取工单统计
        self.register_tool(
            MCPTool(
                name="get_ticket_stats",
                description="获取工单统计信息",
                parameters=[
                    ToolParameter(
                        name="group_by",
                        type="string",
                        description="分组维度: status/type/priority/assigned_to",
                        required=False,
                        enum=["status", "type", "priority", "assigned_to"],
                        default="status",
                    ),
                    ToolParameter(
                        name="days",
                        type="integer",
                        description="统计最近多少天，默认30",
                        required=False,
                        default=30,
                    ),
                ],
                handler=self._get_ticket_stats,
            )
        )

    async def _get_ticket_list(self, args: dict[str, Any]) -> dict[str, Any]:
        """获取工单列表"""
        status = args.get("status")
        ticket_type = args.get("type")
        priority = args.get("priority")
        assigned_to = args.get("assigned_to")
        days = args.get("days", 7)
        limit = args.get("limit", 20)

        since = datetime.now(timezone.utc) - timedelta(days=days)

        query = select(Ticket).where(Ticket.created_at >= since)

        if status:
            query = query.where(Ticket.status == status)
        if ticket_type:
            query = query.where(Ticket.type == ticket_type)
        if priority:
            query = query.where(Ticket.priority == priority)
        if assigned_to:
            query = query.where(Ticket.assigned_to == assigned_to)

        query = query.order_by(Ticket.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        tickets = result.scalars().all()

        return {
            "period_days": days,
            "total_count": len(tickets),
            "tickets": [
                {
                    "ticket_id": t.ticket_id,
                    "title": t.title,
                    "type": t.type,
                    "priority": t.priority,
                    "status": t.status,
                    "assigned_to": t.assigned_to,
                    "device_id": t.device_id,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                }
                for t in tickets
            ],
        }

    async def _get_ticket_detail(self, args: dict[str, Any]) -> dict[str, Any]:
        """获取工单详情"""
        ticket_id = args["ticket_id"]

        query = select(Ticket).where(Ticket.ticket_id == ticket_id)
        result = await self.db.execute(query)
        ticket = result.scalar_one_or_none()

        if not ticket:
            return {
                "found": False,
                "message": f"工单 {ticket_id} 不存在",
            }

        return {
            "found": True,
            "ticket": {
                "ticket_id": ticket.ticket_id,
                "title": ticket.title,
                "description": ticket.description,
                "type": ticket.type,
                "priority": ticket.priority,
                "status": ticket.status,
                "device_id": ticket.device_id,
                "alarm_id": ticket.alarm_id,
                "created_by": ticket.created_by,
                "assigned_to": ticket.assigned_to,
                "due_date": ticket.due_date.isoformat() if ticket.due_date else None,
                "started_at": ticket.started_at.isoformat() if ticket.started_at else None,
                "completed_at": ticket.completed_at.isoformat() if ticket.completed_at else None,
                "work_notes": ticket.work_notes,
                "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
            },
        }

    async def _create_ticket(self, args: dict[str, Any]) -> dict[str, Any]:
        """创建工单"""
        title = args["title"]
        description = args.get("description")
        ticket_type = args["type"]
        priority = args.get("priority", "medium")
        device_id = args.get("device_id")
        alarm_id = args.get("alarm_id")
        created_by = args.get("created_by")

        # 生成工单ID
        ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        ticket = Ticket(
            ticket_id=ticket_id,
            title=title,
            description=description,
            type=ticket_type,
            priority=priority,
            status=TicketStatus.PENDING.value,
            device_id=device_id,
            alarm_id=alarm_id,
            created_by=created_by,
        )

        self.db.add(ticket)
        await self.db.flush()

        return {
            "success": True,
            "ticket_id": ticket_id,
            "message": f"工单已创建: {title}",
        }

    async def _assign_ticket(self, args: dict[str, Any]) -> dict[str, Any]:
        """分配工单"""
        ticket_id = args["ticket_id"]
        assigned_to = args["assigned_to"]

        query = select(Ticket).where(Ticket.ticket_id == ticket_id)
        result = await self.db.execute(query)
        ticket = result.scalar_one_or_none()

        if not ticket:
            return {
                "success": False,
                "message": f"工单 {ticket_id} 不存在",
            }

        if ticket.status == TicketStatus.COMPLETED.value:
            return {
                "success": False,
                "message": "已完成的工单不能重新分配",
            }

        if ticket.status == TicketStatus.CANCELLED.value:
            return {
                "success": False,
                "message": "已取消的工单不能分配",
            }

        ticket.assigned_to = assigned_to
        if ticket.status == TicketStatus.PENDING.value:
            ticket.status = TicketStatus.ASSIGNED.value
        await self.db.flush()

        return {
            "success": True,
            "ticket_id": ticket_id,
            "assigned_to": assigned_to,
            "new_status": ticket.status,
            "message": f"工单已分配给 {assigned_to}",
        }

    async def _update_ticket_status(self, args: dict[str, Any]) -> dict[str, Any]:
        """更新工单状态"""
        ticket_id = args["ticket_id"]
        new_status = args["status"]
        work_notes = args.get("work_notes")

        query = select(Ticket).where(Ticket.ticket_id == ticket_id)
        result = await self.db.execute(query)
        ticket = result.scalar_one_or_none()

        if not ticket:
            return {
                "success": False,
                "message": f"工单 {ticket_id} 不存在",
            }

        old_status = ticket.status
        now = datetime.now(timezone.utc)

        # 状态转换逻辑
        if new_status == TicketStatus.IN_PROGRESS.value and not ticket.started_at:
            ticket.started_at = now
        elif new_status == TicketStatus.COMPLETED.value:
            ticket.completed_at = now

        ticket.status = new_status

        if work_notes:
            existing_notes = ticket.work_notes or ""
            timestamp = now.strftime("%Y-%m-%d %H:%M")
            new_note = f"[{timestamp}] {work_notes}"
            ticket.work_notes = f"{existing_notes}\n{new_note}".strip()

        await self.db.flush()

        return {
            "success": True,
            "ticket_id": ticket_id,
            "old_status": old_status,
            "new_status": new_status,
            "message": f"工单状态已更新: {old_status} -> {new_status}",
        }

    async def _get_ticket_stats(self, args: dict[str, Any]) -> dict[str, Any]:
        """获取工单统计"""
        group_by = args.get("group_by", "status")
        days = args.get("days", 30)

        since = datetime.now(timezone.utc) - timedelta(days=days)

        # 根据分组维度选择字段
        group_column = getattr(Ticket, group_by, Ticket.status)

        query = (
            select(group_column, func.count(Ticket.id).label("count"))
            .where(Ticket.created_at >= since)
            .group_by(group_column)
        )

        result = await self.db.execute(query)
        rows = result.all()

        stats = {str(row[0]) if row[0] else "unknown": row[1] for row in rows}
        total = sum(stats.values())

        # 额外统计
        overdue_query = select(func.count(Ticket.id)).where(
            and_(
                Ticket.due_date < datetime.now(timezone.utc),
                Ticket.status.not_in([TicketStatus.COMPLETED.value, TicketStatus.CANCELLED.value]),
            )
        )
        overdue_result = await self.db.execute(overdue_query)
        overdue_count = overdue_result.scalar() or 0

        return {
            "period_days": days,
            "group_by": group_by,
            "total_count": total,
            "overdue_count": overdue_count,
            "stats": stats,
        }
