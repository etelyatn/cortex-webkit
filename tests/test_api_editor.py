# tests/test_api_editor.py
"""Tests for /api/editor/* lifecycle endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cortex_webkit.config import CortexWebConfig
from cortex_webkit.api.editor import router as editor_router


def _make_app(config: CortexWebConfig, lifecycle_mgr) -> FastAPI:
    """Build a minimal FastAPI app with only the editor router — avoids StaticFiles ordering issues."""
    app = FastAPI()
    app.state.config = config
    app.state.editor_lifecycle = lifecycle_mgr
    app.include_router(editor_router, prefix="/api")
    return app


@pytest.fixture
def mock_lifecycle():
    """Mock EditorLifecycleManager."""
    mgr = MagicMock()
    mgr.state = "disconnected"
    mgr.start = AsyncMock(return_value={"state": "starting", "started_at": 1700000000})
    mgr.stop = AsyncMock(return_value={"state": "stopping"})
    mgr.restart = AsyncMock(return_value={"state": "restarting", "started_at": 1700000000})
    mgr.get_status = MagicMock(return_value={
        "state": "disconnected",
        "started_at": None,
        "error": None,
        "port": None,
        "pid": None,
        "project": None,
    })
    return mgr


@pytest.fixture
def client(mock_lifecycle):
    config = CortexWebConfig(auth_token="test-token")
    app = _make_app(config, mock_lifecycle)
    return TestClient(app, raise_server_exceptions=True)


AUTH = {"Authorization": "Bearer test-token"}


# --- POST /api/editor/start ---

def test_start_returns_202(client):
    resp = client.post("/api/editor/start", headers=AUTH)
    assert resp.status_code == 202
    body = resp.json()
    assert body["state"] == "starting"
    assert "started_at" in body


def test_start_409_when_invalid_state(client, mock_lifecycle):
    mock_lifecycle.start = AsyncMock(side_effect=ValueError("Cannot start editor while stopping"))
    mock_lifecycle.state = "stopping"
    resp = client.post("/api/editor/start", headers=AUTH)
    assert resp.status_code == 409
    body = resp.json()
    assert "error" in body
    assert body["current_state"] == "stopping"


def test_start_requires_auth(client):
    resp = client.post("/api/editor/start")
    assert resp.status_code == 401


# --- POST /api/editor/stop ---

def test_stop_returns_202(client, mock_lifecycle):
    mock_lifecycle.state = "connected"
    resp = client.post("/api/editor/stop", headers=AUTH)
    assert resp.status_code == 202
    body = resp.json()
    assert body["state"] == "stopping"


def test_stop_409_when_invalid_state(client, mock_lifecycle):
    mock_lifecycle.stop = AsyncMock(side_effect=ValueError("Cannot stop editor while disconnected"))
    mock_lifecycle.state = "disconnected"
    resp = client.post("/api/editor/stop", headers=AUTH)
    assert resp.status_code == 409
    body = resp.json()
    assert "error" in body
    assert body["current_state"] == "disconnected"


def test_stop_requires_auth(client):
    resp = client.post("/api/editor/stop")
    assert resp.status_code == 401


# --- POST /api/editor/restart ---

def test_restart_returns_202(client, mock_lifecycle):
    mock_lifecycle.state = "connected"
    resp = client.post("/api/editor/restart", headers=AUTH)
    assert resp.status_code == 202
    body = resp.json()
    assert body["state"] == "restarting"
    assert "started_at" in body


def test_restart_409_when_invalid_state(client, mock_lifecycle):
    mock_lifecycle.restart = AsyncMock(side_effect=ValueError("Cannot restart editor while disconnected"))
    mock_lifecycle.state = "disconnected"
    resp = client.post("/api/editor/restart", headers=AUTH)
    assert resp.status_code == 409
    body = resp.json()
    assert "error" in body
    assert body["current_state"] == "disconnected"


def test_restart_requires_auth(client):
    resp = client.post("/api/editor/restart")
    assert resp.status_code == 401


# --- GET /api/editor/status ---

def test_status_returns_snapshot(client):
    resp = client.get("/api/editor/status", headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert "state" in body
    assert "started_at" in body
    assert "error" in body
    assert "port" in body
    assert "pid" in body
    assert "project" in body


def test_status_requires_auth(client):
    resp = client.get("/api/editor/status")
    assert resp.status_code == 401
