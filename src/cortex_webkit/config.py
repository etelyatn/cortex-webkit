# src/cortex_webkit/config.py
"""Centralized configuration via pydantic-settings."""

import secrets
import shutil
from pydantic_settings import BaseSettings


def _auto_detect_cli() -> str | None:
    """Find claude CLI on PATH."""
    return shutil.which("claude")


class CortexWebConfig(BaseSettings):
    model_config = {"env_prefix": "CORTEX_"}

    # Server
    web_port: int = 8080
    web_host: str = "127.0.0.1"

    # Auth
    auth_token: str = ""

    # CLI
    cli_path: str | None = None

    # UE
    ue_project_dir: str | None = None

    # Limits
    max_sessions: int = 10

    _token_auto_generated: bool = False

    def model_post_init(self, __context) -> None:
        if not self.auth_token:
            self.auth_token = secrets.token_urlsafe(32)
            self._token_auto_generated = True
        if self.cli_path is None:
            self.cli_path = _auto_detect_cli()

    @property
    def port(self) -> int:
        return self.web_port

    @property
    def host(self) -> str:
        return self.web_host

    @property
    def is_localhost(self) -> bool:
        return self.web_host in ("127.0.0.1", "localhost", "::1")

    @property
    def should_embed_token(self) -> bool:
        """Only embed auto-generated tokens for localhost binding."""
        return self.is_localhost and self._token_auto_generated
