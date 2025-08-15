# orchestra.ai
A conversational AI orchestration platform for automating business voice communications.

## Orchestration Webhook
A FastAPI app is provided in `src/orchestra/app.py` with a `/webhook` endpoint. It wires together the `VoiceServer` and `Orchestrator` classes and logs each interaction, completing an audio/text round-trip.

Run the service locally:

```bash
uvicorn orchestra.app:app --host 0.0.0.0 --port 8000
```

Build and run with Docker:

```bash
docker build -f docker/Dockerfile.orchestration -t orchestration .
docker run -p 8000:8000 orchestration
```
