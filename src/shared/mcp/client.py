"""
MCP Client Adapter - 统一的 MCP 工具调用接口
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MCPResult:
    """MCP 调用结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None


class MCPClientAdapter:
    """
    MCP 客户端适配器
    直接调用各 MCP Server 的工具，无需启动独立服务
    """

    def __init__(self):
        self._robot_tools = None
        self._task_tools = None
        self._space_tools = None
        self._initialized = False

    def _ensure_initialized(self):
        """确保工具已初始化"""
        if self._initialized:
            return

        # 初始化机器人工具 (已包含示例数据)
        from src.mcp_servers.robot_gaoxian.storage import InMemoryRobotStorage
        from src.mcp_servers.robot_gaoxian.mock_client import MockGaoxianClient
        from src.mcp_servers.robot_gaoxian.tools import RobotTools

        robot_storage = InMemoryRobotStorage()
        robot_client = MockGaoxianClient(robot_storage)
        self._robot_tools = RobotTools(robot_client, robot_storage)

        # 初始化任务工具 (已包含示例数据)
        from src.mcp_servers.task_manager.storage import InMemoryTaskStorage
        from src.mcp_servers.task_manager.tools import TaskTools

        task_storage = InMemoryTaskStorage()
        self._task_tools = TaskTools(task_storage)

        # 初始化空间工具 (已包含示例数据)
        from src.mcp_servers.space_manager.storage import SpaceStorage
        from src.mcp_servers.space_manager.tools import SpaceManagerTools

        space_storage = SpaceStorage()
        self._space_tools = SpaceManagerTools(space_storage)

        self._initialized = True
        logger.info("MCP Client Adapter initialized")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPResult:
        """
        调用 MCP 工具

        Args:
            tool_name: 工具名称 (如 robot_get_status, task_create_task)
            arguments: 工具参数

        Returns:
            MCPResult: 调用结果
        """
        self._ensure_initialized()

        try:
            # 路由到对应的工具处理器
            if tool_name.startswith("robot_"):
                result = await self._robot_tools.handle(tool_name, arguments)
                if result.success:
                    return MCPResult(success=True, data=result.data)
                else:
                    return MCPResult(success=False, error=result.error)

            elif tool_name.startswith("task_"):
                result = await self._task_tools.handle(tool_name, arguments)
                if result.success:
                    return MCPResult(success=True, data=result.data)
                else:
                    return MCPResult(success=False, error=result.error)

            elif tool_name.startswith("space_"):
                return await self._call_space_tool(tool_name, arguments)

            else:
                return MCPResult(success=False, error=f"Unknown tool: {tool_name}")

        except Exception as e:
            logger.error(f"Tool call failed: {tool_name}, error: {e}")
            return MCPResult(success=False, error=str(e))

    async def _call_space_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPResult:
        """调用空间工具"""
        try:
            if tool_name == "space_list_zones":
                floor_id = arguments.get("floor_id")
                building_id = arguments.get("building_id")
                result = await self._space_tools.list_zones(
                    floor_id=floor_id,
                    building_id=building_id
                )
                return MCPResult(success=True, data=result)

            elif tool_name == "space_get_zone":
                zone_id = arguments.get("zone_id")
                result = await self._space_tools.get_zone(zone_id)
                return MCPResult(success=True, data=result)

            elif tool_name == "space_list_buildings":
                tenant_id = arguments.get("tenant_id")
                result = await self._space_tools.list_buildings(tenant_id)
                return MCPResult(success=True, data=result)

            elif tool_name == "space_list_floors":
                building_id = arguments.get("building_id")
                result = await self._space_tools.list_floors(building_id)
                return MCPResult(success=True, data=result)

            else:
                return MCPResult(success=False, error=f"Unknown space tool: {tool_name}")

        except Exception as e:
            return MCPResult(success=False, error=str(e))


# 全局单例
_client_instance = None


def get_mcp_client() -> MCPClientAdapter:
    """获取 MCP 客户端单例"""
    global _client_instance
    if _client_instance is None:
        _client_instance = MCPClientAdapter()
    return _client_instance
