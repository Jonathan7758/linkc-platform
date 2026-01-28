"""告警处理Agent模块

专门处理告警相关的智能Agent，提供告警分析、处理建议、自动响应等功能。
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


ALARM_SYSTEM_PROMPT = """你是一个专业的建筑设备告警处理助手。你的职责是：

1. 分析告警信息，判断告警的严重程度和紧急性
2. 提供专业的告警处理建议
3. 帮助用户确认和解决告警
4. 生成告警统计报告

你可以使用以下工具：
- get_alarm_list: 获取告警列表
- get_alarm_detail: 获取告警详情
- get_alarm_stats: 获取告警统计
- acknowledge_alarm: 确认告警
- resolve_alarm: 解决告警
- get_alarm_suggestions: 获取处理建议

请用中文回答，保持专业、简洁的风格。在分析告警时，要考虑：
- 告警的设备类型和位置
- 告警的严重级别
- 可能的原因和影响
- 推荐的处理步骤
"""


@dataclass
class AlarmAgentConfig(AgentConfig):
    """告警Agent配置"""
    model: str = "doubao-pro-32k"
    max_tokens: int = 2048
    enable_tools: bool = True
    tool_choice: str = "auto"
    auto_acknowledge: bool = False  # 是否自动确认告警
    severity_threshold: str = "warning"  # 自动处理的严重级别阈值


class AlarmAgent(BaseAgent):
    """告警处理Agent

    专门处理告警相关任务的Agent，支持：
    - 告警分析和分类
    - 处理建议生成
    - 自动/半自动告警响应
    - 告警统计和报告
    """

    def __init__(self, config: AlarmAgentConfig):
        """初始化告警Agent

        Args:
            config: Agent配置
        """
        if not config.system_prompt:
            config.system_prompt = ALARM_SYSTEM_PROMPT
        super().__init__(config)
        self.config: AlarmAgentConfig = config

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
                # 没有工具调用，返回内容
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

        # 根据意图选择工具
        tool_mapping = {
            "list_alarms": ["get_alarm_list", "get_alarm_stats"],
            "alarm_detail": ["get_alarm_detail", "get_alarm_suggestions"],
            "acknowledge": ["get_alarm_detail", "acknowledge_alarm"],
            "resolve": ["get_alarm_detail", "resolve_alarm"],
            "statistics": ["get_alarm_stats"],
            "suggestions": ["get_alarm_detail", "get_alarm_suggestions"],
        }

        return tool_mapping.get(intent, list(self._get_alarm_tools()))

    def _analyze_intent(self, message: str) -> str:
        """分析消息意图

        Args:
            message: 用户消息

        Returns:
            str: 意图类型
        """
        message_lower = message.lower()

        if any(kw in message_lower for kw in ["列表", "所有告警", "告警列表", "有哪些告警"]):
            return "list_alarms"
        elif any(kw in message_lower for kw in ["详情", "详细", "具体"]):
            return "alarm_detail"
        elif any(kw in message_lower for kw in ["确认", "acknowledge", "收到"]):
            return "acknowledge"
        elif any(kw in message_lower for kw in ["解决", "处理完", "已修复", "resolve"]):
            return "resolve"
        elif any(kw in message_lower for kw in ["统计", "汇总", "报告", "分析"]):
            return "statistics"
        elif any(kw in message_lower for kw in ["建议", "怎么处理", "如何解决"]):
            return "suggestions"
        else:
            return "general"

    def _get_alarm_tools(self) -> set[str]:
        """获取告警相关工具名称"""
        return {
            "get_alarm_list",
            "get_alarm_detail",
            "get_alarm_stats",
            "acknowledge_alarm",
            "resolve_alarm",
            "get_alarm_suggestions",
        }

    def _build_messages(self, message: str, context: AgentContext) -> list[dict[str, Any]]:
        """构建LLM消息列表"""
        messages = []

        # 添加系统提示
        if self.config.system_prompt:
            messages.append({
                "role": "system",
                "content": self.config.system_prompt,
            })

        # 添加历史消息
        for msg in context.messages:
            messages.append({
                "role": msg.role.value,
                "content": msg.content,
            })

        # 如果历史中没有当前消息，添加它
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
        alarm_tools = self._get_alarm_tools()

        for server in self._mcp_servers.values():
            if hasattr(server, "get_tools_openai_format"):
                for tool in server.get_tools_openai_format():
                    # 只添加告警相关工具
                    tool_name = tool.get("function", {}).get("name", "")
                    if tool_name in alarm_tools:
                        tools.append(tool)
        return tools

    # ========== 告警专用方法 ==========

    async def analyze_alarm(self, alarm_id: str) -> dict[str, Any]:
        """分析单个告警

        Args:
            alarm_id: 告警ID

        Returns:
            dict: 分析结果
        """
        # 获取告警详情
        detail_result = await self._execute_tool("get_alarm_detail", {"alarm_id": alarm_id})

        if not detail_result.get("success"):
            return {
                "success": False,
                "error": detail_result.get("error", "无法获取告警详情"),
            }

        alarm_data = detail_result.get("result", {})
        if not alarm_data.get("found"):
            return {
                "success": False,
                "error": f"告警 {alarm_id} 不存在",
            }

        alarm = alarm_data.get("alarm", {})

        # 获取处理建议
        suggestions_result = await self._execute_tool(
            "get_alarm_suggestions", {"alarm_id": alarm_id}
        )

        suggestions = []
        if suggestions_result.get("success"):
            suggestions = suggestions_result.get("result", {}).get("suggestions", [])

        # 构建分析结果
        return {
            "success": True,
            "alarm_id": alarm_id,
            "severity": alarm.get("severity"),
            "device_type": alarm.get("device_type"),
            "status": alarm.get("status"),
            "description": alarm.get("description"),
            "analysis": {
                "urgency": self._assess_urgency(alarm),
                "impact": self._assess_impact(alarm),
                "suggestions": suggestions,
            },
        }

    def _assess_urgency(self, alarm: dict) -> str:
        """评估告警紧急程度"""
        severity = alarm.get("severity", "info")
        severity_levels = {"critical": "紧急", "warning": "较高", "info": "一般"}
        return severity_levels.get(severity, "一般")

    def _assess_impact(self, alarm: dict) -> str:
        """评估告警影响范围"""
        device_type = alarm.get("device_type", "")

        if device_type in ["hvac", "elevator"]:
            return "可能影响多个区域的使用体验"
        elif device_type in ["fire_alarm", "security"]:
            return "可能涉及安全问题，需要立即处理"
        elif device_type in ["lighting"]:
            return "影响局部照明，影响范围有限"
        else:
            return "需要进一步评估影响范围"

    async def get_alarm_summary(self, hours: int = 24) -> dict[str, Any]:
        """获取告警摘要

        Args:
            hours: 统计时间范围（小时）

        Returns:
            dict: 告警摘要
        """
        # 获取统计数据
        stats_result = await self._execute_tool(
            "get_alarm_stats", {"group_by": "severity", "hours": hours}
        )

        if not stats_result.get("success"):
            return {
                "success": False,
                "error": stats_result.get("error", "无法获取统计数据"),
            }

        stats = stats_result.get("result", {})

        return {
            "success": True,
            "period_hours": hours,
            "total_alarms": stats.get("total", 0),
            "by_severity": stats.get("stats", {}),
            "summary": self._generate_summary_text(stats),
        }

    def _generate_summary_text(self, stats: dict) -> str:
        """生成摘要文本"""
        total = stats.get("total", 0)
        by_severity = stats.get("stats", {})

        if total == 0:
            return "当前时间段内无告警。"

        critical = by_severity.get("critical", 0)
        warning = by_severity.get("warning", 0)
        info = by_severity.get("info", 0)

        parts = []
        if critical > 0:
            parts.append(f"{critical}个严重告警")
        if warning > 0:
            parts.append(f"{warning}个警告")
        if info > 0:
            parts.append(f"{info}个信息提示")

        return f"共{total}个告警，其中{'、'.join(parts)}。"

    async def batch_acknowledge(self, alarm_ids: list[str], user: str) -> dict[str, Any]:
        """批量确认告警

        Args:
            alarm_ids: 告警ID列表
            user: 确认人

        Returns:
            dict: 批量操作结果
        """
        results = []
        success_count = 0
        fail_count = 0

        for alarm_id in alarm_ids:
            result = await self._execute_tool(
                "acknowledge_alarm",
                {"alarm_id": alarm_id, "acknowledged_by": user}
            )

            if result.get("success") and result.get("result", {}).get("success"):
                success_count += 1
                results.append({"alarm_id": alarm_id, "success": True})
            else:
                fail_count += 1
                results.append({
                    "alarm_id": alarm_id,
                    "success": False,
                    "error": result.get("result", {}).get("message", "操作失败")
                })

        return {
            "success": fail_count == 0,
            "total": len(alarm_ids),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results,
        }
