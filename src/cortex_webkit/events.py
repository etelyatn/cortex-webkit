# src/cortex_webkit/events.py
"""Stream event types for WebSocket chat protocol."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any


class StreamEventType(str, Enum):
    SESSION_INFO = "session_info"
    TURN_STARTED = "turn_started"
    TEXT_DELTA = "text_delta"
    TOOL_CALL_START = "tool_call_start"
    TOOL_INPUT_DELTA = "tool_input_delta"
    TOOL_RESULT = "tool_result"
    TURN_COMPLETE = "turn_complete"
    ERROR = "error"
    REPLAY_START = "replay_start"
    REPLAY_END = "replay_end"


@dataclass
class StreamEvent:
    type: StreamEventType

    # text_delta
    text: str | None = None

    # tool_call_start / tool_input_delta / tool_result
    tool_use_id: str | None = None
    name: str | None = None
    partial_json: str | None = None
    result: Any = None
    is_error: bool | None = None
    duration_ms: int | None = None

    # turn_complete
    usage: dict[str, int] | None = None

    # error
    code: str | None = None
    message: str | None = None
    retryable: bool | None = None

    # session_info
    backend: str | None = None
    session_id: str | None = None
    model: str | None = None
    capabilities: dict[str, Any] | None = None

    # replay_start
    event_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict, omitting None values."""
        result: dict[str, Any] = {"type": self.type.value}
        for f in fields(self):
            if f.name == "type":
                continue
            val = getattr(self, f.name)
            if val is not None:
                result[f.name] = val
        return result

    def to_json(self) -> str:
        """Serialize to JSON string."""
        import json
        return json.dumps(self.to_dict())
