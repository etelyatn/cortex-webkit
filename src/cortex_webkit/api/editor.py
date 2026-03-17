# src/cortex_webkit/api/editor.py
"""POST /api/editor/start|stop|restart and GET /api/editor/status."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from cortex_webkit.auth import verify_token

router = APIRouter()


@router.post("/editor/start")
async def start_editor(request: Request, _=Depends(verify_token)):
    mgr = request.app.state.editor_lifecycle
    try:
        result = await mgr.start()
        return JSONResponse(status_code=202, content=result)
    except ValueError as e:
        return JSONResponse(
            status_code=409,
            content={"error": str(e), "current_state": mgr.state},
        )


@router.post("/editor/stop")
async def stop_editor(request: Request, _=Depends(verify_token)):
    mgr = request.app.state.editor_lifecycle
    try:
        result = await mgr.stop()
        return JSONResponse(status_code=202, content=result)
    except ValueError as e:
        return JSONResponse(
            status_code=409,
            content={"error": str(e), "current_state": mgr.state},
        )


@router.post("/editor/restart")
async def restart_editor(request: Request, _=Depends(verify_token)):
    mgr = request.app.state.editor_lifecycle
    try:
        result = await mgr.restart()
        return JSONResponse(status_code=202, content=result)
    except ValueError as e:
        return JSONResponse(
            status_code=409,
            content={"error": str(e), "current_state": mgr.state},
        )


@router.get("/editor/status")
async def get_editor_status(request: Request, _=Depends(verify_token)):
    mgr = request.app.state.editor_lifecycle
    return mgr.get_status()
