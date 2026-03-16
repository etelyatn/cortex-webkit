# src/cortex_webkit/api/settings.py
"""GET/PUT /api/settings."""

from fastapi import APIRouter, Depends, Request

from cortex_webkit.auth import verify_token
from cortex_webkit.models.commands import SettingsResponse, SettingsUpdate

router = APIRouter()


# In-memory settings (lives in app.state, initialized in lifespan)
_defaults = {
    "model": "claude-sonnet-4-6",
    "effort": "medium",
    "workflow": "direct",
    "access_mode": "full",
    "directive": "",
}


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(request: Request, _=Depends(verify_token)):
    settings = getattr(request.app.state, "settings", dict(_defaults))
    config = request.app.state.config
    return SettingsResponse(
        **settings,
        max_sessions=config.max_sessions,
    )


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    body: SettingsUpdate,
    request: Request,
    _=Depends(verify_token),
):
    if not hasattr(request.app.state, "settings"):
        request.app.state.settings = dict(_defaults)

    updates = body.model_dump(exclude_none=True)
    request.app.state.settings.update(updates)

    config = request.app.state.config
    return SettingsResponse(
        **request.app.state.settings,
        max_sessions=config.max_sessions,
    )
