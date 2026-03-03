"""
L2 引用校验器 — 实体引用存在性校验
"""

from typing import Dict, Any, List, Optional, Protocol

from .base_validator import ValidatorType, ValidationError, ValidationSeverity


class EntityLookup(Protocol):
    """实体查询接口（通过MCP或直接查询）"""

    async def robot_exists(self, robot_id: str) -> bool: ...
    async def zone_exists(self, zone_id: str) -> bool: ...
    async def floor_exists(self, floor_id: str) -> bool: ...
    async def person_exists(self, person_id: str) -> bool: ...


class DefaultEntityLookup:
    """默认实体查询（从context中查找）"""

    def __init__(self, context: Dict[str, Any]):
        self._robots = set(context.get("known_robot_ids", []))
        self._zones = set(context.get("known_zone_ids", []))
        self._floors = set(context.get("known_floor_ids", []))
        self._persons = set(context.get("known_person_ids", []))

    async def robot_exists(self, robot_id: str) -> bool:
        if not self._robots:
            return True  # 无数据时不阻止
        return robot_id in self._robots

    async def zone_exists(self, zone_id: str) -> bool:
        if not self._zones:
            return True
        return zone_id in self._zones

    async def floor_exists(self, floor_id: str) -> bool:
        if not self._floors:
            return True
        return floor_id in self._floors

    async def person_exists(self, person_id: str) -> bool:
        if not self._persons:
            return True
        return person_id in self._persons


class ReferenceValidator:
    """
    L2 引用校验器

    校验内容:
    - robot_id 是否在系统中存在
    - floor_id / zone_id 是否在当前建筑中存在
    - person_id 是否存在且当前在岗
    """

    def __init__(self, entity_lookup: Optional[EntityLookup] = None):
        self._entity_lookup = entity_lookup

    @property
    def validator_type(self) -> ValidatorType:
        return ValidatorType.REFERENCE

    async def validate(
        self,
        decision: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[ValidationError]:
        """校验决策中引用的实体是否真实存在"""
        errors = []
        lookup = self._entity_lookup or DefaultEntityLookup(context)

        assignments = decision.get("assignments", [])
        for i, assignment in enumerate(assignments):
            # 校验 robot_id
            robot_id = assignment.get("robot_id")
            if robot_id:
                if not await lookup.robot_exists(robot_id):
                    errors.append(
                        ValidationError(
                            validator="reference",
                            field=f"assignments[{i}].robot_id",
                            message=f"机器人'{robot_id}'不存在",
                            severity=ValidationSeverity.CRITICAL,
                        )
                    )

            # 校验 zone_id
            zone_id = assignment.get("zone_id")
            if zone_id:
                if not await lookup.zone_exists(zone_id):
                    errors.append(
                        ValidationError(
                            validator="reference",
                            field=f"assignments[{i}].zone_id",
                            message=f"区域'{zone_id}'不存在",
                            severity=ValidationSeverity.CRITICAL,
                        )
                    )

            # 校验 floor_id
            floor_id = assignment.get("floor_id")
            if floor_id:
                if not await lookup.floor_exists(floor_id):
                    errors.append(
                        ValidationError(
                            validator="reference",
                            field=f"assignments[{i}].floor_id",
                            message=f"楼层'{floor_id}'不存在",
                            severity=ValidationSeverity.ERROR,
                        )
                    )

        # 校验 assigned_to (如果存在)
        assigned_to = decision.get("assigned_to")
        if assigned_to and isinstance(assigned_to, str):
            if not await lookup.person_exists(assigned_to):
                errors.append(
                    ValidationError(
                        validator="reference",
                        field="assigned_to",
                        message=f"人员'{assigned_to}'不存在",
                        severity=ValidationSeverity.ERROR,
                    )
                )

        return errors
