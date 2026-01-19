"""
M2: 任务管理 MCP Server - 主入口
================================
基于规格书 docs/specs/M2-task-mcp.md 实现
"""

import asyncio
import json
import logging
from mcp.server import Server
from mcp.types import TextContent, Tool
from pydantic import BaseModel

from .storage import InMemoryTaskStorage
from .tools import TaskTools

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================
# MCP Server 定义
# ============================================================

app = Server("task-manager")

# 全局存储和工具实例
storage = InMemoryTaskStorage()
tools = TaskTools(storage)


# ============================================================
# Tool 定义列表
# ============================================================

TOOL_DEFINITIONS = [
    Tool(
        name="task_list_schedules",
        description="获取清洁排程列表。按租户ID筛选，可选按区域、楼宇、激活状态过滤。",
        inputSchema={
            "type": "object",
            "properties": {
                "tenant_id": {
                    "type": "string",
                    "description": "租户ID（必填）"
                },
                "zone_id": {
                    "type": "string",
                    "description": "区域ID（可选）"
                },
                "building_id": {
                    "type": "string",
                    "description": "楼宇ID（可选）"
                },
                "is_active": {
                    "type": "boolean",
                    "description": "是否激活，默认true"
                }
            },
            "required": ["tenant_id"]
        }
    ),
    Tool(
        name="task_get_schedule",
        description="获取单个排程的详细信息。",
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "string",
                    "description": "排程ID（必填）"
                }
            },
            "required": ["schedule_id"]
        }
    ),
    Tool(
        name="task_create_schedule",
        description="创建新的清洁排程。设置区域、任务类型、频率和时间段。",
        inputSchema={
            "type": "object",
            "properties": {
                "tenant_id": {
                    "type": "string",
                    "description": "租户ID（必填）"
                },
                "zone_id": {
                    "type": "string",
                    "description": "区域ID（必填）"
                },
                "zone_name": {
                    "type": "string",
                    "description": "区域名称（可选，展示用）"
                },
                "task_type": {
                    "type": "string",
                    "enum": ["routine", "deep", "spot", "emergency"],
                    "description": "任务类型（必填）"
                },
                "frequency": {
                    "type": "string",
                    "enum": ["once", "daily", "weekly", "monthly"],
                    "description": "执行频率（必填）"
                },
                "time_slots": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "string", "description": "开始时间 HH:MM"},
                            "end": {"type": "string", "description": "结束时间 HH:MM"},
                            "days": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "星期几执行，1=周一，7=周日"
                            }
                        },
                        "required": ["start", "end"]
                    },
                    "description": "时间段列表（必填）"
                },
                "priority": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "优先级1-10，1最高，默认5"
                },
                "estimated_duration": {
                    "type": "integer",
                    "description": "预计时长（分钟），默认30"
                },
                "created_by": {
                    "type": "string",
                    "description": "创建者"
                }
            },
            "required": ["tenant_id", "zone_id", "task_type", "frequency", "time_slots"]
        }
    ),
    Tool(
        name="task_update_schedule",
        description="更新排程配置。可更新激活状态、优先级、时间段、频率。",
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "string",
                    "description": "排程ID（必填）"
                },
                "updates": {
                    "type": "object",
                    "properties": {
                        "is_active": {"type": "boolean"},
                        "priority": {"type": "integer", "minimum": 1, "maximum": 10},
                        "time_slots": {"type": "array"},
                        "frequency": {"type": "string"}
                    },
                    "description": "要更新的字段（必填）"
                }
            },
            "required": ["schedule_id", "updates"]
        }
    ),
    Tool(
        name="task_list_tasks",
        description="获取清洁任务列表。支持多条件筛选和分页。",
        inputSchema={
            "type": "object",
            "properties": {
                "tenant_id": {
                    "type": "string",
                    "description": "租户ID（必填）"
                },
                "zone_id": {
                    "type": "string",
                    "description": "区域ID（可选）"
                },
                "robot_id": {
                    "type": "string",
                    "description": "机器人ID（可选）"
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "assigned", "in_progress", "completed", "failed", "cancelled"],
                    "description": "任务状态（可选）"
                },
                "date_from": {
                    "type": "string",
                    "description": "开始日期 YYYY-MM-DD（可选）"
                },
                "date_to": {
                    "type": "string",
                    "description": "结束日期 YYYY-MM-DD（可选）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回数量限制，默认50"
                },
                "offset": {
                    "type": "integer",
                    "description": "偏移量，默认0"
                }
            },
            "required": ["tenant_id"]
        }
    ),
    Tool(
        name="task_get_task",
        description="获取单个任务的详细信息。",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "任务ID（必填）"
                }
            },
            "required": ["task_id"]
        }
    ),
    Tool(
        name="task_create_task",
        description="创建新的清洁任务。emergency类型自动设置priority=1。",
        inputSchema={
            "type": "object",
            "properties": {
                "tenant_id": {
                    "type": "string",
                    "description": "租户ID（必填）"
                },
                "zone_id": {
                    "type": "string",
                    "description": "区域ID（必填）"
                },
                "zone_name": {
                    "type": "string",
                    "description": "区域名称（可选）"
                },
                "task_type": {
                    "type": "string",
                    "enum": ["routine", "deep", "spot", "emergency"],
                    "description": "任务类型（必填）"
                },
                "priority": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "优先级1-10，1最高。emergency自动为1"
                },
                "scheduled_start": {
                    "type": "string",
                    "description": "计划开始时间 ISO格式（可选）"
                },
                "schedule_id": {
                    "type": "string",
                    "description": "关联的排程ID（可选）"
                },
                "notes": {
                    "type": "string",
                    "description": "备注（可选）"
                },
                "created_by": {
                    "type": "string",
                    "description": "创建者"
                }
            },
            "required": ["tenant_id", "zone_id", "task_type"]
        }
    ),
    Tool(
        name="task_update_status",
        description="更新任务状态（状态机）。状态流转：pending→assigned→in_progress→completed/failed。完成需completion_rate，失败需failure_reason。",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "任务ID（必填）"
                },
                "status": {
                    "type": "string",
                    "enum": ["assigned", "in_progress", "completed", "failed", "cancelled"],
                    "description": "新状态（必填）"
                },
                "robot_id": {
                    "type": "string",
                    "description": "分配的机器人ID（assigned时必填）"
                },
                "robot_name": {
                    "type": "string",
                    "description": "机器人名称（可选）"
                },
                "actual_start": {
                    "type": "string",
                    "description": "实际开始时间 ISO格式"
                },
                "actual_end": {
                    "type": "string",
                    "description": "实际结束时间 ISO格式"
                },
                "completion_rate": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "完成率0-100（completed时必填）"
                },
                "failure_reason": {
                    "type": "string",
                    "description": "失败原因（failed时必填）"
                }
            },
            "required": ["task_id", "status"]
        }
    ),
    Tool(
        name="task_get_pending_tasks",
        description="获取待执行任务列表。供Agent调度使用，按优先级和计划时间排序。",
        inputSchema={
            "type": "object",
            "properties": {
                "tenant_id": {
                    "type": "string",
                    "description": "租户ID（必填）"
                },
                "zone_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "区域ID列表（可选，不指定返回全部）"
                },
                "max_count": {
                    "type": "integer",
                    "description": "最大返回数量，默认20"
                }
            },
            "required": ["tenant_id"]
        }
    ),
    Tool(
        name="task_generate_daily_tasks",
        description="根据排程生成指定日期的任务。幂等操作，同一排程同一天只生成一次。",
        inputSchema={
            "type": "object",
            "properties": {
                "tenant_id": {
                    "type": "string",
                    "description": "租户ID（必填）"
                },
                "date": {
                    "type": "string",
                    "description": "目标日期 YYYY-MM-DD（必填）"
                }
            },
            "required": ["tenant_id", "date"]
        }
    ),
]


# ============================================================
# MCP 协议处理
# ============================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """返回可用的 Tools 列表"""
    return TOOL_DEFINITIONS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理 Tool 调用"""
    logger.info(f"Tool called: {name}, args: {arguments}")

    result = await tools.handle(name, arguments)

    return [TextContent(
        type="text",
        text=json.dumps(result.model_dump(), ensure_ascii=False)
    )]


# ============================================================
# 入口点
# ============================================================

async def main():
    """MCP Server 入口"""
    from mcp.server.stdio import stdio_server

    logger.info("Starting M2 Task Manager MCP Server...")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
