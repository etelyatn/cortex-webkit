# tests/test_events.py
import json
from cortex_webkit.events import StreamEvent, StreamEventType


def test_text_delta_serialization():
    event = StreamEvent(type=StreamEventType.TEXT_DELTA, text="hello")
    data = event.to_dict()
    assert data == {"type": "text_delta", "text": "hello"}


def test_tool_call_start_serialization():
    event = StreamEvent(
        type=StreamEventType.TOOL_CALL_START,
        tool_use_id="t1",
        name="data.list_datatables",
    )
    data = event.to_dict()
    assert data["type"] == "tool_call_start"
    assert data["tool_use_id"] == "t1"
    assert data["name"] == "data.list_datatables"


def test_turn_complete_with_usage():
    event = StreamEvent(
        type=StreamEventType.TURN_COMPLETE,
        usage={"input_tokens": 100, "output_tokens": 50},
    )
    data = event.to_dict()
    assert data["usage"]["input_tokens"] == 100


def test_error_event():
    event = StreamEvent(
        type=StreamEventType.ERROR,
        code="rate_limit",
        message="Too many requests",
        retryable=True,
    )
    data = event.to_dict()
    assert data["retryable"] is True
