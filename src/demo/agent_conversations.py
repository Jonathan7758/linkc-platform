"""
DM4: Agent对话增强 (Agent Demo Conversations)

职责:
- 提供预设精彩对话场景
- 展示Agent推理过程
- 模拟学习反馈
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import random

logger = logging.getLogger(__name__)


class ConversationScenario(str, Enum):
    """预设对话场景"""
    TASK_SCHEDULING = "task_scheduling"      # 任务调度
    STATUS_QUERY = "status_query"            # 状态查询
    PROBLEM_DIAGNOSIS = "problem_diagnosis"  # 问题诊断
    DATA_ANALYSIS = "data_analysis"          # 数据分析
    BATCH_OPERATION = "batch_operation"      # 批量操作


@dataclass
class ReasoningStep:
    """推理步骤"""
    step: int
    action: str
    description: str
    result: Optional[str] = None
    duration_ms: int = 0


@dataclass
class AgentResponse:
    """Agent响应"""
    message: str
    reasoning_steps: List[ReasoningStep]
    suggestions: List[str] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    requires_confirmation: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "reasoning_steps": [
                {
                    "step": s.step,
                    "action": s.action,
                    "description": s.description,
                    "result": s.result,
                    "duration_ms": s.duration_ms
                }
                for s in self.reasoning_steps
            ],
            "suggestions": self.suggestions,
            "actions": self.actions,
            "requires_confirmation": self.requires_confirmation,
            "metadata": self.metadata
        }


@dataclass
class ConversationMessage:
    """对话消息"""
    role: str  # user, agent, system
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    reasoning: Optional[AgentResponse] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "reasoning": self.reasoning.to_dict() if self.reasoning else None
        }


class AgentConversationService:
    """
    Agent对话演示服务

    提供预设对话场景和智能响应模拟
    """

    _instance: Optional["AgentConversationService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._conversations: Dict[str, List[ConversationMessage]] = {}
        self._learning_records: List[Dict[str, Any]] = []

        # 预设场景配置
        self._scenario_configs = self._init_scenario_configs()

        logger.info("AgentConversationService initialized")

    def _init_scenario_configs(self) -> Dict[ConversationScenario, Dict[str, Any]]:
        """初始化场景配置"""
        return {
            ConversationScenario.TASK_SCHEDULING: {
                "name": "任务调度",
                "sample_inputs": [
                    "安排明天早上8点大堂深度清洁",
                    "帮我安排一个紧急清洁任务",
                    "明天下午3点安排会议室清洁"
                ],
                "description": "展示Agent如何理解任务需求并智能安排"
            },
            ConversationScenario.STATUS_QUERY: {
                "name": "状态查询",
                "sample_inputs": [
                    "现在有哪些机器人空闲",
                    "告诉我机器人A-01的状态",
                    "今天完成了多少清洁任务"
                ],
                "description": "展示Agent如何查询和汇总信息"
            },
            ConversationScenario.PROBLEM_DIAGNOSIS: {
                "name": "问题诊断",
                "sample_inputs": [
                    "28楼的机器人怎么停了",
                    "为什么机器人A-03一直在充电",
                    "有个机器人好像卡住了"
                ],
                "description": "展示Agent如何诊断问题并提供解决方案"
            },
            ConversationScenario.DATA_ANALYSIS: {
                "name": "数据分析",
                "sample_inputs": [
                    "这周的清洁效率怎么样",
                    "帮我分析一下本月的机器人利用率",
                    "哪个区域清洁频率最高"
                ],
                "description": "展示Agent的数据分析能力"
            },
            ConversationScenario.BATCH_OPERATION: {
                "name": "批量操作",
                "sample_inputs": [
                    "把所有电量低于30%的机器人召回充电",
                    "暂停所有3楼的清洁任务",
                    "给所有空闲机器人分配任务"
                ],
                "description": "展示Agent处理复杂批量指令的能力"
            }
        }

    # ==================== 对话处理 ====================

    async def process_message(
        self,
        session_id: str,
        user_message: str,
        scenario: Optional[ConversationScenario] = None
    ) -> AgentResponse:
        """
        处理用户消息

        Args:
            session_id: 会话ID
            user_message: 用户输入
            scenario: 指定场景 (可选，用于演示)

        Returns:
            Agent响应
        """
        # 初始化会话
        if session_id not in self._conversations:
            self._conversations[session_id] = []

        # 记录用户消息
        self._conversations[session_id].append(
            ConversationMessage(role="user", content=user_message)
        )

        # 检测场景
        if scenario is None:
            scenario = self._detect_scenario(user_message)

        # 生成响应
        response = await self._generate_response(user_message, scenario)

        # 记录Agent响应
        self._conversations[session_id].append(
            ConversationMessage(role="agent", content=response.message, reasoning=response)
        )

        return response

    def _detect_scenario(self, message: str) -> ConversationScenario:
        """检测用户意图对应的场景"""
        message_lower = message.lower()

        # 任务调度关键词
        if any(kw in message_lower for kw in ["安排", "调度", "派发", "清洁任务", "深度清洁"]):
            return ConversationScenario.TASK_SCHEDULING

        # 状态查询关键词
        if any(kw in message_lower for kw in ["状态", "空闲", "在哪", "位置", "电量", "完成了多少"]):
            return ConversationScenario.STATUS_QUERY

        # 问题诊断关键词
        if any(kw in message_lower for kw in ["怎么了", "停了", "故障", "卡住", "问题", "为什么"]):
            return ConversationScenario.PROBLEM_DIAGNOSIS

        # 数据分析关键词
        if any(kw in message_lower for kw in ["分析", "效率", "统计", "利用率", "报表", "这周", "本月"]):
            return ConversationScenario.DATA_ANALYSIS

        # 批量操作关键词
        if any(kw in message_lower for kw in ["所有", "批量", "全部", "低于", "召回"]):
            return ConversationScenario.BATCH_OPERATION

        # 默认为状态查询
        return ConversationScenario.STATUS_QUERY

    async def _generate_response(
        self,
        user_message: str,
        scenario: ConversationScenario
    ) -> AgentResponse:
        """生成Agent响应"""

        if scenario == ConversationScenario.TASK_SCHEDULING:
            return await self._handle_task_scheduling(user_message)
        elif scenario == ConversationScenario.STATUS_QUERY:
            return await self._handle_status_query(user_message)
        elif scenario == ConversationScenario.PROBLEM_DIAGNOSIS:
            return await self._handle_problem_diagnosis(user_message)
        elif scenario == ConversationScenario.DATA_ANALYSIS:
            return await self._handle_data_analysis(user_message)
        elif scenario == ConversationScenario.BATCH_OPERATION:
            return await self._handle_batch_operation(user_message)
        else:
            return self._generate_fallback_response()

    # ==================== 场景处理器 ====================

    async def _handle_task_scheduling(self, message: str) -> AgentResponse:
        """处理任务调度场景"""

        # 模拟推理延迟
        await asyncio.sleep(0.3)

        # 解析时间
        scheduled_time = "明天 08:00"
        if "下午" in message:
            scheduled_time = "明天 15:00"
        elif "晚上" in message:
            scheduled_time = "明天 20:00"

        # 解析区域
        zone = "大堂"
        if "会议室" in message:
            zone = "会议室"
        elif "走廊" in message:
            zone = "走廊"
        elif "洗手间" in message:
            zone = "洗手间"

        # 解析任务类型
        task_type = "routine"
        if "深度" in message:
            task_type = "deep_clean"
        elif "紧急" in message:
            task_type = "emergency"

        reasoning_steps = [
            ReasoningStep(
                step=1,
                action="parse_intent",
                description="解析用户意图",
                result=f"创建清洁任务 - {task_type}",
                duration_ms=45
            ),
            ReasoningStep(
                step=2,
                action="identify_zone",
                description="识别目标区域",
                result=f"区域: {zone} (zone_lobby_001)",
                duration_ms=32
            ),
            ReasoningStep(
                step=3,
                action="parse_time",
                description="解析时间安排",
                result=f"时间: {scheduled_time}",
                duration_ms=28
            ),
            ReasoningStep(
                step=4,
                action="evaluate_resources",
                description="评估可用资源",
                result="需要2台机器人，预计90分钟",
                duration_ms=156
            ),
            ReasoningStep(
                step=5,
                action="select_robots",
                description="选择最优机器人",
                result="推荐: 清洁机器人 A-01, A-02",
                duration_ms=89
            ),
            ReasoningStep(
                step=6,
                action="generate_plan",
                description="生成执行计划",
                result="已生成任务计划，等待确认",
                duration_ms=67
            )
        ]

        return AgentResponse(
            message=f"""好的，我已为您安排{scheduled_time}的{zone}{'深度' if task_type == 'deep_clean' else ''}清洁任务。

**任务详情:**
- 目标区域: {zone}
- 计划时间: {scheduled_time}
- 任务类型: {'深度清洁' if task_type == 'deep_clean' else '常规清洁'}
- 预计用时: 90分钟
- 清洁面积: 约800㎡

**资源分配:**
- 机器人: 清洁机器人 A-01、A-02
- A-01 当前电量: 85%，距离目标区域约3分钟
- A-02 当前电量: 92%，可作为备选

是否确认执行此任务？""",
            reasoning_steps=reasoning_steps,
            suggestions=[
                "可以调整执行时间",
                "可以选择其他机器人",
                "可以修改清洁类型"
            ],
            actions=[
                {"type": "create_task", "zone": zone, "time": scheduled_time, "robots": ["robot_001", "robot_002"]},
            ],
            requires_confirmation=True,
            metadata={
                "scenario": "task_scheduling",
                "zone": zone,
                "scheduled_time": scheduled_time,
                "task_type": task_type,
                "estimated_duration": 90
            }
        )

    async def _handle_status_query(self, message: str) -> AgentResponse:
        """处理状态查询场景"""

        await asyncio.sleep(0.2)

        reasoning_steps = [
            ReasoningStep(
                step=1,
                action="parse_query",
                description="解析查询类型",
                result="查询机器人状态",
                duration_ms=35
            ),
            ReasoningStep(
                step=2,
                action="fetch_data",
                description="获取实时数据",
                result="已获取8台机器人状态",
                duration_ms=78
            ),
            ReasoningStep(
                step=3,
                action="analyze",
                description="分析数据",
                result="空闲: 2台, 工作中: 4台, 充电: 1台, 维护: 1台",
                duration_ms=45
            ),
            ReasoningStep(
                step=4,
                action="format_response",
                description="生成响应",
                result="已格式化查询结果",
                duration_ms=23
            )
        ]

        # 根据查询类型生成不同响应
        if "空闲" in message:
            response_msg = """当前有 **2台机器人空闲**，可以立即分配任务:

| 机器人 | 位置 | 电量 | 今日完成 |
|--------|------|------|----------|
| A-02 | 环球贸易广场 1F | 92% | 5个任务 |
| B-03 | 国际金融中心 6F | 88% | 4个任务 |

**推荐:** A-02 电量充足且今日工作量较低，建议优先分配。

需要我为空闲机器人分配任务吗？"""
        elif "完成" in message or "多少" in message:
            response_msg = """**今日清洁任务统计:**

- 已完成: **127个任务**
- 清洁面积: **45,800㎡**
- 总工作时长: **186小时**

**各楼宇完成情况:**
| 楼宇 | 完成任务 | 完成率 |
|------|----------|--------|
| 环球贸易广场 | 48个 | 97.2% |
| 国际金融中心 | 42个 | 96.5% |
| 太古广场 | 37个 | 96.2% |

相比昨天，任务完成数增加了8%。"""
        else:
            response_msg = """**机器人车队状态概览:**

| 状态 | 数量 | 机器人 |
|------|------|--------|
| 🟢 工作中 | 4台 | A-01, B-01, B-02, C-01 |
| 🔵 空闲 | 2台 | A-02, B-03 |
| 🟡 充电中 | 1台 | A-03 (电量35%) |
| 🔧 维护中 | 1台 | C-02 (定期保养) |

**关键指标:**
- 整体利用率: 87.2%
- 平均电量: 72%
- 今日完成任务: 127个

有什么需要我帮您处理的吗？"""

        return AgentResponse(
            message=response_msg,
            reasoning_steps=reasoning_steps,
            suggestions=[
                "查看详细机器人信息",
                "分配任务给空闲机器人",
                "查看今日任务统计"
            ],
            metadata={"scenario": "status_query"}
        )

    async def _handle_problem_diagnosis(self, message: str) -> AgentResponse:
        """处理问题诊断场景"""

        await asyncio.sleep(0.4)

        reasoning_steps = [
            ReasoningStep(
                step=1,
                action="identify_target",
                description="识别问题对象",
                result="机器人 A-03 (28F)",
                duration_ms=42
            ),
            ReasoningStep(
                step=2,
                action="fetch_status",
                description="获取机器人状态",
                result="状态: 已暂停, 电量: 35%",
                duration_ms=65
            ),
            ReasoningStep(
                step=3,
                action="check_alerts",
                description="检查相关告警",
                result="发现1条告警: 电量低",
                duration_ms=58
            ),
            ReasoningStep(
                step=4,
                action="analyze_logs",
                description="分析运行日志",
                result="10:25 触发低电量保护，自动返回充电",
                duration_ms=123
            ),
            ReasoningStep(
                step=5,
                action="diagnose",
                description="生成诊断结论",
                result="原因: 电量不足触发保护机制",
                duration_ms=45
            ),
            ReasoningStep(
                step=6,
                action="suggest_solution",
                description="提供解决方案",
                result="建议: 等待充电完成或手动确认恢复",
                duration_ms=38
            )
        ]

        return AgentResponse(
            message="""**问题诊断报告**

🤖 **机器人:** 清洁机器人 A-03
📍 **位置:** 环球贸易广场 5F (已返回充电站)

**问题原因:**
机器人在执行5F走廊清洁任务时，电量降至20%以下，触发了低电量保护机制，自动暂停任务并返回充电站。

**时间线:**
- 09:15 - 开始5F走廊清洁任务
- 10:25 - 电量降至18%，触发低电量告警
- 10:26 - 自动暂停任务，返回充电站
- 10:32 - 到达充电站，开始充电
- 当前 - 充电中，电量35%

**解决方案:**
1. ⏳ **等待充电** - 预计40分钟后充满，自动恢复工作
2. 🔄 **任务转移** - 将未完成任务分配给其他空闲机器人
3. ✅ **手动恢复** - 确认电量充足后手动恢复任务

建议选择方案2，我可以帮您将任务分配给机器人A-02。是否执行？""",
            reasoning_steps=reasoning_steps,
            suggestions=[
                "等待充电完成",
                "转移任务给其他机器人",
                "查看机器人详细状态"
            ],
            actions=[
                {"type": "transfer_task", "from": "robot_003", "to": "robot_002"}
            ],
            requires_confirmation=True,
            metadata={
                "scenario": "problem_diagnosis",
                "robot_id": "robot_003",
                "issue": "low_battery",
                "recommended_action": "transfer_task"
            }
        )

    async def _handle_data_analysis(self, message: str) -> AgentResponse:
        """处理数据分析场景"""

        await asyncio.sleep(0.5)

        reasoning_steps = [
            ReasoningStep(
                step=1,
                action="parse_request",
                description="解析分析需求",
                result="时间范围: 本周, 指标: 清洁效率",
                duration_ms=38
            ),
            ReasoningStep(
                step=2,
                action="fetch_historical",
                description="获取历史数据",
                result="已加载7天数据，共847条任务记录",
                duration_ms=156
            ),
            ReasoningStep(
                step=3,
                action="calculate_metrics",
                description="计算效率指标",
                result="平均效率: 125㎡/小时",
                duration_ms=89
            ),
            ReasoningStep(
                step=4,
                action="trend_analysis",
                description="趋势分析",
                result="效率提升3.2%，呈上升趋势",
                duration_ms=112
            ),
            ReasoningStep(
                step=5,
                action="identify_insights",
                description="发现洞察",
                result="发现3个优化机会",
                duration_ms=78
            ),
            ReasoningStep(
                step=6,
                action="generate_report",
                description="生成分析报告",
                result="报告已生成",
                duration_ms=45
            )
        ]

        return AgentResponse(
            message="""**本周清洁效率分析报告**

📊 **整体表现: 优秀** ⬆️ +3.2%

**核心指标:**
| 指标 | 本周 | 上周 | 变化 |
|------|------|------|------|
| 任务完成率 | 96.8% | 95.2% | ↑1.6% |
| 平均效率 | 125㎡/h | 121㎡/h | ↑3.3% |
| 机器人利用率 | 87.2% | 85.5% | ↑1.7% |
| 异常停机次数 | 3次 | 7次 | ↓57% |

**每日趋势:**
```
效率 (㎡/小时)
130 |           ●
125 |     ●   ●   ●
120 |   ●   ●
115 | ●
    +------------------
      一 二 三 四 五 六 日
```

**关键洞察:**
1. 📈 **效率持续提升** - 本周效率较上周提升3.2%，主要得益于路径优化
2. ⚡ **高峰时段识别** - 上午9-11点效率最高，建议集中安排重要任务
3. 🔋 **电量管理改善** - 低电量告警减少40%，充电调度更合理

**优化建议:**
- 增加上午时段的任务密度
- 考虑在太古广场增加1台机器人
- 优化3F走廊的清洁路径

需要查看更详细的分析或导出报表吗？""",
            reasoning_steps=reasoning_steps,
            suggestions=[
                "查看各楼宇详细数据",
                "导出周报PDF",
                "对比上月数据"
            ],
            metadata={
                "scenario": "data_analysis",
                "period": "this_week",
                "efficiency_change": "+3.2%"
            }
        )

    async def _handle_batch_operation(self, message: str) -> AgentResponse:
        """处理批量操作场景"""

        await asyncio.sleep(0.35)

        reasoning_steps = [
            ReasoningStep(
                step=1,
                action="parse_condition",
                description="解析筛选条件",
                result="条件: 电量 < 30%",
                duration_ms=42
            ),
            ReasoningStep(
                step=2,
                action="parse_action",
                description="解析目标操作",
                result="操作: 召回充电",
                duration_ms=35
            ),
            ReasoningStep(
                step=3,
                action="query_targets",
                description="查询符合条件的机器人",
                result="找到2台机器人符合条件",
                duration_ms=78
            ),
            ReasoningStep(
                step=4,
                action="validate",
                description="验证操作可行性",
                result="2台机器人可安全召回",
                duration_ms=56
            ),
            ReasoningStep(
                step=5,
                action="impact_analysis",
                description="分析操作影响",
                result="影响: 2个进行中任务将暂停",
                duration_ms=89
            ),
            ReasoningStep(
                step=6,
                action="generate_plan",
                description="生成执行计划",
                result="已生成批量召回计划",
                duration_ms=45
            )
        ]

        return AgentResponse(
            message="""**批量操作确认**

🔍 **筛选条件:** 电量低于30%的机器人
⚡ **目标操作:** 召回至充电站

**符合条件的机器人:**
| 机器人 | 当前电量 | 位置 | 当前任务 |
|--------|----------|------|----------|
| A-03 | 25% | 环球贸易广场 5F | 走廊清洁 (进度68%) |
| B-02 | 28% | 国际金融中心 4F | 办公区清洁 (进度45%) |

**操作影响:**
- ⏸️ 2个进行中的任务将被暂停
- 📋 暂停的任务将自动加入待处理队列
- ⏱️ 预计影响清洁进度约30分钟

**建议处理方案:**
1. 立即召回 - 任务自动转移给其他机器人
2. 完成当前任务后召回 - 延迟约20分钟
3. 仅召回A-03 - B-02电量可支撑完成当前任务

确认执行批量召回操作？""",
            reasoning_steps=reasoning_steps,
            suggestions=[
                "立即执行召回",
                "完成任务后召回",
                "仅召回电量最低的机器人"
            ],
            actions=[
                {"type": "recall", "robot_id": "robot_003"},
                {"type": "recall", "robot_id": "robot_005"}
            ],
            requires_confirmation=True,
            metadata={
                "scenario": "batch_operation",
                "operation": "recall",
                "target_count": 2,
                "affected_tasks": 2
            }
        )

    def _generate_fallback_response(self) -> AgentResponse:
        """生成默认响应"""
        return AgentResponse(
            message="""抱歉，我没有完全理解您的需求。您可以尝试以下操作:

- **任务调度:** "安排明天早上大堂深度清洁"
- **状态查询:** "现在有哪些机器人空闲"
- **问题诊断:** "28楼的机器人怎么停了"
- **数据分析:** "这周的清洁效率怎么样"
- **批量操作:** "把所有电量低于30%的机器人召回充电"

请告诉我您想做什么？""",
            reasoning_steps=[
                ReasoningStep(
                    step=1,
                    action="fallback",
                    description="未能识别用户意图",
                    result="提供帮助选项",
                    duration_ms=15
                )
            ],
            suggestions=[
                "查看机器人状态",
                "安排清洁任务",
                "查看今日数据"
            ]
        )

    # ==================== 确认和学习 ====================

    async def confirm_action(self, session_id: str, confirmed: bool, feedback: Optional[str] = None) -> Dict[str, Any]:
        """确认或拒绝Agent建议的操作"""

        result = {
            "confirmed": confirmed,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }

        if confirmed:
            result["message"] = "操作已确认执行"
            result["status"] = "executed"
        else:
            result["message"] = "操作已取消"
            result["status"] = "cancelled"

            # 如果有反馈，记录学习
            if feedback:
                await self.record_learning(session_id, feedback)
                result["learning_recorded"] = True

        # 记录到对话
        if session_id in self._conversations:
            self._conversations[session_id].append(
                ConversationMessage(
                    role="system",
                    content=f"用户{'确认' if confirmed else '取消'}了操作" + (f"，反馈: {feedback}" if feedback else "")
                )
            )

        return result

    async def record_learning(self, session_id: str, feedback: str) -> Dict[str, Any]:
        """记录学习反馈"""

        learning_record = {
            "id": f"learn_{len(self._learning_records) + 1:04d}",
            "session_id": session_id,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat(),
            "applied": False
        }

        self._learning_records.append(learning_record)

        logger.info(f"Learning recorded: {feedback}")

        return {
            "success": True,
            "learning_id": learning_record["id"],
            "message": f"已记录您的反馈: {feedback}\n下次我会考虑这个因素做出更好的决策。"
        }

    # ==================== 预设场景演示 ====================

    def get_preset_scenarios(self) -> List[Dict[str, Any]]:
        """获取预设场景列表"""
        return [
            {
                "id": scenario.value,
                "name": config["name"],
                "description": config["description"],
                "sample_inputs": config["sample_inputs"]
            }
            for scenario, config in self._scenario_configs.items()
        ]

    async def run_demo_conversation(self, scenario: ConversationScenario) -> Dict[str, Any]:
        """运行预设演示对话"""

        session_id = f"demo_{scenario.value}_{datetime.now().strftime('%H%M%S')}"
        config = self._scenario_configs.get(scenario, {})

        # 使用第一个示例输入
        sample_input = config.get("sample_inputs", ["你好"])[0]

        # 处理消息
        response = await self.process_message(session_id, sample_input, scenario)

        return {
            "session_id": session_id,
            "scenario": scenario.value,
            "scenario_name": config.get("name", "未知"),
            "user_input": sample_input,
            "response": response.to_dict(),
            "conversation": [msg.to_dict() for msg in self._conversations.get(session_id, [])]
        }

    # ==================== 会话管理 ====================

    def get_conversation(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史"""
        return [msg.to_dict() for msg in self._conversations.get(session_id, [])]

    def clear_conversation(self, session_id: str) -> bool:
        """清除会话"""
        if session_id in self._conversations:
            del self._conversations[session_id]
            return True
        return False

    def get_learning_records(self) -> List[Dict[str, Any]]:
        """获取学习记录"""
        return self._learning_records


# 全局实例
agent_conversation_service = AgentConversationService()
