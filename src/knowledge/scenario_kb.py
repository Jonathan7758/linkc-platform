"""
K1 场景知识库 — ScenarioKnowledgeBase

Phase 1 内存实现，提供:
- CRUD: 知识条目的增删改查（软删除）
- 查询: 6维条件匹配，按优先级排序
- Prompt组装: 模板变量填充 + 知识槽注入 + Token限制
- 效果跟踪: 使用计数与效果评分
"""

import logging
import re
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Local dataclass definitions (mirrors ecis-protocols, self-contained)
# ---------------------------------------------------------------------------

@dataclass
class ScenarioKnowledge:
    """场景知识条目"""
    knowledge_id: str
    knowledge_type: str          # domain_fact | scenario_rule | prompt_template | example
    scenario_category: str       # cleaning | security | energy | maintenance
    name: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    applicable_building_types: List[str] = field(default_factory=lambda: ["all"])
    applicable_zones: List[str] = field(default_factory=lambda: ["all"])
    applicable_time_ranges: List[Dict[str, str]] = field(default_factory=list)
    applicable_conditions: Dict[str, Any] = field(default_factory=dict)
    content: Dict[str, Any] = field(default_factory=dict)
    priority: int = 50
    version: str = "1.0"
    enabled: bool = True
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    usage_count: int = 0
    avg_outcome_score: Optional[float] = None
    created_at: Optional[datetime] = None
    created_by: str = ""


@dataclass
class PromptTemplate:
    """Prompt模板"""
    template_id: str
    agent_type: str
    name: str
    system_prompt: str
    variables: List[str] = field(default_factory=list)
    knowledge_slots: List[Dict[str, Any]] = field(default_factory=list)
    base_tokens_estimate: int = 500
    max_knowledge_tokens: int = 2000
    max_total_tokens: int = 4000
    version: str = "1.0"
    is_active: bool = True


# ---------------------------------------------------------------------------
# Token estimation helper
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    """
    粗略估算文本的token数。

    使用 1 token ~= 4 字符的经验法则（对英文合理，中文偏保守）。
    Phase 2 可替换为 tiktoken 精确计算。
    """
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Variable placeholder pattern:  {{variable_name}}
# ---------------------------------------------------------------------------

_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


# ---------------------------------------------------------------------------
# ScenarioKnowledgeBase
# ---------------------------------------------------------------------------

class ScenarioKnowledgeBase:
    """
    K1 场景知识库 — Phase 1 内存实现

    职责:
    - 管理场景知识条目（CRUD + 软删除）
    - 按6维条件查询适用知识
    - 组装Agent Prompt（模板 + 变量 + 知识注入）
    - 记录使用情况和效果评分
    """

    def __init__(self) -> None:
        self._knowledge: Dict[str, ScenarioKnowledge] = {}
        self._templates: Dict[str, PromptTemplate] = {}

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create_knowledge(self, knowledge: ScenarioKnowledge) -> str:
        """
        创建知识条目。

        如果 knowledge_id 为空则自动生成。
        如果 created_at 为空则设为当前时间。
        返回 knowledge_id。
        """
        if not knowledge.knowledge_id:
            knowledge.knowledge_id = f"sk-{uuid.uuid4().hex[:12]}"

        if knowledge.knowledge_id in self._knowledge:
            raise ValueError(
                f"Knowledge ID already exists: {knowledge.knowledge_id}"
            )

        if knowledge.created_at is None:
            knowledge.created_at = datetime.utcnow()

        self._knowledge[knowledge.knowledge_id] = deepcopy(knowledge)
        logger.info(
            "Knowledge created: id=%s name=%s category=%s",
            knowledge.knowledge_id,
            knowledge.name,
            knowledge.scenario_category,
        )
        return knowledge.knowledge_id

    async def get_knowledge(
        self, knowledge_id: str
    ) -> Optional[ScenarioKnowledge]:
        """获取单条知识（返回副本）。"""
        entry = self._knowledge.get(knowledge_id)
        if entry is None:
            return None
        return deepcopy(entry)

    async def update_knowledge(
        self, knowledge_id: str, updates: Dict[str, Any]
    ) -> bool:
        """
        部分更新知识条目。

        仅更新 updates 字典中列出的字段。
        knowledge_id 字段不可修改。
        成功返回 True，知识不存在返回 False。
        """
        entry = self._knowledge.get(knowledge_id)
        if entry is None:
            logger.warning("Update failed — knowledge not found: %s", knowledge_id)
            return False

        immutable_fields = {"knowledge_id", "created_at", "created_by"}
        for key, value in updates.items():
            if key in immutable_fields:
                logger.warning(
                    "Skipping immutable field '%s' in update for %s",
                    key,
                    knowledge_id,
                )
                continue
            if hasattr(entry, key):
                setattr(entry, key, value)
            else:
                logger.warning(
                    "Unknown field '%s' in update for %s", key, knowledge_id
                )

        logger.info("Knowledge updated: %s", knowledge_id)
        return True

    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """
        软删除知识条目（设 enabled=False）。

        成功返回 True，知识不存在返回 False。
        """
        entry = self._knowledge.get(knowledge_id)
        if entry is None:
            logger.warning("Delete failed — knowledge not found: %s", knowledge_id)
            return False

        entry.enabled = False
        logger.info("Knowledge soft-deleted: %s", knowledge_id)
        return True

    # ------------------------------------------------------------------
    # Prompt Template CRUD
    # ------------------------------------------------------------------

    async def create_template(self, template: PromptTemplate) -> str:
        """创建 Prompt 模板，返回 template_id。"""
        if not template.template_id:
            template.template_id = f"pt-{uuid.uuid4().hex[:12]}"

        self._templates[template.template_id] = deepcopy(template)
        logger.info(
            "Template created: id=%s name=%s",
            template.template_id,
            template.name,
        )
        return template.template_id

    async def get_prompt_template(
        self, template_id: str
    ) -> Optional[PromptTemplate]:
        """获取 Prompt 模板（返回副本）。"""
        tmpl = self._templates.get(template_id)
        if tmpl is None:
            return None
        return deepcopy(tmpl)

    # ------------------------------------------------------------------
    # 查询: 6维条件匹配
    # ------------------------------------------------------------------

    async def query_applicable_knowledge(
        self,
        scenario_category: str,
        building_type: str = "all",
        zone_id: str = "all",
        current_time: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None,
        knowledge_types: Optional[List[str]] = None,
        max_items: int = 20,
    ) -> List[ScenarioKnowledge]:
        """
        查询当前上下文适用的知识条目。

        匹配逻辑（6维）:
        1. enabled=True 且在有效期内
        2. scenario_category 匹配
        3. applicable_building_types 包含 building_type 或 "all"
        4. applicable_zones 包含 zone_id 或 "all"
        5. applicable_time_ranges 覆盖 current_time（如有配置）
        6. applicable_conditions 与 conditions 匹配（如有配置）

        结果按 priority 降序排列，截断到 max_items。
        """
        now = datetime.utcnow()
        matched: List[ScenarioKnowledge] = []

        for entry in self._knowledge.values():
            # --- Filter 1: enabled + effective period ---
            if not entry.enabled:
                continue
            if entry.effective_from and entry.effective_from > now:
                continue
            if entry.effective_until and entry.effective_until < now:
                continue

            # --- Filter 2: scenario_category ---
            if entry.scenario_category != scenario_category:
                continue

            # --- Filter 3: building_type ---
            if not self._matches_list(
                entry.applicable_building_types, building_type
            ):
                continue

            # --- Filter 4: zone_id ---
            if not self._matches_list(entry.applicable_zones, zone_id):
                continue

            # --- Filter 5: time range ---
            if current_time and entry.applicable_time_ranges:
                if not self._time_in_ranges(
                    current_time, entry.applicable_time_ranges
                ):
                    continue

            # --- Filter 6: conditions ---
            if entry.applicable_conditions and conditions:
                if not self._conditions_match(
                    entry.applicable_conditions, conditions
                ):
                    continue

            # --- Optional: knowledge_type filter ---
            if knowledge_types and entry.knowledge_type not in knowledge_types:
                continue

            matched.append(deepcopy(entry))

        # Sort by priority descending
        matched.sort(key=lambda k: k.priority, reverse=True)

        return matched[:max_items]

    # ------------------------------------------------------------------
    # Prompt 组装
    # ------------------------------------------------------------------

    async def assemble_prompt(
        self,
        template_id: str,
        variables: Dict[str, str],
        scenario_category: str,
        context: Dict[str, Any],
    ) -> str:
        """
        组装完整的 Agent Prompt。

        流程:
        1. 获取 PromptTemplate
        2. 填充 {{variable}} 占位符
        3. 根据 knowledge_slots 查询适用知识
        4. 将知识注入 prompt 的对应位置
        5. 检查总 token 数不超过 max_total_tokens
        6. 返回组装后的完整 prompt
        """
        template = self._templates.get(template_id)
        if template is None:
            raise ValueError(f"Template not found: {template_id}")

        # Step 1: start with system_prompt
        prompt = template.system_prompt

        # Step 2: fill {{variable}} placeholders
        prompt = self._fill_variables(prompt, variables)

        # Step 3 & 4: inject knowledge for each slot
        remaining_knowledge_tokens = template.max_knowledge_tokens

        for slot in template.knowledge_slots:
            slot_name: str = slot.get("slot_name", "knowledge")
            slot_category: str = slot.get("category", scenario_category)
            slot_max_items: int = slot.get("max_items", 5)

            # Build query context from slot config and caller context
            building_type = context.get("building_type", "all")
            zone_id = context.get("zone_id", "all")
            current_time = context.get("current_time")
            query_conditions = context.get("conditions")
            slot_knowledge_types = slot.get("knowledge_types")

            applicable = await self.query_applicable_knowledge(
                scenario_category=slot_category,
                building_type=building_type,
                zone_id=zone_id,
                current_time=current_time,
                conditions=query_conditions,
                knowledge_types=slot_knowledge_types,
                max_items=slot_max_items,
            )

            # Build knowledge text, respecting remaining token budget
            knowledge_lines: List[str] = []
            for item in applicable:
                content_text = self._knowledge_to_text(item)
                content_tokens = _estimate_tokens(content_text)

                if content_tokens > remaining_knowledge_tokens:
                    logger.debug(
                        "Token budget exhausted for slot '%s', "
                        "skipping knowledge %s",
                        slot_name,
                        item.knowledge_id,
                    )
                    break

                knowledge_lines.append(content_text)
                remaining_knowledge_tokens -= content_tokens

            knowledge_block = "\n".join(knowledge_lines)

            # Inject: replace {{slot_name}} placeholder or append
            slot_placeholder = "{{" + slot_name + "}}"
            if slot_placeholder in prompt:
                prompt = prompt.replace(slot_placeholder, knowledge_block)
            else:
                # Append knowledge block to end if no placeholder found
                if knowledge_block:
                    prompt += f"\n\n### {slot_name}\n{knowledge_block}"

        # Step 5: enforce max_total_tokens
        total_tokens = _estimate_tokens(prompt)
        if total_tokens > template.max_total_tokens:
            max_chars = template.max_total_tokens * 4
            prompt = prompt[:max_chars]
            logger.warning(
                "Prompt truncated from ~%d to ~%d tokens for template %s",
                total_tokens,
                template.max_total_tokens,
                template_id,
            )

        return prompt

    # ------------------------------------------------------------------
    # 效果跟踪
    # ------------------------------------------------------------------

    async def record_usage(
        self,
        knowledge_id: str,
        outcome_score: Optional[float] = None,
    ) -> None:
        """
        记录知识使用次数和效果评分。

        outcome_score 为 None 时仅增加 usage_count。
        否则使用增量均值更新 avg_outcome_score。
        """
        entry = self._knowledge.get(knowledge_id)
        if entry is None:
            logger.warning(
                "record_usage — knowledge not found: %s", knowledge_id
            )
            return

        entry.usage_count += 1

        if outcome_score is not None:
            if entry.avg_outcome_score is None:
                entry.avg_outcome_score = outcome_score
            else:
                # Incremental mean:  new_avg = old_avg + (score - old_avg) / n
                n = entry.usage_count
                entry.avg_outcome_score += (
                    (outcome_score - entry.avg_outcome_score) / n
                )

        logger.debug(
            "Usage recorded: %s count=%d avg_score=%s",
            knowledge_id,
            entry.usage_count,
            entry.avg_outcome_score,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _matches_list(applicable: List[str], value: str) -> bool:
        """
        判断 value 是否被 applicable 列表覆盖。

        如果 applicable 包含 "all" 或 value 在 applicable 中，返回 True。
        如果 value 为 "all"，也视为匹配（调用方不限制）。
        """
        if "all" in applicable:
            return True
        if value == "all":
            return True
        return value in applicable

    @staticmethod
    def _time_in_ranges(
        current_time: str, time_ranges: List[Dict[str, str]]
    ) -> bool:
        """
        判断 current_time (HH:MM) 是否落在任一时间范围内。

        支持跨午夜的范围（如 start=22:00, end=06:00）。
        """
        try:
            cur_parts = current_time.split(":")
            cur_minutes = int(cur_parts[0]) * 60 + int(cur_parts[1])
        except (ValueError, IndexError):
            logger.warning("Invalid current_time format: %s", current_time)
            return False

        for tr in time_ranges:
            start_str = tr.get("start", "00:00")
            end_str = tr.get("end", "23:59")
            try:
                sp = start_str.split(":")
                ep = end_str.split(":")
                start_min = int(sp[0]) * 60 + int(sp[1])
                end_min = int(ep[0]) * 60 + int(ep[1])
            except (ValueError, IndexError):
                continue

            if start_min <= end_min:
                # Normal range (e.g. 06:00 - 09:00)
                if start_min <= cur_minutes <= end_min:
                    return True
            else:
                # Overnight range (e.g. 22:00 - 06:00)
                if cur_minutes >= start_min or cur_minutes <= end_min:
                    return True

        return False

    @staticmethod
    def _conditions_match(
        required: Dict[str, Any], actual: Dict[str, Any]
    ) -> bool:
        """
        简单条件匹配: required 中每个 key 必须在 actual 中存在且值相等。

        Phase 2 可替换为完整的条件引擎（K2 compile_condition）。
        """
        for key, expected_value in required.items():
            actual_value = actual.get(key)
            if actual_value != expected_value:
                return False
        return True

    @staticmethod
    def _fill_variables(text: str, variables: Dict[str, str]) -> str:
        """替换 {{variable_name}} 占位符。未提供的变量保留原占位符。"""

        def _replacer(match: re.Match) -> str:
            var_name = match.group(1)
            return variables.get(var_name, match.group(0))

        return _PLACEHOLDER_RE.sub(_replacer, text)

    @staticmethod
    def _knowledge_to_text(knowledge: ScenarioKnowledge) -> str:
        """
        将知识条目序列化为可注入 prompt 的文本块。

        格式:
        [<knowledge_type>] <name> (priority=<N>)
        <content 的关键字段>
        """
        lines: List[str] = [
            f"[{knowledge.knowledge_type}] {knowledge.name} "
            f"(priority={knowledge.priority})"
        ]

        content = knowledge.content
        if not content:
            return lines[0]

        # 如果有 "fact" / "rule" / "template" 等单字符串摘要，直接输出
        for summary_key in ("fact", "rule", "template", "summary", "text"):
            if summary_key in content:
                lines.append(str(content[summary_key]))

        # 如果有 "details"，按 key=value 输出
        details = content.get("details")
        if isinstance(details, dict):
            for dk, dv in details.items():
                lines.append(f"  {dk}: {dv}")

        return "\n".join(lines)
