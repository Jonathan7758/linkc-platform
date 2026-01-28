"""设备管理MCP Server"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device, DeviceReading
from .base_mcp_server import (
    BaseMCPServer,
    MCPServerType,
    MCPTool,
    ToolParameter,
)


class DeviceNotFoundException(Exception):
    """设备未找到异常"""

    def __init__(self, device_id: str):
        self.device_id = device_id
        super().__init__(f"Device '{device_id}' not found")


class DeviceMCPServer(BaseMCPServer):
    """设备管理MCP Server"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        super().__init__(MCPServerType.DEVICE)

    def _register_tools(self) -> None:
        """注册设备管理工具"""

        # 1. 获取设备状态
        self.register_tool(
            MCPTool(
                name="get_device_status",
                description="获取指定设备的当前状态，包括运行状态、健康度、关键参数等",
                parameters=[
                    ToolParameter(
                        name="device_id",
                        type="string",
                        description="设备唯一标识，如 CH-01, AHU-01",
                        required=True,
                    )
                ],
                handler=self._get_device_status,
            )
        )

        # 2. 获取设备列表
        self.register_tool(
            MCPTool(
                name="get_device_list",
                description="获取设备列表，支持按类型、系统、建筑、状态筛选",
                parameters=[
                    ToolParameter(
                        name="type",
                        type="string",
                        description="设备类型",
                        required=False,
                        enum=[
                            "chiller",
                            "ahu",
                            "fcu",
                            "pump",
                            "cooling_tower",
                            "vav",
                            "transformer",
                            "meter",
                            "elevator",
                            "sensor",
                        ],
                    ),
                    ToolParameter(
                        name="system",
                        type="string",
                        description="所属系统",
                        required=False,
                        enum=[
                            "hvac",
                            "electrical",
                            "plumbing",
                            "fire_protection",
                            "security",
                            "elevator",
                            "bms",
                        ],
                    ),
                    ToolParameter(
                        name="building",
                        type="string",
                        description="建筑名称，如 A栋, B栋",
                        required=False,
                    ),
                    ToolParameter(
                        name="status",
                        type="string",
                        description="设备状态",
                        required=False,
                        enum=["running", "stopped", "fault", "maintenance", "offline"],
                    ),
                    ToolParameter(
                        name="limit",
                        type="integer",
                        description="返回数量限制，默认20",
                        required=False,
                        default=20,
                    ),
                ],
                handler=self._get_device_list,
            )
        )

        # 3. 获取设备读数
        self.register_tool(
            MCPTool(
                name="get_device_readings",
                description="获取设备的历史读数数据",
                parameters=[
                    ToolParameter(
                        name="device_id",
                        type="string",
                        description="设备唯一标识",
                        required=True,
                    ),
                    ToolParameter(
                        name="parameter",
                        type="string",
                        description="参数名称，如 temperature, pressure, current",
                        required=False,
                    ),
                    ToolParameter(
                        name="hours",
                        type="integer",
                        description="查询最近多少小时的数据，默认24",
                        required=False,
                        default=24,
                    ),
                ],
                handler=self._get_device_readings,
            )
        )

        # 4. 获取设备健康度
        self.register_tool(
            MCPTool(
                name="get_device_health",
                description="获取设备健康度详情，包括各项指标评分",
                parameters=[
                    ToolParameter(
                        name="device_id",
                        type="string",
                        description="设备唯一标识",
                        required=True,
                    )
                ],
                handler=self._get_device_health,
            )
        )

        # 5. 获取设备统计
        self.register_tool(
            MCPTool(
                name="get_device_stats",
                description="获取设备统计信息，如各类型数量、各状态数量",
                parameters=[
                    ToolParameter(
                        name="group_by",
                        type="string",
                        description="分组维度",
                        required=False,
                        enum=["type", "system", "status", "building"],
                        default="type",
                    )
                ],
                handler=self._get_device_stats,
            )
        )

        # 6. 控制设备
        self.register_tool(
            MCPTool(
                name="control_device",
                description="发送控制命令到设备（MVP阶段仅模拟）",
                parameters=[
                    ToolParameter(
                        name="device_id",
                        type="string",
                        description="设备唯一标识",
                        required=True,
                    ),
                    ToolParameter(
                        name="action",
                        type="string",
                        description="控制动作",
                        required=True,
                        enum=["start", "stop", "reset", "set_parameter"],
                    ),
                    ToolParameter(
                        name="parameters",
                        type="object",
                        description='控制参数，如 {"temperature": 24}',
                        required=False,
                    ),
                ],
                handler=self._control_device,
            )
        )

    async def _get_device_status(self, args: dict) -> dict:
        """获取设备状态"""
        device_id = args["device_id"]

        result = await self.db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        device = result.scalar_one_or_none()

        if not device:
            raise DeviceNotFoundException(device_id)

        return {
            "device_id": device.device_id,
            "name": device.name,
            "type": device.type if isinstance(device.type, str) else device.type,
            "system": (
                device.system if isinstance(device.system, str) else device.system
            ),
            "status": (
                device.status if isinstance(device.status, str) else device.status
            ),
            "health_score": device.health_score,
            "location": {
                "building": device.building,
                "floor": device.floor,
                "zone": device.zone,
            },
            "parameters": device.parameters,
            "last_updated": device.updated_at.isoformat(),
        }

    async def _get_device_list(self, args: dict) -> dict:
        """获取设备列表"""
        query = select(Device)

        if args.get("type"):
            query = query.where(Device.type == args["type"])
        if args.get("system"):
            query = query.where(Device.system == args["system"])
        if args.get("building"):
            query = query.where(Device.building == args["building"])
        if args.get("status"):
            query = query.where(Device.status == args["status"])

        limit = args.get("limit", 20)
        query = query.limit(limit)

        result = await self.db.execute(query)
        devices = result.scalars().all()

        return {
            "total": len(devices),
            "devices": [
                {
                    "device_id": d.device_id,
                    "name": d.name,
                    "type": d.type if isinstance(d.type, str) else d.type,
                    "status": d.status if isinstance(d.status, str) else d.status,
                    "health_score": d.health_score,
                    "building": d.building,
                }
                for d in devices
            ],
        }

    async def _get_device_readings(self, args: dict) -> dict:
        """获取设备读数"""
        device_id = args["device_id"]
        hours = args.get("hours", 24)
        parameter = args.get("parameter")

        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = (
            select(DeviceReading)
            .where(
                DeviceReading.device_id == device_id,
                DeviceReading.timestamp >= since,
            )
            .order_by(DeviceReading.timestamp.desc())
        )

        if parameter:
            query = query.where(DeviceReading.parameter == parameter)

        result = await self.db.execute(query.limit(100))
        readings = result.scalars().all()

        return {
            "device_id": device_id,
            "period_hours": hours,
            "readings": [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "parameter": r.parameter,
                    "value": r.value,
                    "unit": r.unit,
                }
                for r in readings
            ],
        }

    async def _get_device_health(self, args: dict) -> dict:
        """获取设备健康度"""
        device_id = args["device_id"]

        result = await self.db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        device = result.scalar_one_or_none()

        if not device:
            raise DeviceNotFoundException(device_id)

        # MVP阶段：返回模拟的健康度详情
        recommendations = []
        if device.health_score < 90:
            recommendations.append("建议在下月进行例行保养")
        if device.health_score < 80:
            recommendations.append("健康度较低，请及时检查")

        return {
            "device_id": device.device_id,
            "name": device.name,
            "overall_score": device.health_score,
            "indicators": {
                "运行时长": {"score": 90, "status": "正常"},
                "故障频率": {"score": 95, "status": "正常"},
                "参数稳定性": {"score": 85, "status": "良好"},
                "维护状态": {"score": 88, "status": "良好"},
            },
            "recommendations": recommendations,
        }

    async def _get_device_stats(self, args: dict) -> dict:
        """获取设备统计"""
        group_by = args.get("group_by", "type")

        result = await self.db.execute(select(Device))
        devices = result.scalars().all()

        stats: dict[str, int] = {}
        for device in devices:
            key = getattr(device, group_by, "unknown")
            if hasattr(key, "value"):
                key = key.value
            if key is None:
                key = "unknown"
            stats[key] = stats.get(key, 0) + 1

        return {
            "group_by": group_by,
            "total": len(devices),
            "statistics": stats,
        }

    async def _control_device(self, args: dict) -> dict:
        """控制设备（MVP模拟）"""
        device_id = args["device_id"]
        action = args["action"]
        parameters = args.get("parameters", {})

        # MVP阶段：仅模拟，不实际控制
        return {
            "device_id": device_id,
            "action": action,
            "parameters": parameters,
            "status": "simulated",
            "message": f"模拟执行 {action} 命令成功（MVP阶段不实际控制设备）",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
