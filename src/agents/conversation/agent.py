"""A3: Conversation Agent"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from src.agents.runtime.base import BaseAgent, AgentConfig, AutonomyLevel
from src.agents.runtime.decision import Decision, DecisionResult
from src.shared.llm.base import LLMClient, LLMConfig, LLMProvider, Message, LLMResponse
from src.shared.llm.factory import create_llm_client
from .config import ConversationAgentConfig, ConversationRequest, ConversationResponse, ConversationSession, ConversationTurn
from .tools import MCPToolRegistry

logger = logging.getLogger(__name__)


class ConversationAgent(BaseAgent):
    def __init__(self, config: ConversationAgentConfig, llm_client: Optional[LLMClient] = None):
        agent_config = AgentConfig(
            agent_id=config.agent_id,
            name="Conversation Agent",
            description="Natural language assistant for robot management",
            autonomy_level=AutonomyLevel.L2_LIMITED,
            tenant_id=config.tenant_id,
        )
        super().__init__(agent_config)
        self.conv_config = config
        
        if llm_client:
            self.llm = llm_client
        else:
            llm_config = LLMConfig(
                provider=LLMProvider(config.llm_provider),
                api_key=config.llm_api_key,
                model=config.llm_model,
                base_url=config.llm_base_url,
            )
            self.llm = create_llm_client(llm_config)
        
        self.sessions: Dict[str, ConversationSession] = {}
        self.tools = MCPToolRegistry.get_all_tools()
        self._mcp_client = None

    async def chat(self, request: ConversationRequest) -> ConversationResponse:
        session = self._get_or_create_session(request)
        session.turns.append(ConversationTurn(role="user", content=request.message))
        
        messages = self._build_messages(session)
        actions_taken = []
        
        for _ in range(self.conv_config.max_tool_iterations):
            response = await self.llm.chat(messages, tools=self.tools, tool_choice="auto")
            
            if not response.tool_calls:
                break
            
            for tool_call in response.tool_calls:
                result = await self._execute_tool(tool_call.name, tool_call.arguments)
                actions_taken.append({"tool": tool_call.name, "args": tool_call.arguments, "result": result})
                messages.append(Message(role="assistant", content="", tool_calls=[tool_call]))
                messages.append(self.llm.format_tool_result(tool_call.id, result))
        
        assistant_message = response.content or "Sorry, I could not process your request."
        session.turns.append(ConversationTurn(role="assistant", content=assistant_message))
        session.updated_at = datetime.now(timezone.utc)
        
        return ConversationResponse(
            session_id=request.session_id,
            message=assistant_message,
            actions_taken=actions_taken,
        )

    def _get_or_create_session(self, request: ConversationRequest) -> ConversationSession:
        if request.session_id not in self.sessions:
            self.sessions[request.session_id] = ConversationSession(
                session_id=request.session_id,
                tenant_id=request.tenant_id,
                user_id=request.user_id,
            )
        return self.sessions[request.session_id]

    def _build_messages(self, session: ConversationSession) -> List[Message]:
        messages = [Message(role="system", content=self.conv_config.system_prompt)]
        for turn in session.turns[-self.conv_config.max_history_turns:]:
            messages.append(Message(role=turn.role, content=turn.content))
        return messages

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if not self._mcp_client:
            return {"error": "MCP client not available"}
        try:
            result = await self._mcp_client.call_tool(tool_name, arguments)
            return result.data if result.success else {"error": result.error}
        except Exception as e:
            return {"error": str(e)}

    async def think(self, context: dict) -> Decision:
        return Decision(decision_type="conversation", description="Process conversation", actions=[], auto_approve=True, exceeds_boundary=False)

    async def execute(self, decision: Decision) -> DecisionResult:
        return DecisionResult(success=True, decision=decision, message="Conversation processed")

    async def get_history(self, session_id: str, limit: int = 20) -> List[Dict]:
        session = self.sessions.get(session_id)
        if not session:
            return []
        return [t.model_dump() for t in session.turns[-limit:]]

    async def clear_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

