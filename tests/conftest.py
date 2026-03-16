# tests/conftest.py
"""Shared test fixtures."""

import pytest
from cortex_webkit.config import CortexWebConfig


@pytest.fixture
def config():
    return CortexWebConfig(auth_token="test-token-12345678901234567890")
