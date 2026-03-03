"""
L4 安全校验器 — 硬编码安全红线校验（不可配置）

红线规则:
1. 不允许同时向同一台机器人下发两个任务
2. 不允许向电量<5%的机器人下发任何非充电任务
3. 不允许向已报错的机器人下发任务
4. 不允许向已关闭的区域派遣机器人
5. 单次调度机器人数量不超过建筑总机器人数的80%
"""

from typing import Dict, Any, List
from collections import Counter

from .base_validator import ValidatorType, ValidationError, ValidationSeverity


CRITICAL_BATTERY_THRESHOLD = 5
MAX_DISPATCH_RATIO = 0.8


class SafetyValidator:
    """
    L4 安全红线校验器

    所有规则硬编码，无条件阻止违规决策。
    """

    @property
    def validator_type(self) -> ValidatorType:
        return ValidatorType.SAFETY

    async def validate(
        self,
        decision: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[ValidationError]:
        """执行安全红线校验"""
        errors = []
        assignments = decision.get("assignments", [])

        errors.extend(self._check_duplicate_robot_tasks(assignments))
        errors.extend(self._check_critical_battery(assignments, context))
        errors.extend(self._check_error_robots(assignments, context))
        errors.extend(self._check_closed_zones(assignments, context))
        errors.extend(self._check_dispatch_ratio(assignments, context))

        return errors

    def _check_duplicate_robot_tasks(
        self, assignments: List[Dict[str, Any]]
    ) -> List[ValidationError]:
        """规则1: 不允许同时向同一台机器人下发两个任务"""
        errors = []
        robot_ids = [a.get("robot_id") for a in assignments if a.get("robot_id")]
        duplicates = [rid for rid, count in Counter(robot_ids).items() if count > 1]

        for rid in duplicates:
            errors.append(
                ValidationError(
                    validator="safety",
                    field="assignments.robot_id",
                    message=f"安全红线: 机器人'{rid}'被分配了多个任务",
                    severity=ValidationSeverity.CRITICAL,
                )
            )
        return errors

    def _check_critical_battery(
        self, assignments: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> List[ValidationError]:
        """规则2: 不允许向电量<5%的机器人下发任何非充电任务"""
        errors = []
        robot_states = context.get("robot_states", {})

        for i, assignment in enumerate(assignments):
            robot_id = assignment.get("robot_id")
            if not robot_id or robot_id not in robot_states:
                continue

            state = robot_states[robot_id]
            battery = state.get("battery_level", 100)
            task_type = assignment.get("task_type", "")

            if battery < CRITICAL_BATTERY_THRESHOLD and task_type != "return_to_charger":
                errors.append(
                    ValidationError(
                        validator="safety",
                        field=f"assignments[{i}].robot_id",
                        message=f"安全红线: 机器人'{robot_id}'电量{battery}%低于{CRITICAL_BATTERY_THRESHOLD}%，禁止分配非充电任务",
                        severity=ValidationSeverity.CRITICAL,
                    )
                )
        return errors

    def _check_error_robots(
        self, assignments: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> List[ValidationError]:
        """规则3: 不允许向已报错的机器人下发任务"""
        errors = []
        robot_states = context.get("robot_states", {})

        for i, assignment in enumerate(assignments):
            robot_id = assignment.get("robot_id")
            if not robot_id or robot_id not in robot_states:
                continue

            state = robot_states[robot_id]
            status = state.get("status", "idle")

            if status == "error":
                errors.append(
                    ValidationError(
                        validator="safety",
                        field=f"assignments[{i}].robot_id",
                        message=f"安全红线: 机器人'{robot_id}'处于错误状态，禁止分配任务",
                        severity=ValidationSeverity.CRITICAL,
                    )
                )
        return errors

    def _check_closed_zones(
        self, assignments: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> List[ValidationError]:
        """规则4: 不允许向已关闭的区域派遣机器人"""
        errors = []
        closed_zones = set(context.get("closed_zones", []))

        for i, assignment in enumerate(assignments):
            zone_id = assignment.get("zone_id")
            if zone_id and zone_id in closed_zones:
                errors.append(
                    ValidationError(
                        validator="safety",
                        field=f"assignments[{i}].zone_id",
                        message=f"安全红线: 区域'{zone_id}'已关闭，禁止派遣机器人",
                        severity=ValidationSeverity.CRITICAL,
                    )
                )
        return errors

    def _check_dispatch_ratio(
        self, assignments: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> List[ValidationError]:
        """规则5: 单次调度机器人数量不超过建筑总机器人数的80%"""
        errors = []
        total_robots = context.get("total_robots_in_building", 0)

        if total_robots <= 0:
            return errors

        unique_robots = len(set(a.get("robot_id") for a in assignments if a.get("robot_id")))
        max_allowed = int(total_robots * MAX_DISPATCH_RATIO)

        if unique_robots > max_allowed:
            errors.append(
                ValidationError(
                    validator="safety",
                    field="assignments",
                    message=f"安全红线: 单次调度{unique_robots}台机器人超过上限{max_allowed}台(总数{total_robots}的{int(MAX_DISPATCH_RATIO*100)}%)",
                    severity=ValidationSeverity.CRITICAL,
                )
            )
        return errors
