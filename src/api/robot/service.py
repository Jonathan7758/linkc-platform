"""
G4: 机器人管理API - 服务层
============================
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
import uuid

from .models import (
    RobotCreate, RobotUpdate, RobotControlRequest,
    RobotListItem, RobotDetail, RobotStatus2, RobotListResponse,
    ControlResponse, RobotError, Position, RobotStatistics,
    PositionHistory, StatusHistory,
    RobotBrand, RobotStatus, ControlCommand
)

logger = logging.getLogger(__name__)


class RobotService:
    """机器人管理服务"""

    def __init__(self, mcp_client=None, data_query=None):
        """
        初始化服务

        Args:
            mcp_client: MCP客户端（用于控制机器人）
            data_query: 数据查询服务（用于历史数据）
        """
        self.mcp_client = mcp_client
        self.data_query = data_query

        # 内存存储（测试用）
        self._robots: Dict[str, Dict[str, Any]] = {}
        self._init_sample_data()

    def _init_sample_data(self):
        """初始化示例数据"""
        now = datetime.now(timezone.utc)
        sample_robots = [
            {
                "robot_id": "robot_001",
                "tenant_id": "tenant_001",
                "name": "清洁机器人A-01",
                "brand": "gaoxian",
                "model": "GS-50",
                "serial_number": "GX2024010001",
                "building_id": "building_001",
                "building_name": "A座",
                "current_floor_id": "floor_001",
                "current_floor_name": "1F",
                "status": "idle",
                "battery_level": 85,
                "position": {"x": 5.0, "y": 5.0, "orientation": 0.0, "floor_id": "floor_001"},
                "capabilities": ["cleaning", "mopping", "mapping"],
                "firmware_version": "2.3.1",
                "current_task_id": None,
                "last_active_at": now,
                "created_at": now,
                "updated_at": now
            },
            {
                "robot_id": "robot_002",
                "tenant_id": "tenant_001",
                "name": "清洁机器人A-02",
                "brand": "gaoxian",
                "model": "GS-50",
                "serial_number": "GX2024010002",
                "building_id": "building_001",
                "building_name": "A座",
                "current_floor_id": "floor_001",
                "current_floor_name": "1F",
                "status": "charging",
                "battery_level": 45,
                "position": {"x": 8.0, "y": 5.0, "orientation": 180.0, "floor_id": "floor_001"},
                "capabilities": ["cleaning", "mopping"],
                "firmware_version": "2.3.0",
                "current_task_id": None,
                "last_active_at": now,
                "created_at": now,
                "updated_at": now
            },
            {
                "robot_id": "robot_003",
                "tenant_id": "tenant_001",
                "name": "清洁机器人B-01",
                "brand": "gaoxian",
                "model": "GS-75",
                "serial_number": "GX2024020001",
                "building_id": "building_001",
                "building_name": "A座",
                "current_floor_id": "floor_002",
                "current_floor_name": "2F",
                "status": "working",
                "battery_level": 72,
                "position": {"x": 15.0, "y": 20.0, "orientation": 90.0, "floor_id": "floor_002"},
                "capabilities": ["cleaning", "mopping", "mapping", "elevator"],
                "firmware_version": "2.4.0",
                "current_task_id": "task_001",
                "last_active_at": now,
                "created_at": now,
                "updated_at": now
            }
        ]

        for robot in sample_robots:
            self._robots[robot["robot_id"]] = robot

    # ========== 列表查询 ==========

    async def list_robots(
        self,
        tenant_id: str,
        building_id: str = None,
        brand: str = None,
        status: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> RobotListResponse:
        """获取机器人列表"""
        # 过滤
        robots = [r for r in self._robots.values() if r.get("tenant_id") == tenant_id]

        if building_id:
            robots = [r for r in robots if r.get("building_id") == building_id]
        if brand:
            robots = [r for r in robots if r.get("brand") == brand]
        if status:
            robots = [r for r in robots if r.get("status") == status]

        # 分页
        total = len(robots)
        start = (page - 1) * page_size
        end = start + page_size
        page_robots = robots[start:end]

        # 转换
        items = [self._to_list_item(r) for r in page_robots]

        return RobotListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )

    def _to_list_item(self, data: Dict) -> RobotListItem:
        """转换为列表项"""
        position = None
        if data.get("position"):
            position = Position(**data["position"])

        return RobotListItem(
            robot_id=data["robot_id"],
            name=data["name"],
            brand=data["brand"],
            model=data["model"],
            serial_number=data.get("serial_number"),
            building_id=data.get("building_id"),
            building_name=data.get("building_name"),
            current_floor_id=data.get("current_floor_id"),
            current_floor_name=data.get("current_floor_name"),
            status=data["status"],
            battery_level=data.get("battery_level", 0),
            position=position,
            current_task_id=data.get("current_task_id"),
            last_active_at=data.get("last_active_at"),
            created_at=data.get("created_at", datetime.now(timezone.utc))
        )

    # ========== 详情查询 ==========

    async def get_robot(self, robot_id: str, tenant_id: str) -> Optional[RobotDetail]:
        """获取机器人详情"""
        robot = self._robots.get(robot_id)
        if not robot or robot.get("tenant_id") != tenant_id:
            return None

        return self._to_detail(robot)

    def _to_detail(self, data: Dict) -> RobotDetail:
        """转换为详情"""
        position = None
        if data.get("position"):
            position = Position(**data["position"])

        return RobotDetail(
            robot_id=data["robot_id"],
            name=data["name"],
            brand=data["brand"],
            model=data["model"],
            serial_number=data.get("serial_number"),
            building_id=data.get("building_id"),
            building_name=data.get("building_name"),
            current_floor_id=data.get("current_floor_id"),
            current_floor_name=data.get("current_floor_name"),
            status=data["status"],
            battery_level=data.get("battery_level", 0),
            position=position,
            current_task_id=data.get("current_task_id"),
            last_active_at=data.get("last_active_at"),
            created_at=data.get("created_at", datetime.now(timezone.utc)),
            firmware_version=data.get("firmware_version"),
            capabilities=data.get("capabilities", []),
            consumables=data.get("consumables"),
            current_task=data.get("current_task"),
            statistics=RobotStatistics(
                total_tasks=156,
                total_area_cleaned=45600.5,
                total_working_hours=312.5,
                average_efficiency=145.8
            ),
            updated_at=data.get("updated_at")
        )

    # ========== 创建/更新/删除 ==========

    async def create_robot(self, data: RobotCreate) -> RobotDetail:
        """创建机器人"""
        robot_id = f"robot_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        robot = {
            "robot_id": robot_id,
            "tenant_id": data.tenant_id,
            "name": data.name,
            "brand": data.brand.value,
            "model": data.model,
            "serial_number": data.serial_number,
            "building_id": data.building_id,
            "status": "offline",
            "battery_level": 0,
            "position": None,
            "capabilities": [],
            "current_task_id": None,
            "last_active_at": None,
            "created_at": now,
            "updated_at": now,
            "connection_config": data.connection_config
        }

        self._robots[robot_id] = robot
        logger.info(f"Created robot: {robot_id}")

        return self._to_detail(robot)

    async def update_robot(self, robot_id: str, tenant_id: str, data: RobotUpdate) -> Optional[RobotDetail]:
        """更新机器人"""
        robot = self._robots.get(robot_id)
        if not robot or robot.get("tenant_id") != tenant_id:
            return None

        if data.name is not None:
            robot["name"] = data.name
        if data.building_id is not None:
            robot["building_id"] = data.building_id
        if data.connection_config is not None:
            robot["connection_config"] = data.connection_config

        robot["updated_at"] = datetime.now(timezone.utc)
        logger.info(f"Updated robot: {robot_id}")

        return self._to_detail(robot)

    async def delete_robot(self, robot_id: str, tenant_id: str) -> bool:
        """删除机器人"""
        robot = self._robots.get(robot_id)
        if not robot or robot.get("tenant_id") != tenant_id:
            return False

        del self._robots[robot_id]
        logger.info(f"Deleted robot: {robot_id}")
        return True

    # ========== 实时状态 ==========

    async def get_status(self, robot_id: str, tenant_id: str) -> Optional[RobotStatus2]:
        """获取机器人实时状态"""
        robot = self._robots.get(robot_id)
        if not robot or robot.get("tenant_id") != tenant_id:
            return None

        # 如果有MCP客户端，从MCP获取
        if self.mcp_client:
            try:
                result = await self.mcp_client.call_tool(
                    "robot_get_status",
                    {"robot_id": robot_id}
                )
                if result.success and result.data:
                    data = result.data
                    return RobotStatus2(
                        robot_id=robot_id,
                        status=data.get("status", "unknown"),
                        battery_level=data.get("battery_level", 0),
                        position=Position(
                            x=data.get("current_location", {}).get("x", 0),
                            y=data.get("current_location", {}).get("y", 0),
                            orientation=0,
                            floor_id=data.get("current_location", {}).get("floor_id")
                        ) if data.get("current_location") else None,
                        speed=data.get("speed"),
                        cleaning_mode=data.get("cleaning_mode"),
                        current_task_id=data.get("current_task_id"),
                        task_progress=data.get("task_progress"),
                        errors=[],
                        timestamp=datetime.now(timezone.utc)
                    )
            except Exception as e:
                logger.error(f"Failed to get status from MCP: {e}")

        # 返回内存数据
        position = None
        if robot.get("position"):
            position = Position(**robot["position"])

        return RobotStatus2(
            robot_id=robot_id,
            status=robot["status"],
            battery_level=robot.get("battery_level", 0),
            position=position,
            speed=None,
            cleaning_mode=None,
            current_task_id=robot.get("current_task_id"),
            task_progress=None,
            errors=[],
            timestamp=datetime.now(timezone.utc)
        )

    # ========== 控制指令 ==========

    async def send_control(
        self,
        robot_id: str,
        tenant_id: str,
        request: RobotControlRequest
    ) -> Optional[ControlResponse]:
        """发送控制指令"""
        robot = self._robots.get(robot_id)
        if not robot or robot.get("tenant_id") != tenant_id:
            return None

        now = datetime.now(timezone.utc)
        success = True
        message = f"Command {request.command.value} sent successfully"

        # 如果有MCP客户端，通过MCP发送
        if self.mcp_client:
            try:
                tool_name = self._command_to_tool(request.command)
                args = {"robot_id": robot_id}
                if request.params:
                    args.update(request.params)

                result = await self.mcp_client.call_tool(tool_name, args)
                success = result.success
                if not success:
                    message = result.error or "Command failed"
            except Exception as e:
                logger.error(f"Failed to send command via MCP: {e}")
                success = False
                message = str(e)
        else:
            # 模拟状态更新
            if request.command == ControlCommand.GO_CHARGE:
                robot["status"] = "charging"
            elif request.command == ControlCommand.PAUSE:
                robot["status"] = "paused"
            elif request.command == ControlCommand.RESUME:
                robot["status"] = "working"
            elif request.command == ControlCommand.STOP:
                robot["status"] = "idle"

        return ControlResponse(
            success=success,
            robot_id=robot_id,
            command=request.command.value,
            message=message,
            timestamp=now
        )

    def _command_to_tool(self, command: ControlCommand) -> str:
        """命令转工具名"""
        mapping = {
            ControlCommand.START: "robot_start_task",
            ControlCommand.PAUSE: "robot_pause_task",
            ControlCommand.RESUME: "robot_resume_task",
            ControlCommand.STOP: "robot_cancel_task",
            ControlCommand.GO_CHARGE: "robot_go_to_charge",
            ControlCommand.GO_HOME: "robot_go_to_location",
            ControlCommand.GO_TO: "robot_go_to_location",
        }
        return mapping.get(command, "robot_send_command")

    # ========== 错误查询 ==========

    async def get_errors(
        self,
        robot_id: str,
        tenant_id: str,
        active_only: bool = False
    ) -> List[RobotError]:
        """获取机器人错误"""
        robot = self._robots.get(robot_id)
        if not robot or robot.get("tenant_id") != tenant_id:
            return []

        # 模拟数据
        return []

    # ========== 历史数据 ==========

    async def get_position_history(
        self,
        robot_id: str,
        tenant_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[PositionHistory]:
        """获取位置历史"""
        robot = self._robots.get(robot_id)
        if not robot or robot.get("tenant_id") != tenant_id:
            return []

        if self.data_query:
            try:
                track = await self.data_query.get_position_track(
                    tenant_id, robot_id, start_time, end_time
                )
                return [
                    PositionHistory(
                        timestamp=p.timestamp,
                        x=p.x,
                        y=p.y,
                        floor_id=p.floor_id
                    )
                    for p in track
                ]
            except Exception as e:
                logger.error(f"Failed to get position history: {e}")

        return []

    async def get_status_history(
        self,
        robot_id: str,
        tenant_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[StatusHistory]:
        """获取状态历史"""
        robot = self._robots.get(robot_id)
        if not robot or robot.get("tenant_id") != tenant_id:
            return []

        if self.data_query:
            try:
                history = await self.data_query.get_status_history(
                    tenant_id, robot_id, start_time, end_time
                )
                return [
                    StatusHistory(
                        timestamp=h.timestamp,
                        status=h.status,
                        battery_level=h.battery_level
                    )
                    for h in history
                ]
            except Exception as e:
                logger.error(f"Failed to get status history: {e}")

        return []
