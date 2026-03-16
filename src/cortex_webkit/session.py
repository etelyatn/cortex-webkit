# src/cortex_webkit/session.py
"""Session manager and ChatSession."""

from __future__ import annotations

import uuid
import logging
from collections import deque
from typing import Any

from cortex_webkit.backends.base import ChatBackend
from cortex_webkit.config import CortexWebConfig
from cortex_webkit.models.chat import SessionInfo

logger = logging.getLogger(__name__)

_DEFAULT_BUFFER_SIZE = 500


class ChatSession:
    """One chat session — owns a backend, event buffer, and WS reference."""

    def __init__(
        self,
        session_id: str,
        model: str | None = None,
        directive: str | None = None,
        buffer_size: int = _DEFAULT_BUFFER_SIZE,
    ):
        self.id = session_id
        self.model = model or ""
        self.directive = directive or ""
        self.backend: ChatBackend | None = None
        self.websocket = None  # WebSocket reference (nullable)
        self._buffer: deque[dict[str, Any]] = deque(maxlen=buffer_size)
        self._message_count = 0

    @property
    def state(self) -> str:
        if self.backend is None:
            return "idle"
        return self.backend.get_state()

    def buffer_event(self, event: dict[str, Any]) -> None:
        self._buffer.append(event)

    def get_buffered_events(self) -> list[dict[str, Any]]:
        return list(self._buffer)

    def increment_messages(self) -> None:
        self._message_count += 1

    def info(self) -> SessionInfo:
        return SessionInfo(
            id=self.id,
            backend="cli",
            model=self.model,
            state=self.state,
            message_count=self._message_count,
        )


class SessionManager:
    """App-scoped singleton owning all chat sessions."""

    def __init__(self, config: CortexWebConfig):
        self._config = config
        self._sessions: dict[str, ChatSession] = {}

    async def create_session(
        self,
        model: str | None = None,
        directive: str | None = None,
    ) -> ChatSession:
        if len(self._sessions) >= self._config.max_sessions:
            raise RuntimeError(
                f"Cannot create session: max sessions ({self._config.max_sessions}) reached"
            )

        session_id = str(uuid.uuid4())
        session = ChatSession(
            session_id=session_id,
            model=model,
            directive=directive,
        )
        self._sessions[session_id] = session
        logger.info("Created session %s", session_id)
        return session

    def get_session(self, session_id: str) -> ChatSession | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[SessionInfo]:
        return [s.info() for s in self._sessions.values()]

    async def delete_session(self, session_id: str) -> bool:
        session = self._sessions.pop(session_id, None)
        if session is None:
            return False
        if session.backend is not None:
            await session.backend.shutdown()
        logger.info("Deleted session %s", session_id)
        return True

    async def shutdown_all(self) -> None:
        for session_id in list(self._sessions.keys()):
            await self.delete_session(session_id)
