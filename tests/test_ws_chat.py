# tests/test_ws_chat.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from cortex_webkit.app import create_app
from cortex_webkit.config import CortexWebConfig
from cortex_webkit.session import SessionManager


@pytest.fixture
def client():
    config = CortexWebConfig(auth_token="test-token", cli_path="echo")
    app = create_app(config)
    mock_ue = MagicMock()
    mock_ue.get_status = AsyncMock(return_value={"connected": False})
    app.state.ue_connection = mock_ue
    app.state.session_manager = SessionManager(config=config)
    app.state.settings = {"model": "claude-sonnet-4-6", "effort": "medium", "workflow": "direct", "access_mode": "full", "directive": ""}
    return TestClient(app)


AUTH = {"Authorization": "Bearer test-token"}


def test_ws_chat_auth_rejected(client):
    """Invalid token should close connection with 4003."""
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/chat?session_id=test&token=wrong") as ws:
            pass


def test_ws_chat_session_not_found(client):
    """Non-existent session should send error and close."""
    with client.websocket_connect("/ws/chat?session_id=nonexistent&token=test-token") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert msg["code"] == "session_not_found"


def test_ws_chat_session_info_on_connect(client):
    """Valid session should receive session_info on connect."""
    resp = client.post("/api/sessions", json={}, headers=AUTH)
    session_id = resp.json()["id"]

    with client.websocket_connect(f"/ws/chat?session_id={session_id}&token=test-token") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "session_info"
        assert msg["session_id"] == session_id


def test_ws_chat_replay_on_reconnect(client):
    """Buffered events should be replayed on reconnect."""
    resp = client.post("/api/sessions", json={}, headers=AUTH)
    session_id = resp.json()["id"]

    # Buffer some events manually
    mgr = client.app.state.session_manager
    session = mgr.get_session(session_id)
    session.buffer_event({"type": "text_delta", "text": "hello"})
    session.buffer_event({"type": "text_delta", "text": " world"})

    with client.websocket_connect(f"/ws/chat?session_id={session_id}&token=test-token") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "replay_start"
        assert msg["event_count"] == 2
        ws.receive_json()  # text_delta 1
        ws.receive_json()  # text_delta 2
        msg = ws.receive_json()
        assert msg["type"] == "replay_end"
