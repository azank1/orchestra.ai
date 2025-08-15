from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, Any, List
import asyncio
from openai import OpenAI

from ..interfaces import (
    OrchestrationInterface,
    ConversationState,
    Message,
    MessageType,
)
from ..execution.tool_executor import ToolExecutor
from ..settings import settings


class GraphState(TypedDict):
    messages: list
    user_input: str
    intent: str
    tool_calls: list
    tool_results: list
    final_response: str
    session_id: str


class LangGraphOrchestrator(OrchestrationInterface):
    """Core orchestration engine using LangGraph"""

    def __init__(self):
        self.graph = self._build_graph()
        self.tool_executor = ToolExecutor()
        self.client = OpenAI(api_key=settings.orchestration.openai_api_key)
        # TODO: Add checkpointer for state persistence

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        workflow = StateGraph(GraphState)

        # Add nodes
        workflow.add_node("intent_parser", self._parse_intent)
        workflow.add_node("tool_selector", self._select_tools)
        workflow.add_node("tool_executor", self._execute_tools)
        workflow.add_node("response_generator", self._generate_response)

        # Define edges
        workflow.set_entry_point("intent_parser")
        workflow.add_conditional_edges(
            "intent_parser",
            self._should_use_tools,
            {
                "use_tools": "tool_selector",
                "direct_response": "response_generator"
            }
        )
        workflow.add_edge("tool_selector", "tool_executor")
        workflow.add_edge("tool_executor", "response_generator")
        workflow.add_edge("response_generator", END)

        return workflow.compile()

    async def process_message(self, message: Message, state: ConversationState) -> ConversationState:
        """Run the LangGraph workflow for a given message"""
        graph_state: GraphState = {
            "messages": [m.model_dump() for m in state.messages] + [message.model_dump()],
            "user_input": message.content,
            "intent": "",
            "tool_calls": [],
            "tool_results": [],
            "final_response": "",
            "session_id": message.session_id,
        }

        result: GraphState = await self.graph.ainvoke(graph_state)

        # update conversation state
        state.messages.append(message)
        if result.get("final_response"):
            ai_msg = Message(
                type=MessageType.SYSTEM_RESPONSE,
                content=result["final_response"],
                metadata={},
                timestamp=asyncio.get_event_loop().time(),
                session_id=message.session_id,
            )
            state.messages.append(ai_msg)
        state.current_intent = result.get("intent")
        return state

    async def _parse_intent(self, state: GraphState) -> GraphState:
        """Parse user intent using an LLM"""
        user_input = state["user_input"]
        try:
            completion = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=settings.orchestration.model_name,
                    messages=[
                        {"role": "system", "content": "Classify user intent in one word."},
                        {"role": "user", "content": user_input},
                    ],
                    max_tokens=5,
                    temperature=settings.orchestration.temperature,
                ),
            )
            intent = completion.choices[0].message.content.strip().lower()
        except Exception:
            text = user_input.lower()
            if "menu" in text:
                intent = "menu_query"
            elif "hours" in text:
                intent = "business_hours"
            else:
                intent = "general"

        state["intent"] = intent
        return state

    def _should_use_tools(self, state: GraphState) -> str:
        """Determine if tools are needed"""
        if state.get("intent") in {"menu_query", "business_hours"}:
            return "use_tools"
        return "direct_response"

    async def _select_tools(self, state: GraphState) -> GraphState:
        """Select appropriate tools based on intent"""
        intent = state.get("intent")
        tool_calls: List[Dict[str, Any]] = []
        if intent == "menu_query":
            tool_calls.append({"tool_name": "get_menu", "parameters": {}})
        elif intent == "business_hours":
            tool_calls.append({"tool_name": "get_business_hours", "parameters": {}})
        state["tool_calls"] = tool_calls
        return state

    async def _execute_tools(self, state: GraphState) -> GraphState:
        """Execute selected tools"""
        results: List[Dict[str, Any]] = []
        for call in state.get("tool_calls", []):
            res = await self.tool_executor.execute(
                call["tool_name"], call.get("parameters", {})
            )
            results.append({call["tool_name"]: res})
        state["tool_results"] = results
        return state

    async def _generate_response(self, state: GraphState) -> GraphState:
        """Generate final response"""
        tool_context = ""
        if state.get("tool_results"):
            tool_context = str(state["tool_results"])
        prompt = f"User: {state['user_input']}. Tool results: {tool_context}. Respond conversationally."
        try:
            completion = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=settings.orchestration.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=settings.orchestration.temperature,
                ),
            )
            response = completion.choices[0].message.content.strip()
        except Exception:
            if tool_context:
                response = tool_context
            else:
                response = "I'm here to help."
        state["final_response"] = response
        return state
