import asyncio
import json
import os
from typing import Optional

import redis

from ..interfaces import PersistenceInterface, ConversationState


class SessionManager(PersistenceInterface):
    """Redis-based session state management"""

    def __init__(self):
        self.redis_client = None
        self._connect()

    def _connect(self):
        """Connect to Redis"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
        except Exception:
            self.redis_client = None

    async def get_session(self, session_id: str) -> Optional[ConversationState]:
        """Get conversation state by session ID"""
        if not self.redis_client:
            return None
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: self.redis_client.get(session_id))
        if not data:
            return None
        payload = json.loads(data)
        return ConversationState(**payload)

    async def save_state(self, state: ConversationState) -> None:
        """Save conversation state to Redis"""
        if not self.redis_client:
            return
        loop = asyncio.get_event_loop()
        data = json.dumps(state.model_dump())
        await loop.run_in_executor(None, lambda: self.redis_client.set(state.session_id, data))

    async def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session"""
        if not self.redis_client:
            return False
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: self.redis_client.delete(session_id)
        )
        return result > 0

    async def get_or_create_session(self, session_id: str) -> ConversationState:
        """Get existing session or create new one"""
        state = await self.get_session(session_id)
        if not state:
            state = ConversationState(session_id=session_id)
        return state
