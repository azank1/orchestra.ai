from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio

# Import architecture components
from .interfaces import Message, MessageType, ConversationState
from .orchestration.langgraph_orchestrator import LangGraphOrchestrator
from .persistence.session_manager import SessionManager
from .persistence.logging_service import LoggingService
from .voice.webhook_handler import VoiceWebhookHandler
from .settings import settings


# Request/Response models
class VoiceRequest(BaseModel):
    message: str
    session_id: str
    phone_number: Optional[str] = None
    metadata: Dict[str, Any] = {}


class VoiceResponse(BaseModel):
    response: str
    session_id: str
    should_end_call: bool = False
    metadata: Dict[str, Any] = {}


# Initialize FastAPI
app = FastAPI(
    title="Orchestra.ai",
    description="Multi-Agent Voice Orchestration Platform",
    version="1.0.0"
)

# Initialize services (TODO: Implement proper initialization)
orchestrator = LangGraphOrchestrator()
session_manager = SessionManager()
logging_service = LoggingService()
voice_handler = VoiceWebhookHandler()


@app.post("/webhook/voice", response_model=VoiceResponse)
async def handle_voice_webhook(
    request: VoiceRequest,
    background_tasks: BackgroundTasks
):
    """Main voice webhook endpoint"""
    try:
        # Create message
        message = Message(
            type=MessageType.USER_INPUT,
            content=request.message,
            session_id=request.session_id,
            timestamp=asyncio.get_event_loop().time(),
            metadata=request.metadata
        )

        # Get conversation state
        state = await session_manager.get_or_create_session(request.session_id)

        # Process through orchestration
        updated_state = await orchestrator.process_message(message, state)

        # Save state
        await session_manager.save_state(updated_state)

        # Get response
        if updated_state.messages:
            response_text = updated_state.messages[-1].content
        else:
            response_text = "I understand, let me help you with that."

        # Log interaction
        background_tasks.add_task(
            logging_service.log_interaction,
            {
                "session_id": request.session_id,
                "user_input": request.message,
                "ai_response": response_text,
                "intent": updated_state.current_intent
            }
        )

        return VoiceResponse(
            response=response_text,
            session_id=request.session_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "services": {
            "orchestration": "ready",
            "persistence": "ready",
            "voice": "ready"
        }
    }


# Keep existing endpoints from current app.py if they exist
