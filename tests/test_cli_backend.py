# tests/test_cli_backend.py
import pytest
import json
from cortex_webkit.backends.cli import CliBackend, parse_ndjson_line
from cortex_webkit.events import StreamEventType


def test_parse_text_delta():
    """Content block delta → text_delta event."""
    line = json.dumps({
        "type": "stream_event",
        "event": {
            "type": "content_block_delta",
            "delta": {"type": "text_delta", "text": "Hello"},
        },
    })
    events = parse_ndjson_line(line)
    assert len(events) == 1
    assert events[0].type == StreamEventType.TEXT_DELTA
    assert events[0].text == "Hello"


def test_parse_tool_use():
    """Assistant message with tool_use content → tool_call_start event."""
    line = json.dumps({
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": "t1", "name": "data.list_datatables", "input": {"filter": "*"}},
            ],
            "usage": {"input_tokens": 100, "output_tokens": 50},
        },
    })
    events = parse_ndjson_line(line)
    tool_events = [e for e in events if e.type == StreamEventType.TOOL_CALL_START]
    assert len(tool_events) == 1
    assert tool_events[0].name == "data.list_datatables"
    assert tool_events[0].tool_use_id == "t1"


def test_parse_result():
    """Result message → turn_complete event."""
    line = json.dumps({
        "type": "result",
        "duration_ms": 1500,
        "num_turns": 2,
        "session_id": "abc-123",
    })
    events = parse_ndjson_line(line)
    assert len(events) == 1
    assert events[0].type == StreamEventType.TURN_COMPLETE


def test_parse_system_error():
    """System error → error event."""
    line = json.dumps({
        "type": "system",
        "subtype": "error",
        "message": "Rate limit exceeded",
    })
    events = parse_ndjson_line(line)
    assert len(events) == 1
    assert events[0].type == StreamEventType.ERROR
    assert events[0].message == "Rate limit exceeded"


def test_parse_tool_result():
    """User message with tool_result → tool_result event."""
    line = json.dumps({
        "type": "user",
        "message": {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "t1",
                    "content": "Success: 4 items found",
                    "is_error": False,
                },
            ],
        },
    })
    events = parse_ndjson_line(line)
    tool_results = [e for e in events if e.type == StreamEventType.TOOL_RESULT]
    assert len(tool_results) == 1
    assert tool_results[0].tool_use_id == "t1"
    assert tool_results[0].is_error is False


def test_build_command_line():
    """Verify CLI arguments are built correctly."""
    args = CliBackend.build_command_args(
        cli_path="/usr/bin/claude",
        session_id="abc-123",
        mcp_config_path="/tmp/mcp.json",
        model="claude-sonnet-4-6",
        directive="You are helpful.",
    )
    assert args[0] == "/usr/bin/claude"
    assert "-p" in args
    assert "--input-format" in args
    assert args[args.index("--input-format") + 1] == "stream-json"
    assert "--output-format" in args
    assert args[args.index("--output-format") + 1] == "stream-json"
    assert "--session-id" in args
    assert "--mcp-config" in args
    assert "--model" in args
    assert "--append-system-prompt" in args
    assert "--dangerously-skip-permissions" in args
    assert "--include-partial-messages" in args
