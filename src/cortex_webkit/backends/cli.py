# src/cortex_webkit/backends/cli.py
"""CliBackend — manages claude -p subprocess with NDJSON streaming."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from cortex_webkit.backends.base import ChatBackend
from cortex_webkit.events import StreamEvent, StreamEventType

logger = logging.getLogger(__name__)


def parse_ndjson_line(line: str) -> list[StreamEvent]:
    """Parse a single NDJSON line from claude -p stdout into StreamEvents.

    Port of CortexStreamEventParser::ParseNdjsonLine from C++.
    """
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return []

    msg_type = data.get("type", "")
    events: list[StreamEvent] = []

    if msg_type == "system":
        subtype = data.get("subtype", "")
        if subtype in ("error", "warning"):
            events.append(StreamEvent(
                type=StreamEventType.ERROR,
                code=subtype,
                message=data.get("message", ""),
                retryable=subtype != "error",
            ))
        elif subtype == "init":
            events.append(StreamEvent(
                type=StreamEventType.SESSION_INFO,
                session_id=data.get("session_id"),
                model=data.get("model"),
                backend="cli",
            ))

    elif msg_type == "stream_event":
        event = data.get("event", {})
        event_type = event.get("type", "")
        if event_type == "content_block_delta":
            delta = event.get("delta", {})
            delta_type = delta.get("type", "")
            if delta_type == "text_delta":
                events.append(StreamEvent(
                    type=StreamEventType.TEXT_DELTA,
                    text=delta.get("text", ""),
                ))
            elif delta_type == "input_json_delta":
                events.append(StreamEvent(
                    type=StreamEventType.TOOL_INPUT_DELTA,
                    tool_use_id=event.get("index"),
                    partial_json=delta.get("partial_json", ""),
                ))

    elif msg_type == "content_block_delta":
        # Legacy format
        delta = data.get("delta", {})
        if delta.get("type") == "text_delta":
            events.append(StreamEvent(
                type=StreamEventType.TEXT_DELTA,
                text=delta.get("text", ""),
            ))

    elif msg_type == "assistant":
        message = data.get("message", {})
        content = message.get("content", [])
        usage = message.get("usage", {})

        for block in content:
            block_type = block.get("type", "")
            if block_type == "text":
                events.append(StreamEvent(
                    type=StreamEventType.TEXT_DELTA,
                    text=block.get("text", ""),
                ))
            elif block_type == "tool_use":
                events.append(StreamEvent(
                    type=StreamEventType.TOOL_CALL_START,
                    tool_use_id=block.get("id"),
                    name=block.get("name"),
                ))
                tool_input = block.get("input")
                if tool_input:
                    events.append(StreamEvent(
                        type=StreamEventType.TOOL_INPUT_DELTA,
                        tool_use_id=block.get("id"),
                        partial_json=json.dumps(tool_input),
                    ))

        if usage and events:
            for e in reversed(events):
                if e.type == StreamEventType.TEXT_DELTA:
                    e.usage = {
                        "input_tokens": usage.get("input_tokens", 0),
                        "output_tokens": usage.get("output_tokens", 0),
                        "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
                        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
                    }
                    break

    elif msg_type == "user":
        message = data.get("message", {})
        content = message.get("content", [])
        for block in content:
            if block.get("type") == "tool_result":
                result_content = block.get("content", "")
                if isinstance(result_content, list):
                    result_content = "\n".join(
                        b.get("text", "") for b in result_content if b.get("type") == "text"
                    )
                events.append(StreamEvent(
                    type=StreamEventType.TOOL_RESULT,
                    tool_use_id=block.get("tool_use_id"),
                    result=result_content,
                    is_error=block.get("is_error", False),
                ))

    elif msg_type == "result":
        events.append(StreamEvent(
            type=StreamEventType.TURN_COMPLETE,
            usage={
                "input_tokens": data.get("input_tokens", 0),
                "output_tokens": data.get("output_tokens", 0),
            },
        ))

    return events


class CliBackend(ChatBackend):
    """Manages a claude -p subprocess with NDJSON stdin/stdout."""

    def __init__(
        self,
        cli_path: str,
        session_id: str,
        mcp_config_path: str,
        model: str = "",
        directive: str = "",
    ):
        self._cli_path = cli_path
        self._session_id = session_id
        self._mcp_config_path = mcp_config_path
        self._model = model
        self._directive = directive
        self._process: asyncio.subprocess.Process | None = None
        self._state = "idle"

    @staticmethod
    def build_command_args(
        cli_path: str,
        session_id: str,
        mcp_config_path: str,
        model: str = "",
        directive: str = "",
    ) -> list[str]:
        """Build CLI command line arguments."""
        args = [
            cli_path,
            "-p",
            "--input-format", "stream-json",
            "--output-format", "stream-json",
            "--verbose",
            "--include-partial-messages",
            "--session-id", session_id,
            "--mcp-config", mcp_config_path,
            "--dangerously-skip-permissions",
        ]
        if model:
            args.extend(["--model", model])
        if directive:
            args.extend(["--append-system-prompt", directive])
        return args

    async def _ensure_process(self) -> asyncio.subprocess.Process:
        if self._process is not None and self._process.returncode is None:
            return self._process

        args = self.build_command_args(
            cli_path=self._cli_path,
            session_id=self._session_id,
            mcp_config_path=self._mcp_config_path,
            model=self._model,
            directive=self._directive,
        )

        logger.info("Spawning CLI: %s", " ".join(args))

        import sys
        import subprocess
        kwargs: dict[str, Any] = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        self._process = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            **kwargs,
        )
        self._state = "idle"
        return self._process

    async def send_message(self, message: str) -> AsyncGenerator[StreamEvent, None]:
        proc = await self._ensure_process()
        self._state = "processing"

        envelope = json.dumps({
            "type": "user",
            "message": {"role": "user", "content": message},
        }) + "\n"

        try:
            proc.stdin.write(envelope.encode())
            await proc.stdin.drain()
        except (BrokenPipeError, ConnectionResetError):
            self._state = "disconnected"
            yield StreamEvent(
                type=StreamEventType.ERROR,
                code="process_crash",
                message="CLI process terminated unexpectedly",
                retryable=True,
            )
            return

        turn_usage = {"input_tokens": 0, "output_tokens": 0}
        buffer = ""
        while True:
            try:
                chunk = await asyncio.wait_for(
                    proc.stdout.read(4096),
                    timeout=300.0,
                )
            except asyncio.TimeoutError:
                self._state = "idle"
                yield StreamEvent(
                    type=StreamEventType.ERROR,
                    code="timeout",
                    message="Turn timed out after 300s",
                    retryable=False,
                )
                return

            if not chunk:
                self._state = "disconnected"
                yield StreamEvent(
                    type=StreamEventType.ERROR,
                    code="process_exit",
                    message="CLI process exited",
                    retryable=True,
                )
                return

            buffer += chunk.decode(errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                events = parse_ndjson_line(line)
                for event in events:
                    if event.usage:
                        turn_usage["input_tokens"] += event.usage.get("input_tokens", 0)
                        turn_usage["output_tokens"] += event.usage.get("output_tokens", 0)
                        for k in ("cache_read_input_tokens", "cache_creation_input_tokens"):
                            if event.usage.get(k):
                                turn_usage[k] = turn_usage.get(k, 0) + event.usage[k]

                    if event.type == StreamEventType.TURN_COMPLETE:
                        event.usage = turn_usage
                        yield event
                        self._state = "idle"
                        return

                    yield event

    async def cancel(self) -> None:
        if self._process is None or self._process.returncode is not None:
            return

        self._state = "idle"

        try:
            self._process.stdin.close()
        except Exception:
            pass

        try:
            await asyncio.wait_for(self._process.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            self._process.kill()
            await self._process.wait()

        self._process = None

    async def shutdown(self) -> None:
        if self._process is None:
            return
        try:
            self._process.kill()
            await self._process.wait()
        except ProcessLookupError:
            pass
        self._process = None
        self._state = "disconnected"

    def get_state(self) -> str:
        if self._process is None or self._process.returncode is not None:
            return "disconnected"
        return self._state


def generate_mcp_config(project_dir: str | None = None) -> str:
    """Generate a temporary .mcp.json pointing to cortex-mcp."""
    import shutil
    import sys

    cortex_mcp_path = shutil.which("cortex-mcp")
    if cortex_mcp_path:
        command = cortex_mcp_path
        args: list[str] = []
    else:
        command = "uv"
        args = ["run", "cortex-mcp"]

    env: dict[str, str] = {}
    if project_dir:
        env["CORTEX_PROJECT_DIR"] = project_dir

    config = {
        "mcpServers": {
            "cortex-mcp": {
                "command": command,
                "args": args,
                "env": env,
            }
        }
    }

    path = os.path.join(tempfile.gettempdir(), f"cortex-mcp-{uuid.uuid4().hex[:8]}.json")
    with open(path, "w") as f:
        json.dump(config, f)
    return path
