# tests/test_api_commands.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from cortex_webkit.app import create_app
from cortex_webkit.config import CortexWebConfig


@pytest.fixture
def client():
    config = CortexWebConfig(auth_token="test-token")
    app = create_app(config)
    # Inject mock UE connection (lifespan doesn't run in TestClient)
    from unittest.mock import AsyncMock as AM
    mock_ue = MagicMock()
    mock_ue.send_command = AM(return_value={"success": True, "data": {"items": []}})
    app.state.ue_connection = mock_ue
    app.state.session_manager = MagicMock()
    app.state.settings = {"model": "claude-sonnet-4-6", "effort": "medium", "workflow": "direct", "access_mode": "full", "directive": ""}
    return TestClient(app)


AUTH = {"Authorization": "Bearer test-token"}


def test_execute_command(client):
    resp = client.post(
        "/api/commands",
        json={"domain": "data", "command": "list_datatables", "params": {}},
        headers=AUTH,
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_command_no_auth(client):
    resp = client.post("/api/commands", json={"domain": "data", "command": "list_datatables"})
    assert resp.status_code == 401


def test_command_validation_error(client):
    resp = client.post("/api/commands", json={}, headers=AUTH)
    assert resp.status_code == 422
