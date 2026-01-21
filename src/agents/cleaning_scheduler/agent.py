"""
A2: 清洁调度 Agent 实现
======================
智能调度清洁任务到合适的机器人。

主要功能：
1. 获取待分配任务
2. 获取可用机器人
3. 智能匹配任务和机器人
4. 执行任务分配
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging

from src.agents.runtime.base import BaseAgent, AgentConfig, AutonomyLevel
from src.agents.runtime.decision import Decision, DecisionResult

logger = logging.getLogger(__name__)


# ============================================================
# 调度策略
# ============================================================

@dataclass
class SchedulingContext:
    """调度上下文"""
    tenant_id: str
    pending_tasks: List[Dict[str, Any]] = field(default_factory=list)
    available_robots: List[Dict[str, Any]] = field(default_factory=list)
    zone_info: Dict[str, Any] = field(default_factory=dict)  # zone_id -> zone info


@dataclass
class TaskAssignment:
    """任务分配结果"""
    task_id: str
    robot_id: str
    score: float
    reason: str


class SchedulingStrategy:
    """调度策略基类"""

    def match(
        self,
        task: Dict[str, Any],
        robots: List[Dict[str, Any]],
        context: SchedulingContext
    ) -> Optional[TaskAssignment]:
        """为任务匹配最佳机器人"""
        raise NotImplementedError


class PriorityBasedStrategy(SchedulingStrategy):
    """
    基于优先级的调度策略

    考虑因素：
    1. 任务优先级 (1-10, 1最高)
    2. 机器人电量
    3. 机器人位置（同楼层优先）
    4. 机器人能力匹配
    """

    def match(
        self,
        task: Dict[str, Any],
        robots: List[Dict[str, Any]],
        context: SchedulingContext
    ) -> Optional[TaskAssignment]:
        if not robots:
            return None

        task_id = task.get("task_id")
        task_zone = task.get("zone_id")
        task_type = task.get("task_type", "routine")
        task_priority = task.get("priority", 5)

        best_robot = None
        best_score = -1
        best_reason = ""

        for robot in robots:
            robot_id = robot.get("robot_id")
            battery = robot.get("battery_level", 50)
            robot_zone = robot.get("current_zone_id")
            capabilities = robot.get("capabilities", {})

            # 计算匹配分数
            score = 0.0
            reasons = []

            # 1. 电量分数 (最高30分)
            if battery >= 80:
                score += 30
                reasons.append(f"高电量({battery}%)")
            elif battery >= 50:
                score += 20
                reasons.append(f"中电量({battery}%)")
            elif battery >= 30:
                score += 10
                reasons.append(f"低电量({battery}%)")
            else:
                score += 0
                reasons.append(f"电量不足({battery}%)")

            # 2. 位置分数 (最高30分)
            if robot_zone == task_zone:
                score += 30
                reasons.append("同区域")
            elif self._same_floor(robot_zone, task_zone, context):
                score += 20
                reasons.append("同楼层")
            else:
                score += 10
                reasons.append("跨楼层")

            # 3. 能力匹配 (最高20分)
            task_mode = self._get_cleaning_mode(task_type)
            if capabilities.get(task_mode, False):
                score += 20
                reasons.append(f"支持{task_mode}")
            else:
                # 默认认为支持基础清洁
                score += 10

            # 4. 空闲时间加分 (最高20分)
            idle_bonus = min(20, robot.get("idle_minutes", 0) // 5)
            score += idle_bonus
            if idle_bonus > 10:
                reasons.append("长时间空闲")

            # 选择最佳机器人
            if score > best_score:
                best_score = score
                best_robot = robot
                best_reason = ", ".join(reasons)

        if best_robot:
            return TaskAssignment(
                task_id=task_id,
                robot_id=best_robot.get("robot_id"),
                score=best_score,
                reason=f"优先级{task_priority}, {best_reason}"
            )

        return None

    def _same_floor(
        self,
        zone1: str,
        zone2: str,
        context: SchedulingContext
    ) -> bool:
        """检查两个区域是否在同一楼层"""
        if not zone1 or not zone2:
            return False

        zone1_info = context.zone_info.get(zone1, {})
        zone2_info = context.zone_info.get(zone2, {})

        return zone1_info.get("floor_id") == zone2_info.get("floor_id")

    def _get_cleaning_mode(self, task_type: str) -> str:
        """将任务类型转换为清洁模式"""
        mapping = {
            "routine": "vacuum",
            "deep": "vacuum_mop",
            "spot": "spot",
            "emergency": "vacuum"
        }
        return mapping.get(task_type, "vacuum")


# ============================================================
# 清洁调度 Agent
# ============================================================

class CleaningSchedulerAgent(BaseAgent):
    """
    清洁调度 Agent

    职责：
    1. 监控待分配的清洁任务
    2. 检查可用的机器人
    3. 智能匹配任务和机器人
    4. 执行任务分配并更新状态
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        task_tools=None,
        robot_tools=None,
        space_tools=None,
        strategy: Optional[SchedulingStrategy] = None
    ):
        """
        初始化清洁调度Agent

        Args:
            config: Agent配置
            task_tools: 任务管理MCP工具
            robot_tools: 机器人控制MCP工具
            space_tools: 空间管理MCP工具
            strategy: 调度策略（默认使用优先级策略）
        """
        if config is None:
            config = AgentConfig(
                name="清洁调度Agent",
                description="智能调度清洁任务到合适的机器人",
                autonomy_level=AutonomyLevel.L2_LIMITED,
                max_tasks_per_decision=5,
                max_battery_threshold=20
            )
        super().__init__(config)

        self.task_tools = task_tools
        self.robot_tools = robot_tools
        self.space_tools = space_tools
        self.strategy = strategy or PriorityBasedStrategy()

        # 统计信息
        self._stats = {
            "total_assignments": 0,
            "successful_assignments": 0,
            "failed_assignments": 0,
            "last_run": None
        }

    async def think(self, context: dict) -> Decision:
        """
        分析当前情况，决定如何调度任务

        Args:
            context: 包含 tenant_id 等上下文信息

        Returns:
            调度决策
        """
        decision = Decision(
            decision_type="task_scheduling",
            description="分析待处理任务并分配给合适的机器人"
        )

        tenant_id = context.get("tenant_id", self.config.tenant_id)

        try:
            # 构建调度上下文
            scheduling_ctx = await self._build_scheduling_context(tenant_id)

            # 检查是否有待分配任务
            if not scheduling_ctx.pending_tasks:
                decision.description = "没有待分配的任务"
                decision.confidence = 1.0
                decision.auto_approve = True
                return decision

            # 检查是否有可用机器人
            if not scheduling_ctx.available_robots:
                decision.description = "没有可用的机器人"
                decision.confidence = 1.0
                decision.auto_approve = True
                return decision

            # 按优先级排序任务 (1最高)
            sorted_tasks = sorted(
                scheduling_ctx.pending_tasks,
                key=lambda t: t.get("priority", 5)
            )

            # 生成分配方案
            assignments = []
            used_robots = set()

            for task in sorted_tasks:
                # 过滤已使用的机器人
                available = [
                    r for r in scheduling_ctx.available_robots
                    if r.get("robot_id") not in used_robots
                ]

                if not available:
                    break

                # 匹配最佳机器人
                assignment = self.strategy.match(task, available, scheduling_ctx)
                if assignment:
                    assignments.append(assignment)
                    used_robots.add(assignment.robot_id)

                    # 添加分配动作
                    decision.add_action(
                        action_type="assign_task",
                        params={
                            "task_id": assignment.task_id,
                            "robot_id": assignment.robot_id,
                            "task_type": task.get("task_type", "routine"),
                            "zone_id": task.get("zone_id"),
                            "reason": assignment.reason,
                            "score": assignment.score
                        }
                    )

            # 设置决策属性
            if assignments:
                decision.description = f"分配 {len(assignments)} 个任务给机器人"
                decision.reasoning = (
                    f"找到 {len(scheduling_ctx.pending_tasks)} 个待分配任务，"
                    f"{len(scheduling_ctx.available_robots)} 个可用机器人，"
                    f"生成 {len(assignments)} 个分配方案"
                )
                decision.confidence = self._calculate_confidence(assignments)

                # 检查是否超出自主边界
                if len(assignments) > self.config.max_tasks_per_decision:
                    decision.exceeds_boundary = True
                    decision.reasoning += f"（超出单次分配上限 {self.config.max_tasks_per_decision}）"
                else:
                    decision.auto_approve = True
            else:
                decision.description = "无法生成有效的分配方案"
                decision.confidence = 0.5

        except Exception as e:
            logger.error(f"Scheduling think error: {e}")
            decision.confidence = 0.0
            decision.reasoning = f"决策过程出错: {str(e)}"

        return decision

    async def execute(self, decision: Decision) -> DecisionResult:
        """
        执行任务分配决策

        Args:
            decision: 待执行的决策

        Returns:
            执行结果
        """
        result = DecisionResult(decision=decision)

        if not decision.actions:
            result.success = True
            result.message = "没有需要执行的动作"
            return result

        self._stats["last_run"] = datetime.now(timezone.utc).isoformat()

        for action in decision.actions:
            if action["type"] != "assign_task":
                continue

            params = action["params"]
            task_id = params["task_id"]
            robot_id = params["robot_id"]
            task_type = params.get("task_type", "routine")
            zone_id = params.get("zone_id")

            try:
                # 1. 更新任务状态为已分配
                if self.task_tools:
                    update_result = await self.task_tools.handle("task_update_status", {
                        "task_id": task_id,
                        "status": "assigned",
                        "robot_id": robot_id
                    })

                    if not update_result.success:
                        result.add_failed_action(action, f"任务状态更新失败: {update_result.error}")
                        self._stats["failed_assignments"] += 1
                        continue

                # 2. 向机器人发送任务
                if self.robot_tools and zone_id:
                    # 将任务类型转换为清洁模式
                    cleaning_mode = self._get_cleaning_mode(task_type)

                    start_result = await self.robot_tools.handle("robot_start_task", {
                        "robot_id": robot_id,
                        "task_id": task_id,
                        "zone_id": zone_id,
                        "task_type": cleaning_mode
                    })

                    if not start_result.success:
                        # 回滚任务状态
                        if self.task_tools:
                            await self.task_tools.handle("task_update_status", {
                                "task_id": task_id,
                                "status": "pending"
                            })
                        result.add_failed_action(action, f"机器人启动失败: {start_result.error}")
                        self._stats["failed_assignments"] += 1
                        continue

                # 3. 更新任务状态为执行中
                if self.task_tools:
                    await self.task_tools.handle("task_update_status", {
                        "task_id": task_id,
                        "status": "in_progress"
                    })

                result.add_executed_action(action, {
                    "task_id": task_id,
                    "robot_id": robot_id,
                    "status": "started"
                })
                self._stats["successful_assignments"] += 1
                self._stats["total_assignments"] += 1

            except Exception as e:
                logger.error(f"Execute action error: {e}")
                result.add_failed_action(action, str(e))
                self._stats["failed_assignments"] += 1

        result.success = len(result.actions_failed) == 0
        result.message = (
            f"成功分配 {len(result.actions_executed)} 个任务"
            if result.success
            else f"分配失败 {len(result.actions_failed)} 个任务"
        )

        return result

    async def _build_scheduling_context(self, tenant_id: str) -> SchedulingContext:
        """构建调度上下文"""
        ctx = SchedulingContext(tenant_id=tenant_id)

        # 获取待分配任务
        if self.task_tools:
            tasks_result = await self.task_tools.handle("task_get_pending_tasks", {
                "tenant_id": tenant_id,
                "limit": 20
            })
            if tasks_result.success:
                ctx.pending_tasks = tasks_result.data.get("tasks", [])

        # 获取可用机器人
        if self.robot_tools:
            robots_result = await self.robot_tools.handle("robot_list_robots", {
                "tenant_id": tenant_id,
                "status": "idle"
            })
            if robots_result.success:
                robots = robots_result.data.get("robots", [])
                # 过滤低电量机器人
                ctx.available_robots = [
                    r for r in robots
                    if r.get("battery_level", 0) >= self.config.max_battery_threshold
                ]

        # 获取区域信息
        if self.space_tools:
            # 收集所有涉及的zone_id
            zone_ids = set()
            for task in ctx.pending_tasks:
                if task.get("zone_id"):
                    zone_ids.add(task["zone_id"])
            for robot in ctx.available_robots:
                if robot.get("current_zone_id"):
                    zone_ids.add(robot["current_zone_id"])

            # 查询区域信息
            for zone_id in zone_ids:
                zone_result = await self.space_tools.handle("space_get_zone", {
                    "zone_id": zone_id
                })
                if zone_result.success:
                    ctx.zone_info[zone_id] = zone_result.data.get("zone", {})

        return ctx

    def _calculate_confidence(self, assignments: List[TaskAssignment]) -> float:
        """计算决策置信度"""
        if not assignments:
            return 1.0

        # 基于平均匹配分数计算置信度
        avg_score = sum(a.score for a in assignments) / len(assignments)
        # 满分100，转换为0-1的置信度
        confidence = min(1.0, avg_score / 80)

        # 分配数量越多，置信度略降
        confidence -= len(assignments) * 0.02

        return max(0.5, confidence)

    def _get_cleaning_mode(self, task_type: str) -> str:
        """将任务类型转换为机器人清洁模式"""
        mapping = {
            "routine": "vacuum",
            "deep": "vacuum_mop",
            "spot": "vacuum",
            "emergency": "vacuum"
        }
        return mapping.get(task_type, "vacuum")

    def get_stats(self) -> Dict[str, Any]:
        """获取Agent统计信息"""
        return {
            **self._stats,
            "agent_id": self.agent_id,
            "state": self.state.value,
            "last_activity": self.last_activity.isoformat()
        }
