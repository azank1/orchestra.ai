# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import logging

# Import Orchestra.ai brain processing
try:
    from src.orchestra.main import process_message  # type: ignore
except Exception:  # pragma: no cover - fallback for environments without brain
    async def process_message(*args, **kwargs):
        raise RuntimeError("Orchestra brain not available")

from src.orchestra.persistence.session_manager import SessionManager

# Initialize FastAPI
app = FastAPI(
    title="Orchestra.ai",
    description="Voice orchestration platform",
    version="0.1.0"
)

# Initialize services
logger = logging.getLogger(__name__)
session_manager = SessionManager()

# Request/Response models
class TestRequest(BaseModel):
    text: str
    session_id: Optional[str] = None

class TestResponse(BaseModel):
    success: bool
    text: str
    session_id: str
    timestamp: str


class VoicePayload(BaseModel):
    message: str
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Orchestra.ai",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/test")
async def test_command(request: TestRequest):
    """
    Test endpoint - for now just echoes back
    """
    # Generate session ID if not provided
    session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
    
    # For now, just echo back
    return TestResponse(
        success=True,
        text=f"Received: {request.text}",
        session_id=session_id,
        timestamp=datetime.now().isoformat()
    )


@app.post("/webhook/voice")
async def handle_voice_webhook(payload: VoicePayload):
    """Webhook endpoint for voice platform messages"""
    session_id = payload.session_id or f"session_{uuid.uuid4().hex[:8]}"

    try:
        # Retrieve or create session state
        state = await session_manager.get_or_create_session(session_id)

        # Process message through Orchestra brain
        updated_state = await process_message(payload.message, state)

        # Persist updated state
        await session_manager.save_state(updated_state)

        # Extract response text
        response_text = (
            updated_state.messages[-1].content
            if getattr(updated_state, "messages", None)
            else ""
        )

        logger.info("voice webhook processed", extra={"session_id": session_id})
        return {"response": response_text, "session_id": session_id}

    except Exception as exc:  # pragma: no cover
        logger.exception("voice webhook failed", exc_info=exc)
        raise HTTPException(status_code=500, detail="Error processing voice message")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Orchestra.ai")
    print("📝 Test at: http://localhost:8000/test")
    print("📚 Docs at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
