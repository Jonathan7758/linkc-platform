"""
M2: 任务管理 MCP Server - 主入口
================================
"""

import asyncio
import json
from mcp.server import Server
from mcp.types import TextContent, Tool

from src.mcp_servers.task_manager.tools import TaskManagerTools
from src.mcp_servers.task_manager.storage import TaskStorage


app = Server("linkc-task-manager")
storage = TaskStorage()
tools = TaskManagerTools(storage)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的 Tools"""
    return [
        Tool(
            name="create_task",
            description="创建清洁任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "string"},
                    "name": {"type": "string"},
                    "zone_id": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"]},
                    "cleaning_mode": {"type": "string", "enum": ["standard", "deep", "quick", "spot"]},
                    "scheduled_start": {"type": "string", "description": "ISO格式时间"},
                    "estimated_duration": {"type": "integer", "description": "预计时长(分钟)"},
                    "notes": {"type": "string"}
                },
                "required": ["tenant_id", "name", "zone_id"]
            }
        ),
        Tool(
            name="list_tasks",
            description="列出任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "string"},
                    "status": {"type": "string"},
                    "zone_id": {"type": "string"},
                    "robot_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 50}
                },
                "required": ["tenant_id"]
            }
        ),
        Tool(
            name="get_task",
            description="获取任务详情",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"}
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="assign_task",
            description="分配任务给机器人",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "robot_id": {"type": "string"},
                    "assigned_by": {"type": "string", "description": "分配者ID"}
                },
                "required": ["task_id", "robot_id", "assigned_by"]
            }
        ),
        Tool(
            name="update_task_status",
            description="更新任务状态",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "status": {"type": "string", "enum": ["pending", "assigned", "in_progress", "completed", "failed", "cancelled"]},
                    "completion_rate": {"type": "number", "minimum": 0, "maximum": 100},
                    "notes": {"type": "string"}
                },
                "required": ["task_id", "status"]
            }
        ),
        Tool(
            name="get_pending_tasks",
            description="获取待分配的任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "string"}
                },
                "required": ["tenant_id"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理 Tool 调用"""
    try:
        if name == "create_task":
            result = await tools.create_task(
                tenant_id=arguments["tenant_id"],
                name=arguments["name"],
                zone_id=arguments["zone_id"],
                priority=arguments.get("priority", "normal"),
                cleaning_mode=arguments.get("cleaning_mode", "standard"),
                scheduled_start=arguments.get("scheduled_start"),
                estimated_duration=arguments.get("estimated_duration"),
                notes=arguments.get("notes")
            )
        elif name == "list_tasks":
            result = await tools.list_tasks(
                tenant_id=arguments["tenant_id"],
                status=arguments.get("status"),
                zone_id=arguments.get("zone_id"),
                robot_id=arguments.get("robot_id"),
                limit=arguments.get("limit", 50)
            )
        elif name == "get_task":
            result = await tools.get_task(arguments["task_id"])
        elif name == "assign_task":
            result = await tools.assign_task(
                task_id=arguments["task_id"],
                robot_id=arguments["robot_id"],
                assigned_by=arguments["assigned_by"]
            )
        elif name == "update_task_status":
            result = await tools.update_task_status(
                task_id=arguments["task_id"],
                status=arguments["status"],
                completion_rate=arguments.get("completion_rate"),
                notes=arguments.get("notes")
            )
        elif name == "get_pending_tasks":
            result = await tools.get_pending_tasks(arguments["tenant_id"])
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
