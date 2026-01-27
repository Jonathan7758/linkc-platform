"""
M1: 空间管理 MCP Server - 主入口
================================
"""

import asyncio
import json
from mcp.server import Server
from mcp.types import TextContent, Tool

from src.mcp_servers.space_manager.tools import SpaceManagerTools
from src.mcp_servers.space_manager.storage import SpaceStorage


# 创建 MCP Server 实例
app = Server("ecis-robot-space-manager")

# 存储层
storage = SpaceStorage()

# Tools 实现
tools = SpaceManagerTools(storage)


# ============================================================
# Tool 定义
# ============================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的 Tools"""
    return [
        # ============ Building Tools ============
        Tool(
            name="list_buildings",
            description="列出所有楼宇",
            inputSchema={
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "string", "description": "租户ID"}
                },
                "required": ["tenant_id"]
            }
        ),
        Tool(
            name="get_building",
            description="获取楼宇详情",
            inputSchema={
                "type": "object",
                "properties": {
                    "building_id": {"type": "string", "description": "楼宇ID"}
                },
                "required": ["building_id"]
            }
        ),

        # ============ Floor Tools ============
        Tool(
            name="list_floors",
            description="列出楼宇的所有楼层",
            inputSchema={
                "type": "object",
                "properties": {
                    "building_id": {"type": "string", "description": "楼宇ID"}
                },
                "required": ["building_id"]
            }
        ),
        Tool(
            name="get_floor",
            description="获取楼层详情",
            inputSchema={
                "type": "object",
                "properties": {
                    "floor_id": {"type": "string", "description": "楼层ID"}
                },
                "required": ["floor_id"]
            }
        ),

        # ============ Zone Tools ============
        Tool(
            name="list_zones",
            description="列出区域，可按楼层或楼宇筛选",
            inputSchema={
                "type": "object",
                "properties": {
                    "floor_id": {"type": "string", "description": "楼层ID"},
                    "building_id": {"type": "string", "description": "楼宇ID"},
                    "zone_type": {"type": "string", "description": "区域类型"}
                }
            }
        ),
        Tool(
            name="get_zone",
            description="获取区域详情",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "区域ID"}
                },
                "required": ["zone_id"]
            }
        ),
        Tool(
            name="update_zone",
            description="更新区域信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "区域ID"},
                    "name": {"type": "string", "description": "区域名称"},
                    "zone_type": {"type": "string", "description": "区域类型"},
                    "cleanable": {"type": "boolean", "description": "是否可清洁"},
                    "clean_priority": {"type": "integer", "description": "清洁优先级1-10"},
                    "clean_frequency": {"type": "string", "description": "清洁频率: hourly/daily/weekly"}
                },
                "required": ["zone_id"]
            }
        ),

        # ============ Point Tools ============
        Tool(
            name="list_points",
            description="列出点位，可按区域、楼层或类型筛选",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "区域ID"},
                    "floor_id": {"type": "string", "description": "楼层ID"},
                    "point_type": {"type": "string", "description": "点位类型: charging/waypoint/entrance/exit/landmark"}
                }
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理 Tool 调用"""

    try:
        if name == "list_buildings":
            result = await tools.list_buildings(arguments.get("tenant_id", ""))

        elif name == "get_building":
            result = await tools.get_building(arguments.get("building_id", ""))

        elif name == "list_floors":
            result = await tools.list_floors(arguments.get("building_id", ""))

        elif name == "get_floor":
            result = await tools.get_floor(arguments.get("floor_id", ""))

        elif name == "list_zones":
            result = await tools.list_zones(
                floor_id=arguments.get("floor_id"),
                building_id=arguments.get("building_id"),
                zone_type=arguments.get("zone_type")
            )

        elif name == "get_zone":
            result = await tools.get_zone(arguments.get("zone_id", ""))

        elif name == "update_zone":
            result = await tools.update_zone(
                zone_id=arguments.get("zone_id", ""),
                name=arguments.get("name"),
                zone_type=arguments.get("zone_type"),
                cleanable=arguments.get("cleanable"),
                clean_priority=arguments.get("clean_priority"),
                clean_frequency=arguments.get("clean_frequency")
            )

        elif name == "list_points":
            result = await tools.list_points(
                zone_id=arguments.get("zone_id"),
                floor_id=arguments.get("floor_id"),
                point_type=arguments.get("point_type")
            )

        else:
            result = {"success": False, "error": f"Unknown tool: {name}", "error_code": "UNKNOWN_TOOL"}

        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    except Exception as e:
        error_result = {"success": False, "error": str(e), "error_code": "INTERNAL_ERROR"}
        return [TextContent(type="text", text=json.dumps(error_result))]


# ============================================================
# 启动入口
# ============================================================

async def main():
    """启动 MCP Server"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
