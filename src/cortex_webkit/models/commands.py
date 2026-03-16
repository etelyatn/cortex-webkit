# src/cortex_webkit/models/commands.py
"""Command request/response models."""

from typing import Any
from pydantic import BaseModel


class CommandRequest(BaseModel):
    domain: str
    command: str
    params: dict[str, Any] | None = None


class CommandResponse(BaseModel):
    success: bool
    data: Any = None
    error: str | None = None
    duration_ms: int | None = None


class StatusResponse(BaseModel):
    connected: bool
    port: int | None = None
    pid: int | None = None
    project: str | None = None
    domains: list[str] | None = None


class SettingsResponse(BaseModel):
    model: str
    effort: str
    workflow: str
    access_mode: str
    directive: str
    max_sessions: int


class SettingsUpdate(BaseModel):
    model: str | None = None
    effort: str | None = None
    workflow: str | None = None
    access_mode: str | None = None
    directive: str | None = None
