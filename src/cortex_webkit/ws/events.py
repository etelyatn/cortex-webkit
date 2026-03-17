# src/cortex_webkit/ws/events.py
"""WebSocket /ws/events — UE connection state and notifications."""

import asyncio
import logging
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()

_BUSY_STATES = {"starting", "stopping", "restarting"}


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

    event_bus = websocket.app.state.event_bus
    ue = websocket.app.state.ue_connection
    lifecycle = websocket.app.state.editor_lifecycle

    queue = event_bus.subscribe()
    try:
        last_ue_status = None
        while True:
            # Wait up to 3s for a lifecycle event
            try:
                event = await asyncio.wait_for(queue.get(), timeout=3.0)
                await websocket.send_json(event)
                # Drain any additional queued events
                while not queue.empty():
                    await websocket.send_json(await queue.get())
            except asyncio.TimeoutError:
                pass  # Time to poll UE status

            # Poll UE status, suppress during lifecycle transitions
            if lifecycle.state not in _BUSY_STATES:
                ue_status = await ue.get_status()
                if ue_status != last_ue_status:
                    await websocket.send_json({"type": "ue_status", **ue_status})
                    last_ue_status = ue_status

    except WebSocketDisconnect:
        logger.debug("Events WebSocket disconnected")
    finally:
        event_bus.unsubscribe(queue)
