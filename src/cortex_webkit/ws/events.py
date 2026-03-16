# src/cortex_webkit/ws/events.py
"""WebSocket /ws/events — UE connection state and notifications."""

import asyncio
import logging
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/events")
async def ws_events(
    websocket: WebSocket,
    token: str = Query(...),
):
    config = websocket.app.state.config

    if token != config.auth_token:
        await websocket.close(code=4003, reason="Invalid token")
        return

    await websocket.accept()

    try:
        # Poll UE connection status every 3 seconds
        last_status = None
        while True:
            ue = websocket.app.state.ue_connection
            status = await ue.get_status()

            # Only send on change
            if status != last_status:
                await websocket.send_json({
                    "type": "ue_status",
                    **status,
                })
                last_status = status

            # Also check for incoming client messages (cancel, etc.)
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=3.0)
            except asyncio.TimeoutError:
                pass  # Normal — just poll again

    except WebSocketDisconnect:
        logger.debug("Events WebSocket disconnected")
