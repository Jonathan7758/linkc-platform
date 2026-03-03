"""
L1 Schema校验器 — JSON结构校验
"""

import json
from typing import Dict, Any, List

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

from .base_validator import ValidatorType, ValidationError, ValidationSeverity
from .schemas.cleaning_scheduler import CLEANING_SCHEDULE_DECISION_SCHEMA


class SchemaValidator:
    """
    L1 Schema校验器

    校验内容:
    - 决策JSON是否包含所有必填字段
    - 字段类型是否正确
    - 枚举值是否在允许范围内
    - 数值是否在合理区间
    """

    def __init__(self):
        self._schemas: Dict[str, Dict[str, Any]] = {
            "cleaning_scheduler": CLEANING_SCHEDULE_DECISION_SCHEMA,
        }

    @property
    def validator_type(self) -> ValidatorType:
        return ValidatorType.SCHEMA

    async def register_schema(self, agent_type: str, schema: Dict[str, Any]) -> None:
        """注册Agent类型对应的决策Schema"""
        self._schemas[agent_type] = schema

    async def validate(
        self,
        decision: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[ValidationError]:
        """执行Schema校验"""
        agent_type = context.get("agent_type", "cleaning_scheduler")
        schema = self._schemas.get(agent_type)

        if schema is None:
            return [
                ValidationError(
                    validator="schema",
                    field="",
                    message=f"未找到agent_type={agent_type}的决策Schema",
                    severity=ValidationSeverity.ERROR,
                )
            ]

        if HAS_JSONSCHEMA:
            return self._validate_with_jsonschema(decision, schema)
        else:
            return self._validate_basic(decision, schema)

    def _validate_with_jsonschema(
        self, decision: Dict[str, Any], schema: Dict[str, Any]
    ) -> List[ValidationError]:
        """使用jsonschema库进行校验"""
        errors = []
        validator = jsonschema.Draft7Validator(schema)

        for error in validator.iter_errors(decision):
            path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else ""
            severity = ValidationSeverity.CRITICAL if error.validator == "required" else ValidationSeverity.ERROR

            errors.append(
                ValidationError(
                    validator="schema",
                    field=path or error.json_path.replace("$.", ""),
                    message=error.message,
                    severity=severity,
                )
            )

        return errors

    def _validate_basic(
        self, decision: Dict[str, Any], schema: Dict[str, Any]
    ) -> List[ValidationError]:
        """基础校验（不依赖jsonschema库）"""
        errors = []

        # 检查必填字段
        required = schema.get("required", [])
        for field_name in required:
            if field_name not in decision:
                errors.append(
                    ValidationError(
                        validator="schema",
                        field=field_name,
                        message=f"缺少必填字段: {field_name}",
                        severity=ValidationSeverity.CRITICAL,
                    )
                )

        properties = schema.get("properties", {})
        for field_name, field_schema in properties.items():
            if field_name not in decision:
                continue

            value = decision[field_name]

            # 类型检查
            expected_type = field_schema.get("type")
            if expected_type:
                type_map = {
                    "string": str,
                    "integer": int,
                    "number": (int, float),
                    "boolean": bool,
                    "array": list,
                    "object": dict,
                }
                py_type = type_map.get(expected_type)
                if py_type and not isinstance(value, py_type):
                    errors.append(
                        ValidationError(
                            validator="schema",
                            field=field_name,
                            message=f"字段{field_name}类型错误: 期望{expected_type}, 实际{type(value).__name__}",
                            severity=ValidationSeverity.ERROR,
                        )
                    )
                    continue

            # 枚举检查
            enum_values = field_schema.get("enum")
            if enum_values and value not in enum_values:
                errors.append(
                    ValidationError(
                        validator="schema",
                        field=field_name,
                        message=f"字段{field_name}值'{value}'不在允许范围{enum_values}",
                        severity=ValidationSeverity.ERROR,
                    )
                )

            # 数值范围检查
            if isinstance(value, (int, float)):
                minimum = field_schema.get("minimum")
                maximum = field_schema.get("maximum")
                if minimum is not None and value < minimum:
                    errors.append(
                        ValidationError(
                            validator="schema",
                            field=field_name,
                            message=f"字段{field_name}值{value}小于最小值{minimum}",
                            severity=ValidationSeverity.ERROR,
                        )
                    )
                if maximum is not None and value > maximum:
                    errors.append(
                        ValidationError(
                            validator="schema",
                            field=field_name,
                            message=f"字段{field_name}值{value}大于最大值{maximum}",
                            severity=ValidationSeverity.ERROR,
                        )
                    )

            # 数组内容校验
            if isinstance(value, list) and "items" in field_schema:
                items_schema = field_schema["items"]
                for i, item in enumerate(value):
                    if isinstance(item, dict) and items_schema.get("type") == "object":
                        item_required = items_schema.get("required", [])
                        for req_field in item_required:
                            if req_field not in item:
                                errors.append(
                                    ValidationError(
                                        validator="schema",
                                        field=f"{field_name}[{i}].{req_field}",
                                        message=f"数组{field_name}第{i}项缺少必填字段: {req_field}",
                                        severity=ValidationSeverity.CRITICAL,
                                    )
                                )

                        # 检查数组项内的枚举和范围
                        item_props = items_schema.get("properties", {})
                        for prop_name, prop_schema in item_props.items():
                            if prop_name not in item:
                                continue
                            prop_val = item[prop_name]
                            prop_enum = prop_schema.get("enum")
                            if prop_enum and prop_val not in prop_enum:
                                errors.append(
                                    ValidationError(
                                        validator="schema",
                                        field=f"{field_name}[{i}].{prop_name}",
                                        message=f"值'{prop_val}'不在允许范围{prop_enum}",
                                        severity=ValidationSeverity.ERROR,
                                    )
                                )
                            prop_min = prop_schema.get("minimum")
                            prop_max = prop_schema.get("maximum")
                            if isinstance(prop_val, (int, float)):
                                if prop_min is not None and prop_val < prop_min:
                                    errors.append(
                                        ValidationError(
                                            validator="schema",
                                            field=f"{field_name}[{i}].{prop_name}",
                                            message=f"值{prop_val}小于最小值{prop_min}",
                                            severity=ValidationSeverity.ERROR,
                                        )
                                    )
                                if prop_max is not None and prop_val > prop_max:
                                    errors.append(
                                        ValidationError(
                                            validator="schema",
                                            field=f"{field_name}[{i}].{prop_name}",
                                            message=f"值{prop_val}大于最大值{prop_max}",
                                            severity=ValidationSeverity.ERROR,
                                        )
                                    )

        return errors
