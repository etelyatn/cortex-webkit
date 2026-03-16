# src/cortex_webkit/models/chat.py
"""Chat request/response models."""

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class SessionInfo(BaseModel):
    id: str
    backend: str = "cli"
    model: str = ""
    state: str = "idle"
    message_count: int = 0


class SessionCreate(BaseModel):
    model: str | None = None
    directive: str | None = None


class SessionListResponse(BaseModel):
    sessions: list[SessionInfo]
