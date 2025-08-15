# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

# Initialize FastAPI
app = FastAPI(
    title="Orchestra.ai",
    description="Voice orchestration platform",
    version="0.1.0"
)

# Request/Response models
class TestRequest(BaseModel):
    text: str
    session_id: Optional[str] = None

class TestResponse(BaseModel):
    success: bool
    text: str
    session_id: str
    timestamp: str

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

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Orchestra.ai")
    print("📝 Test at: http://localhost:8000/test")
    print("📚 Docs at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)