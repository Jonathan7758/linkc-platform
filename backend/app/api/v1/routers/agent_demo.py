"""
DM4: Agent对话演示API路由 (Agent Demo Conversations API Router)

提供Agent对话演示的API端点:
- POST /api/v1/agent-demo/chat - 发送消息
- POST /api/v1/agent-demo/confirm - 确认操作
- POST /api/v1/agent-demo/feedback - 提交反馈
- GET /api/v1/agent-demo/scenarios - 获取预设场景
- POST /api/v1/agent-demo/run-demo - 运行演示对话
- GET /api/v1/agent-demo/conversation/{session_id} - 获取会话历史
- DELETE /api/v1/agent-demo/conversation/{session_id} - 清除会话
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

router = APIRouter(prefix="/agent-demo", tags=["agent-demo"])


# ==================== Pydantic 模型 ====================

class ScenarioEnum(str, Enum):
    """对话场景"""
    task_scheduling = "task_scheduling"
    status_query = "status_query"
    problem_diagnosis = "problem_diagnosis"
    data_analysis = "data_analysis"
    batch_operation = "batch_operation"


class ChatRequest(BaseModel):
    """发送消息请求"""
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="用户消息")
    scenario: Optional[ScenarioEnum] = Field(None, description="指定场景 (可选)")


class ConfirmRequest(BaseModel):
    """确认操作请求"""
    session_id: str = Field(..., description="会话ID")
    confirmed: bool = Field(..., description="是否确认")
    feedback: Optional[str] = Field(None, description="反馈信息 (拒绝时可选)")


class FeedbackRequest(BaseModel):
    """提交反馈请求"""
    session_id: str = Field(..., description="会话ID")
    feedback: str = Field(..., description="反馈内容")


class RunDemoRequest(BaseModel):
    """运行演示请求"""
    scenario: ScenarioEnum = Field(..., description="演示场景")


# ==================== 服务实例 ====================

_agent_service = None


def get_agent_service():
    """获取Agent对话服务实例"""
    global _agent_service
    if _agent_service is None:
        from src.demo.agent_conversations import agent_conversation_service
        _agent_service = agent_conversation_service
    return _agent_service


# ==================== API 端点 ====================

@router.post("/chat")
async def send_chat_message(request: ChatRequest):
    """
    发送消息给Agent

    Agent会分析消息意图并生成响应，包括:
    - 推理过程
    - 建议操作
    - 确认请求
    """
    service = get_agent_service()

    # 转换场景枚举
    scenario = None
    if request.scenario:
        from src.demo.agent_conversations import ConversationScenario
        scenario_map = {
            ScenarioEnum.task_scheduling: ConversationScenario.TASK_SCHEDULING,
            ScenarioEnum.status_query: ConversationScenario.STATUS_QUERY,
            ScenarioEnum.problem_diagnosis: ConversationScenario.PROBLEM_DIAGNOSIS,
            ScenarioEnum.data_analysis: ConversationScenario.DATA_ANALYSIS,
            ScenarioEnum.batch_operation: ConversationScenario.BATCH_OPERATION,
        }
        scenario = scenario_map.get(request.scenario)

    response = await service.process_message(
        session_id=request.session_id,
        user_message=request.message,
        scenario=scenario
    )

    return {
        "success": True,
        "session_id": request.session_id,
        "response": response.to_dict()
    }


@router.post("/confirm")
async def confirm_action(request: ConfirmRequest):
    """
    确认或拒绝Agent建议的操作

    如果拒绝并提供反馈，Agent会记录学习
    """
    service = get_agent_service()

    result = await service.confirm_action(
        session_id=request.session_id,
        confirmed=request.confirmed,
        feedback=request.feedback
    )

    return {
        "success": True,
        **result
    }


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    提交学习反馈

    Agent会记录反馈用于改进决策
    """
    service = get_agent_service()

    result = await service.record_learning(
        session_id=request.session_id,
        feedback=request.feedback
    )

    return {
        "success": True,
        **result
    }


@router.get("/scenarios")
async def get_preset_scenarios():
    """
    获取预设对话场景列表

    返回5个预设场景:
    - task_scheduling: 任务调度
    - status_query: 状态查询
    - problem_diagnosis: 问题诊断
    - data_analysis: 数据分析
    - batch_operation: 批量操作
    """
    service = get_agent_service()
    scenarios = service.get_preset_scenarios()

    return {
        "success": True,
        "scenarios": scenarios,
        "total": len(scenarios)
    }


@router.post("/run-demo")
async def run_demo_conversation(request: RunDemoRequest):
    """
    运行预设演示对话

    自动使用场景的示例输入，展示完整的Agent交互
    """
    service = get_agent_service()

    from src.demo.agent_conversations import ConversationScenario
    scenario_map = {
        ScenarioEnum.task_scheduling: ConversationScenario.TASK_SCHEDULING,
        ScenarioEnum.status_query: ConversationScenario.STATUS_QUERY,
        ScenarioEnum.problem_diagnosis: ConversationScenario.PROBLEM_DIAGNOSIS,
        ScenarioEnum.data_analysis: ConversationScenario.DATA_ANALYSIS,
        ScenarioEnum.batch_operation: ConversationScenario.BATCH_OPERATION,
    }

    result = await service.run_demo_conversation(scenario_map[request.scenario])

    return {
        "success": True,
        **result
    }


@router.get("/conversation/{session_id}")
async def get_conversation_history(session_id: str):
    """
    获取会话历史
    """
    service = get_agent_service()
    conversation = service.get_conversation(session_id)

    if not conversation:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return {
        "success": True,
        "session_id": session_id,
        "messages": conversation,
        "total": len(conversation)
    }


@router.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """
    清除会话历史
    """
    service = get_agent_service()
    success = service.clear_conversation(session_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return {
        "success": True,
        "message": f"Session {session_id} cleared"
    }


@router.get("/learning-records")
async def get_learning_records():
    """
    获取学习记录

    展示Agent从用户反馈中学习的内容
    """
    service = get_agent_service()
    records = service.get_learning_records()

    return {
        "success": True,
        "records": records,
        "total": len(records)
    }
