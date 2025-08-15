from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from enum import Enum


class MessageType(Enum):
    USER_INPUT = "user_input"
    SYSTEM_RESPONSE = "system_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


class Message(BaseModel):
    type: MessageType
    content: str
    metadata: Dict[str, Any] = {}
    timestamp: float
    session_id: str


class ConversationState(BaseModel):
    session_id: str
    messages: List[Message] = []
    context: Dict[str, Any] = {}
    current_intent: Optional[str] = None
    pending_tool_calls: List[Dict[str, Any]] = []


# Layer interfaces (empty for now)
class VoiceInterface(ABC):
    @abstractmethod
    async def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass


class OrchestrationInterface(ABC):
    @abstractmethod
    async def process_message(self, message: Message, state: ConversationState) -> ConversationState:
        pass


class ToolInterface(ABC):
    @abstractmethod
    async def execute(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        pass


class PersistenceInterface(ABC):
    @abstractmethod
    async def save_state(self, state: ConversationState) -> None:
        pass
