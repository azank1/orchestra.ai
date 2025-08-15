"""FastAPI application for orchestration webhook."""
from fastapi import FastAPI, Request

# These imports rely on existing modules within the project.
# They are expected to provide the audio/text orchestration utilities.
from .voice_server import VoiceServer
from .orchestrator import Orchestrator
from .logging import log_interaction

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    """Handle audio/text round-trips via the orchestration pipeline."""
    payload = await request.json()

    voice_server = VoiceServer()
    orchestrator = Orchestrator()

    # If text isn't provided, attempt to transcribe from audio input
    user_text = payload.get("text")
    if not user_text and "audio" in payload:
        user_text = await voice_server.transcribe(payload["audio"])

    # Generate a response from the orchestrator
    response_text = await orchestrator.respond(user_text)

    # Log the interaction for auditing/analytics
    await log_interaction(user_text, response_text)

    # Return synthesized audio along with text response
    audio_payload = await voice_server.synthesize(response_text)
    return {"text": response_text, "audio": audio_payload}
