# tests/test_auth.py
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from cortex_webkit.auth import verify_token
from cortex_webkit.config import CortexWebConfig


def _make_app(config: CortexWebConfig) -> FastAPI:
    app = FastAPI()
    app.state.config = config

    @app.get("/protected")
    async def protected(token: str = Depends(verify_token)):
        return {"ok": True}

    return app


def test_valid_bearer_token():
    config = CortexWebConfig(auth_token="secret123")
    client = TestClient(_make_app(config))
    resp = client.get("/protected", headers={"Authorization": "Bearer secret123"})
    assert resp.status_code == 200


def test_missing_token():
    config = CortexWebConfig(auth_token="secret123")
    client = TestClient(_make_app(config))
    resp = client.get("/protected")
    assert resp.status_code == 401


def test_wrong_token():
    config = CortexWebConfig(auth_token="secret123")
    client = TestClient(_make_app(config))
    resp = client.get("/protected", headers={"Authorization": "Bearer wrong"})
    assert resp.status_code == 403
