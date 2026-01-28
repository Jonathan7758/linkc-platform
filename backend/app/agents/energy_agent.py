"""能耗分析Agent模块

专门处理能耗相关的智能Agent，提供能耗分析、节能建议、异常检测等功能。
"""
import json
from dataclasses import dataclass, field
from typing import Any

from app.agents.base_agent import (
    BaseAgent,
    AgentConfig,
    AgentContext,
    AgentMessage,
    AgentResult,
    AgentState,
    MessageRole,
)


ENERGY_SYSTEM_PROMPT = """你是一个专业的建筑能耗分析助手。你的职责是：

1. 分析能耗数据，识别用能规律和异常
2. 提供专业的节能建议
3. 生成能耗报告和趋势分析
4. 对比不同建筑、不同时期的能耗情况

你可以使用以下工具：
- get_energy_consumption: 获取能耗数据
- get_energy_trend: 获取能耗趋势
- get_energy_comparison: 获取同比环比数据
- get_energy_ranking: 获取能耗排名
- get_energy_anomaly: 检测能耗异常

请用中文回答，保持专业、简洁的风格。在分析能耗时，要考虑：
- 能源类型（电、水、气等）
- 时间因素（季节、工作日/休息日）
- 空间因素（建筑、楼层）
- 对比基准（历史数据、行业标准）
"""


@dataclass
class EnergyAgentConfig(AgentConfig):
    """能耗Agent配置"""
    model: str = "doubao-pro-32k"
    max_tokens: int = 2048
    enable_tools: bool = True
    tool_choice: str = "auto"
    default_energy_type: str = "electricity"  # 默认能源类型
    anomaly_threshold: float = 1.5  # 异常检测阈值


class EnergyAgent(BaseAgent):
    """能耗分析Agent

    专门处理能耗相关任务的Agent，支持：
    - 能耗数据查询和分析
    - 趋势分析和预测
    - 异常检测和告警
    - 节能建议生成
    """

    def __init__(self, config: EnergyAgentConfig):
        """初始化能耗Agent

        Args:
            config: Agent配置
        """
        if not config.system_prompt:
            config.system_prompt = ENERGY_SYSTEM_PROMPT
        super().__init__(config)
        self.config: EnergyAgentConfig = config

    async def _process_message(self, message: str, context: AgentContext) -> str:
        """处理消息

        Args:
            message: 用户消息
            context: 上下文

        Returns:
            str: 响应内容
        """
        if not self._llm_client:
            return "LLM客户端未配置"

        # 分析消息意图
        intent = self._analyze_intent(message)
        context.set_variable("intent", intent)

        iterations = 0
        max_iterations = self.config.max_iterations
        messages = self._build_messages(message, context)
        tool_results_messages = []

        while iterations < max_iterations:
            iterations += 1

            # 构建请求参数
            request_params = {
                "model": self.config.model,
                "messages": messages + tool_results_messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            }

            # 添加工具
            if self.config.enable_tools:
                tools = self.get_tools_for_llm()
                if tools:
                    request_params["tools"] = tools
                    request_params["tool_choice"] = self.config.tool_choice

            # 调用LLM
            response = await self._llm_client.chat.completions.create(**request_params)
            assistant_message = response.choices[0].message

            # 检查是否有工具调用
            if assistant_message.tool_calls:
                # 添加助手消息
                tool_results_messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]
                })

                # 执行工具调用
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                    # 执行工具
                    tool_result = await self._execute_tool(tool_name, arguments)

                    # 添加工具结果
                    tool_results_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": self._format_tool_result(tool_result),
                    })
            else:
                return assistant_message.content or ""

        return "抱歉，处理请求时遇到了问题。请稍后重试。"

    async def _select_tools(self, message: str, context: AgentContext) -> list[str]:
        """选择要使用的工具

        Args:
            message: 用户消息
            context: 上下文

        Returns:
            list: 工具名称列表
        """
        intent = context.get_variable("intent", "unknown")

        tool_mapping = {
            "consumption": ["get_energy_consumption"],
            "trend": ["get_energy_trend"],
            "comparison": ["get_energy_comparison", "get_energy_consumption"],
            "ranking": ["get_energy_ranking"],
            "anomaly": ["get_energy_anomaly"],
            "report": ["get_energy_consumption", "get_energy_trend", "get_energy_comparison"],
        }

        return tool_mapping.get(intent, list(self._get_energy_tools()))

    def _analyze_intent(self, message: str) -> str:
        """分析消息意图

        Args:
            message: 用户消息

        Returns:
            str: 意图类型
        """
        message_lower = message.lower()

        if any(kw in message_lower for kw in ["用量", "消耗", "用了多少"]):
            return "consumption"
        elif any(kw in message_lower for kw in ["趋势", "变化", "走势"]):
            return "trend"
        elif any(kw in message_lower for kw in ["对比", "同比", "环比", "比较"]):
            return "comparison"
        elif any(kw in message_lower for kw in ["排名", "最高", "最多"]):
            return "ranking"
        elif any(kw in message_lower for kw in ["异常", "突增", "波动"]):
            return "anomaly"
        elif any(kw in message_lower for kw in ["报告", "报表", "分析"]):
            return "report"
        else:
            return "general"

    def _get_energy_tools(self) -> set[str]:
        """获取能耗相关工具名称"""
        return {
            "get_energy_consumption",
            "get_energy_trend",
            "get_energy_comparison",
            "get_energy_ranking",
            "get_energy_anomaly",
        }

    def _build_messages(self, message: str, context: AgentContext) -> list[dict[str, Any]]:
        """构建LLM消息列表"""
        messages = []

        if self.config.system_prompt:
            messages.append({
                "role": "system",
                "content": self.config.system_prompt,
            })

        for msg in context.messages:
            messages.append({
                "role": msg.role.value,
                "content": msg.content,
            })

        if not context.messages or context.messages[-1].content != message:
            messages.append({
                "role": "user",
                "content": message,
            })

        return messages

    async def _execute_tool(self, tool_name: str, arguments: dict) -> dict[str, Any]:
        """执行工具调用"""
        for server_name, server in self._mcp_servers.items():
            tools = server.list_tools()
            tool_names = []
            for t in tools:
                name = t.name
                if callable(name):
                    name = name()
                tool_names.append(name)

            if tool_name in tool_names:
                return await self.call_tool(server_name, tool_name, arguments)

        return {
            "success": False,
            "error": f"Tool '{tool_name}' not found",
        }

    def _format_tool_result(self, result: dict[str, Any]) -> str:
        """格式化工具结果"""
        if result.get("success"):
            return json.dumps(result.get("result", {}), ensure_ascii=False, indent=2)
        else:
            return f"Error: {result.get('error', 'Unknown error')}"

    def get_tools_for_llm(self) -> list[dict[str, Any]]:
        """获取LLM可用的工具格式"""
        tools = []
        energy_tools = self._get_energy_tools()

        for server in self._mcp_servers.values():
            if hasattr(server, "get_tools_openai_format"):
                for tool in server.get_tools_openai_format():
                    tool_name = tool.get("function", {}).get("name", "")
                    if tool_name in energy_tools:
                        tools.append(tool)
        return tools

    # ========== 能耗专用方法 ==========

    async def analyze_consumption(
        self,
        energy_type: str | None = None,
        building: str | None = None,
        hours: int = 24,
    ) -> dict[str, Any]:
        """分析能耗数据

        Args:
            energy_type: 能源类型
            building: 建筑名称
            hours: 时间范围（小时）

        Returns:
            dict: 分析结果
        """
        energy_type = energy_type or self.config.default_energy_type

        # 获取能耗数据
        consumption_result = await self._execute_tool(
            "get_energy_consumption",
            {
                "energy_type": energy_type,
                "building": building,
                "hours": hours,
            }
        )

        if not consumption_result.get("success"):
            return {
                "success": False,
                "error": consumption_result.get("error", "无法获取能耗数据"),
            }

        data = consumption_result.get("result", {})

        # 生成分析
        analysis = {
            "total_consumption": data.get("total_consumption", 0),
            "average_consumption": data.get("average_consumption", 0),
            "reading_count": data.get("total_readings", 0),
            "assessment": self._assess_consumption(data),
        }

        return {
            "success": True,
            "energy_type": energy_type,
            "building": building,
            "period_hours": hours,
            "analysis": analysis,
        }

    def _assess_consumption(self, data: dict) -> str:
        """评估能耗水平"""
        total = data.get("total_consumption", 0)
        avg = data.get("average_consumption", 0)

        if avg == 0:
            return "暂无足够数据进行评估"

        # 简单评估逻辑
        if total > avg * 1.5:
            return "能耗偏高，建议检查是否有设备异常运行"
        elif total < avg * 0.5:
            return "能耗偏低，请确认设备是否正常运行"
        else:
            return "能耗处于正常范围"

    async def get_energy_insights(
        self,
        building: str | None = None,
        days: int = 7,
    ) -> dict[str, Any]:
        """获取能耗洞察

        Args:
            building: 建筑名称
            days: 分析天数

        Returns:
            dict: 洞察结果
        """
        insights = []

        # 获取趋势数据
        trend_result = await self._execute_tool(
            "get_energy_trend",
            {
                "energy_type": self.config.default_energy_type,
                "building": building,
                "period": "day",
                "days": days,
            }
        )

        if trend_result.get("success"):
            trend_data = trend_result.get("result", {})
            trend_insight = self._analyze_trend(trend_data)
            if trend_insight:
                insights.append(trend_insight)

        # 获取对比数据
        comparison_result = await self._execute_tool(
            "get_energy_comparison",
            {
                "energy_type": self.config.default_energy_type,
                "building": building,
                "compare_type": "wow",  # 周环比
            }
        )

        if comparison_result.get("success"):
            comparison_data = comparison_result.get("result", {})
            comparison_insight = self._analyze_comparison(comparison_data)
            if comparison_insight:
                insights.append(comparison_insight)

        # 获取异常数据
        anomaly_result = await self._execute_tool(
            "get_energy_anomaly",
            {
                "building": building,
                "threshold": self.config.anomaly_threshold,
                "hours": days * 24,
            }
        )

        if anomaly_result.get("success"):
            anomaly_data = anomaly_result.get("result", {})
            anomaly_insight = self._analyze_anomaly(anomaly_data)
            if anomaly_insight:
                insights.append(anomaly_insight)

        return {
            "success": True,
            "building": building,
            "period_days": days,
            "insights": insights,
            "suggestions": self._generate_suggestions(insights),
        }

    def _analyze_trend(self, trend_data: dict) -> dict[str, Any] | None:
        """分析趋势数据"""
        trend_list = trend_data.get("trend", [])
        if len(trend_list) < 2:
            return None

        # 计算趋势方向
        values = [t.get("value", 0) for t in trend_list]
        first_half = sum(values[:len(values)//2]) / max(len(values)//2, 1)
        second_half = sum(values[len(values)//2:]) / max(len(values) - len(values)//2, 1)

        if second_half > first_half * 1.1:
            direction = "上升"
            concern = "high"
        elif second_half < first_half * 0.9:
            direction = "下降"
            concern = "low"
        else:
            direction = "平稳"
            concern = "normal"

        return {
            "type": "trend",
            "title": f"能耗趋势{direction}",
            "description": f"近期能耗呈{direction}趋势",
            "concern_level": concern,
        }

    def _analyze_comparison(self, comparison_data: dict) -> dict[str, Any] | None:
        """分析对比数据"""
        change_rate = comparison_data.get("change_rate", 0)
        trend = comparison_data.get("trend", "stable")

        if abs(change_rate) < 5:
            return None

        if trend == "up":
            concern = "high" if change_rate > 20 else "medium"
            description = f"较上周增长{change_rate:.1f}%"
        else:
            concern = "low"
            description = f"较上周下降{abs(change_rate):.1f}%"

        return {
            "type": "comparison",
            "title": f"周环比{'上升' if trend == 'up' else '下降'}",
            "description": description,
            "concern_level": concern,
        }

    def _analyze_anomaly(self, anomaly_data: dict) -> dict[str, Any] | None:
        """分析异常数据"""
        anomaly_count = anomaly_data.get("anomaly_count", 0)

        if anomaly_count == 0:
            return None

        return {
            "type": "anomaly",
            "title": f"发现{anomaly_count}个异常",
            "description": f"检测到{anomaly_count}个能耗异常点，建议检查相关设备",
            "concern_level": "high" if anomaly_count > 3 else "medium",
        }

    def _generate_suggestions(self, insights: list[dict]) -> list[str]:
        """根据洞察生成建议"""
        suggestions = []

        for insight in insights:
            insight_type = insight.get("type")
            concern = insight.get("concern_level")

            if insight_type == "trend" and concern == "high":
                suggestions.append("能耗持续上升，建议检查是否有设备长时间运行或效率下降")
            elif insight_type == "comparison" and concern == "high":
                suggestions.append("周环比增幅较大，建议对比分析本周与上周的使用情况差异")
            elif insight_type == "anomaly":
                suggestions.append("存在能耗异常，建议排查异常时段的设备运行状态")

        if not suggestions:
            suggestions.append("当前能耗状态良好，建议继续保持")

        return suggestions

    async def get_building_comparison(
        self,
        energy_type: str | None = None,
        days: int = 7,
        limit: int = 10,
    ) -> dict[str, Any]:
        """获取建筑能耗对比

        Args:
            energy_type: 能源类型
            days: 统计天数
            limit: 返回数量

        Returns:
            dict: 对比结果
        """
        energy_type = energy_type or self.config.default_energy_type

        ranking_result = await self._execute_tool(
            "get_energy_ranking",
            {
                "energy_type": energy_type,
                "group_by": "building",
                "days": days,
                "limit": limit,
            }
        )

        if not ranking_result.get("success"):
            return {
                "success": False,
                "error": ranking_result.get("error", "无法获取排名数据"),
            }

        data = ranking_result.get("result", {})
        ranking = data.get("ranking", [])

        # 计算总量和平均值
        total = sum(r.get("consumption", 0) for r in ranking)
        avg = total / len(ranking) if ranking else 0

        # 标记高能耗建筑
        high_consumption = [
            r for r in ranking
            if r.get("consumption", 0) > avg * 1.3
        ]

        return {
            "success": True,
            "energy_type": energy_type,
            "period_days": days,
            "ranking": ranking,
            "statistics": {
                "total": round(total, 2),
                "average": round(avg, 2),
                "high_consumption_count": len(high_consumption),
            },
            "high_consumption_buildings": [r.get("name") for r in high_consumption],
        }

    async def detect_anomalies(
        self,
        building: str | None = None,
        hours: int = 24,
    ) -> dict[str, Any]:
        """检测能耗异常

        Args:
            building: 建筑名称
            hours: 检测时间范围

        Returns:
            dict: 异常检测结果
        """
        result = await self._execute_tool(
            "get_energy_anomaly",
            {
                "building": building,
                "threshold": self.config.anomaly_threshold,
                "hours": hours,
            }
        )

        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "异常检测失败"),
            }

        data = result.get("result", {})
        anomalies = data.get("anomalies", [])

        # 按严重程度排序
        sorted_anomalies = sorted(
            anomalies,
            key=lambda x: x.get("ratio", 0),
            reverse=True
        )

        return {
            "success": True,
            "building": building,
            "period_hours": hours,
            "threshold": self.config.anomaly_threshold,
            "total_readings": data.get("total_readings", 0),
            "anomaly_count": len(anomalies),
            "anomalies": sorted_anomalies[:10],  # 只返回前10个
            "summary": self._generate_anomaly_summary(anomalies),
        }

    def _generate_anomaly_summary(self, anomalies: list[dict]) -> str:
        """生成异常摘要"""
        if not anomalies:
            return "未检测到能耗异常"

        count = len(anomalies)
        max_ratio = max(a.get("ratio", 0) for a in anomalies)

        if max_ratio > 3:
            severity = "严重"
        elif max_ratio > 2:
            severity = "中等"
        else:
            severity = "轻微"

        return f"检测到{count}个{severity}异常，最高超标{max_ratio:.1f}倍"
