# tests/test_api_settings.py
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from cortex_webkit.app import create_app
from cortex_webkit.config import CortexWebConfig


@pytest.fixture
def client():
    config = CortexWebConfig(auth_token="test-token")
    app = create_app(config)
    # Inject mocks (lifespan doesn't run in TestClient)
    from unittest.mock import AsyncMock
    mock_ue = MagicMock()
    mock_ue.get_status = AsyncMock(return_value={"connected": False})
    mock_ue.get_capabilities = AsyncMock(return_value={"domains": []})
    app.state.ue_connection = mock_ue
    app.state.session_manager = MagicMock()
    app.state.settings = {
        "model": "claude-sonnet-4-6",
        "effort": "medium",
        "workflow": "direct",
        "access_mode": "full",
        "directive": "",
    }
    return TestClient(app)


AUTH = {"Authorization": "Bearer test-token"}


def test_get_default_settings(client):
    resp = client.get("/api/settings", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["model"] == "claude-sonnet-4-6"
    assert data["effort"] == "medium"
    assert data["max_sessions"] == 10


def test_update_settings(client):
    resp = client.put("/api/settings", json={"model": "claude-opus-4-6", "effort": "high"}, headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["model"] == "claude-opus-4-6"
    assert resp.json()["effort"] == "high"

    # Verify persistence within session
    resp = client.get("/api/settings", headers=AUTH)
    assert resp.json()["model"] == "claude-opus-4-6"


def test_settings_no_auth(client):
    resp = client.get("/api/settings")
    assert resp.status_code == 401
