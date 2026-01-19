"""
M3: 高仙机器人 MCP Server - 主入口
==================================
基于规格书 docs/specs/M3-gaoxian-mcp.md 实现
"""

import asyncio
import json
import os
import logging
from mcp.server import Server
from mcp.types import TextContent, Tool

from .storage import InMemoryRobotStorage
from .mock_client import MockGaoxianClient
from .tools import RobotTools

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================
# MCP Server 定义
# ============================================================

app = Server("gaoxian-robot")

# 全局存储和客户端实例
storage = InMemoryRobotStorage()

# 根据环境变量选择客户端
USE_MOCK = os.getenv("GAOXIAN_USE_MOCK", "true").lower() == "true"
if USE_MOCK:
    client = MockGaoxianClient(storage)
else:
    # TODO: 实现真实的高仙 API 客户端
    client = MockGaoxianClient(storage)

tools = RobotTools(client, storage)


# ============================================================
# Tool 定义列表
# ============================================================

TOOL_DEFINITIONS = [
    Tool(
        name="robot_list_robots",
        description="获取机器人列表。按租户ID筛选，可选按楼宇、状态、类型过滤。",
        inputSchema={
            "type": "object",
            "properties": {
                "tenant_id": {
                    "type": "string",
                    "description": "租户ID（必填）"
                },
                "building_id": {
                    "type": "string",
                    "description": "楼宇ID（可选）"
                },
                "status": {
                    "type": "string",
                    "enum": ["offline", "idle", "working", "paused", "charging", "error", "maintenance"],
                    "description": "机器人状态（可选）"
                },
                "robot_type": {
                    "type": "string",
                    "enum": ["cleaning", "security", "delivery", "disinfection"],
                    "description": "机器人类型（可选）"
                }
            },
            "required": ["tenant_id"]
        }
    ),
    Tool(
        name="robot_get_robot",
        description="获取单个机器人详情，包含配置和能力信息。",
        inputSchema={
            "type": "object",
            "properties": {
                "robot_id": {
                    "type": "string",
                    "description": "机器人ID（必填）"
                }
            },
            "required": ["robot_id"]
        }
    ),
    Tool(
        name="robot_get_status",
        description="获取机器人实时状态，包含位置、电量、当前任务等信息。",
        inputSchema={
            "type": "object",
            "properties": {
                "robot_id": {
                    "type": "string",
                    "description": "机器人ID（必填）"
                }
            },
            "required": ["robot_id"]
        }
    ),
    Tool(
        name="robot_batch_get_status",
        description="批量获取机器人状态，最多20个。",
        inputSchema={
            "type": "object",
            "properties": {
                "robot_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 20,
                    "description": "机器人ID列表（必填，最多20个）"
                }
            },
            "required": ["robot_ids"]
        }
    ),
    Tool(
        name="robot_start_task",
        description="启动清洁任务。前置条件：机器人空闲或充电中，电量>=20%，无严重故障。",
        inputSchema={
            "type": "object",
            "properties": {
                "robot_id": {
                    "type": "string",
                    "description": "机器人ID（必填）"
                },
                "zone_id": {
                    "type": "string",
                    "description": "清洁区域ID（必填）"
                },
                "task_type": {
                    "type": "string",
                    "enum": ["vacuum", "mop", "vacuum_mop"],
                    "description": "任务类型（必填）"
                },
                "cleaning_mode": {
                    "type": "string",
                    "enum": ["eco", "standard", "deep"],
                    "description": "清洁强度，默认standard"
                },
                "task_id": {
                    "type": "string",
                    "description": "关联的M2任务ID（可选）"
                }
            },
            "required": ["robot_id", "zone_id", "task_type"]
        }
    ),
    Tool(
        name="robot_pause_task",
        description="暂停当前任务。只有working状态可暂停。",
        inputSchema={
            "type": "object",
            "properties": {
                "robot_id": {
                    "type": "string",
                    "description": "机器人ID（必填）"
                },
                "reason": {
                    "type": "string",
                    "description": "暂停原因（可选）"
                }
            },
            "required": ["robot_id"]
        }
    ),
    Tool(
        name="robot_resume_task",
        description="恢复暂停的任务。只有paused状态可恢复。",
        inputSchema={
            "type": "object",
            "properties": {
                "robot_id": {
                    "type": "string",
                    "description": "机器人ID（必填）"
                }
            },
            "required": ["robot_id"]
        }
    ),
    Tool(
        name="robot_cancel_task",
        description="取消当前任务。working或paused状态可取消。",
        inputSchema={
            "type": "object",
            "properties": {
                "robot_id": {
                    "type": "string",
                    "description": "机器人ID（必填）"
                },
                "reason": {
                    "type": "string",
                    "description": "取消原因（可选）"
                }
            },
            "required": ["robot_id"]
        }
    ),
    Tool(
        name="robot_go_to_location",
        description="指挥机器人移动到指定位置。机器人必须处于idle状态。",
        inputSchema={
            "type": "object",
            "properties": {
                "robot_id": {
                    "type": "string",
                    "description": "机器人ID（必填）"
                },
                "target_location": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number", "description": "X坐标"},
                        "y": {"type": "number", "description": "Y坐标"},
                        "floor_id": {"type": "string", "description": "楼层ID"}
                    },
                    "required": ["x", "y"],
                    "description": "目标位置（必填）"
                },
                "reason": {
                    "type": "string",
                    "description": "移动原因（可选）"
                }
            },
            "required": ["robot_id", "target_location"]
        }
    ),
    Tool(
        name="robot_go_to_charge",
        description="指挥机器人返回充电桩。默认只有idle状态可返回，force=true可强制。",
        inputSchema={
            "type": "object",
            "properties": {
                "robot_id": {
                    "type": "string",
                    "description": "机器人ID（必填）"
                },
                "force": {
                    "type": "boolean",
                    "description": "是否强制返回（会取消当前任务），默认false"
                }
            },
            "required": ["robot_id"]
        }
    ),
    Tool(
        name="robot_get_errors",
        description="获取机器人故障列表。可按机器人、严重级别筛选。",
        inputSchema={
            "type": "object",
            "properties": {
                "robot_id": {
                    "type": "string",
                    "description": "机器人ID（可选，不填查询所有）"
                },
                "tenant_id": {
                    "type": "string",
                    "description": "租户ID（可选）"
                },
                "severity": {
                    "type": "string",
                    "enum": ["warning", "error", "critical"],
                    "description": "严重级别（可选）"
                },
                "resolved": {
                    "type": "boolean",
                    "description": "是否已解决，默认false查询未解决的"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回数量限制，默认50"
                }
            }
        }
    ),
    Tool(
        name="robot_clear_error",
        description="清除机器人故障。只能清除warning级别，除非force=true。",
        inputSchema={
            "type": "object",
            "properties": {
                "robot_id": {
                    "type": "string",
                    "description": "机器人ID（必填）"
                },
                "error_id": {
                    "type": "string",
                    "description": "故障ID（可选，不填清除所有可清除的）"
                },
                "force": {
                    "type": "boolean",
                    "description": "强制清除（可清除error/critical级别），默认false"
                }
            },
            "required": ["robot_id"]
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

    logger.info("Starting M3 Gaoxian Robot MCP Server...")
    logger.info(f"Using mock client: {USE_MOCK}")

    # 启动模拟循环（仅Mock模式）
    if USE_MOCK:
        await client.start_simulation()

    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    finally:
        if USE_MOCK:
            await client.stop_simulation()


if __name__ == "__main__":
    asyncio.run(main())
