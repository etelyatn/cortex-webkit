# tests/test_api_sessions.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from cortex_webkit.app import create_app
from cortex_webkit.config import CortexWebConfig
from cortex_webkit.session import SessionManager


@pytest.fixture
def client():
    config = CortexWebConfig(auth_token="test-token")
    app = create_app(config)
    # Inject real SessionManager + mock UE connection
    mock_ue = MagicMock()
    mock_ue.get_status = AsyncMock(return_value={"connected": False})
    mock_ue.get_capabilities = AsyncMock(return_value={"domains": []})
    app.state.ue_connection = mock_ue
    app.state.session_manager = SessionManager(config=config)
    app.state.settings = {"model": "claude-sonnet-4-6", "effort": "medium", "workflow": "direct", "access_mode": "full", "directive": ""}
    return TestClient(app)


AUTH = {"Authorization": "Bearer test-token"}


def test_create_session(client):
    resp = client.post("/api/sessions", json={}, headers=AUTH)
    assert resp.status_code == 200
    assert "id" in resp.json()


def test_list_sessions(client):
    client.post("/api/sessions", json={}, headers=AUTH)
    resp = client.get("/api/sessions", headers=AUTH)
    assert resp.status_code == 200
    assert len(resp.json()["sessions"]) >= 1


def test_get_session(client):
    create_resp = client.post("/api/sessions", json={}, headers=AUTH)
    session_id = create_resp.json()["id"]

    resp = client.get(f"/api/sessions/{session_id}", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["id"] == session_id


def test_delete_session(client):
    create_resp = client.post("/api/sessions", json={}, headers=AUTH)
    session_id = create_resp.json()["id"]

    resp = client.delete(f"/api/sessions/{session_id}", headers=AUTH)
    assert resp.status_code == 200

    resp = client.get(f"/api/sessions/{session_id}", headers=AUTH)
    assert resp.status_code == 404


def test_get_nonexistent_session(client):
    resp = client.get("/api/sessions/nonexistent", headers=AUTH)
    assert resp.status_code == 404
