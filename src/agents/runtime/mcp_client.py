"""
A1: MCP 客户端封装
==================
统一的 MCP Tool 调用接口
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """工具调用结果"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


# MCP Server名称到Tool前缀的映射
TOOL_SERVER_MAPPING = {
    "robot": "gaoxian",
    "space": "space",
    "task": "task",
    "gaoxian": "gaoxian",
    "ecovacs": "ecovacs",
}


class MCPClient:
    """
    MCP 客户端封装
    
    统一管理与多个 MCP Server 的连接和工具调用
    """
    
    def __init__(self, servers: Optional[Dict[str, str]] = None):
        """
        初始化 MCP 客户端
        
        Args:
            servers: MCP Server 配置 {"gaoxian": "http://localhost:8001", ...}
        """
        self.servers = servers or {}
        self._mcp_handlers: Dict[str, Any] = {}
        self._connected = False
    
    async def connect(self) -> None:
        """连接所有 MCP Server"""
        logger.info("Connecting to MCP servers...")
        
        # 尝试加载本地 MCP handlers
        await self._load_local_handlers()
        
        self._connected = True
        logger.info(f"MCP client connected, handlers: {list(self._mcp_handlers.keys())}")
    
    async def disconnect(self) -> None:
        """断开所有连接"""
        self._mcp_handlers.clear()
        self._connected = False
        logger.info("MCP client disconnected")
    
    async def _load_local_handlers(self) -> None:
        """加载本地 MCP handlers (用于本地/测试环境)"""
        try:
            # 高仙机器人 MCP
            from src.mcp_servers.robot_gaoxian.storage import InMemoryRobotStorage
            from src.mcp_servers.robot_gaoxian.mock_client import MockGaoxianClient
            from src.mcp_servers.robot_gaoxian.tools import RobotTools
            
            storage = InMemoryRobotStorage()
            client = MockGaoxianClient(storage)
            self._mcp_handlers["gaoxian"] = RobotTools(client, storage)
            logger.info("Loaded Gaoxian MCP handler")
        except ImportError as e:
            logger.debug(f"Gaoxian MCP not available: {e}")
        
        try:
            # 空间管理 MCP
            from src.mcp_servers.space_manager.storage import InMemorySpaceStorage
            from src.mcp_servers.space_manager.tools import SpaceTools
            
            storage = InMemorySpaceStorage()
            self._mcp_handlers["space"] = SpaceTools(storage)
            logger.info("Loaded Space MCP handler")
        except ImportError as e:
            logger.debug(f"Space MCP not available: {e}")
        
        try:
            # 任务管理 MCP
            from src.mcp_servers.task_manager.storage import InMemoryTaskStorage
            from src.mcp_servers.task_manager.tools import TaskTools
            
            storage = InMemoryTaskStorage()
            self._mcp_handlers["task"] = TaskTools(storage)
            logger.info("Loaded Task MCP handler")
        except ImportError as e:
            logger.debug(f"Task MCP not available: {e}")
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """
        调用 MCP Tool
        
        Args:
            tool_name: 工具名称 (如 robot_list_robots, space_get_building)
            arguments: 工具参数
            
        Returns:
            ToolResult
        """
        if not self._connected:
            return ToolResult(
                success=False,
                error="MCP client not connected",
                error_code="NOT_CONNECTED"
            )
        
        # 根据 tool_name 确定 MCP Server
        server_name = self._get_server_for_tool(tool_name)
        
        handler = self._mcp_handlers.get(server_name)
        if not handler:
            return ToolResult(
                success=False,
                error=f"No handler for server: {server_name}",
                error_code="UNKNOWN_SERVER"
            )
        
        try:
            # 调用 MCP handler
            result = await handler.handle(tool_name, arguments)
            
            if hasattr(result, 'success'):
                return ToolResult(
                    success=result.success,
                    data=result.data if hasattr(result, 'data') else None,
                    error=result.error if hasattr(result, 'error') else None
                )
            else:
                return ToolResult(success=True, data=result)
                
        except Exception as e:
            logger.error(f"MCP call error: {tool_name} - {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_code="MCP_ERROR"
            )
    
    def _get_server_for_tool(self, tool_name: str) -> str:
        """根据工具名称确定 MCP Server"""
        # 工具命名规则: {prefix}_{action}
        # 例如: robot_list_robots, space_get_building
        prefix = tool_name.split("_")[0]
        return TOOL_SERVER_MAPPING.get(prefix, prefix)
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    def get_available_tools(self) -> Dict[str, list]:
        """获取可用的工具列表"""
        tools = {}
        for server_name, handler in self._mcp_handlers.items():
            if hasattr(handler, 'get_tools'):
                tools[server_name] = handler.get_tools()
            else:
                tools[server_name] = ["(tools list not available)"]
        return tools
