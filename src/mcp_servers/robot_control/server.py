"""
M3: 机器人控制 MCP Server - 主入口
==================================
"""

import asyncio
import json
from mcp.server import Server
from mcp.types import TextContent, Tool

from src.mcp_servers.robot_control.tools import RobotControlTools
from src.mcp_servers.robot_control.storage import RobotStorage


app = Server("ecis-robot-robot-control")
storage = RobotStorage()
tools = RobotControlTools(storage)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的 Tools"""
    return [
        Tool(
            name="list_robots",
            description="列出机器人",
            inputSchema={
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "string"},
                    "building_id": {"type": "string"},
                    "status": {"type": "string", "enum": ["idle", "working", "charging", "error", "offline"]}
                },
                "required": ["tenant_id"]
            }
        ),
        Tool(
            name="get_robot_status",
            description="获取机器人状态",
            inputSchema={
                "type": "object",
                "properties": {
                    "robot_id": {"type": "string"}
                },
                "required": ["robot_id"]
            }
        ),
        Tool(
            name="start_cleaning",
            description="启动机器人清洁任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "robot_id": {"type": "string"},
                    "zone_id": {"type": "string"},
                    "cleaning_mode": {"type": "string", "enum": ["standard", "deep", "quick", "spot"]}
                },
                "required": ["robot_id", "zone_id"]
            }
        ),
        Tool(
            name="stop_cleaning",
            description="停止机器人清洁任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "robot_id": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["robot_id"]
            }
        ),
        Tool(
            name="send_to_charger",
            description="发送机器人去充电",
            inputSchema={
                "type": "object",
                "properties": {
                    "robot_id": {"type": "string"}
                },
                "required": ["robot_id"]
            }
        ),
        Tool(
            name="get_available_robots",
            description="获取可用的机器人（空闲且电量充足）",
            inputSchema={
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "string"},
                    "min_battery": {"type": "integer", "default": 20, "description": "最低电量要求(%)"}
                },
                "required": ["tenant_id"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理 Tool 调用"""
    try:
        if name == "list_robots":
            result = await tools.list_robots(
                tenant_id=arguments["tenant_id"],
                building_id=arguments.get("building_id"),
                status=arguments.get("status")
            )
        elif name == "get_robot_status":
            result = await tools.get_robot_status(arguments["robot_id"])
        elif name == "start_cleaning":
            result = await tools.start_cleaning(
                robot_id=arguments["robot_id"],
                zone_id=arguments["zone_id"],
                cleaning_mode=arguments.get("cleaning_mode", "standard")
            )
        elif name == "stop_cleaning":
            result = await tools.stop_cleaning(
                robot_id=arguments["robot_id"],
                reason=arguments.get("reason")
            )
        elif name == "send_to_charger":
            result = await tools.send_to_charger(arguments["robot_id"])
        elif name == "get_available_robots":
            result = await tools.get_available_robots(
                tenant_id=arguments["tenant_id"],
                min_battery=arguments.get("min_battery", 20)
            )
        else:
            result = {"success": False, "error": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
    
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}))]


async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
