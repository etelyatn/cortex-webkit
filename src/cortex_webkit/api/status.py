# src/cortex_webkit/api/status.py
"""GET /api/status and /api/capabilities."""

from fastapi import APIRouter, Depends, Request

from cortex_webkit.auth import verify_token

router = APIRouter()


@router.get("/status")
async def get_status(request: Request, _=Depends(verify_token)):
    ue = request.app.state.ue_connection
    return await ue.get_status()


@router.get("/capabilities")
async def get_capabilities(request: Request, _=Depends(verify_token)):
    ue = request.app.state.ue_connection
    return await ue.get_capabilities()
