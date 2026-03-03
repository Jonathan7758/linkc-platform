"""
校验器基类和公共类型定义
"""

from typing import Dict, Any, List, Protocol
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class ValidatorType(Enum):
    SCHEMA = "schema"
    REFERENCE = "reference"
    CONSTRAINT = "constraint"
    SAFETY = "safety"


class ValidationSeverity(Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """单条校验错误"""
    validator: str
    field: str
    message: str
    severity: ValidationSeverity
    rule_id: Optional[str] = None
    suggested_fix: Optional[str] = None


@dataclass
class ValidationResult:
    """校验结果"""
    valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    corrected_decision: Optional[Dict[str, Any]] = None
    validation_duration_ms: int = 0
    validators_executed: List[str] = field(default_factory=list)


class BaseValidator(Protocol):
    """校验器基类接口"""

    @property
    def validator_type(self) -> ValidatorType: ...

    async def validate(
        self,
        decision: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[ValidationError]:
        """执行校验，返回错误列表。空列表表示校验通过。"""
        ...
