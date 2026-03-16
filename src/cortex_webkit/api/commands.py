# src/cortex_webkit/api/commands.py
"""POST /api/commands — execute UE commands via cortex-mcp."""

import json
import time
import pathlib
import fnmatch
from fastapi import APIRouter, Depends, Request

from cortex_webkit.auth import verify_token
from cortex_webkit.models.commands import CommandRequest, CommandResponse

router = APIRouter()

# Load risk classification
_risk_file = pathlib.Path(__file__).parent.parent / "data" / "command_risk.json"
_risk_map: dict[str, list[str]] = {}
if _risk_file.exists():
    _risk_map = json.loads(_risk_file.read_text())


def classify_risk(domain: str, command: str) -> str:
    """Classify command risk level: destructive, mutating, or read-only."""
    full = f"{domain}.{command}"
    for level in ("destructive", "mutating"):
        for pattern in _risk_map.get(level, []):
            if fnmatch.fnmatch(full, pattern):
                return level
    return "read-only"


@router.post("/commands", response_model=CommandResponse)
async def execute_command(
    body: CommandRequest,
    request: Request,
    _=Depends(verify_token),
):
    ue = request.app.state.ue_connection
    full_command = f"{body.domain}.{body.command}"

    # Read-only mode enforcement
    settings = getattr(request.app.state, "settings", {})
    if settings.get("access_mode") == "read-only":
        risk = classify_risk(body.domain, body.command)
        if risk != "read-only":
            return CommandResponse(
                success=False,
                error=f"Read-only mode: {risk} command '{full_command}' blocked",
            )

    # Long-poll timeout for deferred commands (PIE/QA) — up to 35s
    params = dict(body.params) if body.params else {}
    timeout = params.pop("_timeout", None)
    effective_timeout = float(timeout) if timeout else 35.0

    start = time.monotonic()
    result = await ue.send_command(full_command, params or None, timeout=effective_timeout)
    duration_ms = int((time.monotonic() - start) * 1000)

    return CommandResponse(
        success=result.get("success", False),
        data=result.get("data"),
        error=result.get("error"),
        duration_ms=duration_ms,
    )
