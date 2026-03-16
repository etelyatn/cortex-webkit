# tests/test_api_status.py
import pytest
from unittest.mock import MagicMock, patch
from cortex_webkit.services.unreal import AsyncUEConnection


@pytest.mark.asyncio
async def test_async_send_command():
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"success": True, "data": {"items": []}}
    mock_conn.connected = True

    with patch.object(AsyncUEConnection, "_create_connection", return_value=mock_conn):
        ue = AsyncUEConnection()
        ue._conn = mock_conn
        result = await ue.send_command("data.list_datatables", {"filter": "*"})
        assert result["success"] is True
        mock_conn.send_command.assert_called_once()


@pytest.mark.asyncio
async def test_get_status_disconnected():
    ue = AsyncUEConnection()
    status = await ue.get_status()
    assert status["connected"] is False


from fastapi.testclient import TestClient
from cortex_webkit.app import create_app
from cortex_webkit.config import CortexWebConfig
from unittest.mock import AsyncMock


@pytest.fixture
def client():
    config = CortexWebConfig(auth_token="test-token")
    app = create_app(config)
    ue = AsyncMock()
    ue.get_status.return_value = {"connected": False}
    ue.get_capabilities.return_value = {"domains": []}
    app.state.ue_connection = ue
    return TestClient(app, raise_server_exceptions=True)


def test_status_endpoint(client):
    resp = client.get("/api/status", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 200
    assert "connected" in resp.json()


def test_capabilities_endpoint(client):
    resp = client.get("/api/capabilities", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 200


def test_status_no_auth(client):
    resp = client.get("/api/status")
    assert resp.status_code == 401
