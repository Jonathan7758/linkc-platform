"""
DecisionValidator — 决策校验管道主类

串联四层校验链: Schema → Reference → Constraint → Safety
"""

import time
from typing import Dict, Any, List, Optional

from .base_validator import (
    ValidatorType,
    ValidationError,
    ValidationResult,
    ValidationSeverity,
)
from .schema_validator import SchemaValidator
from .reference_validator import ReferenceValidator
from .constraint_validator import ConstraintValidator
from .safety_validator import SafetyValidator


class DecisionValidator:
    """
    A5 决策校验管道

    按 L1→L2→L3→L4 顺序执行四层校验。
    CRITICAL错误会立即中断后续校验。
    """

    def __init__(
        self,
        schema_validator: Optional[SchemaValidator] = None,
        reference_validator: Optional[ReferenceValidator] = None,
        constraint_validator: Optional[ConstraintValidator] = None,
        safety_validator: Optional[SafetyValidator] = None,
    ):
        self.schema_validator = schema_validator or SchemaValidator()
        self.reference_validator = reference_validator or ReferenceValidator()
        self.constraint_validator = constraint_validator or ConstraintValidator()
        self.safety_validator = safety_validator or SafetyValidator()

        self._validators = [
            self.schema_validator,
            self.reference_validator,
            self.constraint_validator,
            self.safety_validator,
        ]

    async def validate(
        self,
        decision: Dict[str, Any],
        context: Dict[str, Any],
        agent_type: str = "cleaning_scheduler",
    ) -> ValidationResult:
        """
        执行全链路校验

        Args:
            decision: LLM输出的决策JSON
            context: 决策上下文
            agent_type: Agent类型

        Returns:
            ValidationResult
        """
        start_time = time.monotonic()
        ctx = dict(context)
        ctx["agent_type"] = agent_type

        result = ValidationResult(valid=True)

        for validator in self._validators:
            vtype = validator.validator_type.value
            result.validators_executed.append(vtype)

            try:
                errors = await validator.validate(decision, ctx)
            except Exception as e:
                errors = [
                    ValidationError(
                        validator=vtype,
                        field="",
                        message=f"校验器{vtype}执行异常: {str(e)}",
                        severity=ValidationSeverity.ERROR,
                    )
                ]

            has_critical = False
            for error in errors:
                if error.severity in (ValidationSeverity.CRITICAL, ValidationSeverity.ERROR):
                    result.valid = False
                    result.errors.append(error)
                    if error.severity == ValidationSeverity.CRITICAL:
                        has_critical = True
                elif error.severity == ValidationSeverity.WARNING:
                    result.warnings.append(error)

            # CRITICAL错误立即中断后续校验
            if has_critical:
                break

            # L3 可能产生自动修正
            if hasattr(validator, "get_corrections") and errors:
                corrections = await validator.get_corrections(decision, errors)
                if corrections:
                    result.corrected_decision = corrections

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        result.validation_duration_ms = elapsed_ms

        return result

    async def validate_partial(
        self,
        decision: Dict[str, Any],
        validators: List[ValidatorType],
        context: Dict[str, Any],
        agent_type: str = "cleaning_scheduler",
    ) -> ValidationResult:
        """仅执行指定的校验器"""
        start_time = time.monotonic()
        ctx = dict(context)
        ctx["agent_type"] = agent_type

        result = ValidationResult(valid=True)
        validator_map = {v.validator_type: v for v in self._validators}

        for vtype in validators:
            validator = validator_map.get(vtype)
            if validator is None:
                continue

            result.validators_executed.append(vtype.value)

            try:
                errors = await validator.validate(decision, ctx)
            except Exception as e:
                errors = [
                    ValidationError(
                        validator=vtype.value,
                        field="",
                        message=f"校验器{vtype.value}执行异常: {str(e)}",
                        severity=ValidationSeverity.ERROR,
                    )
                ]

            for error in errors:
                if error.severity in (ValidationSeverity.CRITICAL, ValidationSeverity.ERROR):
                    result.valid = False
                    result.errors.append(error)
                elif error.severity == ValidationSeverity.WARNING:
                    result.warnings.append(error)

        result.validation_duration_ms = int((time.monotonic() - start_time) * 1000)
        return result
