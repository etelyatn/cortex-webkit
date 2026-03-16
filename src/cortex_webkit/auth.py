# src/cortex_webkit/auth.py
"""Bearer token authentication."""

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer_scheme = HTTPBearer(auto_error=False)


async def verify_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    """FastAPI dependency — reads auth token from app.state.config, validates Bearer header."""
    config = request.app.state.config
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    if credentials.credentials != config.auth_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    return credentials.credentials


# Note: WebSocket auth is handled inline in WS handlers (not as a Depends)
# because HTTPException does not work with WebSocket endpoints in FastAPI.
# Handlers should check `token != config.auth_token` and call `websocket.close(4003)`.
