"""
Tower C 场景知识种子数据加载器

提供 Tower C（45层办公塔楼，20台清洁机器人）的初始场景知识和 Prompt 模板。
通过 load_tower_c_seed_data() 将全部种子数据加载到 ScenarioKnowledgeBase 中。
"""

import logging
from datetime import datetime
from typing import Dict, List

from .scenario_kb import PromptTemplate, ScenarioKnowledge, ScenarioKnowledgeBase

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tower C 初始场景知识
# ---------------------------------------------------------------------------

TOWER_C_INITIAL_KNOWLEDGE: List[ScenarioKnowledge] = [
    # ----- sk-tc-001: 楼层配置 -----
    ScenarioKnowledge(
        knowledge_id="sk-tc-001",
        knowledge_type="domain_fact",
        scenario_category="cleaning",
        name="Tower C楼层配置",
        description="Tower C 办公塔楼的完整楼层划分、功能区域及重点区域标注",
        tags=["building-layout", "floor-plan", "tower-c"],
        applicable_building_types=["office_tower"],
        applicable_zones=["all"],
        content={
            "fact": (
                "Tower C共45层，B2-B1为地下车库，1-3层为商业裙楼，"
                "4-45层为办公楼层。配备20台清洁机器人，分4组部署。"
            ),
            "details": {
                "total_floors": 45,
                "underground": ["B2", "B1"],
                "commercial": [1, 2, 3],
                "office": list(range(4, 46)),
                "vip_zones": ["1F-大堂", "45F-行政层"],
                "high_traffic": ["1F", "B1-停车场入口", "3F-餐饮区"],
                "robot_count": 20,
                "robot_groups": {
                    "group_A": {"robots": 5, "floors": ["B2", "B1", "1F", "2F", "3F"]},
                    "group_B": {"robots": 5, "floors": list(range(4, 18))},
                    "group_C": {"robots": 5, "floors": list(range(18, 32))},
                    "group_D": {"robots": 5, "floors": list(range(32, 46))},
                },
                "elevators": {
                    "service_elevators": 3,
                    "freight_elevator": 1,
                    "max_robots_per_elevator": 1,
                },
                "charging_stations": {
                    "B1": 4,
                    "15F": 4,
                    "30F": 4,
                    "45F": 4,
                    "total": 16,
                },
            },
        },
        priority=90,
        version="1.0",
        enabled=True,
        created_by="system-seed",
    ),

    # ----- sk-tc-002: 清洁时间窗口 -----
    ScenarioKnowledge(
        knowledge_id="sk-tc-002",
        knowledge_type="scenario_rule",
        scenario_category="cleaning",
        name="清洁时间窗口",
        description="各区域类型允许清洁作业的时间窗口约束，确保不干扰正常办公",
        tags=["time-window", "scheduling", "constraint"],
        applicable_building_types=["office_tower"],
        applicable_zones=["all"],
        applicable_time_ranges=[{"start": "00:00", "end": "23:59"}],
        content={
            "rule": (
                "办公区域清洁应在营业时间外（22:00-08:00）进行；"
                "大堂和公共区域可在营业时间内清洁但需错峰，避开上下班高峰；"
                "地下车库清洁时间不受限但应避开早晚车流高峰。"
            ),
            "details": {
                "office_floors_4_to_45": {
                    "cleaning_window": "22:00-08:00",
                    "deep_clean_window": "01:00-05:00",
                    "note": "周末及法定假日可全天清洁",
                },
                "lobby_1F": {
                    "cleaning_window": "06:00-09:00,12:00-13:30,18:00-22:00",
                    "continuous_maintenance": True,
                    "note": "大堂全天保持一台机器人待命做快速保洁",
                },
                "commercial_2F_3F": {
                    "cleaning_window": "22:00-09:00,14:00-17:00",
                    "note": "避开午餐高峰11:30-13:30",
                },
                "parking_B2_B1": {
                    "cleaning_window": "10:00-16:00,22:00-06:00",
                    "note": "避开早高峰07:30-09:30和晚高峰17:30-19:30",
                },
            },
        },
        priority=80,
        version="1.0",
        enabled=True,
        created_by="system-seed",
    ),

    # ----- sk-tc-003: 机器人充电策略 -----
    ScenarioKnowledge(
        knowledge_id="sk-tc-003",
        knowledge_type="scenario_rule",
        scenario_category="cleaning",
        name="机器人充电策略",
        description="20台清洁机器人的电量管理和充电调度规则",
        tags=["charging", "battery", "robot-management"],
        applicable_building_types=["office_tower"],
        applicable_zones=["all"],
        content={
            "rule": (
                "电量低于20%必须立即返回充电站；电量低于50%时不分配跨楼层组任务；"
                "夜间深度清洁前（22:00）所有机器人应完成充电至80%以上；"
                "充电站采用就近原则，每个充电站同时最多服务4台机器人。"
            ),
            "details": {
                "battery_thresholds": {
                    "critical": 10,
                    "low": 20,
                    "moderate": 50,
                    "full": 100,
                },
                "charging_rules": {
                    "critical_action": "立即停止任务，原地等待救援或就近充电",
                    "low_action": "完成当前子任务后返回最近充电站",
                    "moderate_action": "禁止分配预计耗电超过30%的任务",
                    "pre_night_shift": "22:00前所有参与夜班的机器人充至80%以上",
                },
                "charging_station_assignment": {
                    "B1_station": ["group_A"],
                    "15F_station": ["group_B"],
                    "30F_station": ["group_C"],
                    "45F_station": ["group_D"],
                },
                "charging_duration_estimate": {
                    "20_to_80_percent": "45分钟",
                    "20_to_100_percent": "75分钟",
                    "0_to_100_percent": "90分钟",
                },
                "max_concurrent_per_station": 4,
            },
        },
        priority=85,
        version="1.0",
        enabled=True,
        created_by="system-seed",
    ),

    # ----- sk-tc-004: 清洁调度 Prompt 模板 -----
    ScenarioKnowledge(
        knowledge_id="sk-tc-004",
        knowledge_type="prompt_template",
        scenario_category="cleaning",
        name="清洁调度Prompt模板",
        description="清洁调度Agent的系统提示词模板引用，关联 pt-tc-001 模板",
        tags=["prompt", "agent-template", "cleaning-scheduler"],
        applicable_building_types=["office_tower"],
        applicable_zones=["all"],
        content={
            "template": (
                "本条目关联 Prompt 模板 pt-tc-001 (cleaning_scheduler_prompt)，"
                "用于清洁调度Agent的系统提示词组装。模板包含建筑名称、当前时间、"
                "机器人数量等变量槽位，以及领域知识和场景规则的知识注入槽。"
            ),
            "details": {
                "linked_template_id": "pt-tc-001",
                "agent_type": "cleaning_scheduler",
                "variable_count": 3,
                "knowledge_slot_count": 2,
            },
        },
        priority=70,
        version="1.0",
        enabled=True,
        created_by="system-seed",
    ),

    # ----- sk-tc-005: 大堂清洁标准 -----
    ScenarioKnowledge(
        knowledge_id="sk-tc-005",
        knowledge_type="domain_fact",
        scenario_category="cleaning",
        name="大堂清洁标准",
        description="1F主大堂的清洁质量标准、频次要求和特殊注意事项",
        tags=["lobby", "cleaning-standard", "quality"],
        applicable_building_types=["office_tower"],
        applicable_zones=["1F-大堂"],
        content={
            "fact": (
                "1F主大堂是Tower C的门面区域，面积约800平方米，采用大理石地面。"
                "要求每日深度清洁2次，日间保持一台机器人循环保洁。"
                "雨天需增加地面除湿频次，防止滑倒风险。"
            ),
            "details": {
                "area_sqm": 800,
                "floor_material": "大理石",
                "daily_deep_clean_count": 2,
                "deep_clean_schedule": ["06:00-07:30", "21:00-22:30"],
                "daytime_maintenance": {
                    "mode": "循环保洁",
                    "robot_count": 1,
                    "patrol_interval_minutes": 30,
                },
                "rainy_day_protocol": {
                    "floor_drying_frequency": "每15分钟一次",
                    "entrance_mat_check": "每30分钟更换/清洁",
                    "wet_floor_signs": True,
                },
                "quality_metrics": {
                    "floor_shine_score_min": 85,
                    "dust_particle_max_per_sqm": 5,
                    "response_time_minutes_max": 10,
                },
                "special_areas": [
                    "旋转门入口区域",
                    "前台接待区",
                    "电梯等候区",
                    "访客休息区",
                ],
            },
        },
        priority=75,
        version="1.0",
        enabled=True,
        created_by="system-seed",
    ),

    # ----- sk-tc-006: 高峰期人流规律 -----
    ScenarioKnowledge(
        knowledge_id="sk-tc-006",
        knowledge_type="domain_fact",
        scenario_category="cleaning",
        name="高峰期人流规律",
        description="Tower C工作日和周末各时段的人流量分布规律，用于清洁调度的错峰策略",
        tags=["traffic-pattern", "peak-hours", "scheduling-reference"],
        applicable_building_types=["office_tower"],
        applicable_zones=["all"],
        content={
            "fact": (
                "Tower C工作日约有6000人次进出。早高峰08:00-09:30集中在大堂和电梯区，"
                "午高峰11:30-13:30集中在3F餐饮区，晚高峰17:30-19:00集中在大堂。"
                "周末人流量约为工作日的15%，主要集中在商业裙楼。"
            ),
            "details": {
                "weekday_traffic": {
                    "daily_total_person_trips": 6000,
                    "morning_peak": {
                        "time": "08:00-09:30",
                        "zones": ["1F-大堂", "电梯区"],
                        "intensity": "高",
                        "person_trips": 2500,
                    },
                    "lunch_peak": {
                        "time": "11:30-13:30",
                        "zones": ["3F-餐饮区", "1F-大堂", "电梯区"],
                        "intensity": "高",
                        "person_trips": 1800,
                    },
                    "evening_peak": {
                        "time": "17:30-19:00",
                        "zones": ["1F-大堂", "电梯区", "B1-停车场入口"],
                        "intensity": "高",
                        "person_trips": 2200,
                    },
                    "off_peak": {
                        "time": "10:00-11:30,14:00-17:30",
                        "zones": ["办公楼层走廊", "公共洗手间"],
                        "intensity": "低",
                        "note": "适合安排楼层间机器人清洁任务",
                    },
                    "night": {
                        "time": "19:00-08:00",
                        "zones": ["全楼"],
                        "intensity": "极低",
                        "note": "最佳深度清洁时段，仅少量加班人员",
                    },
                },
                "weekend_traffic": {
                    "daily_total_person_trips": 900,
                    "peak_time": "10:00-18:00",
                    "primary_zones": ["1F-3F商业裙楼"],
                    "office_floors_occupancy": "极低",
                    "note": "周末可安排办公楼层全面深度清洁",
                },
                "special_events": {
                    "tenant_moving": "提前24小时通知，相关楼层暂停常规清洁",
                    "building_inspection": "提前48小时通知，全楼增加一次深度清洁",
                    "holiday_season": "商业裙楼人流量增加约40%，增派2台机器人",
                },
            },
        },
        priority=70,
        version="1.0",
        enabled=True,
        created_by="system-seed",
    ),
]


# ---------------------------------------------------------------------------
# Tower C Prompt 模板
# ---------------------------------------------------------------------------

TOWER_C_PROMPT_TEMPLATES: List[PromptTemplate] = [
    PromptTemplate(
        template_id="pt-tc-001",
        agent_type="cleaning_scheduler",
        name="cleaning_scheduler_prompt",
        system_prompt=(
            "你是 {{building_name}} 的智能清洁调度Agent。\n"
            "\n"
            "当前时间: {{current_time}}\n"
            "可调度机器人数量: {{robot_count}}\n"
            "\n"
            "## 你的职责\n"
            "根据楼宇的实际情况和当前状态，制定最优的清洁任务调度方案。\n"
            "你需要综合考虑以下因素:\n"
            "- 各区域的清洁时间窗口约束\n"
            "- 机器人的电量状态和充电需求\n"
            "- 当前时段的人流量分布\n"
            "- 各区域的清洁优先级和质量标准\n"
            "\n"
            "## 楼宇领域知识\n"
            "{{domain_knowledge}}\n"
            "\n"
            "## 调度规则\n"
            "{{scenario_rules}}\n"
            "\n"
            "## 输出要求\n"
            "请以 JSON 格式输出调度方案，包含:\n"
            '1. "assignments": 任务分配列表，每项包含 robot_id, zone, task_type, '
            "priority, estimated_duration_minutes\n"
            '2. "charging_plan": 需要充电的机器人列表，包含 robot_id, '
            "target_station, current_battery\n"
            '3. "reasoning": 简要说明调度决策的理由\n'
        ),
        variables=["building_name", "current_time", "robot_count"],
        knowledge_slots=[
            {
                "slot_name": "domain_knowledge",
                "category": "cleaning",
                "knowledge_types": ["domain_fact"],
                "max_items": 5,
            },
            {
                "slot_name": "scenario_rules",
                "category": "cleaning",
                "knowledge_types": ["scenario_rule"],
                "max_items": 3,
            },
        ],
        base_tokens_estimate=600,
        max_knowledge_tokens=2000,
        max_total_tokens=4000,
        version="1.0",
        is_active=True,
    ),
]


# ---------------------------------------------------------------------------
# 种子数据加载函数
# ---------------------------------------------------------------------------

async def load_tower_c_seed_data(kb: ScenarioKnowledgeBase) -> Dict[str, int]:
    """
    将 Tower C 的全部种子数据加载到 ScenarioKnowledgeBase 中。

    加载内容:
    - TOWER_C_INITIAL_KNOWLEDGE 中的所有场景知识条目
    - TOWER_C_PROMPT_TEMPLATES 中的所有 Prompt 模板

    Args:
        kb: 目标场景知识库实例

    Returns:
        {"knowledge_loaded": N, "templates_loaded": M}
        N 为成功加载的知识条目数，M 为成功加载的模板数

    Raises:
        不抛出异常。单条加载失败会记录警告日志并继续加载其余条目。
    """
    knowledge_loaded = 0
    templates_loaded = 0

    # --- 加载场景知识条目 ---
    for knowledge in TOWER_C_INITIAL_KNOWLEDGE:
        try:
            await kb.create_knowledge(knowledge)
            knowledge_loaded += 1
            logger.info(
                "Seed knowledge loaded: %s (%s)",
                knowledge.knowledge_id,
                knowledge.name,
            )
        except ValueError as exc:
            # knowledge_id 已存在等情况，跳过并记录
            logger.warning(
                "Skipped seed knowledge %s: %s",
                knowledge.knowledge_id,
                exc,
            )
        except Exception:
            logger.exception(
                "Failed to load seed knowledge %s",
                knowledge.knowledge_id,
            )

    # --- 加载 Prompt 模板 ---
    for template in TOWER_C_PROMPT_TEMPLATES:
        try:
            await kb.create_template(template)
            templates_loaded += 1
            logger.info(
                "Seed template loaded: %s (%s)",
                template.template_id,
                template.name,
            )
        except Exception:
            logger.exception(
                "Failed to load seed template %s",
                template.template_id,
            )

    summary = {
        "knowledge_loaded": knowledge_loaded,
        "templates_loaded": templates_loaded,
    }

    logger.info(
        "Tower C seed data loading complete: %d knowledge entries, %d templates",
        knowledge_loaded,
        templates_loaded,
    )

    return summary
