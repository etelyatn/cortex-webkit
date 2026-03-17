# scripts/mock_server.py
"""Mock backend for frontend development without UE or Claude CLI."""

import asyncio
import json
import time
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Cortex WebKit Mock Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MOCK_TOKEN = "mock-token"

# --- REST Endpoints ---

@app.get("/api/status")
async def status():
    return {"connected": True, "port": 8742, "pid": 12345, "project": "CortexSandbox"}


@app.get("/api/capabilities")
async def capabilities():
    return {
        "domains": [
            {
                "name": "data",
                "description": "Data domain",
                "version": "1.0.0",
                "commands": [
                    {"name": "list_datatables", "description": "List all DataTables", "params": [
                        {"name": "filter", "type": "string", "description": "Wildcard filter"},
                        {"name": "limit", "type": "integer", "default": 100},
                    ]},
                    {"name": "get_datatable", "description": "Get DataTable details", "params": [
                        {"name": "path", "type": "string", "required": True},
                    ]},
                ],
            },
            {
                "name": "blueprint",
                "description": "Blueprint domain",
                "version": "1.0.0",
                "commands": [
                    {"name": "compile", "description": "Compile a Blueprint", "params": [
                        {"name": "path", "type": "string", "required": True},
                    ]},
                    {"name": "list_blueprints", "description": "List Blueprints", "params": [
                        {"name": "filter", "type": "string"},
                    ]},
                ],
            },
        ]
    }


@app.post("/api/commands")
async def execute_command(body: dict):
    await asyncio.sleep(0.1)  # Simulate latency
    return {
        "success": True,
        "data": {"items": [{"name": "MockTable1"}, {"name": "MockTable2"}], "count": 2},
        "duration_ms": 120,
    }


_sessions: dict[str, dict] = {}

@app.post("/api/sessions")
async def create_session(body: dict | None = None):
    sid = str(uuid.uuid4())
    _sessions[sid] = {"id": sid, "backend": "cli", "model": "claude-sonnet-4-6", "state": "idle", "message_count": 0}
    return _sessions[sid]


@app.get("/api/sessions")
async def list_sessions():
    return {"sessions": list(_sessions.values())}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    return _sessions.get(session_id, {"error": "not found"})


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    _sessions.pop(session_id, None)
    return {"deleted": True}


@app.get("/api/settings")
async def get_settings():
    return {"model": "claude-sonnet-4-6", "effort": "medium", "workflow": "direct", "access_mode": "full", "directive": "", "max_sessions": 10}


@app.put("/api/settings")
async def update_settings(body: dict):
    return {**body, "max_sessions": 10}


# --- WebSocket: Chat ---

@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket, session_id: str = Query(""), token: str = Query("")):
    await websocket.accept()
    await websocket.send_json({"type": "session_info", "backend": "cli", "session_id": session_id, "model": "claude-sonnet-4-6"})

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "user_message":
                content = msg.get("content", "")

                # Simulate streaming response
                await websocket.send_json({"type": "turn_started"})

                response = f"I received your message: \"{content}\"\n\nHere's a mock response with **markdown** and `code`."
                for i in range(0, len(response), 5):
                    chunk = response[i : i + 5]
                    await websocket.send_json({"type": "text_delta", "text": chunk})
                    await asyncio.sleep(0.02)

                # Simulate a tool call with streaming input
                tool_id = f"tool_{uuid.uuid4().hex[:8]}"
                await websocket.send_json({"type": "tool_call_start", "tool_use_id": tool_id, "name": "data.list_datatables"})
                await asyncio.sleep(0.1)
                await websocket.send_json({"type": "tool_input_delta", "tool_use_id": tool_id, "partial_json": '{"filter":'})
                await asyncio.sleep(0.1)
                await websocket.send_json({"type": "tool_input_delta", "tool_use_id": tool_id, "partial_json": ' "Enemy*"}'})
                await asyncio.sleep(0.1)
                await websocket.send_json({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "result": {"items": [{"name": "EnemyStats"}, {"name": "WeaponData"}], "count": 2},
                    "is_error": False,
                    "duration_ms": 120,
                })

                await websocket.send_json({
                    "type": "turn_complete",
                    "usage": {"input_tokens": 150, "output_tokens": 75},
                })

    except WebSocketDisconnect:
        pass


# --- WebSocket: Events ---

@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket, token: str = Query("")):
    await websocket.accept()
    while True:
        await websocket.send_json({"type": "ue_status", "connected": True, "port": 8742, "pid": 12345, "project": "CortexSandbox"})
        await asyncio.sleep(3)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
