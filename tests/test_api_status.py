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
