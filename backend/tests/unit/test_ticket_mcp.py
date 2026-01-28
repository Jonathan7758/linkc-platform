"""工单MCP单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

from app.mcp_servers.ticket_mcp import TicketMCPServer
from app.models.ticket import TicketStatus


class TestTicketMCPServer:
    """TicketMCPServer测试"""

    @pytest.fixture
    def mock_db(self):
        """创建mock数据库会话"""
        return MagicMock()

    @pytest.fixture
    def ticket_mcp(self, mock_db):
        """创建工单MCP实例"""
        return TicketMCPServer(mock_db)

    def test_init(self, ticket_mcp):
        """测试初始化"""
        assert ticket_mcp.server_type.value == "ticket"
        assert len(ticket_mcp._tools) == 6

    def test_tools_registered(self, ticket_mcp):
        """测试工具注册"""
        tool_names = list(ticket_mcp._tools.keys())
        assert "get_ticket_list" in tool_names
        assert "get_ticket_detail" in tool_names
        assert "create_ticket" in tool_names
        assert "assign_ticket" in tool_names
        assert "update_ticket_status" in tool_names
        assert "get_ticket_stats" in tool_names


class TestGetTicketList:
    """get_ticket_list测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def ticket_mcp(self, mock_db):
        return TicketMCPServer(mock_db)

    @pytest.fixture
    def sample_tickets(self):
        """示例工单数据"""
        ticket1 = MagicMock()
        ticket1.ticket_id = "TKT-20260125-ABC123"
        ticket1.title = "空调维修"
        ticket1.type = "repair"
        ticket1.priority = "high"
        ticket1.status = "pending"
        ticket1.assigned_to = None
        ticket1.device_id = "DEV-001"
        ticket1.created_at = datetime.now(timezone.utc)
        ticket1.due_date = None

        ticket2 = MagicMock()
        ticket2.ticket_id = "TKT-20260125-DEF456"
        ticket2.title = "设备巡检"
        ticket2.type = "inspection"
        ticket2.priority = "medium"
        ticket2.status = "in_progress"
        ticket2.assigned_to = "张工"
        ticket2.device_id = "DEV-002"
        ticket2.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        ticket2.due_date = datetime.now(timezone.utc) + timedelta(days=1)

        return [ticket1, ticket2]

    @pytest.mark.asyncio
    async def test_get_ticket_list_all(self, ticket_mcp, mock_db, sample_tickets):
        """测试获取所有工单"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = sample_tickets
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await ticket_mcp._get_ticket_list({})

        assert result["total_count"] == 2
        assert len(result["tickets"]) == 2

    @pytest.mark.asyncio
    async def test_get_ticket_list_with_filter(self, ticket_mcp, mock_db, sample_tickets):
        """测试带过滤条件"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_tickets[0]]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await ticket_mcp._get_ticket_list({
            "status": "pending",
            "type": "repair"
        })

        assert result["total_count"] == 1

    @pytest.mark.asyncio
    async def test_get_ticket_list_empty(self, ticket_mcp, mock_db):
        """测试无数据"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await ticket_mcp._get_ticket_list({})

        assert result["total_count"] == 0


class TestGetTicketDetail:
    """get_ticket_detail测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def ticket_mcp(self, mock_db):
        return TicketMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_get_ticket_detail_found(self, ticket_mcp, mock_db):
        """测试找到工单"""
        ticket = MagicMock()
        ticket.ticket_id = "TKT-20260125-ABC123"
        ticket.title = "空调维修"
        ticket.description = "A栋3楼空调不制冷"
        ticket.type = "repair"
        ticket.priority = "high"
        ticket.status = "pending"
        ticket.device_id = "DEV-001"
        ticket.alarm_id = None
        ticket.created_by = "系统"
        ticket.assigned_to = None
        ticket.due_date = None
        ticket.started_at = None
        ticket.completed_at = None
        ticket.work_notes = None
        ticket.created_at = datetime.now(timezone.utc)
        ticket.updated_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ticket
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await ticket_mcp._get_ticket_detail({"ticket_id": "TKT-20260125-ABC123"})

        assert result["found"] is True
        assert result["ticket"]["title"] == "空调维修"

    @pytest.mark.asyncio
    async def test_get_ticket_detail_not_found(self, ticket_mcp, mock_db):
        """测试未找到工单"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await ticket_mcp._get_ticket_detail({"ticket_id": "TKT-NOTEXIST"})

        assert result["found"] is False


class TestCreateTicket:
    """create_ticket测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def ticket_mcp(self, mock_db):
        return TicketMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_create_ticket_success(self, ticket_mcp, mock_db):
        """测试创建工单成功"""
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        result = await ticket_mcp._create_ticket({
            "title": "空调维修",
            "description": "A栋3楼空调不制冷",
            "type": "repair",
            "priority": "high",
        })

        assert result["success"] is True
        assert result["ticket_id"].startswith("TKT-")
        mock_db.add.assert_called_once()


class TestAssignTicket:
    """assign_ticket测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def ticket_mcp(self, mock_db):
        return TicketMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_assign_ticket_success(self, ticket_mcp, mock_db):
        """测试分配工单成功"""
        ticket = MagicMock()
        ticket.ticket_id = "TKT-20260125-ABC123"
        ticket.status = TicketStatus.PENDING.value

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ticket
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        result = await ticket_mcp._assign_ticket({
            "ticket_id": "TKT-20260125-ABC123",
            "assigned_to": "张工"
        })

        assert result["success"] is True
        assert result["assigned_to"] == "张工"
        assert ticket.assigned_to == "张工"

    @pytest.mark.asyncio
    async def test_assign_ticket_not_found(self, ticket_mcp, mock_db):
        """测试工单不存在"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await ticket_mcp._assign_ticket({
            "ticket_id": "TKT-NOTEXIST",
            "assigned_to": "张工"
        })

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_assign_completed_ticket(self, ticket_mcp, mock_db):
        """测试分配已完成工单"""
        ticket = MagicMock()
        ticket.status = TicketStatus.COMPLETED.value

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ticket
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await ticket_mcp._assign_ticket({
            "ticket_id": "TKT-20260125-ABC123",
            "assigned_to": "张工"
        })

        assert result["success"] is False


class TestUpdateTicketStatus:
    """update_ticket_status测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def ticket_mcp(self, mock_db):
        return TicketMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_update_status_to_in_progress(self, ticket_mcp, mock_db):
        """测试更新状态为进行中"""
        ticket = MagicMock()
        ticket.ticket_id = "TKT-20260125-ABC123"
        ticket.status = TicketStatus.ASSIGNED.value
        ticket.started_at = None
        ticket.completed_at = None
        ticket.work_notes = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ticket
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        result = await ticket_mcp._update_ticket_status({
            "ticket_id": "TKT-20260125-ABC123",
            "status": "in_progress",
            "work_notes": "开始处理"
        })

        assert result["success"] is True
        assert result["new_status"] == "in_progress"
        assert ticket.started_at is not None

    @pytest.mark.asyncio
    async def test_update_status_to_completed(self, ticket_mcp, mock_db):
        """测试更新状态为已完成"""
        ticket = MagicMock()
        ticket.ticket_id = "TKT-20260125-ABC123"
        ticket.status = TicketStatus.IN_PROGRESS.value
        ticket.started_at = datetime.now(timezone.utc) - timedelta(hours=2)
        ticket.completed_at = None
        ticket.work_notes = "开始处理"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ticket
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        result = await ticket_mcp._update_ticket_status({
            "ticket_id": "TKT-20260125-ABC123",
            "status": "completed",
            "work_notes": "已修复"
        })

        assert result["success"] is True
        assert result["new_status"] == "completed"
        assert ticket.completed_at is not None


class TestGetTicketStats:
    """get_ticket_stats测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def ticket_mcp(self, mock_db):
        return TicketMCPServer(mock_db)

    @pytest.mark.asyncio
    async def test_get_stats_by_status(self, ticket_mcp, mock_db):
        """测试按状态统计"""
        mock_result1 = MagicMock()
        mock_result1.all.return_value = [
            ("pending", 5),
            ("in_progress", 3),
            ("completed", 10),
        ]

        mock_result2 = MagicMock()
        mock_result2.scalar.return_value = 2

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        result = await ticket_mcp._get_ticket_stats({"group_by": "status"})

        assert result["total_count"] == 18
        assert result["stats"]["pending"] == 5
        assert result["overdue_count"] == 2

    @pytest.mark.asyncio
    async def test_get_stats_by_type(self, ticket_mcp, mock_db):
        """测试按类型统计"""
        mock_result1 = MagicMock()
        mock_result1.all.return_value = [
            ("repair", 8),
            ("maintenance", 5),
            ("inspection", 3),
        ]

        mock_result2 = MagicMock()
        mock_result2.scalar.return_value = 1

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        result = await ticket_mcp._get_ticket_stats({"group_by": "type"})

        assert result["group_by"] == "type"
        assert result["stats"]["repair"] == 8
