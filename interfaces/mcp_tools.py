"""
LinkC Platform - MCP Tool 接口定义
==================================
定义所有 MCP Server 提供的 Tool 接口规范。

MCP Server 实现必须遵循这些接口定义。
"""

from typing import Optional, Protocol, runtime_checkable
from pydantic import BaseModel, Field


# ============================================================
# Tool 输入/输出 Schema 基类
# ============================================================

class ToolInput(BaseModel):
    """Tool输入基类"""
    pass


class ToolOutput(BaseModel):
    """Tool输出基类"""
    success: bool = Field(default=True)
    message: Optional[str] = None
    error: Optional[str] = None


# ============================================================
# M1: 空间管理 MCP Server Tools
# ============================================================

# --- list_buildings ---
class ListBuildingsInput(ToolInput):
    """列出楼宇"""
    tenant_id: str


class ListBuildingsOutput(ToolOutput):
    """楼宇列表"""
    buildings: list = Field(default_factory=list)
    total: int = 0


# --- get_building ---
class GetBuildingInput(ToolInput):
    """获取楼宇详情"""
    building_id: str


class GetBuildingOutput(ToolOutput):
    """楼宇详情"""
    building: Optional[dict] = None


# --- list_floors ---
class ListFloorsInput(ToolInput):
    """列出楼层"""
    building_id: str


class ListFloorsOutput(ToolOutput):
    """楼层列表"""
    floors: list = Field(default_factory=list)
    total: int = 0


# --- list_zones ---
class ListZonesInput(ToolInput):
    """列出区域"""
    floor_id: Optional[str] = None
    building_id: Optional[str] = None
    zone_type: Optional[str] = None


class ListZonesOutput(ToolOutput):
    """区域列表"""
    zones: list = Field(default_factory=list)
    total: int = 0


# --- get_zone ---
class GetZoneInput(ToolInput):
    """获取区域详情"""
    zone_id: str


class GetZoneOutput(ToolOutput):
    """区域详情"""
    zone: Optional[dict] = None


# ============================================================
# M2: 任务管理 MCP Server Tools
# ============================================================

# --- create_task ---
class CreateTaskInput(ToolInput):
    """创建任务"""
    tenant_id: str
    name: str
    zone_id: str
    priority: str = "normal"
    cleaning_mode: str = "standard"
    scheduled_start: Optional[str] = None  # ISO格式时间


class CreateTaskOutput(ToolOutput):
    """创建任务结果"""
    task_id: Optional[str] = None
    task: Optional[dict] = None


# --- list_tasks ---
class ListTasksInput(ToolInput):
    """列出任务"""
    tenant_id: str
    status: Optional[str] = None
    zone_id: Optional[str] = None
    robot_id: Optional[str] = None
    limit: int = 50


class ListTasksOutput(ToolOutput):
    """任务列表"""
    tasks: list = Field(default_factory=list)
    total: int = 0


# --- get_task ---
class GetTaskInput(ToolInput):
    """获取任务详情"""
    task_id: str


class GetTaskOutput(ToolOutput):
    """任务详情"""
    task: Optional[dict] = None


# --- assign_task ---
class AssignTaskInput(ToolInput):
    """分配任务给机器人"""
    task_id: str
    robot_id: str
    assigned_by: str  # agent_id 或 user_id


class AssignTaskOutput(ToolOutput):
    """分配结果"""
    task_id: str = ""
    robot_id: str = ""


# --- update_task_status ---
class UpdateTaskStatusInput(ToolInput):
    """更新任务状态"""
    task_id: str
    status: str
    completion_rate: Optional[float] = None
    notes: Optional[str] = None


class UpdateTaskStatusOutput(ToolOutput):
    """更新结果"""
    task: Optional[dict] = None


# ============================================================
# M3: 机器人控制 MCP Server Tools (高仙)
# ============================================================

# --- list_robots ---
class ListRobotsInput(ToolInput):
    """列出机器人"""
    tenant_id: str
    building_id: Optional[str] = None
    status: Optional[str] = None


class ListRobotsOutput(ToolOutput):
    """机器人列表"""
    robots: list = Field(default_factory=list)
    total: int = 0


# --- get_robot_status ---
class GetRobotStatusInput(ToolInput):
    """获取机器人状态"""
    robot_id: str


class GetRobotStatusOutput(ToolOutput):
    """机器人状态"""
    robot_id: str = ""
    status: str = ""
    battery_level: int = 0
    current_zone_id: Optional[str] = None
    position: Optional[dict] = None


# --- start_cleaning ---
class StartCleaningInput(ToolInput):
    """启动清洁任务"""
    robot_id: str
    zone_id: str
    cleaning_mode: str = "standard"


class StartCleaningOutput(ToolOutput):
    """启动结果"""
    robot_id: str = ""
    task_started: bool = False


# --- stop_cleaning ---
class StopCleaningInput(ToolInput):
    """停止清洁任务"""
    robot_id: str
    reason: Optional[str] = None


class StopCleaningOutput(ToolOutput):
    """停止结果"""
    robot_id: str = ""
    stopped: bool = False


# --- send_to_charger ---
class SendToChargerInput(ToolInput):
    """发送机器人去充电"""
    robot_id: str


class SendToChargerOutput(ToolOutput):
    """充电指令结果"""
    robot_id: str = ""
    command_sent: bool = False


# ============================================================
# MCP Server 协议接口
# ============================================================

@runtime_checkable
class SpaceManagerProtocol(Protocol):
    """空间管理 MCP Server 协议"""
    
    async def list_buildings(self, input: ListBuildingsInput) -> ListBuildingsOutput: ...
    async def get_building(self, input: GetBuildingInput) -> GetBuildingOutput: ...
    async def list_floors(self, input: ListFloorsInput) -> ListFloorsOutput: ...
    async def list_zones(self, input: ListZonesInput) -> ListZonesOutput: ...
    async def get_zone(self, input: GetZoneInput) -> GetZoneOutput: ...


@runtime_checkable
class TaskManagerProtocol(Protocol):
    """任务管理 MCP Server 协议"""
    
    async def create_task(self, input: CreateTaskInput) -> CreateTaskOutput: ...
    async def list_tasks(self, input: ListTasksInput) -> ListTasksOutput: ...
    async def get_task(self, input: GetTaskInput) -> GetTaskOutput: ...
    async def assign_task(self, input: AssignTaskInput) -> AssignTaskOutput: ...
    async def update_task_status(self, input: UpdateTaskStatusInput) -> UpdateTaskStatusOutput: ...


@runtime_checkable
class RobotControlProtocol(Protocol):
    """机器人控制 MCP Server 协议"""
    
    async def list_robots(self, input: ListRobotsInput) -> ListRobotsOutput: ...
    async def get_robot_status(self, input: GetRobotStatusInput) -> GetRobotStatusOutput: ...
    async def start_cleaning(self, input: StartCleaningInput) -> StartCleaningOutput: ...
    async def stop_cleaning(self, input: StopCleaningInput) -> StopCleaningOutput: ...
    async def send_to_charger(self, input: SendToChargerInput) -> SendToChargerOutput: ...


# ============================================================
# 导出
# ============================================================

__all__ = [
    # Base
    "ToolInput", "ToolOutput",
    # M1: Space
    "ListBuildingsInput", "ListBuildingsOutput",
    "GetBuildingInput", "GetBuildingOutput",
    "ListFloorsInput", "ListFloorsOutput",
    "ListZonesInput", "ListZonesOutput",
    "GetZoneInput", "GetZoneOutput",
    # M2: Task
    "CreateTaskInput", "CreateTaskOutput",
    "ListTasksInput", "ListTasksOutput",
    "GetTaskInput", "GetTaskOutput",
    "AssignTaskInput", "AssignTaskOutput",
    "UpdateTaskStatusInput", "UpdateTaskStatusOutput",
    # M3: Robot
    "ListRobotsInput", "ListRobotsOutput",
    "GetRobotStatusInput", "GetRobotStatusOutput",
    "StartCleaningInput", "StartCleaningOutput",
    "StopCleaningInput", "StopCleaningOutput",
    "SendToChargerInput", "SendToChargerOutput",
    # Protocols
    "SpaceManagerProtocol", "TaskManagerProtocol", "RobotControlProtocol",
]
