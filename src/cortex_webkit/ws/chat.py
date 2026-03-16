# src/cortex_webkit/ws/chat.py
"""WebSocket /ws/chat — streaming chat via CLI subprocess."""

import asyncio
import json
import logging
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from cortex_webkit.backends.cli import CliBackend, generate_mcp_config
from cortex_webkit.events import StreamEvent, StreamEventType

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/chat")
async def ws_chat(
    websocket: WebSocket,
    session_id: str = Query(...),
    token: str = Query(...),
):
    config = websocket.app.state.config

    # Auth
    if token != config.auth_token:
        await websocket.close(code=4003, reason="Invalid token")
        return

    await websocket.accept()

    # Find or create session
    mgr = websocket.app.state.session_manager
    session = mgr.get_session(session_id)
    if session is None:
        await websocket.send_json({"type": "error", "code": "session_not_found", "message": "Session not found", "retryable": False})
        await websocket.close(code=4004)
        return

    # Attach WebSocket to session
    session.websocket = websocket

    # Replay buffered events on reconnect
    buffered = session.get_buffered_events()
    if buffered:
        await websocket.send_json({"type": "replay_start", "event_count": len(buffered)})
        for event in buffered:
            await websocket.send_json(event)
        await websocket.send_json({"type": "replay_end"})

    # Send session info
    await websocket.send_json({
        "type": "session_info",
        "backend": "cli",
        "session_id": session_id,
        "model": session.model,
    })

    # Ensure CLI backend exists
    if session.backend is None:
        mcp_config_path = generate_mcp_config(config.ue_project_dir)
        session.backend = CliBackend(
            cli_path=config.cli_path or "claude",
            session_id=session_id,
            mcp_config_path=mcp_config_path,
            model=session.model,
            directive=session.directive,
        )

    async def _stream_turn(content: str):
        """Stream a full turn, sending events to WebSocket and buffering."""
        async for event in session.backend.send_message(content):
            event_dict = event.to_dict()
            session.buffer_event(event_dict)
            await websocket.send_json(event_dict)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "code": "invalid_json", "message": "Invalid JSON", "retryable": False})
                continue

            msg_type = msg.get("type")

            if msg_type == "user_message":
                content = msg.get("content", "")
                if not content:
                    continue

                # Reject if already processing
                if session.backend.get_state() == "processing":
                    await websocket.send_json({"type": "error", "code": "busy", "message": "Turn already in progress", "retryable": False})
                    continue

                session.increment_messages()
                await websocket.send_json({"type": "turn_started"})

                stream_task = asyncio.create_task(_stream_turn(content))

                try:
                    while not stream_task.done():
                        try:
                            cancel_raw = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
                            cancel_msg = json.loads(cancel_raw)
                            if cancel_msg.get("type") == "cancel":
                                await session.backend.cancel()
                                stream_task.cancel()
                                try:
                                    await stream_task
                                except asyncio.CancelledError:
                                    pass
                                break
                        except asyncio.TimeoutError:
                            continue
                except Exception:
                    if not stream_task.done():
                        stream_task.cancel()
                    raise

                if not stream_task.done():
                    await stream_task

            elif msg_type == "cancel":
                if session.backend:
                    await session.backend.cancel()

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for session %s", session_id)
        session.websocket = None
