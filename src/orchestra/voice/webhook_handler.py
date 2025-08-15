from typing import Dict, Any

from ..interfaces import VoiceInterface


class VoiceWebhookHandler(VoiceInterface):
    """Handles voice platform webhook integration"""

    def __init__(self):
        self.supported_platforms = ["vapi", "retell", "bland"]

    async def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming voice webhook and normalize payload"""
        platform = (payload.get("platform") or "").lower()
        message = payload.get("message") or payload.get("text") or ""
        session_id = (
            payload.get("session_id")
            or payload.get("sessionId")
            or payload.get("call_id")
            or ""
        )
        metadata = {
            k: v
            for k, v in payload.items()
            if k not in {"platform", "message", "text", "session_id", "sessionId", "call_id"}
        }
        metadata["platform"] = platform
        return {"message": message, "session_id": session_id, "metadata": metadata}

    async def format_response(self, response_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Format response for voice platform"""
        platform = metadata.get("platform")
        response: Dict[str, Any] = {"message": response_text}
        if platform in {"vapi", "retell", "bland"}:
            response["endCall"] = metadata.get("should_end_call", False)
        return response
