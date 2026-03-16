# tests/test_config.py
import os
import pytest
from cortex_webkit.config import CortexWebConfig


def test_default_config():
    config = CortexWebConfig()
    assert config.port == 8080
    assert config.host == "127.0.0.1"
    assert config.max_sessions == 10
    assert config.auth_token is not None  # auto-generated
    assert len(config.auth_token) >= 32


def test_env_override(monkeypatch):
    monkeypatch.setenv("CORTEX_WEB_PORT", "9090")
    monkeypatch.setenv("CORTEX_AUTH_TOKEN", "my-secret")
    config = CortexWebConfig()
    assert config.port == 9090
    assert config.auth_token == "my-secret"


def test_localhost_auto_token():
    config = CortexWebConfig()
    assert config.is_localhost is True
    assert config.should_embed_token is True


def test_remote_no_auto_token(monkeypatch):
    monkeypatch.setenv("CORTEX_WEB_HOST", "0.0.0.0")
    monkeypatch.setenv("CORTEX_AUTH_TOKEN", "explicit-token")
    config = CortexWebConfig()
    assert config.is_localhost is False
    assert config.should_embed_token is False
